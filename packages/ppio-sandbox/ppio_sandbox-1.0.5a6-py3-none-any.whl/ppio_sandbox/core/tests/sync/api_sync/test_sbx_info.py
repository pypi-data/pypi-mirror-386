import pytest

from ppio_sandbox.core import Sandbox


@pytest.mark.skip_debug()
def test_get_info(sandbox: Sandbox):
    info = Sandbox.get_info(sandbox.sandbox_id)
    assert info.sandbox_id == sandbox.sandbox_id
