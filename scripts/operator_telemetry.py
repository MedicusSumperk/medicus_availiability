"""Best-effort Operator telemetry for Medicus tool endpoints.

Telemetry is deliberately non-blocking and must never change a tool result.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


LOGGER = logging.getLogger(__name__)
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="operator-telemetry")
_SEQUENCE_LOCK = threading.Lock()
_SEQUENCES: dict[str, int] = {}

_SENSITIVE_KEYS = {
    "authorization", "bearer_token", "token", "api_key", "password", "secret",
    "birth_number", "rodne_cislo", "rodcis", "birth_number_last4", "idpac",
}
_PHONE_KEYS = {"phone", "phone_number", "caller_phone", "caller_id"}


def _sanitize(value: Any, key: str | None = None) -> Any:
    normalized_key = (key or "").lower().replace("-", "_")
    if normalized_key in _SENSITIVE_KEYS or normalized_key.startswith("secret__"):
        return "[REDACTED]"
    if normalized_key in _PHONE_KEYS and value:
        digits = "".join(character for character in str(value) if character.isdigit())
        return f"••• {digits[-3:]}" if digits else "[REDACTED]"
    if isinstance(value, dict):
        return {str(item_key): _sanitize(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, str) and len(value) > 16_000:
        return value[:16_000] + "…[TRUNCATED]"
    return value


def _next_sequence(conversation_id: str) -> int:
    with _SEQUENCE_LOCK:
        sequence = _SEQUENCES.get(conversation_id, 0) + 1
        _SEQUENCES[conversation_id] = sequence
        if len(_SEQUENCES) > 10_000:
            _SEQUENCES.clear()
            _SEQUENCES[conversation_id] = sequence
        return sequence


def telemetry_config(api_config: dict[str, Any]) -> dict[str, Any]:
    return {
        "url": os.getenv("OPERATOR_INGEST_URL") or api_config.get("operator_ingest_url"),
        "token": os.getenv("OPERATOR_INGEST_TOKEN") or api_config.get("operator_ingest_token"),
        "tenant": os.getenv("OPERATOR_TENANT_KEY") or api_config.get("operator_tenant_key"),
        "timeout": float(api_config.get("operator_timeout_seconds", 1.5)),
    }


def _post_event(config: dict[str, Any], payload: dict[str, Any]) -> None:
    request = Request(
        str(config["url"]).rstrip("/") + "/v1/events/tool",
        data=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Operator-Token": str(config["token"]),
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=float(config["timeout"])) as response:  # noqa: S310
            response.read(1)
    except (OSError, URLError, ValueError) as error:
        LOGGER.warning("Operator telemetry delivery failed: %s", error)


def emit_tool_event(
    api_config: dict[str, Any],
    *,
    conversation_id: str | None,
    tool_name: str,
    endpoint: str,
    started_monotonic: float,
    request_payload: dict[str, Any] | None,
    response_payload: dict[str, Any] | None,
    http_status: int,
    business_ok: bool | None,
    error_code: str | None = None,
    trace_id: str | None = None,
) -> None:
    config = telemetry_config(api_config)
    if not conversation_id or not config["url"] or not config["token"] or not config["tenant"]:
        return
    duration_ms = max(0, round((time.perf_counter() - started_monotonic) * 1000))
    payload = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "tool.completed" if business_ok is not False and http_status < 400 else "tool.failed",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "tenant_key": config["tenant"],
        "conversation_id": conversation_id,
        "source": "medicus-api",
        "tool_call": {
            "name": tool_name,
            "endpoint": endpoint,
            "sequence_no": _next_sequence(conversation_id),
            "duration_ms": duration_ms,
            "http_status": http_status,
            "business_ok": business_ok,
            "is_error": business_ok is False or http_status >= 400,
            "error_code": error_code,
            "request_safe": _sanitize(request_payload or {}),
            "response_safe": _sanitize(response_payload or {}),
            "trace_id": trace_id or uuid.uuid4().hex,
        },
    }
    _EXECUTOR.submit(_post_event, config, payload)
