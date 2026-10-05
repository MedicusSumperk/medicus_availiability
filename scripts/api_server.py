"""Local API service for ElevenLabs webhook/tool integration.

Run behind Cloudflare Tunnel. The service itself should bind to localhost.
"""

from __future__ import annotations

import json
import os
import sys
import time
import hmac
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Body, Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from availability_search import compact_options, search_availability  # noqa: E402
from appointment_write import write_appointment  # noqa: E402
from paired_appointments import write_transaction  # noqa: E402
from approval_execution import approve as execute_staff_approval  # noqa: E402
from business_rules import agent_capabilities  # noqa: E402
from db import connect_to_db  # noqa: E402
from handoff_summary import build_handoff_summary  # noqa: E402
from handoff_config import durable_handoff_enabled, handoff_store
from operator_telemetry import emit_tool_event  # noqa: E402
from patient_lookup import lookup_patient  # noqa: E402
from approval_store import ApprovalStore, ProposalConflict, ProposalNotFound
from approval_proposals import issue_patient_reference, offer_snapshot, submit_proposal, replay_proposal, revalidate_proposal
from approval_proposals import resolve_move_search, verified_move_availability
from call_context import call_anchor as resolve_call_anchor, InvalidConversation


API_CONFIG_PATH = PROJECT_ROOT / "config" / "api.local.json"
API_CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "config" / "api.local.example.json"


def load_api_config() -> dict[str, Any]:
    if API_CONFIG_PATH.exists():
        with API_CONFIG_PATH.open("r", encoding="utf-8-sig") as config_file:
            return json.load(config_file)
    if API_CONFIG_EXAMPLE_PATH.exists():
        with API_CONFIG_EXAMPLE_PATH.open("r", encoding="utf-8-sig") as config_file:
            return json.load(config_file)
    return {}


API_CONFIG = load_api_config()
API_TOKEN = os.getenv("MEDICUS_API_TOKEN") or API_CONFIG.get("bearer_token")


def approval_store():
    if API_CONFIG.get('enable_staff_approval') is not True:
        raise HTTPException(status_code=503, detail='Staff review is not configured')
    path=API_CONFIG.get('approval_store_path')
    if not path or not Path(path).is_absolute():
        raise HTTPException(status_code=503, detail='Staff review store is not configured')
    return ApprovalStore(path)


def approval_tenant():
    tenant=API_CONFIG.get('operator_tenant_key')
    if not tenant:
        raise HTTPException(status_code=503,detail='Staff review tenant is not configured')
    return tenant


def call_anchor(conversation):
    return resolve_call_anchor(API_CONFIG, conversation)


def require_staff_auth(x_staff_token: str | None = Header(default=None, alias='X-Staff-Token')):
    expected=API_CONFIG.get('staff_approval_token')
    if not isinstance(expected, str) or len(expected)<32 or expected==API_TOKEN or expected.strip()!=expected:
        raise HTTPException(status_code=503,detail='Staff authentication is not configured')
    if not x_staff_token or not hmac.compare_digest(x_staff_token.encode('utf-8'),expected.encode('utf-8')):
        raise HTTPException(status_code=401,detail='Invalid staff credential')


class AvailabilityRequest(BaseModel):
    service: str = "skin"
    date_from: str | None = None
    date_to: str | None = None
    days_ahead: int | None = None
    include_weekends: bool = False
    weekdays: list[int] = Field(default_factory=list)
    time_from: str | None = None
    time_to: str | None = None
    doctor_id: int | None = None
    doctor_name: str | None = None
    emergency: bool = False
    limit: int | None = None
    compact: bool = False


class PlaceholderRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


def require_auth(authorization: str | None = Header(default=None),
                 x_conversation_id: str | None = Header(default=None, alias='X-Conversation-Id')) -> None:
    if not isinstance(API_TOKEN, str) or not API_TOKEN.strip() or API_TOKEN.strip() == 'CHANGE_ME' or API_TOKEN.strip() != API_TOKEN:
        raise HTTPException(status_code=503, detail="API authentication is not configured")
    scheme, _, supplied = (authorization or '').partition(' ')
    if scheme.lower() != 'bearer' or not hmac.compare_digest(supplied.encode('utf-8'), API_TOKEN.encode('utf-8')):
        raise HTTPException(status_code=401, detail="invalid Authorization bearer token")
    if x_conversation_id is not None:
        try:
            call_anchor(x_conversation_id)
        except (ProposalConflict, InvalidConversation) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=503, detail='Call context is unavailable') from error


app = FastAPI(title="Medicus Local API", version="0.1.0")


class StaffProposalDecision(BaseModel):
    version: int = Field(ge=1)
    actor_user_id: str = Field(min_length=1, max_length=160)


class StaffProposalVersion(BaseModel):
    version: int = Field(ge=1)


@app.post('/staff/proposals/{proposal_id}/revalidate', dependencies=[Depends(require_staff_auth)])
def revalidate_staff_proposal(proposal_id: str, request: StaffProposalVersion):
    connection = None
    try:
        store = approval_store()
        tenant = approval_tenant()
        store.pending_payload(tenant, proposal_id, request.version)
        connection = connect_to_db()
        return revalidate_proposal(store, connection.cursor(), tenant, proposal_id, request.version)
    except ProposalNotFound as error:
        raise HTTPException(status_code=404, detail='Proposal not found') from error
    except ProposalConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=503, detail='Proposal could not be verified; no write performed') from error
    finally:
        if connection is not None:
            try:
                connection.rollback()
            finally:
                connection.close()


@app.get('/staff/proposals', dependencies=[Depends(require_staff_auth)])
def staff_proposals(cursor: str | None = None, include_closed: bool = False):
    try:
        return approval_store().page(approval_tenant(), cursor=cursor, include_closed=include_closed)
    except ProposalConflict as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get('/staff/proposals/{proposal_id}', dependencies=[Depends(require_staff_auth)])
def staff_proposal(proposal_id: str):
    try:
        return approval_store().detail(approval_tenant(),proposal_id)
    except ProposalNotFound as error:
        raise HTTPException(status_code=404,detail='Proposal not found') from error


@app.post('/staff/proposals/{proposal_id}/reject', dependencies=[Depends(require_staff_auth)])
def reject_proposal(proposal_id: str, decision: StaffProposalDecision):
    try:
        card,_=approval_store().decide(approval_tenant(),proposal_id,decision.version,decision.actor_user_id,approve=False)
        return card
    except ProposalNotFound as error:
        raise HTTPException(status_code=404,detail='Proposal not found') from error
    except ProposalConflict as error:
        raise HTTPException(status_code=409,detail=str(error)) from error


@app.post('/staff/proposals/{proposal_id}/approve', dependencies=[Depends(require_staff_auth)])
def approve_proposal(proposal_id: str, decision: StaffProposalDecision):
    try:
        return execute_staff_approval(approval_store(), approval_tenant(), proposal_id,
                                      decision.version, decision.actor_user_id, API_CONFIG)
    except ProposalNotFound as error:
        raise HTTPException(status_code=404, detail='Proposal not found') from error
    except ProposalConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=503, detail='Execution status unavailable; inspect the existing proposal before retrying') from error


def normalize_availability_payload(request: dict[str, Any] | AvailabilityRequest | None) -> dict[str, Any]:
    if request is None:
        payload: dict[str, Any] = {}
    elif isinstance(request, AvailabilityRequest):
        payload = request.dict(exclude_none=True)
    elif isinstance(request, dict):
        payload = {key: value for key, value in request.items() if value is not None}
    else:
        raise ValueError("request body must be a JSON object")

    if not payload.get("doctor_name"):
        for alias in ("doctor", "preferred_doctor", "doctorName", "doctor_text", "physician", "lekar"):
            if payload.get(alias):
                payload["doctor_name"] = payload[alias]
                break

    if not payload.get("weekdays") and payload.get("weekday") not in (None, ""):
        payload["weekdays"] = [payload["weekday"]]

    return payload


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "medicus-local-api"}


@app.get("/agent-capabilities", dependencies=[Depends(require_auth)])
def agent_capabilities_get() -> dict[str, Any]:
    try:
        return agent_capabilities(staff_review=API_CONFIG.get('enable_staff_approval') is True,
                                  writes_enabled=API_CONFIG.get('enable_appointment_writes') is True)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Service capabilities could not be verified") from error


@app.post("/agent-capabilities", dependencies=[Depends(require_auth)])
def agent_capabilities_post(_request: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
    return agent_capabilities_get()


@app.post("/doctor-availability", dependencies=[Depends(require_auth)])
def doctor_availability(
    request: dict[str, Any] | None = Body(default=None),
    x_conversation_id: str | None = Header(default=None, alias="X-Conversation-Id"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, Any]:
    connection = None
    started = time.perf_counter()
    payload: dict[str, Any] = {}
    try:
        payload = normalize_availability_payload(request)
        payload.setdefault("days_ahead", API_CONFIG.get("default_days_ahead", 30))
        payload.setdefault("limit", API_CONFIG.get("default_limit", 3))
        payload.setdefault("max_limit", API_CONFIG.get("max_limit", 10))
        anchor = call_anchor(x_conversation_id)

        connection = connect_to_db()
        cursor = connection.cursor()
        move_binding = None
        if payload.get('reschedule_appointment_id') is not None:
            if API_CONFIG.get('enable_staff_approval') is not True or not x_conversation_id:
                raise ProposalConflict('Verified staff-review context is required for rescheduling search')
            move_binding = resolve_move_search(approval_store(), cursor, approval_tenant(), x_conversation_id, payload)
        with verified_move_availability(cursor,
                move_binding['patient']['idpac'] if move_binding else None,
                move_binding['source'] if move_binding else ()) as exclusions:
            response = search_availability(cursor, payload, call_started_at=anchor, **exclusions)
        response.setdefault('filters', {})['call_time_source'] = (
            'first_server_processing' if durable_handoff_enabled(API_CONFIG) and x_conversation_id else 'current_request_processing')
        if API_CONFIG.get('enable_staff_approval') is True and x_conversation_id:
            store=approval_store()
            for option in response.get('options',[]):
                option['call_started_at'] = anchor.isoformat()
                offer = offer_snapshot(option)
                if move_binding:
                    offer = {'offer': offer, 'move_binding': move_binding}
                option['offer_token']=store.issue_grant(approval_tenant(),x_conversation_id,'offer',offer)
        result = compact_options(response) if payload.get("compact") else response
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="doctor_availability",
            endpoint="/doctor-availability", started_monotonic=started, request_payload={},
            response_payload=result, http_status=200, business_ok=result.get("ok"), trace_id=x_trace_id,
        )
        return result
    except ValueError as error:
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="doctor_availability",
            endpoint="/doctor-availability", started_monotonic=started, request_payload={},
            response_payload={"ok": False, "error_code": "validation_error"}, http_status=400, business_ok=False,
            error_code="validation_error", trace_id=x_trace_id,
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # noqa: BLE001
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="doctor_availability",
            endpoint="/doctor-availability", started_monotonic=started, request_payload={},
            response_payload={"ok": False, "error_code": "availability_failed"}, http_status=500, business_ok=False,
            error_code="availability_failed", trace_id=x_trace_id,
        )
        raise HTTPException(status_code=500, detail="Doctor availability could not be verified") from error
    finally:
        if connection is not None:
            connection.close()


@app.post("/patient-lookup", dependencies=[Depends(require_auth)])
def patient_lookup(
    request: dict[str, Any] | None = Body(default=None),
    x_conversation_id: str | None = Header(default=None, alias="X-Conversation-Id"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, Any]:
    connection = None
    started = time.perf_counter()
    payload: dict[str, Any] = {}
    try:
        payload = {key: value for key, value in (request or {}).items() if value is not None}
        call_anchor(x_conversation_id)
        connection = connect_to_db()
        cursor = connection.cursor()
        result = lookup_patient(cursor, payload)
        if API_CONFIG.get('enable_staff_approval') is True and x_conversation_id:
            reference=issue_patient_reference(approval_store(),cursor,approval_tenant(),x_conversation_id,payload,result)
            if reference:
                result['patient_verification_token']=reference
            result['approval_identity_verified']=bool(reference)
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="patient_lookup",
            endpoint="/patient-lookup", started_monotonic=started, request_payload=payload,
            response_payload=result, http_status=200, business_ok=result.get("ok", True), trace_id=x_trace_id,
        )
        return result
    except ValueError as error:
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="patient_lookup",
            endpoint="/patient-lookup", started_monotonic=started, request_payload=payload,
            response_payload={"detail": str(error)}, http_status=400, business_ok=False,
            error_code="validation_error", trace_id=x_trace_id,
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # noqa: BLE001
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="patient_lookup",
            endpoint="/patient-lookup", started_monotonic=started, request_payload=payload,
            response_payload={"detail": "internal error"}, http_status=500, business_ok=False,
            error_code=type(error).__name__, trace_id=x_trace_id,
        )
        raise HTTPException(status_code=500, detail="Patient lookup could not be completed; contact staff") from error
    finally:
        if connection is not None:
            connection.close()


@app.post("/book-appointment", dependencies=[Depends(require_auth)])
def book_appointment(
    request: dict[str, Any] | None = Body(default=None),
    x_conversation_id: str | None = Header(default=None, alias="X-Conversation-Id"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, Any]:
    connection = None
    started = time.perf_counter()
    payload: dict[str, Any] = {}

    def record_review(response):
        # Tokens, identity and caller-controlled text belong neither in tool logs
        # nor in failure emails. Keep the actual state distinct from a booking.
        action = payload.get('action')
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="book_appointment",
            endpoint="/book-appointment", started_monotonic=started,
            request_payload={'action': action if action in {'create', 'cancel', 'reschedule'} else 'unknown'},
            response_payload={key: response[key] for key in ('ok', 'status', 'booking_confirmed', 'proposal_id') if key in response},
            http_status=200, business_ok=response.get('ok'),
            error_code=None if response.get('ok') else 'proposal_rejected', trace_id=x_trace_id,
        )
        return response

    try:
        payload = {key: value for key, value in (request or {}).items() if value is not None}
        payload.setdefault("action", "create")
        if API_CONFIG.get('enable_staff_approval') is True:
            try:
                existing = replay_proposal(approval_store(), approval_tenant(), x_conversation_id, payload)
            except ProposalConflict as error:
                return record_review({'ok':False,'status':'proposal_rejected','booking_confirmed':False,'message':str(error)})
            if existing is not None:
                return record_review(existing)
        connection = connect_to_db()
        cursor = connection.cursor()
        if API_CONFIG.get('enable_staff_approval') is True:
            try:
                response=submit_proposal(approval_store(),cursor,approval_tenant(),x_conversation_id,payload)
            except ProposalConflict as error:
                response={'ok':False,'status':'proposal_rejected','booking_confirmed':False,'message':str(error)}
            finally:
                connection.rollback()
            return record_review(response)
        response = write_transaction(connection, payload, API_CONFIG, legacy_writer=write_appointment)
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="book_appointment",
            endpoint="/book-appointment", started_monotonic=started, request_payload=payload,
            response_payload=response, http_status=200, business_ok=response.get("ok"),
            error_code=None if response.get("ok") else response.get("status"), trace_id=x_trace_id,
        )
        return response
    except ValueError as error:
        if connection is not None:
            connection.rollback()
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="book_appointment",
            endpoint="/book-appointment", started_monotonic=started, request_payload=payload,
            response_payload={"detail": str(error)}, http_status=400, business_ok=False,
            error_code="validation_error", trace_id=x_trace_id,
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # noqa: BLE001
        if connection is not None:
            connection.rollback()
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="book_appointment",
            endpoint="/book-appointment", started_monotonic=started, request_payload=payload,
            response_payload={"detail": "internal error"}, http_status=500, business_ok=False,
            error_code=type(error).__name__, trace_id=x_trace_id,
        )
        raise HTTPException(status_code=500, detail="Appointment request failed; contact staff and retain the same request_id.") from error
    finally:
        if connection is not None:
            connection.close()


@app.post("/handoff-summary", dependencies=[Depends(require_auth)])
def handoff_summary(
    request: dict[str, Any] | None = Body(default=None),
    x_conversation_id: str | None = Header(default=None, alias="X-Conversation-Id"),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
) -> dict[str, Any]:
    started = time.perf_counter()
    payload: dict[str, Any] = {}
    try:
        payload = {key: value for key, value in (request or {}).items() if value is not None}
        result = build_handoff_summary(payload, API_CONFIG)
        if durable_handoff_enabled(API_CONFIG):
            saved=handoff_store(API_CONFIG).store_handoff(approval_tenant(),x_conversation_id,payload.get('request_id'),result)
            result.update(saved)
        else:
            result.update(stored=False, delivery_status='not_queued')
        # Free-text handoff context is stored for staff, never technical logs.
        telemetry_result={key:result.get(key) for key in ('ok','mode','stored','delivery_status','handoff_id')}
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="handoff_summary",
            endpoint="/handoff-summary", started_monotonic=started, request_payload={'mode':result['mode']},
            response_payload=telemetry_result, http_status=200, business_ok=result.get("ok"), trace_id=x_trace_id,
        )
        return result
    except ValueError as error:
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="handoff_summary",
            endpoint="/handoff-summary", started_monotonic=started, request_payload={'mode':payload.get('mode')},
            response_payload={"detail": str(error)}, http_status=400, business_ok=False,
            error_code="validation_error", trace_id=x_trace_id,
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # noqa: BLE001
        emit_tool_event(
            API_CONFIG, conversation_id=x_conversation_id, tool_name="handoff_summary",
            endpoint="/handoff-summary", started_monotonic=started, request_payload={'mode':payload.get('mode')},
            response_payload={"detail": "internal error"}, http_status=500, business_ok=False,
            error_code=type(error).__name__, trace_id=x_trace_id,
        )
        raise HTTPException(status_code=500, detail="Handoff could not be stored; attempt live transfer") from error


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host=str(API_CONFIG.get("host", "127.0.0.1")),
        port=int(API_CONFIG.get("port", 8000)),
        reload=False,
    )
