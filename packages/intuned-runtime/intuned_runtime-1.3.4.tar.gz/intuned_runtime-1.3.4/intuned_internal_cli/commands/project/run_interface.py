import asyncio
import os
import signal
import socket
import sys
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from typing import cast
from typing import Literal

from pydantic import Field
from pydantic import ValidationError

from intuned_internal_cli.utils.wrapper import internal_cli_command
from runtime.backend_functions import get_auth_session_parameters
from runtime.context import IntunedContext
from runtime.errors.run_api_errors import ApiNotFoundError
from runtime.errors.run_api_errors import InternalInvalidInputError
from runtime.errors.run_api_errors import RunApiError
from runtime.run.run_api import import_function_from_api_dir
from runtime.run.run_api import run_api
from runtime.types.run_types import CamelBaseModel
from runtime.types.run_types import RunApiParameters
from runtime.types.run_types import RunAutomationSuccessResult

from ...utils.unix_socket import JSONUnixSocket

throttle_time = 60


class StartMessage(CamelBaseModel):
    type: Literal["start"] = "start"
    parameters: RunApiParameters


class NextMessageParameters(CamelBaseModel):
    value: str


class NextMessage(CamelBaseModel):
    type: Literal["next"] = "next"
    parameters: NextMessageParameters


class AbortMessage(CamelBaseModel):
    type: Literal["abort"] = "abort"
    parameters: dict[str, Any] = {}


class TokenUpdateMessageParameters(CamelBaseModel):
    functionsToken: str


class TokenUpdateMessage(CamelBaseModel):
    type: Literal["tokenUpdate"] = "tokenUpdate"
    parameters: TokenUpdateMessageParameters


class PingMessage(CamelBaseModel):
    type: Literal["ping"] = "ping"
    parameters: dict[str, Any] = {}


Message = StartMessage | NextMessage | AbortMessage | TokenUpdateMessage | PingMessage


class MessageWrapper(CamelBaseModel):
    message: Message = Field(
        discriminator="type",
    )


@internal_cli_command
async def project__run_interface(
    socket_path: str,
    *,
    jsonl: bool = False,
):
    """
    Runs the current project. Project must contain an "api" directory with API functions.

    Args:
        socket_path (str): Path to the socket file.
        jsonl (bool, optional): Use a JSONL client instead of socket. Defaults to False.

    """

    # create unix socket client of type socket.socket
    if not socket_path:
        raise Exception("socket_path is required")

    timeout_timestamp = time.time()
    client = SocketClient(socket_path) if not jsonl else JSONLFileClient(socket_path)
    connected = await client.connect()
    if not connected:
        raise Exception("Failed to connect to UDAS")

    run_api_task: asyncio.Task[RunAutomationSuccessResult] | None = cast(
        asyncio.Task[RunAutomationSuccessResult] | None, None
    )

    def done(exitCode: int = 0):
        client.close()
        loop.remove_signal_handler(signal.SIGTERM)
        loop.remove_signal_handler(signal.SIGINT)
        sys.exit(exitCode)

    def interrupt_signal_handler():
        async def _impl():
            if run_api_task is not None:
                run_api_task.cancel()
            # wait for graceful exit, if not, force exit
            await asyncio.sleep(60)
            done(1)

        asyncio.create_task(_impl())

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, interrupt_signal_handler)
    loop.add_signal_handler(signal.SIGINT, interrupt_signal_handler)

    messages_generator = client.receive_messages()

    async def receive_messages():
        message: Any = None
        try:
            message = await messages_generator.__anext__()
            validated_message = MessageWrapper(message=message)
            return validated_message.message
        except StopAsyncIteration:
            return None
        except ValidationError as e:
            print("Validation error", message, e)
            return InternalInvalidInputError(
                "Invalid input", {key: str(value) for key, value in e.__dict__.items() if not key.startswith("_")}
            )

    run_api_task: asyncio.Task[RunAutomationSuccessResult] | None = cast(
        asyncio.Task[RunAutomationSuccessResult] | None, None
    )

    def import_function(file_path: str, automation_name: str | None = None):
        return import_function_from_api_dir(
            automation_function_name=automation_name, file_path=file_path, base_dir=os.getcwd()
        )

    async def handle_message(message: Message):
        nonlocal run_api_task
        if message.type == "start":

            async def extend_timeout():
                nonlocal timeout_timestamp
                if time.time() - timeout_timestamp < throttle_time:
                    return
                timeout_timestamp = time.time()
                await client.send_message({"type": "extend"})

            IntunedContext.current().functions_token = message.parameters.functions_token
            IntunedContext.current().extend_timeout = extend_timeout
            IntunedContext.current().get_auth_session_parameters = get_auth_session_parameters
            IntunedContext.current().run_context = message.parameters.context
            run_api_task = asyncio.create_task(
                run_api(
                    message.parameters,
                    import_function=import_function,
                ),
            )
            return

        elif message.type == "abort":
            if run_api_task is not None:
                run_api_task.cancel()
            return
        elif message.type == "tokenUpdate":
            IntunedContext.current().functions_token = message.parameters.functionsToken
            return
        else:
            # todo handle this case?
            raise NotImplementedError()

    receive_messages_task = asyncio.create_task(receive_messages())

    while True:
        tasks: list[asyncio.Task[Message | RunApiError | None] | asyncio.Task[RunAutomationSuccessResult]] = [
            receive_messages_task,
        ]
        if run_api_task is not None:
            tasks.append(run_api_task)
        message_or_result, _ = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )
        if message_or_result.pop() == receive_messages_task:
            message = await receive_messages_task
            if message is None:
                if run_api_task is not None and not run_api_task.done():
                    run_api_task.cancel()
                break
            if isinstance(message, RunApiError):
                await client.send_message({"type": "done", "success": False, "result": message.json})
                break
            if message.type == "ping":
                api_files = await get_python_files_from_dir(Path() / "api")
                apis = [f'api/{str(p.with_suffix("").as_posix())}' for p in api_files]

                for api in [*apis, "auth-sessions/create", "auth-sessions/check"]:
                    try:
                        import_function(api)
                    except ApiNotFoundError:
                        pass
                await client.send_message({"type": "pong"})
                break
            await handle_message(message)
            receive_messages_task = asyncio.create_task(receive_messages())
            continue

        if run_api_task is None:
            continue

        try:
            result = await run_api_task  # type: ignore
            await client.send_message(
                {
                    "type": "done",
                    "success": True,
                    "result": {
                        "result": result.result,
                        "session": result.session.model_dump(by_alias=True) if result.session else None,
                        "extendedPayloads": [
                            {
                                "api": payload.api_name,
                                "parameters": payload.parameters,
                            }
                            for payload in result.payload_to_append
                        ]
                        if result.payload_to_append is not None
                        else None,
                    },
                }
            )
        except RunApiError as e:
            print("Error", e)
            await client.send_message({"type": "done", "success": False, "result": e.json})
        except asyncio.CancelledError:
            await client.send_message({"type": "done", "success": False, "result": None})
        break

    done()


class SocketClient:
    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.json_socket = None

    async def connect(self):
        try:
            self.sock.connect(self.socket_path)
            self.json_socket = JSONUnixSocket(self.sock)
            return True
        except Exception as e:
            print(f"Failed to connect to UDAS: {e}")
            return False

    def receive_messages(self) -> AsyncGenerator[dict[str, Any], None]:
        if self.json_socket is None:
            raise Exception("Socket not connected")

        return self.json_socket.receive_json()

    async def send_message(self, message: dict[str, Any]):
        if self.json_socket is None:
            raise Exception("Socket not connected")

        await self.json_socket.send_json(message)

    def close(self):
        if not self.sock:
            return
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


class JSONLFileClient(SocketClient):
    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.fp = None

    async def connect(self):
        if not os.path.exists(self.socket_path):
            return False
        self.fp = open(self.socket_path, "r+b", buffering=0)
        return True

    def receive_messages(self) -> AsyncGenerator[dict[str, Any], None]:
        import json

        async def generator():
            if self.fp is None:
                raise Exception("Socket not connected")
            while True:
                line = self.fp.readline()
                if not line:
                    break
                yield json.loads(line.decode("utf-8"))

        return generator()

    async def send_message(self, message: dict[str, Any]):
        print("Sending message", message)

    def close(self):
        if not self.fp:
            return
        self.fp.close()


async def get_python_files_from_dir(dir: Path) -> list[Path]:
    """Get all Python files under a directory, returning relative paths."""
    python_files: list[Path] = []

    file_tree = await asyncio.to_thread(os.walk, dir)
    for root, _, files in file_tree:
        for file in files:
            if file.endswith(".py"):
                full_path = Path(root) / file
                relative_path = full_path.relative_to(dir)
                python_files.append(relative_path)
    return python_files
