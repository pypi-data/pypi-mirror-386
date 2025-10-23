from ppio_sandbox.core import Sandbox
from ppio_sandbox.core.sandbox.commands.command_handle import PtySize


def test_send_input(sandbox: Sandbox):
    terminal = sandbox.pty.create(PtySize(cols=80, rows=24))
    sandbox.pty.send_stdin(terminal.pid, b"exit\n")
    result = terminal.wait()
    assert result.exit_code == 0
