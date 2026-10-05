"""Host-admin recovery only; never exposed as an ElevenLabs tool.

Run with the service configuration and protected store directory permissions.
Listing omits staff summary, phone and patient identifiers. Requeue preserves
the event ID and requires explicit selection of one terminal failed request.
"""
import sys
from pathlib import Path

# Embedded Windows Python does not add the script directory automatically.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import getpass
import json
from pathlib import Path
from approval_store import ProposalConflict, ProposalNotFound
from handoff_config import handoff_store


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retry', metavar='HANDOFF_ID')
    args=parser.parse_args()
    config=json.loads((Path(__file__).resolve().parents[1]/'config/api.local.json').read_text(encoding='utf-8-sig'))
    tenant=config.get('operator_tenant_key')
    try:
        store=handoff_store(config, existing=True)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    try:
        result=store.requeue_failed_handoff(tenant,args.retry,getpass.getuser()) if args.retry else store.failed_handoffs(tenant)
    except (ProposalConflict,ProposalNotFound,ValueError) as error:
        raise SystemExit(str(error)) from None
    print(json.dumps(result,ensure_ascii=True))


if __name__=='__main__':
    main()
