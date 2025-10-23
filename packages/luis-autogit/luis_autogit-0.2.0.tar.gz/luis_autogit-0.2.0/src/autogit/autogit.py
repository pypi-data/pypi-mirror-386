#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys

from slugify import slugify


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
        description="Create and checkout a new git branch using the provided title as the branch name.",
    )
    p.add_argument(
        "-b",
        "--title",
        required=True,
        help="Human-friendly ticket title, e.g. 'Fix login redirect'",
    )
    p.add_argument(
        "-l",
        "--link",
        required=True,
        help="Machine-friendly link to extract as the prefix and number for the branch, e.g. 'https://example.com/PREFIX-1234'",
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
        _checkout(title, link)

    if args.command == "createworkspace":
        base_path = os.path.expanduser("~/Desktop/Workspace")
        _create_folder(base_path)

    # If we reach here, subcommand is unknown (argparse would normally prevent this)
    parser.print_help()
    sys.exit(2)


def _checkout(title, link):
    # Create and checkout branch
    branch_name = name_branch(link, title)
    try:
        proc = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(f"Failed to create and checkout branch '{branch_name}'.", file=sys.stderr)
    except FileNotFoundError:
        print("git executable not found on PATH", file=sys.stderr)
        sys.exit(127)

    print(f"Now on branch '{branch_name}'.")
    sys.exit(0)


def _create_folder(base_path: str):
    # Resolve base path (expand ~ and env vars)
    base_path = os.path.expandvars(os.path.expanduser(base_path))

    # Get current git branch name
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("git executable not found on PATH", file=sys.stderr)
        sys.exit(127)

    if proc.returncode != 0:
        print("Failed to determine current git branch (are you in a git repository?)", file=sys.stderr)
        sys.exit(proc.returncode or 1)

    branch_name = proc.stdout.strip()
    if not branch_name:
        print("Could not determine current git branch name.", file=sys.stderr)
        sys.exit(1)

    # Compose final directory path and create it
    target_dir = os.path.join(base_path, branch_name)
    try:
        os.makedirs(target_dir, exist_ok=True)
    except OSError as e:
        print(f"Failed to create directory '{target_dir}': {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Created/exists: {target_dir}")
    sys.exit(0)


def name_branch(link, title):
    if len(link.split("/")) < 3:
        print("Link must be in the format 'https://example.com/PREFIX-1234'")
        sys.exit(1)
    prefix = link.split("/")[-1].split("-")[0].upper()
    ticket_number = link.split("-")[-1]
    branch_name = "-".join([prefix.upper(), ticket_number, slugify(title)])
    return branch_name
