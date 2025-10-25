import pytest

from autogit.commands import checkout


class DummyProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_checkout_success(monkeypatch, capsys):
    # Mock subprocess.run to succeed
    def fake_run(cmd, check=False, capture_output=True, text=True):
        assert cmd[:3] == ["git", "checkout", "-b"]
        return DummyProc(returncode=0)

    monkeypatch.setattr(checkout.subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as ex:
        checkout.run(title="Fix login redirect", link="https://example.com/ABC-1234")
    assert ex.value.code == 0

    out, err = capsys.readouterr()
    assert "Now on branch 'ABC-1234-fix-login-redirect'." in out
    assert err == ""


def test_checkout_git_not_found(monkeypatch, capsys):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(checkout.subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as ex:
        checkout.run(title="Title", link="https://example.com/ABC-1")
    assert ex.value.code == 127

    out, err = capsys.readouterr()
    assert out == ""
    assert "git executable not found on PATH" in err


def test_checkout_git_failure_nonzero(monkeypatch, capsys):
    # Simulate git failing to create the branch; current implementation exits with the git return code
    def fake_run(cmd, check=False, capture_output=True, text=True):
        return DummyProc(returncode=1, stderr="failed")

    monkeypatch.setattr(checkout.subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as ex:
        checkout.run(title="X", link="https://example.com/ABC-99")
    # On failure, should exit with the non-zero code and not print success message
    assert ex.value.code == 1

    out, err = capsys.readouterr()
    assert "Failed to create and checkout branch 'ABC-99-x'." in err
    assert out == ""
