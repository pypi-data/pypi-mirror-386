"""
Command-line interface for jitxlib.parts package.

Example:
.. code-block:: bash

    # Using --json argument
    python -m jitxlib.parts save-component --port 7681 --json '{"mpn": "..."}'

    # Using stdin
    cat component.json | python -m jitxlib.parts save-component --port 7681
"""

import argparse
import sys

from ._save import save_component_command


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m jitxlib.parts", description="JITX Parts Database CLI"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # save-component subcommand
    save_parser = subparsers.add_parser(
        "save-component", help="Save a component from JSON data to a Python file"
    )
    save_parser.add_argument(
        "--json",
        type=str,
        required=False,
        help="JSON string containing component data (if not provided, reads from stdin)",
    )
    save_parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Port number for websocket connection. It is used for the downloading of 3D models",
    )

    return parser


def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    match args.command:
        case "save-component":
            save_component_command(args.json, args.port)
        case _:
            parser.print_help()
            sys.exit(1)


main()
