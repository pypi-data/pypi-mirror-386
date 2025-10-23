import os
import subprocess
import sys


def run(base_path: str) -> None:
    """Create a directory named after the current git branch inside base_path."""
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

    print(f"Created/exists: {target_dir}")
    sys.exit(0)
