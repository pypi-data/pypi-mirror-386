from ppio_sandbox.core import Sandbox


def test_exists(sandbox: Sandbox):
    filename = "test_exists.txt"

    sandbox.files.write(filename, "test")
    assert sandbox.files.exists(filename)
