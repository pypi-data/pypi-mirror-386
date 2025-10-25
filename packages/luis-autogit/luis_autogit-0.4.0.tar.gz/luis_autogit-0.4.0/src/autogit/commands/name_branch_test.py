import pytest

from .checkout import name_branch


def test_name_branch_happy_path():
    link = "https://example.com/ABC-1234"
    title = "Fix login redirect"
    assert name_branch(link, title) == "ABC-1234-fix-login-redirect"


def test_name_branch_uppercases_prefix():
    link = "https://example.com/abc-5"
    title = "Implement Feature"
    # Prefix should be uppercased; title slugified to lowercase with hyphens
    assert name_branch(link, title) == "ABC-5-implement-feature"


def test_name_branch_invalid_link_exits(capsys):
    # Link without enough '/' segments should trigger SystemExit(1)
    with pytest.raises(SystemExit) as excinfo:
        name_branch("invalid", "Anything")
    assert excinfo.value.code == 1

    # Verify helpful message is printed
    captured = capsys.readouterr()
    assert "Link must be in the format" in captured.out
