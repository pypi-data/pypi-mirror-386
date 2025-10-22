import logging
import sys
import traceback

import arguably
from dotenv import find_dotenv
from dotenv import load_dotenv
from more_termcolor import bold  # type: ignore
from more_termcolor import red  # type: ignore

from intuned_internal_cli.utils.setup_ide_functions_token import setup_ide_functions_token
from runtime.context.context import IntunedContext

from . import commands

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logging.getLogger("runtime").setLevel(logging.INFO)
logging.getLogger("intuned_runtime").setLevel(logging.INFO)
logging.getLogger("intuned_browser").setLevel(logging.INFO)


def run():
    dotenv = find_dotenv(usecwd=True)
    if dotenv:
        load_dotenv(dotenv, override=True)
    try:
        with IntunedContext():
            setup_ide_functions_token()
            arguably.run(name="intuned-internal")
    except ValueError as e:
        print(bold(red(str(e))))
        sys.exit(1)
    except KeyboardInterrupt:
        print(bold(red("\n🛑 Aborted")))
        sys.exit(1)
    except Exception as e:
        tb_list = traceback.extract_tb(e.__traceback__)

        DEPTH_THRESHOLD = 4

        if len(tb_list) > DEPTH_THRESHOLD:
            relevant_frames = tb_list[DEPTH_THRESHOLD:]  # Show last 2 frames - adjust as needed
            formatted_tb = "".join(traceback.format_list(relevant_frames))
            print(f"Traceback (most recent call last):\n{formatted_tb}{type(e).__name__}: {str(e)}")
        else:
            # For shallow traces, show everything
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

        print(red(bold(f"❌ An error occurred: {e}")))
        sys.exit(1)


__all__ = ["commands", "run"]
