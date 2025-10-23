import json
import pathlib
import typing

import click

from unitelabs.cdk import utils
from unitelabs.cdk.config import get_connector_config
from unitelabs.cdk.main import load


@click.group(context_settings=dict(show_default=True))
def config() -> click.Group:
    """Configure a connector."""


@config.command()
@click.option(
    "--app",
    type=str,
    metavar="IMPORT",
    default=utils.find_factory,
    show_default=False,
    help="The application factory function to load, in the form 'module:name'.",
)
@click.option(
    "-p",
    "--path",
    type=click.Path(
        exists=False,
        dir_okay=False,
        writable=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    default=pathlib.Path("./schema.json"),
    help="Path to the configuration schema file.",
)
@utils.coroutine
async def schema(app, path: pathlib.Path) -> None:  # noqa: ANN001
    """Create a configuration jsonschema."""
    await load(app)
    config = get_connector_config()
    with path.open("w") as file:
        json.dump(config.schema(), file, indent=2)


@config.command()
@click.option(
    "--app",
    type=str,
    metavar="IMPORT",
    default=utils.find_factory,
    show_default=False,
    help="The application factory function to load, in the form 'module:name'.",
)
@click.option(
    "-f",
    "--field",
    type=str,
    required=False,
    help="The name of the field in the schema to get more information about, otherwise the entire schema is shown.",
)
@utils.coroutine
async def show(app, field: typing.Optional[str] = None) -> None:  # noqa: ANN001
    """Visualize the configuration options."""
    await load(app)
    config = get_connector_config()
    description = config.describe(field)

    from rich.console import Console
    from rich.table import Column, Table

    table = Table(
        Column("Field", justify="left"),
        Column("Type", justify="right"),
        Column("Description", justify="right"),
        Column("Example", justify="right"),
        title=f"{config.__name__} Definition",
        show_lines=True,
    )

    for name, values in description.items():
        if not isinstance(values, dict):
            table.add_row(field, *description.values())
            break
        if "values" not in values:
            table.add_row(name, *values.values())
        else:
            table.add_row(name, values["type"], values["description"], values["default"])

    console = Console()
    console.print(table)


@config.command()
@click.option(
    "--app",
    type=str,
    metavar="IMPORT",
    default=utils.find_factory,
    show_default=False,
    help="The application factory function to load, in the form 'module:name'.",
)
@click.option(
    "--path",
    type=click.Path(
        exists=False,
        dir_okay=False,
        writable=True,
        resolve_path=True,
        path_type=pathlib.Path,
    ),
    default=pathlib.Path("./config.json"),
    help="Path to the configuration file.",
)
@utils.coroutine
async def create(app, path: pathlib.Path) -> None:  # noqa: ANN001
    """Create a configuration file."""
    await load(app)
    config = get_connector_config()
    config().dump(path)


if __name__ == "__main__":
    config()
