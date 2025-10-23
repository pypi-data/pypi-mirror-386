import pytest
from ppio_sandbox.core import InvalidArgumentException

from ppio_sandbox.code_interpreter import AsyncSandbox


async def test_create_new_kernel(async_sandbox: AsyncSandbox):
    await async_sandbox.create_code_context()


async def test_independence_of_kernels(async_sandbox: AsyncSandbox):
    context = await async_sandbox.create_code_context()
    await async_sandbox.run_code("x = 1")

    r = await async_sandbox.run_code("x", context=context)
    assert r.error is not None
    assert r.error.value == "name 'x' is not defined"


async def test_pass_context_and_language(async_sandbox: AsyncSandbox):
    context = await async_sandbox.create_code_context(language="python")
    with pytest.raises(InvalidArgumentException):
        await async_sandbox.run_code(
            "console.log('Hello, World!')", language="js", context=context
        )
