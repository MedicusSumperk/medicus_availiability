"""Independent durable handoff switch; never enables appointment operations."""
from pathlib import Path

from approval_store import ApprovalStore


def durable_handoff_enabled(config):
    # Staff-review installations already depend on durable handoffs.
    return (config.get('enable_durable_handoff') is True
            or config.get('enable_staff_approval') is True)


def handoff_store(config, *, existing=False):
    path = Path(config.get('approval_store_path') or '')
    if (not durable_handoff_enabled(config)
            or not config.get('operator_tenant_key')
            or not path.is_absolute()
            or (existing and not path.is_file())):
        raise ValueError('Durable handoff store and tenant must be configured')
    return ApprovalStore(path)
