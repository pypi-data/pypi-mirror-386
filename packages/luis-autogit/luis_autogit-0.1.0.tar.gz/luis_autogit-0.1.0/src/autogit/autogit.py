#!/usr/bin/env python3

import argparse
import subprocess
import sys

from slugify import slugify

def main():
    parser = argparse.ArgumentParser(
        prog="autogit",
        description="Utilities to automate common git workflows",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser(
        "checkout",
        help="Create and switch to a new git branch for the ticket",
        description=(
            "Create and checkout a new git branch using the provided label as the branch name."
        ),
    )
    p.add_argument(
        "-b",
        "--title",
        required=True,
        help="Human-friendly ticket title, e.g. 'Fix login redirect'",
    )
    p.add_argument(
        "-l",
        "--label",
        required=True,
        help=(
            "Machine-friendly label to extract as the prefix and number for the branch, e.g. 'PREFIX-1234-fix-login-redirect'"
        ),
    )

    args = parser.parse_args()

    if args.command == "checkout":
        title = args.title
        label = args.label

        # Create and checkout branch
        try:
            if len(label.split("-")) < 3:
                print("Label must be in the format PREFIX-1234-something")
                sys.exit(1)
            prefix = label.split("-")[0].upper()
            ticket_number = label.split("-")[1]
            branch_name = "-".join([prefix.upper(), ticket_number, slugify(title)])

            proc = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                check=False,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                print(
                    f"Failed to create and checkout branch '{branch_name}'.",
                    file=sys.stderr,
                )
                if proc.stderr.strip():
                    print(proc.stderr.strip(), file=sys.stderr)
                sys.exit(proc.returncode or 1)
        except FileNotFoundError:
            print("git executable not found on PATH", file=sys.stderr)
            sys.exit(127)

        print(f"Now on branch '{branch_name}'.")
        sys.exit(0)

    # If we reach here, subcommand is unknown (argparse would normally prevent this)
    parser.print_help()
    sys.exit(2)
