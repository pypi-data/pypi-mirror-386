# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
"""
Service interface and session management.

This module provides the user-facing API for interacting with distributed services,
including session management, context propagation, and dynamic endpoint registration.
"""

import contextvars
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, ParamSpec, TypeVar

from monarch._src.actor.endpoint import EndpointProperty

from .replica import Replica

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class Session:
    """Simple session data holder."""

    session_id: str


# Context variable for session state
_session_context = contextvars.ContextVar("session_context")


class SessionContext:
    """
    Async context manager for stateful service sessions with automatic lifecycle management.

    Provides a convenient way to maintain stateful connections to replicas across multiple
    requests. Sessions ensure that all requests within the context are routed to the same
    replica, enabling stateful interactions while handling session lifecycle automatically.

    Example:

        >>> async with service.session() as session:
        ...     # All calls within this block use the same replica
        ...     result1 = await service.my_endpoint(arg1)
        ...     result2 = await service.another_endpoint(result1)

    """

    def __init__(self, service: "ServiceInterface"):
        self.service = service
        self.session_id: str | None = None
        self._token = None

    async def __aenter__(self):
        """Start a session and set context variables."""
        self.session_id = await self.service.start_session()
        # Set context for this async task
        context_value = {"session_id": self.session_id}
        self._token = _session_context.set(context_value)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Terminate the session and restore context."""
        if self._token:
            _session_context.reset(self._token)
        if self.session_id:
            await self.service.terminate_session(self.session_id)
            self.session_id = None


class ServiceEndpoint(Generic[P, R]):
    """
    This extends Monarch's actor APIs for service endpoints.
    - `route(*args, **kwargs)`: Routes the request to a single replica.
    - `fanout(*args, **kwargs)`: Broadcasts the request to all healthy replicas.

    Monarch's native actor APIs do not apply for services.
    """

    def __init__(self, service, endpoint_name: str):
        self.service = service
        self.endpoint_name = endpoint_name

    async def route(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Chooses a replica to call based on context and load balancing strategy."""
        # Extract sess_id from kwargs if present
        sess_id = kwargs.pop("sess_id", None)
        return await self.service._call(sess_id, self.endpoint_name, *args, **kwargs)

    async def fanout(self, *args: P.args, **kwargs: P.kwargs) -> list[R]:
        """Broadcasts a request to all healthy replicas and returns the results as a list."""
        result = await self.service.call_all(self.endpoint_name, *args, **kwargs)
        return result

    async def choose(self, *args: P.args, **kwargs: P.kwargs) -> R:
        raise NotImplementedError(
            "You tried to use choose() on a service, not an actor. "
            "Services only support route() and fanout()."
        )

    async def call(self, *args: P.args, **kwargs: P.kwargs) -> list[R]:
        raise NotImplementedError(
            "You tried to use call() on a service, not an actor. "
            "Services only support route() and fanout()."
        )

    async def call_one(self, *args: P.args, **kwargs: P.kwargs) -> R:
        raise NotImplementedError(
            "You tried to use a call_one() on a service, not an actor. "
            "Services only support route() and fanout()."
        )

    async def broadcast(self, *args: P.args, **kwargs: P.kwargs) -> list[R]:
        raise NotImplementedError(
            "You tried to use broadcast() on a service, not an actor. "
            "Services only support route() and fanout()."
        )

    async def generate(self, *args: P.args, **kwargs: P.kwargs):
        raise NotImplementedError(
            "You tried to use generate() on a service, not an actor. "
            "Services only support route() and fanout()."
        )


class ServiceEndpointV2(Generic[P, R]):
    """An endpoint object specific to services.

    This loosely mimics the Endpoint APIs exposed in Monarch, with
    a few key differences:
    - Only choose and call are retained (dropping stream and call_one)
    - Call returns a list directly rather than a ValueMesh.

    These changes are made with Forge use cases in mind, but can
    certainly be expanded/adapted in the future.

    """

    def __init__(self, actor_mesh, endpoint_name: str):
        self.actor_mesh = actor_mesh
        self.endpoint_name = endpoint_name

    async def choose(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Chooses a replica to call based on context and load balancing strategy."""
        # Extract sess_id from kwargs if present
        sess_id = kwargs.pop("sess_id", None)
        return await self.actor_mesh.call.call_one(
            sess_id, self.endpoint_name, *args, **kwargs
        )

    async def call(self, *args: P.args, **kwargs: P.kwargs) -> list[R]:
        """Broadcasts a request to all healthy replicas and returns the results as a list."""
        result = await self.actor_mesh.call_all.call_one(
            self.endpoint_name, *args, **kwargs
        )
        return result


class ServiceInterface:
    """
    A lightweight interface to the base Service class.

    This is a temporary workaround until Monarch supports nested
    actors.

    """

    def __init__(self, _service, actor_def):
        self._service = _service
        self.actor_def = actor_def

        # Dynamically create ServiceEndpoint objects for user's actor endpoints
        # Inspect the actor_def directly to find endpoints
        for attr_name in dir(actor_def):
            attr_value = getattr(actor_def, attr_name)
            if isinstance(attr_value, EndpointProperty):
                # Create a ServiceEndpoint that will route through the Service Actor
                endpoint = ServiceEndpoint(self._service, attr_name)
                setattr(self, attr_name, endpoint)

    # Session management methods - handled by ServiceInterface
    async def start_session(self) -> str:
        """Starts a new session for stateful request handling."""
        return await self._service.start_session()

    async def terminate_session(self, sess_id: str):
        """Terminates an active session and cleans up associated resources."""
        return await self._service.terminate_session(sess_id)

    async def shutdown(self) -> None:
        """
        Shut down the underlying Service.
        """
        await self._service.stop()

    def session(self) -> "SessionContext":
        """Returns a context manager for session-based calls."""
        return SessionContext(self)

    async def get_metrics(self):
        """Get comprehensive service metrics for monitoring and analysis."""
        return self._service.get_metrics()

    async def get_metrics_summary(self):
        """Get a summary of key metrics for monitoring and debugging."""
        return self._service.get_metrics_summary()

    # Testing method - forwarded to Service Actor
    async def _get_internal_state(self):
        """
        Get comprehensive internal state for testing purposes.

        Returns:
            dict: Complete internal state including sessions, replicas, and metrics
        """
        return await self._service._get_internal_state()

    def __getattr__(self, name: str):
        """Forward all other attribute access to the underlying Service Actor."""
        _service = object.__getattribute__(self, "_service")
        # Forward everything else to the _service
        if hasattr(_service, name):
            return getattr(_service, name)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


class ServiceInterfaceV2:
    """
    A lightweight interface to a Service Actor running on a single-node mesh.

    This interface holds references to the proc_mesh and actor_mesh (both of size 1)
    and exposes its user-defined actor endpoints as ServiceEndpoint objects that
    route through the Service Actor's _call and _call_all endpoints.

    The ServiceInterface acts as the handle that is returned to end clients,
    providing a simple interface that makes actual calls to the Service Actor.

    This is also needed to simplify serializing a handle to the service, in case
    we want to pass this to other actors in the future.

    """

    def __init__(self, _proc_mesh, _service, actor_def):
        self._proc_mesh = _proc_mesh
        self._service = _service
        self.actor_def = actor_def

        # Dynamically create ServiceEndpoint objects for user's actor endpoints
        # Inspect the actor_def directly to find endpoints
        for attr_name in dir(actor_def):
            attr_value = getattr(actor_def, attr_name)
            if isinstance(attr_value, EndpointProperty):
                # Create a ServiceEndpoint that will route through the Service Actor
                endpoint = ServiceEndpointV2(self._service, attr_name)
                setattr(self, attr_name, endpoint)

    # Session management methods - handled by ServiceInterface
    async def start_session(self) -> str:
        """Starts a new session for stateful request handling."""
        return await self._service.start_session.call_one()

    async def terminate_session(self, sess_id: str):
        """Terminates an active session and cleans up associated resources."""
        return await self._service.terminate_session.call_one(sess_id)

    def session(self) -> "SessionContext":
        """Returns a context manager for session-based calls."""
        return SessionContext(self)

    # Metrics methods - forwarded to Service Actor
    async def get_metrics(self):
        """Get comprehensive service metrics for monitoring and analysis."""
        return await self._service.get_metrics.call_one()

    async def get_metrics_summary(self):
        """Get a summary of key metrics for monitoring and debugging."""
        return await self._service.get_metrics_summary.call_one()

    # Testing method - forwarded to Service Actor
    async def _get_internal_state(self):
        """
        Get comprehensive internal state for testing purposes.

        Returns:
            dict: Complete internal state including sessions, replicas, and metrics
        """
        return await self._service._get_internal_state.call_one()

    def __getattr__(self, name: str):
        """Forward all other attribute access to the underlying Service Actor."""
        _service = object.__getattribute__(self, "_service")
        # Forward everything else to the _service
        if hasattr(_service, name):
            return getattr(_service, name)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


class Router(ABC):
    """Abstract base class for routing logic."""

    @abstractmethod
    def get_replica(
        self,
        healthy_replicas: list[Replica],
        sess_id: str | None = None,
        session_map: dict[str, int] | None = None,
    ) -> Replica:
        """Select a replica from the list based on routing logic."""
        pass
