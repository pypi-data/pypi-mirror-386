import os
import builtins
import pytest

from autogit.commands import createworkspace


class DummyProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_createworkspace_success_with_ticket_file(monkeypatch, tmp_path, capsys):
    # Simulate current branch with ticket prefix
    def fake_run(cmd, check=False, capture_output=True, text=True):
        assert cmd == ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        return DummyProc(returncode=0, stdout="ABC-1234-fix-login\n")

    monkeypatch.setattr(createworkspace.subprocess, "run", fake_run)

    base = tmp_path / "Workspace"

    with pytest.raises(SystemExit) as ex:
        createworkspace.run(str(base))
    assert ex.value.code == 0

    out, err = capsys.readouterr()
    # Verify directory created
    target_dir = base / "ABC-1234-fix-login"
    assert target_dir.is_dir()
    assert (target_dir / "ABC-1234.txt").is_file()
    assert f"Created/exists: {target_dir}" in out
    assert err == ""


def test_createworkspace_warn_no_ticket(monkeypatch, tmp_path, capsys):
    def fake_run(cmd, check=False, capture_output=True, text=True):
        return DummyProc(returncode=0, stdout="feature-awesome\n")

    monkeypatch.setattr(createworkspace.subprocess, "run", fake_run)

    base = tmp_path / "Workspace"
    with pytest.raises(SystemExit) as ex:
        createworkspace.run(str(base))
    assert ex.value.code == 0

    target_dir = base / "feature-awesome"
    assert target_dir.is_dir()
    # No ticket file created
    assert not any(p.name.endswith(".txt") for p in target_dir.iterdir())

    out, err = capsys.readouterr()
    assert "skipping ticket file creation" in err


def test_createworkspace_git_not_found(monkeypatch, tmp_path, capsys):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(createworkspace.subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as ex:
        createworkspace.run(str(tmp_path))
    assert ex.value.code == 127

    out, err = capsys.readouterr()
    assert "git executable not found on PATH" in err


def test_createworkspace_not_in_repo(monkeypatch, tmp_path, capsys):
    def fake_run(cmd, check=False, capture_output=True, text=True):
        return DummyProc(returncode=128, stdout="", stderr="fatal: not a git repository")

    monkeypatch.setattr(createworkspace.subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as ex:
        createworkspace.run(str(tmp_path))
    assert ex.value.code == 128

    out, err = capsys.readouterr()
    assert "Failed to determine current git branch" in err


def test_createworkspace_oserror_on_makedirs(monkeypatch, tmp_path, capsys):
    def fake_run(cmd, check=False, capture_output=True, text=True):
        return DummyProc(returncode=0, stdout="ABC-1234-foo\n")

    def fake_makedirs(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(createworkspace.subprocess, "run", fake_run)
    monkeypatch.setattr(createworkspace.os, "makedirs", fake_makedirs)

    with pytest.raises(SystemExit) as ex:
        createworkspace.run(str(tmp_path))
    assert ex.value.code == 1

    out, err = capsys.readouterr()
    assert "Failed to create directory" in err


def test_createworkspace_oserror_on_ticket_file(monkeypatch, tmp_path, capsys):
    def fake_run(cmd, check=False, capture_output=True, text=True):
        return DummyProc(returncode=0, stdout="ABC-1234-foo\n")

    def fake_open(*args, **kwargs):
        raise OSError("denied")

    monkeypatch.setattr(createworkspace.subprocess, "run", fake_run)
    monkeypatch.setattr(builtins, "open", fake_open)

    with pytest.raises(SystemExit) as ex:
        createworkspace.run(str(tmp_path))
    assert ex.value.code == 1

    out, err = capsys.readouterr()
    assert "Failed to create file" in err
