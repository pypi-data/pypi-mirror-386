#!/usr/bin/env python

import os
import sys
import glob
import typer
from loguru import logger
from pathlib import Path
from chutes.entrypoint.api_key import create_api_key
from chutes.entrypoint.deploy import deploy_chute
from chutes.entrypoint.register import register
from chutes.entrypoint.build import build_image
from chutes.entrypoint.report import report_invocation
from chutes.entrypoint.run import run_chute
from chutes.entrypoint.fingerprint import change_fingerprint
from chutes.entrypoint.share import share_chute
from chutes.entrypoint.warmup import warmup_chute
from chutes.entrypoint.secret import create_secret
from chutes.crud import chutes_app, images_app, api_keys_app, secrets_app

app = typer.Typer(no_args_is_help=True)

# Inject our custom libs.
if len(sys.argv) > 1 and sys.argv[1] == "run" and "CHUTE_LD_PRELOAD_INJECTED" not in os.environ:
    logger_lib = Path(__file__).parent / "chutes-logintercept.so"
    netnanny_lib = Path(__file__).parent / "chutes-netnanny.so"
    env = os.environ.copy()
    injected_libs = env.get("LD_PRELOAD", "").split(":")
    netnanny_already_injected = any(
        os.path.basename(lib) == "chutes-netnanny.so" for lib in injected_libs if lib
    )
    libs_to_inject = [str(logger_lib)]
    if netnanny_already_injected:
        existing_netnanny = next(
            lib for lib in injected_libs if lib and os.path.basename(lib) == "chutes-netnanny.so"
        )
        libs_to_inject.append(existing_netnanny)
    else:
        logger.warning("NetNanny was not injected system wide")
        env["CHUTES_NETNANNY_UNSAFE"] = "1"
        libs_to_inject.append(str(netnanny_lib))
    env["LD_PRELOAD"] = ":".join(libs_to_inject)
    env["CHUTE_LD_PRELOAD_INJECTED"] = "1"
    [os.remove(f) for f in glob.glob("/tmp/_chute*log*")]
    os.execve(sys.executable, [sys.executable] + sys.argv, env)

app.command(name="register", help="Create an account with the chutes run platform!")(register)
app.command(help="Change your fingerprint!", no_args_is_help=True, name="refinger")(
    change_fingerprint
)
app.command(help="Report an invocation!", no_args_is_help=True, name="report")(report_invocation)
app.command(help="Run a chute!", no_args_is_help=True, name="run")(run_chute)
app.command(help="Deploy a chute!", no_args_is_help=True, name="deploy")(deploy_chute)
app.command(help="Build an image!", no_args_is_help=True, name="build")(build_image)
app.command(help="Share a chute!", no_args_is_help=True, name="share")(share_chute)
app.command(help="Warm up a chute!", no_args_is_help=True, name="warmup")(warmup_chute)

# Chutes
app.add_typer(chutes_app, name="chutes")

# Images
app.add_typer(images_app, name="images")

# API Keys
api_keys_app.command(
    help="Create an API key for the chutes run platform!",
    no_args_is_help=True,
    name="create",
)(create_api_key)
app.add_typer(api_keys_app)

# Secrets
secrets_app.command(
    help="Create a secret!",
    no_args_is_help=True,
    name="create",
)(create_secret)
app.add_typer(secrets_app)

if __name__ == "__main__":
    app()
