"""
Basic tests for PPIO Sandbox SDK.
"""

from ppio_sandbox import __version__

def test_version():
    """Test that version is defined."""
    assert __version__ == "1.0.0"
