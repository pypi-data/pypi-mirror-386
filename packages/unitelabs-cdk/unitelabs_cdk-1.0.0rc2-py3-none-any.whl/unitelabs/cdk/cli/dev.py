import asyncio
import logging
import pathlib

import click

from unitelabs.cdk import utils
from unitelabs.cdk.config import get_connector_config, read_config_file

from ..logging import configure_logging
from ..main import run


class TLSConfigurationError(Exception):
    """TLS Configuration is invalid."""


@click.command()
@click.option(
    "--app",
    type=str,
    metavar="IMPORT",
    default=utils.find_factory,
    show_default=False,
    help="The application factory function to load, in the form 'module:name'.",
)
@click.option(
    "-cfg",
    "--config-path",
    type=click.Path(path_type=pathlib.Path),
    default=None,
    help="Path to the configuration file.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase the verbosity of the default logger. Use a custom log-config for fine grained handling.",
)
@utils.coroutine
async def dev(app: str, config_path: pathlib.Path, verbose: int) -> None:
    """Application Entrypoint."""
    import watchfiles

    log_level = logging.ERROR - verbose * 10 if verbose else None
    configure_logging(log_level=log_level)

    async def callback(changes: set[tuple[watchfiles.Change, str]]) -> None:
        """Receive file changes."""

        logger = logging.getLogger("Watcher")
        logger.info("Detected file change: %s", changes.pop()[1])

    await watchfiles.arun_process(".", target=process, args=(app, config_path, verbose), callback=callback)


def process(app: str, config_path: pathlib.Path, verbose: int) -> None:
    """Run the connector in a separate process."""

    try:
        config = read_config_file(config_path)
    except FileNotFoundError:
        click.echo("No config file was found or provided, creating a default configuration.")
        config = get_connector_config().to_dict()

    log_level = logging.ERROR - verbose * 10 if verbose else None
    log_config = config.get("logging", None)
    configure_logging(log_config, log_level=log_level)

    asyncio.run(run(app, config))
