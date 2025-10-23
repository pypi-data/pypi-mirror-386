from contextvars import ContextVar, Token
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

call_id_ctx: ContextVar[str | None] = ContextVar("call_id", default=None)
_CURRENT_CALL_ID: str | None = None
_ORIGINAL_FACTORY = logging.getLogRecordFactory()
_CALL_ID_ENABLED = True

@dataclass(slots=True)
class CallContextToken:
    """Token capturing prior state for restoring logging context."""

    context_token: Token
    previous_global: str | None


def _contextual_record_factory(*args, **kwargs) -> logging.LogRecord:
    """Attach the call ID from context to every log record."""
    if not _CALL_ID_ENABLED:
        return _ORIGINAL_FACTORY(*args, **kwargs)

    record = _ORIGINAL_FACTORY(*args, **kwargs)
    call_id = call_id_ctx.get()
    if not call_id:
        call_id = _CURRENT_CALL_ID

    message = record.getMessage()

    if call_id:
        record.msg = f"[call:{call_id}] {message}"
        record.args = ()
    else:
        record.msg = message
        record.args = ()

    record.call_id = call_id or "-"
    return record


logging.setLogRecordFactory(_contextual_record_factory)


def set_call_context(call_id: str) -> CallContextToken:
    """Store the call ID into the logging context."""

    global _CURRENT_CALL_ID

    token = CallContextToken(
        context_token=call_id_ctx.set(call_id),
        previous_global=_CURRENT_CALL_ID,
    )
    _CURRENT_CALL_ID = call_id
    return token


def clear_call_context(token: CallContextToken) -> None:
    """Reset the call context using the provided token."""

    global _CURRENT_CALL_ID

    #failing TODO: fix
    #call_id_ctx.reset(token.context_token)
    _CURRENT_CALL_ID = token.previous_global


def configure_call_id_logging(enabled: bool) -> None:
    """Configure whether call ID logging is enabled."""

    logger.info(f"Configuring call ID logging to {enabled}")
    global _CALL_ID_ENABLED
    _CALL_ID_ENABLED = enabled
