"""
gvit CLI.
"""

import sys

import typer

# from gvit.commands.pull import pull
from gvit.commands.clone import clone
from gvit.commands.config import setup, add_extra_deps, remove_extra_deps, show
from gvit.utils.utils import get_version
from gvit.utils.globals import ASCII_LOGO


app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})

config = typer.Typer(help="Configuration management commands.")
config.command()(setup)
config.command()(add_extra_deps)
config.command()(remove_extra_deps)
config.command()(show)

app.add_typer(config, name="config")
app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})(clone)
# app.command()(pull)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", "-V", is_flag=True, help="Show the version and exit.")
) -> None:
    """gvit - Git-aware Virtual Environment Manager"""
    if len(sys.argv) == 1:
        typer.echo(ASCII_LOGO)
        typer.echo("Use `gvit --help` to see available commands.\n")
        raise typer.Exit()
    if version:
        typer.echo(get_version())
        raise typer.Exit()


if __name__ == "__main__":
    app()
