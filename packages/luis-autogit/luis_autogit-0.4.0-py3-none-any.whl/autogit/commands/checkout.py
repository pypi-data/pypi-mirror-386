import subprocess
import sys
from slugify import slugify
from urllib.parse import urlparse


def run(title: str, link: str) -> None:
    """Create and checkout a new git branch based on link and title."""
    branch_name = name_branch(link, title)
    try:
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
            sys.exit(proc.returncode)
    except FileNotFoundError:
        print("git executable not found on PATH", file=sys.stderr)
        sys.exit(127)

    print(f"Now on branch '{branch_name}'.")
    sys.exit(0)


def name_branch(link, title):
    # Validate that link is a well-formed URL with scheme and netloc
    try:
        parsed = urlparse(link)
    except Exception:
        print("Link must be in the format 'https://example.com/PREFIX-1234'")
        sys.exit(1)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        print("Link must be in the format 'https://example.com/PREFIX-1234'")
        sys.exit(1)

    # Extract last path segment expected to be like PREFIX-1234
    last_segment = parsed.path.strip("/").split("/")[-1] if parsed.path else ""
    if not last_segment or "-" not in last_segment:
        print("Link must be in the format 'https://example.com/PREFIX-1234'")
        sys.exit(1)

    prefix = last_segment.split("-")[0].upper()
    ticket_number = last_segment.split("-")[-1]
    branch_name = "-".join([prefix.upper(), ticket_number, slugify(title)])
    return branch_name
