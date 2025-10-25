"""Asynchronous Python client for Python Portainer."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Self
from urllib.parse import urlparse

from aiohttp import ClientError, ClientResponseError, ClientSession
from aiohttp.hdrs import METH_GET
from yarl import URL

from pyportainer.exceptions import (
    PortainerAuthenticationError,
    PortainerConnectionError,
    PortainerError,
    PortainerNotFoundError,
    PortainerTimeoutError,
)
from pyportainer.models.docker import DockerContainer, DockerContainerStats
from pyportainer.models.docker_inspect import DockerInfo, DockerInspect, DockerVersion
from pyportainer.models.portainer import Endpoint

try:
    VERSION = metadata.version(__package__)
except metadata.PackageNotFoundError:  # pragma: no cover
    VERSION = "DEV-0.0.0"  # pylint: disable=invalid-name


@dataclass
class Portainer:
    """Main class for handling connections with the Python Portainer API."""

    request_timeout: float = 10.0
    session: ClientSession | None = None

    _close_session: bool = False

    def __init__(
        self,
        api_url: str,
        api_key: str,
        *,
        request_timeout: float = 10.0,
        session: ClientSession | None = None,
    ) -> None:
        """Initialize the Portainer object.

        Args:
        ----
            api_url: URL of the Portainer API.
            api_key: API key for authentication.
            request_timeout: Timeout for requests (in seconds).
            session: Optional aiohttp session to use.

        """
        self._api_key = api_key
        self._request_timeout = request_timeout
        self._session = session

        parsed_url = urlparse(api_url)
        self._api_host = parsed_url.hostname or "localhost"
        self._api_scheme = parsed_url.scheme or "http"
        self._api_port = parsed_url.port or 9000

    async def _request(
        self,
        uri: str,
        *,
        method: str = METH_GET,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Handle a request to the Python Portainer API.

        Args:
        ----
            uri: Request URI, without '/api/', for example, 'status'.
            method: HTTP method to use.
            params: Extra options to improve or limit the response.

        Returns:
        -------
            A Python dictionary (JSON decoded) with the response from
            the Python Portainer API.

        Raises:
        ------
            Python PortainerAuthenticationError: If the API key is invalid.

        """
        url = URL.build(
            scheme=self._api_scheme,
            host=self._api_host,
            port=self._api_port,
            path="/api/",
        ).join(URL(uri))

        headers = {
            "Accept": "application/json, text/plain",
            "User-Agent": f"PythonPortainer/{VERSION}",
            "X-API-Key": self._api_key,
        }

        if self._session is None:
            self._session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self._request_timeout):
                response = await self._session.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
        except TimeoutError as err:
            msg = f"Timeout error while accessing {method} {url}: {err}"
            raise PortainerTimeoutError(msg) from err
        except ClientResponseError as err:
            if err.status == 401:
                msg = f"Authentication failed for {method} {url}: Invalid API key"
                raise PortainerAuthenticationError(msg) from err
            if err.status == 404:
                msg = f"Resource not found at {method} {url}: {err}"
                raise PortainerNotFoundError(msg) from err
            msg = f"Connection error for {method} {url}: {err}"
            raise PortainerConnectionError(msg) from err
        except (ClientError, socket.gaierror) as err:
            msg = f"Unexpected error during {method} {url}: {err}"
            raise PortainerConnectionError(msg) from err

        if response.status in (204, 304):
            return None

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected content type response from the Portainer API"
            raise PortainerError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        return await response.json()

    async def get_endpoints(self) -> list[Endpoint]:
        """Get the list of endpoints from the Portainer API.

        Returns
        -------
            A list of Endpoint objects.

        """
        endpoints = await self._request("endpoints")

        return [Endpoint.from_dict(endpoint) for endpoint in endpoints]

    async def get_containers(self, endpoint_id: int) -> list[DockerContainer]:
        """Get the list of containers from the Portainer API.

        Args:
        ----
            endpoint_id: The ID of the endpoint to get containers from.
            all: If True, include all containers. If False, only running containers.

        Returns:
        -------
            A list of containers.

        """
        containers = await self._request(f"endpoints/{endpoint_id}/docker/containers/json?all=1")

        return [DockerContainer.from_dict(container) for container in containers]

    async def start_container(self, endpoint_id: int, container_id: str) -> Any:
        """Start a container on the specified endpoint.

        Args:
        ----
            endpoint_id: The ID of the endpoint.
            container_id: The ID of the container to start.

        """
        return await self._request(
            f"endpoints/{endpoint_id}/docker/containers/{container_id}/start",
            method="POST",
        )

    async def stop_container(self, endpoint_id: int, container_id: str) -> Any:
        """Stop a container on the specified endpoint.

        Args:
        ----
            endpoint_id: The ID of the endpoint.
            container_id: The ID of the container to stop.

        """
        return await self._request(
            f"endpoints/{endpoint_id}/docker/containers/{container_id}/stop",
            method="POST",
        )

    async def restart_container(self, endpoint_id: int, container_id: str) -> Any:
        """Restart a container on the specified endpoint.

        Args:
        ----
            endpoint_id: The ID of the endpoint.
            container_id: The ID of the container to restart.

        """
        return await self._request(
            f"endpoints/{endpoint_id}/docker/containers/{container_id}/restart",
            method="POST",
        )

    async def pause_container(self, endpoint_id: int, container_id: str) -> Any:
        """Pause a container on the specified endpoint.

        Args:
        ----
            endpoint_id: The ID of the endpoint.
            container_id: The ID of the container to pause.

        """
        return await self._request(
            f"endpoints/{endpoint_id}/docker/containers/{container_id}/pause",
            method="POST",
        )

    async def unpause_container(self, endpoint_id: int, container_id: str) -> Any:
        """Unpause a container on the specified endpoint.

        Args:
        ----
            endpoint_id: The ID of the endpoint.
            container_id: The ID of the container to unpause.

        """
        return await self._request(
            f"endpoints/{endpoint_id}/docker/containers/{container_id}/unpause",
            method="POST",
        )

    async def kill_container(self, endpoint_id: int, container_id: str) -> Any:
        """Kill a container on the specified endpoint.

        Args:
        ----
            endpoint_id: The ID of the endpoint.
            container_id: The ID of the container to kill.

        """
        return await self._request(
            f"endpoints/{endpoint_id}/docker/containers/{container_id}/kill",
            method="POST",
        )

    async def inspect_container(self, endpoint_id: int, container_id: str) -> DockerInspect:
        """Inspect a container on the specified endpoint.

        Args:
        ----
            endpoint_id: The ID of the endpoint.
            container_id: The ID of the container to inspect.

        Returns:
        -------
            A DockerContainer object with the inspected data.

        """
        container = await self._request(f"endpoints/{endpoint_id}/docker/containers/{container_id}/json")

        return DockerInspect.from_dict(container)

    async def docker_version(self, endpoint_id: int) -> DockerVersion:
        """Get the Docker version on the specified endpoint.

        Args:
        ----
            endpoint_id: The ID of the endpoint.

        Returns:
        -------
            A DockerVersion object with the Docker version data.

        """
        version = await self._request(f"endpoints/{endpoint_id}/docker/version")

        return DockerVersion.from_dict(version)

    async def docker_info(self, endpoint_id: int) -> DockerInfo:
        """Get the Docker info on the specified endpoint.

        Args:
        ----
            endpoint_id: The ID of the endpoint.

        Returns:
        -------
            A DockerInfo object with the Docker info data.

        """
        info = await self._request(f"endpoints/{endpoint_id}/docker/info")

        return DockerInfo.from_dict(info)

    async def container_stats(
        self,
        endpoint_id: int,
        container_id: str,
        *,
        stream: bool = False,
    ) -> Any:
        """Get the stats of a container on the specified endpoint.

        Args:
        ----
            endpoint_id: The ID of the endpoint.
            container_id: The ID of the container to get stats from.
            stream: If True, stream the stats. If False, get a single snapshot.

        Returns:
        -------
            The stats of the container.

        """
        params = {"stream": str(stream).lower()}
        stats = await self._request(
            f"endpoints/{endpoint_id}/docker/containers/{container_id}/stats",
            params=params,
        )

        return DockerContainerStats.from_dict(stats)

    async def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The Portainer object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()
