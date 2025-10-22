from functools import WRAPPER_ASSIGNMENTS
from functools import wraps

import pytimeparse  # type: ignore

from intuned_cli.controller.authsession import execute_run_validate_auth_session_cli
from intuned_cli.utils.auth_session_helpers import assert_auth_enabled
from intuned_cli.utils.wrapper import cli_command


async def _run_validate_authsession_impl(
    id: str,
    /,
    *,
    check_attempts: int = 1,
    create_attempts: int = 1,
    proxy: str | None = None,
    timeout: str = "10 min",
    no_auto_recreate: bool = False,
    headless: bool = False,
    trace: bool = False,
    keep_browser_open: bool = False,
):
    """Execute an AuthSession:Validate run to validate an auth session

    Args:
        id (str): ID of the auth session to validate
        check_attempts (int, optional): [--check-attempts]. Number of attempts to check the auth session validity. Defaults to 1.
        create_attempts (int, optional): [--create-attempts]. Number of attempts to create a new auth session if it is invalid. Defaults to 1.
        proxy (str | None, optional): [--proxy]. Proxy URL to use for the auth session command. Defaults to None.
        timeout (str, optional): [--timeout]. Timeout for the auth session command - seconds or pytimeparse-formatted string. Defaults to "10 min".
        no_auto_recreate (bool, optional): [--no-auto-recreate]. Disable auto recreation of the auth session if it is invalid. Defaults to False.
        headless (bool, optional): [--headless]. Run the API in headless mode (default: False). This will not open a browser window.
        trace (bool, optional): [--trace]. Capture a trace of each attempt, useful for debugging. Defaults to False.
        keep_browser_open (bool, optional): [--keep-browser-open]. Keep the last browser open after execution for debugging. Defaults to False.
    """
    await assert_auth_enabled()

    auto_recreate = not no_auto_recreate

    timeout_value = pytimeparse.parse(timeout)  # type: ignore
    if timeout_value is None:
        raise ValueError(
            f"Invalid timeout format: {timeout}. Please use a valid time format like '10 min' or '600 seconds'."
        )

    await execute_run_validate_auth_session_cli(
        id=id,
        auto_recreate=auto_recreate,
        check_retries=check_attempts,
        create_retries=create_attempts,
        headless=headless,
        proxy=proxy,
        timeout=timeout_value,
        trace=trace,
        keep_browser_open=keep_browser_open,
    )


@cli_command
@wraps(_run_validate_authsession_impl, (a for a in WRAPPER_ASSIGNMENTS if a != "__name__"))
async def run__authsession__validate(
    *args,  # type: ignore
    **kwargs,  # type: ignore
):
    return await _run_validate_authsession_impl(*args, **kwargs)  # type: ignore


@cli_command
@wraps(_run_validate_authsession_impl, (a for a in WRAPPER_ASSIGNMENTS if a != "__name__"))
async def authsession__validate(
    *args,  # type: ignore
    **kwargs,  # type: ignore
):
    return await _run_validate_authsession_impl(*args, **kwargs)  # type: ignore
