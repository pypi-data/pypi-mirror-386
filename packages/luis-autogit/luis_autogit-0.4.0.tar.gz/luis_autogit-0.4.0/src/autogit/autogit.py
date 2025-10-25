#!/usr/bin/env python3

import argparse
import os
import sys

from .commands import checkout, createworkspace


def main():
    parser = argparse.ArgumentParser(
        prog="autogit",
        description="Utilities to automate frequently used git workflows",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # checkout subcommand
    p = subparsers.add_parser(
        "checkout",
        help="Create and switch to a new git branch for the ticket",
        description=(
            "Create and checkout a new git branch using the provided title and link.\n"
            "Usage: autogit checkout <title> <link>\n"
            "Example: autogit checkout 'Fix login redirect' https://example.com/ABC-1234"
        ),
    )
    # Positional arguments: title then link
    p.add_argument(
        "title",
        help="Human-friendly ticket title, e.g. 'Fix login redirect'",
    )
    p.add_argument(
        "link",
        help=(
            "Machine-friendly link to extract the prefix and number for the branch, e.g. "
            "'https://example.com/PREFIX-1234'"
        ),
    )

    # createworkspace subcommand
    subparsers.add_parser(
        "createworkspace",
        help="Create a folder named after the current git branch inside your Workspace folder",
        description=(
            "Create a directory with the name of the current branch inside the hardcoded path '~/Desktop/Workspace'.\n"
            "Example: autogit createworkspace"
        ),
    )

    args = parser.parse_args()

    if args.command == "checkout":
        title = args.title
        link = args.link
        checkout.run(title, link)

    if args.command == "createworkspace":
        base_path = os.path.expanduser("~/Desktop/Workspace")
        createworkspace.run(base_path)

    # If we reach here, subcommand is unknown (argparse would normally prevent this)
    parser.print_help()
    sys.exit(2)
