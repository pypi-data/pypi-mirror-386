import datetime

from typing import Optional, Dict, List
from packaging.version import Version
from typing_extensions import Unpack

from ppio_sandbox.core.api.client.types import UNSET
from ppio_sandbox.core.sandbox.main import SandboxBase
from ppio_sandbox.core.sandbox.sandbox_api import SandboxInfo, SandboxMetrics, SandboxQuery
from ppio_sandbox.core.exceptions import TemplateException, SandboxException, NotFoundException
from ppio_sandbox.core.api import AsyncApiClient, SandboxCreateResponse
from ppio_sandbox.core.api.client.models import (
    NewSandbox,
    PostSandboxesSandboxIDTimeoutBody,
    Error,
    ResumedSandbox,
    PausedSandbox,
)
from ppio_sandbox.core.api.client.api.sandboxes import (
    get_sandboxes_sandbox_id,
    post_sandboxes_sandbox_id_timeout,
    delete_sandboxes_sandbox_id,
    post_sandboxes,
    get_sandboxes_sandbox_id_metrics,
    post_sandboxes_sandbox_id_pause,
    post_sandboxes_sandbox_id_resume,
)
from ppio_sandbox.core.connection_config import ConnectionConfig, ApiParams
from ppio_sandbox.core.api import handle_api_exception
from ppio_sandbox.core.sandbox_async.paginator import AsyncSandboxPaginator


class SandboxApi(SandboxBase):
    @staticmethod
    def list(
        query: Optional[SandboxQuery] = None,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        **opts: Unpack[ApiParams],
    ) -> AsyncSandboxPaginator:
        """
        List all running sandboxes.

        :param query: Filter the list of sandboxes by metadata or state, e.g. `SandboxListQuery(metadata={"key": "value"})` or `SandboxListQuery(state=[SandboxState.RUNNING])`
        :param limit: Maximum number of sandboxes to return per page
        :param next_token: Token for pagination

        :return: List of running sandboxes
        """
        return AsyncSandboxPaginator(
            query=query,
            limit=limit,
            next_token=next_token,
            **opts,
        )

    @classmethod
    async def _cls_get_info(
        cls,
        sandbox_id: str,
        **opts: Unpack[ApiParams],
    ) -> SandboxInfo:
        """
        Get the sandbox info.
        :param sandbox_id: Sandbox ID

        :return: Sandbox info
        """
        config = ConnectionConfig(**opts)

        async with AsyncApiClient(
            config,
            limits=SandboxBase._limits,
        ) as api_client:
            res = await get_sandboxes_sandbox_id.asyncio_detailed(
                sandbox_id,
                client=api_client,
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

            if res.parsed is None:
                raise Exception("Body of the request is None")

            if isinstance(res.parsed, Error):
                raise SandboxException(f"{res.parsed.message}: Request failed")

            return SandboxInfo._from_sandbox_detail(res.parsed)

    @classmethod
    async def _cls_kill(
        cls,
        sandbox_id: str,
        **opts: Unpack[ApiParams],
    ) -> bool:
        config = ConnectionConfig(**opts)

        if config.debug:
            # Skip killing the sandbox in debug mode
            return True

        async with AsyncApiClient(
            config,
            limits=SandboxBase._limits,
        ) as api_client:
            res = await delete_sandboxes_sandbox_id.asyncio_detailed(
                sandbox_id,
                client=api_client,
            )

            if res.status_code == 404:
                return False

            if res.status_code >= 300:
                raise handle_api_exception(res)

            return True

    @classmethod
    async def _cls_set_timeout(
        cls,
        sandbox_id: str,
        timeout: int,
        **opts: Unpack[ApiParams],
    ) -> None:
        config = ConnectionConfig(**opts)

        if config.debug:
            # Skip setting the timeout in debug mode
            return

        async with AsyncApiClient(
            config,
            limits=SandboxBase._limits,
        ) as api_client:
            res = await post_sandboxes_sandbox_id_timeout.asyncio_detailed(
                sandbox_id,
                client=api_client,
                body=PostSandboxesSandboxIDTimeoutBody(timeout=timeout),
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

    @classmethod
    async def _create_sandbox(
        cls,
        template: str,
        timeout: int,
        auto_pause: bool,
        allow_internet_access: bool,
        metadata: Optional[Dict[str, str]],
        env_vars: Optional[Dict[str, str]],
        secure: bool,
        node_id: Optional[str],
        **opts: Unpack[ApiParams],
    ) -> SandboxCreateResponse:
        config = ConnectionConfig(**opts)

        async with AsyncApiClient(
            config,
            limits=SandboxBase._limits,
        ) as api_client:
            res = await post_sandboxes.asyncio_detailed(
                body=NewSandbox(
                    template_id=template,
                    auto_pause=auto_pause,
                    metadata=metadata or {},
                    timeout=timeout,
                    env_vars=env_vars or {},
                    secure=secure,
                    allow_internet_access=allow_internet_access,
                    node_id=node_id,
                ),
                client=api_client,
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

            if res.parsed is None:
                raise Exception("Body of the request is None")

            if isinstance(res.parsed, Error):
                raise SandboxException(f"{res.parsed.message}: Request failed")

            if Version(res.parsed.envd_version) < Version("0.1.0"):
                await SandboxApi._cls_kill(res.parsed.sandbox_id)
                raise TemplateException(
                    "You need to update the template to use the new SDK. "
                    "You can do this by running `ppio-sandbox-cli template build` in the directory with the template."
                )

            return SandboxCreateResponse(
                sandbox_id=f"{res.parsed.sandbox_id}-{res.parsed.client_id}",
                sandbox_domain=res.parsed.domain,
                envd_version=res.parsed.envd_version,
                envd_access_token=res.parsed.envd_access_token,
            )

    @classmethod
    async def _cls_clone_sandboxes(
        cls,
        sandbox_id: str,
        count: int = 1,
        node_id: Optional[str] = None,
        strict: bool = False,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ) -> List[dict]:
        """
        Low-level async clone API call. Returns minimal info needed to construct SDK instances.
        
        :param timeout: Timeout for cloned sandboxes in seconds. If omitted, backend applies:
                        - running parent: inherit parent's timeout
                        - paused parent: 15 seconds
        """
        config = ConnectionConfig(**opts)

        async with AsyncApiClient(
            config,
            limits=SandboxBase._limits,
        ) as api_client:
            client = api_client.get_async_httpx_client()

            body = {
                "count": count,
                "strict": strict,
            }
            if node_id:
                body["nodeID"] = node_id
            if timeout is not None:
                body["timeout"] = timeout

            # Use 300s default when user did not specify request_timeout in opts
            user_specified_timeout = (
                'request_timeout' in opts and opts.get('request_timeout') is not None
            )
            effective_timeout = (
                config.request_timeout if user_specified_timeout else 300.0
            )

            res = await client.post(
                f"/sandboxes/{sandbox_id}/clone",
                json=body,
                timeout=effective_timeout,
            )

            if res.status_code == 404:
                raise NotFoundException(f"Sandbox {sandbox_id} not found")

            if res.status_code >= 300:
                # Try to extract error message
                try:
                    data = res.json()
                    message = data.get("message") or res.text
                except Exception:
                    message = res.text
                raise SandboxException(message)

            try:
                data = res.json() or {}
            except Exception:
                raise SandboxException("Clone response data is invalid")

            sandboxes = []
            for sb in (data.get("sandboxes") or []):
                sandbox_id_full = f"{sb.get('sandboxID')}-{sb.get('clientID')}"
                sandboxes.append(
                    {
                        "sandbox_id": sandbox_id_full,
                        "envd_version": sb.get("envdVersion"),
                        "envd_access_token": sb.get("envdAccessToken"),
                    }
                )

            return sandboxes

    @classmethod
    async def _cls_get_metrics(
        cls,
        sandbox_id: str,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
        **opts: Unpack[ApiParams],
    ) -> List[SandboxMetrics]:
        """
        Get the metrics of the sandbox specified by sandbox ID.

        :param sandbox_id: Sandbox ID
        :param start: Start time for the metrics, defaults to the start of the sandbox
        :param end: End time for the metrics, defaults to the current time

        :return: List of sandbox metrics containing CPU, memory and disk usage information
        """
        config = ConnectionConfig(**opts)

        if config.debug:
            # Skip getting the metrics in debug mode
            return []

        async with AsyncApiClient(
            config,
            limits=SandboxBase._limits,
        ) as api_client:
            res = await get_sandboxes_sandbox_id_metrics.asyncio_detailed(
                sandbox_id,
                start=int(start.timestamp() * 1000) if start else UNSET,
                end=int(end.timestamp() * 1000) if end else UNSET,
                client=api_client,
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

            if res.parsed is None:
                return []

            # Check if res.parse is Error
            if isinstance(res.parsed, Error):
                raise SandboxException(f"{res.parsed.message}: Request failed")

            # Convert to typed SandboxMetrics objects
            return [
                SandboxMetrics(
                    cpu_count=metric.cpu_count,
                    cpu_used_pct=metric.cpu_used_pct,
                    disk_total=metric.disk_total,
                    disk_used=metric.disk_used,
                    mem_total=metric.mem_total,
                    mem_used=metric.mem_used,
                    timestamp=metric.timestamp,
                )
                for metric in res.parsed
            ]

    @classmethod
    async def _cls_pause(
        cls,
        sandbox_id: str,
        sync: Optional[bool] = None,
        **opts: Unpack[ApiParams],
    ) -> str:
        config = ConnectionConfig(**opts)

        async with AsyncApiClient(
            config,
            limits=SandboxBase._limits,
        ) as api_client:
            res = await post_sandboxes_sandbox_id_pause.asyncio_detailed(
                sandbox_id,
                client=api_client,
                body=PausedSandbox(sync=sync),
            )

            if res.status_code == 404:
                raise NotFoundException(f"Sandbox {sandbox_id} not found")

            if res.status_code == 409:
                return sandbox_id

            if res.status_code >= 300:
                raise handle_api_exception(res)

            return sandbox_id

    @classmethod
    async def _cls_resume(
        cls,
        sandbox_id: str,
        timeout: Optional[int] = None,
        auto_pause: Optional[bool] = False,
        **opts: Unpack[ApiParams],
    ) -> bool:
        timeout = timeout or SandboxBase.default_sandbox_timeout

        # Temporary solution (02/12/2025),
        # Options discussed:
        # 1. No set - never sure how long the sandbox will be running
        # 2. Always set the timeout in code - the user can't just connect to the sandbox
        #       without changing the timeout, round trip to the server time
        # 3. Set the timeout in resume on backend - side effect on error
        # 4. Create new endpoint for connect
        try:
            await SandboxApi._cls_set_timeout(
                sandbox_id=sandbox_id,
                timeout=timeout,
                **opts,
            )
            return False
        except SandboxException:
            # Sandbox is not running, resume it
            config = ConnectionConfig(**opts)

            async with AsyncApiClient(
                config,
                limits=SandboxBase._limits,
            ) as api_client:
                res = await post_sandboxes_sandbox_id_resume.asyncio_detailed(
                    sandbox_id,
                    client=api_client,
                    body=ResumedSandbox(timeout=timeout, auto_pause=auto_pause),
                )

                if res.status_code == 404:
                    raise NotFoundException(f"Paused sandbox {sandbox_id} not found")

                if res.status_code == 409:
                    return False

                if res.status_code >= 300:
                    raise handle_api_exception(res)

                return True
