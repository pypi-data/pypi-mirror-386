import asyncio
import logging
import os

import click
import dynaconf

from roboherd.herd import RoboHerd
from roboherd.herd.manager import HerdManager
from roboherd.util import create_connection
from roboherd.register import register as run_register
from roboherd.validators import validators
from roboherd.version import __version__

logging.basicConfig(level=logging.INFO)
logging.captureWarnings(True)


@click.group(invoke_without_command=True)
@click.option(
    "--connection_string",
    default=None,
    help="Connection string to the websocket mqtt broker",
)
@click.option(
    "--base_url",
    default=None,
    help="Base url to create cows with",
)
@click.option("--config_file", default="roboherd.toml", help="Configuration file")
@click.option(
    "--version", is_flag=True, default=False, help="display version then exit"
)
@click.pass_context
def main(
    ctx: click.Context,
    connection_string: str,
    base_url: str,
    config_file: str,
    version: bool,
):
    """Configuration is usually loaded from the config_file. These options can be overwritten by passing as a command line argument."""
    if version:
        print(f"roboherd version: {__version__}")
        exit(0)

    settings = dynaconf.Dynaconf(
        settings_files=[config_file],
        envvar_prefix="ROBOHERD",
        validators=validators,
    )
    ctx.ensure_object(dict)

    ctx.obj["config_file"] = config_file
    ctx.obj["settings"] = settings

    if connection_string:
        ctx.obj["connection_string"] = connection_string
    else:
        ctx.obj["connection_string"] = settings.connection_string  # type: ignore

    if base_url:
        ctx.obj["base_url"] = base_url
    else:
        ctx.obj["base_url"] = settings.base_url  # type: ignore

    print("Please specify a command")


@main.command()
@click.option("--fail", is_flag=True, default=False, help="Fail if actors do not exist")
@click.pass_context
def check(ctx: click.Context, fail: bool):
    """Checks that the connection is configured correctly"""

    create_connection(ctx)

    herd = RoboHerd(base_url=ctx.obj["base_url"])

    settings = ctx.obj["settings"]

    if settings.get("cow"):
        herd.manager = HerdManager.from_settings(settings)
        asyncio.run(herd.check(ctx.obj["connection"], raise_if_cows_to_create=fail))
    else:
        click.echo("No cows specified")
        exit(1)


@main.command()
@click.pass_context
def run(ctx: click.Context):
    """Runs the roboherd by connecting to the server."""

    create_connection(ctx)

    herd = RoboHerd(base_url=ctx.obj["base_url"])

    settings = ctx.obj["settings"]

    if settings.get("cow"):
        herd.manager = HerdManager.from_settings(settings)
        asyncio.run(herd.run(ctx.obj["connection"]))
    else:
        click.echo("No cows specified")
        exit(1)


@main.command()
@click.pass_context
def watch(ctx):
    """Watches the file the module is in for changes and then restarts roboherd.

    Note: Options for roboherd are currently ignored (FIXME)."""
    import watchfiles

    watchfiles.run_process("roboherd", target="roboherd run")


@main.command()
@click.pass_context
@click.option("--name", help="Name for the account to be created", prompt=True)
@click.option(
    "--password",
    help="Password for the account to be created",
    hide_input=True,
    prompt=True,
)
@click.option("--fediverse", help="Fediverse handle", prompt=True)
def register(ctx: click.Context, name: str, password: str, fediverse: str):
    """Registers a new account on dev.bovine.social. All three options are required. If not provided, you will be prompted for them."""

    if os.path.exists(ctx.obj["config_file"]):
        click.echo("Config file already exists")
        exit(1)

    if len(password) < 6:
        click.echo("Password should have at least 6 characters")
        exit(1)

    asyncio.run(run_register(ctx.obj["config_file"], name, password, fediverse))


if __name__ == "__main__":
    main()
