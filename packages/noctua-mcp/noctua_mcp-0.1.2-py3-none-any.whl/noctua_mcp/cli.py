"""Command line interface for noctua-mcp."""

from __future__ import annotations

import sys
import typer
from typing_extensions import Annotated

from noctua_mcp.mcp_server import mcp

app = typer.Typer()


@app.command()
def serve(
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
):
    """
    Start the Noctua MCP server.

    The server communicates via stdio and exposes tools for GO-CAM model editing.

    Environment variables:
    - BARISTA_TOKEN: token for privileged Barista calls (required for mutations)
    - BARISTA_BASE: Barista base URL (default: http://barista-dev.berkeleybop.org)
    - BARISTA_NAMESPACE: Minerva namespace (default: minerva_public_dev)
    - BARISTA_PROVIDED_BY: provided-by agent (default: http://geneontology.org)
    """
    if verbose:
        typer.echo("Starting Noctua MCP server...", err=True)

    # Run the MCP server
    mcp.run()


@app.command()
def version():
    """Print the version."""
    try:
        from noctua_mcp import __version__
        typer.echo(f"noctua-mcp version: {__version__}")
    except ImportError:
        typer.echo("Version information not available")


def main() -> None:
    """Main entry point."""
    # For backward compatibility, if no args provided, run serve
    if len(sys.argv) == 1:
        serve()
    else:
        app()


if __name__ == "__main__":
    main()
