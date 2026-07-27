"""Build structured handoff summaries for live transfer or callback."""

from __future__ import annotations

from datetime import datetime
from typing import Any


SUPPORTED_HANDOFF_MODES = {"live_transfer", "callback"}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _compact_patient(request: dict[str, Any]) -> dict[str, Any]:
    patient = request.get("patient") if isinstance(request.get("patient"), dict) else {}
    return {
        "verified": bool(request.get("patient_verified") or patient.get("verified")),
        "idpac": patient.get("idpac") or request.get("idpac"),
        "name": _clean(patient.get("name") or request.get("patient_name")),
    }


def build_handoff_summary(request: dict[str, Any] | None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    request = request or {}
    config = config or {}
    mode = _clean(request.get("mode") or "callback").lower()
    if mode not in SUPPORTED_HANDOFF_MODES:
        raise ValueError("mode must be one of: live_transfer, callback")

    caller_phone = _clean(request.get("caller_phone") or request.get("phone"))
    reason = _clean(request.get("reason") or "needs_staff")
    intent = _clean(request.get("intent"))
    conversation_summary = _clean(request.get("conversation_summary") or request.get("summary"))
    recommended_next_step = _clean(request.get("recommended_next_step") or request.get("next_step"))
    patient = _compact_patient(request)
    selected_slot = request.get("selected_slot") if isinstance(request.get("selected_slot"), dict) else {}
    appointments = request.get("appointments") if isinstance(request.get("appointments"), list) else []

    summary_parts = [
        f"Handoff mode: {mode}.",
        f"Reason: {reason}.",
    ]
    if caller_phone:
        summary_parts.append(f"Caller phone: {caller_phone}.")
    if intent:
        summary_parts.append(f"Intent: {intent}.")
    if patient["verified"]:
        summary_parts.append(f"Patient identity verified; internal idpac: {patient['idpac']}.")
    else:
        summary_parts.append("Patient identity is not verified.")
    if selected_slot:
        slot_text = " ".join(
            part
            for part in [
                _clean(selected_slot.get("date")),
                _clean(selected_slot.get("start_time") or selected_slot.get("time")),
                _clean(selected_slot.get("doctor_name")),
                _clean(selected_slot.get("service")),
            ]
            if part
        )
        if slot_text:
            summary_parts.append(f"Selected slot: {slot_text}.")
    if appointments:
        summary_parts.append(f"Known appointment count in current context: {len(appointments)}.")
    if conversation_summary:
        summary_parts.append(f"Conversation summary: {conversation_summary}.")
    if recommended_next_step:
        summary_parts.append(f"Recommended next step: {recommended_next_step}.")

    return {
        "ok": True,
        "mode": mode,
        "reason": reason,
        "caller_phone": caller_phone or None,
        "patient": patient,
        "selected_slot": selected_slot,
        "appointments": appointments,
        "summary_for_staff": " ".join(summary_parts),
        "recommended_next_step": recommended_next_step or None,
        "transfer_target": config.get("handoff_phone") if mode == "live_transfer" else None,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
