"""Server-observed call time, independent of permission to book appointments."""
from datetime import datetime, timezone

from handoff_config import durable_handoff_enabled, handoff_store


class InvalidConversation(ValueError):
    pass


def call_anchor(config, conversation):
    if conversation is not None and (
        not isinstance(conversation, str) or not 1 <= len(conversation) <= 160
        or any(c.isspace() or c in '{}' for c in conversation)
        or conversation.startswith('system__')
    ):
        raise InvalidConversation('Valid runtime conversation reference is required')
    if conversation and durable_handoff_enabled(config):
        # Do not silently create a replacement store if deployed state is lost.
        stamp = handoff_store(config, existing=True).first_seen(
            config['operator_tenant_key'], conversation)
        return datetime.fromtimestamp(stamp, timezone.utc)
    return datetime.now(timezone.utc)
