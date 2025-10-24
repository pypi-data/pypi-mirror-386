"""MCP Callbacks."""

from typing import Any

from mcp.shared.context import RequestContext
from mcp.shared.session import RequestResponder
from mcp.types import (
    INVALID_REQUEST,
    ClientResult,
    CreateMessageRequestParams,
    ErrorData,
    ListRootsResult,
    LoggingMessageNotificationParams,
    ServerNotification,
    ServerRequest,
)

from flock.logging.logging import FlockLogger
from flock.mcp.types.handlers import (
    handle_incoming_exception,
    handle_incoming_request,
    handle_incoming_server_notification,
    handle_logging_message,
)


async def default_sampling_callback(
    ctx: RequestContext, params: CreateMessageRequestParams, logger: FlockLogger
) -> ErrorData:
    """Default Callback for Sampling."""
    logger.info("Rejecting Sampling Request.")
    return ErrorData(code=INVALID_REQUEST, message="Sampling not supported.")


async def default_message_handler(
    req: RequestResponder[ServerRequest, ClientResult] | ServerNotification | Exception,
    logger: FlockLogger,
    associated_client: Any,
) -> None:
    """Default Message Handler."""
    if isinstance(req, Exception):
        await handle_incoming_exception(
            e=req,
            logger_to_use=logger,
            associated_client=associated_client,
        )
    elif isinstance(req, ServerNotification):
        await handle_incoming_server_notification(
            n=req,
            logger=logger,
            client=associated_client,
        )
    elif isinstance(req, RequestResponder[ServerRequest, ClientResult]):
        await handle_incoming_request(
            req=req,
            logger_to_use=logger,
            associated_client=associated_client,
        )


async def default_list_roots_callback(
    associated_client: Any,
    logger: FlockLogger,
) -> ListRootsResult | ErrorData:
    """Default List Roots Callback."""
    if associated_client.config.feature_config.roots_enabled:
        # Use lock-free version to avoid deadlock during initialization
        # when the lock is already held by _connect()
        current_roots = associated_client._get_roots_no_lock()
        logger.debug(f"Server requested list/roots. Sending: {current_roots}")
        return ListRootsResult(roots=current_roots)
    return ErrorData(code=INVALID_REQUEST, message="List roots not supported.")


async def default_logging_callback(
    params: LoggingMessageNotificationParams,
    logger: FlockLogger,
    server_name: str,
) -> None:
    """Default Logging Handling Callback."""
    await handle_logging_message(params=params, logger=logger, server_name=server_name)
