import os
import subprocess
import sys
import re


def run(base_path: str) -> None:
    """Create a directory named after the current git branch inside base_path.

    Additionally, create an empty file inside that directory named PREFIX-1234.txt
    based on the ticket identifier derived from the current branch name.
    """
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
        print(
            "Failed to determine current git branch (are you in a git repository?)",
            file=sys.stderr,
        )
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

    # Create ticket file PREFIX-1234.txt when branch matches that pattern
    m = re.match(r"^([A-Za-z]+-\d+)", branch_name)
    if m:
        ticket_id = m.group(1)
        ticket_file = os.path.join(target_dir, f"{ticket_id}.txt")
        try:
            # Create the file if it doesn't exist; idempotent
            open(ticket_file, "a").close()
        except OSError as e:
            print(f"Failed to create file '{ticket_file}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Non-fatal: workspace directory is still useful even if branch name
        # does not follow the expected PREFIX-1234 format.
        print(
            "Warning: current branch name does not match 'PREFIX-1234-*'; skipping ticket file creation.",
            file=sys.stderr,
        )

    print(f"Created/exists: {target_dir}")
    sys.exit(0)
