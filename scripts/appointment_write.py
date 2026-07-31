"""Appointment write helpers for the local API.

The module performs database writes only after re-validating the requested slot
with the same availability logic used by /doctor-availability.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from availability_search import search_availability
from business_rules import load_business_rules, service_enabled_for_booking, service_followup_enabled


SUPPORTED_ACTIONS = {"create", "cancel", "reschedule"}
DEFAULT_TYPE = 1
DEFAULT_PRISEL = "N"
DEFAULT_CREATED_BY = 10
DEFAULT_SKIN_FOLLOWUP_IDCINNOSTI = 6
DEFAULT_SKIN_FOLLOWUP_INFO = "AI_DERMATOSCOPE_RESERVATION"
DEFAULT_INFO_PREFIX = "AI_RECEPTION"


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_date(value: Any, field_name: str) -> date:
    if isinstance(value, date):
        return value
    text = _clean(value)
    if not text:
        raise ValueError(f"{field_name} is required")
    return date.fromisoformat(text)


def _parse_time(value: Any, field_name: str) -> time:
    if isinstance(value, time):
        return value
    text = _clean(value)
    if not text:
        raise ValueError(f"{field_name} is required")
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"{field_name} must use HH:MM or HH:MM:SS")


def _format_time(value: time) -> str:
    return value.strftime("%H:%M")


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "ano", "y"}


def _configured_bool(config: dict[str, Any], key: str, default: bool = False) -> bool:
    if key not in config:
        return default
    return _bool(config.get(key))


def _write_enabled(config: dict[str, Any]) -> bool:
    return _configured_bool(config, "enable_appointment_writes", False)


def _cancel_enabled(config: dict[str, Any]) -> bool:
    return _configured_bool(config, "enable_appointment_cancellations", False)


def _created_by(config: dict[str, Any]) -> int:
    return int(config.get("appointment_created_by") or DEFAULT_CREATED_BY)


def _info_prefix(config: dict[str, Any]) -> str:
    return _clean(config.get("appointment_info_prefix")) or DEFAULT_INFO_PREFIX


def _skin_followup_idcinnosti(config: dict[str, Any]) -> int:
    rules = load_business_rules()
    followup = rules.get("services", {}).get("skin", {}).get("followup", {})
    if followup.get("idcinnosti") is not None:
        return int(followup["idcinnosti"])
    return int(config.get("skin_followup_idcinnosti") or DEFAULT_SKIN_FOLLOWUP_IDCINNOSTI)


def _skin_followup_info(config: dict[str, Any]) -> str:
    rules = load_business_rules()
    followup = rules.get("services", {}).get("skin", {}).get("followup", {})
    if _clean(followup.get("info")):
        return _clean(followup["info"])
    return _clean(config.get("skin_followup_info")) or DEFAULT_SKIN_FOLLOWUP_INFO


def _service_followup_enabled(service: str) -> bool:
    rules = load_business_rules()
    return service_followup_enabled(rules, service)


def _service_info(service: str, option: dict[str, Any], request: dict[str, Any], config: dict[str, Any]) -> str:
    explicit_info = _clean(request.get("info"))
    if explicit_info:
        return explicit_info

    prefix = _info_prefix(config)
    if service == "plasma":
        marker = _clean(option.get("info_marker")) or _clean(config.get("plasma_info_marker")) or "plazma"
        return f"{prefix} {marker}".strip()
    if service == "dermatoscope_first":
        return f"{prefix} dermatoscope_first".strip()
    return f"{prefix} {service}".strip()


def _require_patient_verified(request: dict[str, Any]) -> None:
    if not _bool(request.get("patient_verified")):
        raise ValueError("patient_verified=true is required for appointment writes")


def _appointment_ids(request: dict[str, Any], required: bool = True) -> list[int]:
    values = request.get("appointment_ids")
    if values is None and request.get("appointment_id") is not None:
        values = [request["appointment_id"]]
    if values is None:
        if required:
            raise ValueError("appointment_id or appointment_ids is required")
        return []
    if not isinstance(values, list):
        values = [values]
    ids = [int(value) for value in values]
    if required and not ids:
        raise ValueError("appointment_id or appointment_ids is required")
    return ids


def _fetch_appointment_rows(cursor, appointment_ids: list[int]) -> list[dict[str, Any]]:
    if not appointment_ids:
        return []
    placeholders = ", ".join("?" for _ in appointment_ids)
    cursor.execute(
        f"""
        SELECT
            IDOBJ,
            IDPAC,
            IDPRAC,
            IDUZI,
            DATUM,
            CAS,
            CASDO,
            TYP,
            PRISEL,
            IDCINNOSTI,
            INFO
        FROM OBJOBJ
        WHERE IDOBJ IN ({placeholders})
        ORDER BY DATUM, CAS, IDOBJ
        """,
        tuple(appointment_ids),
    )
    rows = []
    for row in cursor.fetchall():
        idobj, idpac, idprac, iduzi, datum, cas, casdo, typ, prisel, idcinnosti, info = row
        rows.append(
            {
                "idobj": int(idobj),
                "idpac": int(idpac) if idpac is not None else None,
                "idprac": int(idprac) if idprac is not None else None,
                "doctor_id": int(iduzi) if iduzi is not None else None,
                "date": datum.isoformat() if hasattr(datum, "isoformat") else _clean(datum),
                "start_time": cas.strftime("%H:%M") if hasattr(cas, "strftime") else _clean(cas),
                "end_time": casdo.strftime("%H:%M") if hasattr(casdo, "strftime") else _clean(casdo),
                "typ": int(typ) if typ is not None else None,
                "prisel": _clean(prisel),
                "idcinnosti": int(idcinnosti) if idcinnosti is not None else None,
                "info": _clean(info),
            }
        )
    return rows


def _expand_related_appointment_ids(
    cursor,
    appointment_ids: list[int],
    rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[int]:
    """Include legacy immediate skin follow-up rows when cancelling/moving."""
    include_related = _bool(config.get("include_related_appointments_by_default", True))
    if not include_related:
        return appointment_ids

    expanded = list(dict.fromkeys(appointment_ids))
    followup_idcinnosti = _skin_followup_idcinnosti(config)
    for row in rows:
        if row.get("idcinnosti") is not None:
            continue
        cursor.execute(
            """
            SELECT FIRST 1 IDOBJ
            FROM OBJOBJ
            WHERE IDPAC = ?
              AND IDPRAC = ?
              AND IDUZI = ?
              AND DATUM = ?
              AND CAS = ?
              AND IDCINNOSTI = ?
              AND IDOBJ <> ?
            ORDER BY IDOBJ
            """,
            (
                row["idpac"],
                row["idprac"],
                row["doctor_id"],
                _parse_date(row["date"], "date"),
                _parse_time(row["end_time"], "end_time"),
                followup_idcinnosti,
                row["idobj"],
            ),
        )
        related = cursor.fetchone()
        if related:
            related_id = int(related[0])
            if related_id not in expanded:
                expanded.append(related_id)
    return expanded


def _find_exact_bookable_option(cursor, request: dict[str, Any]) -> dict[str, Any]:
    service = _clean(request.get("service") or "skin").lower()
    rules = load_business_rules()
    supported_services = {
        service_key
        for service_key, service_rules in rules.get("services", {}).items()
        if service_enabled_for_booking(rules, service_key)
    }
    if service not in supported_services:
        raise ValueError(f"service must be one of: {', '.join(sorted(supported_services))}")

    target_date = _parse_date(request.get("date"), "date")
    start_time = _parse_time(
        request.get("start_time") or request.get("technical_start_time") or request.get("time"),
        "start_time",
    )
    if request.get("doctor_id") is None and not request.get("doctor_name"):
        raise ValueError("doctor_name or doctor_id is required for appointment writes")

    availability_request: dict[str, Any] = {
        "service": service,
        "date_from": target_date.isoformat(),
        "date_to": target_date.isoformat(),
        "time_from": _format_time(start_time),
        "time_to": _format_time(start_time),
        "limit": int(request.get("availability_limit") or 10),
        "max_limit": int(request.get("availability_max_limit") or 50),
    }
    if request.get("doctor_id") is not None:
        availability_request["doctor_id"] = int(request["doctor_id"])
    if request.get("doctor_name"):
        availability_request["doctor_name"] = request["doctor_name"]
    if request.get("emergency") is not None:
        availability_request["emergency"] = request["emergency"]

    response = search_availability(cursor, availability_request)
    doctor_filter = response.get("filters", {}).get("doctor", {})
    if request.get("doctor_name") and doctor_filter.get("match_type") not in {"exact", "partial"}:
        return {
            "error": "doctor_not_resolved",
            "availability_response": response,
        }

    for option in response.get("options", []):
        if option.get("date") != target_date.isoformat():
            continue
        if option.get("start_time") != _format_time(start_time):
            continue
        if request.get("doctor_id") is not None and int(option["doctor_id"]) != int(request["doctor_id"]):
            continue
        return option

    return {
        "error": "slot_not_bookable",
        "availability_response": response,
    }


def _find_conflicts(cursor, idprac: int, doctor_id: int, target_date: date, start_time: time, end_time: time) -> list[dict[str, Any]]:
    cursor.execute(
        """
        SELECT IDOBJ, IDPAC, IDPRAC, IDUZI, DATUM, CAS, CASDO, TYP, IDCINNOSTI, INFO
        FROM OBJOBJ
        WHERE IDPRAC = ?
          AND IDUZI = ?
          AND DATUM = ?
          AND CAS < ?
          AND CASDO > ?
        ORDER BY CAS, IDOBJ
        """,
        (idprac, doctor_id, target_date, end_time, start_time),
    )
    conflicts: list[dict[str, Any]] = []
    for row in cursor.fetchall():
        idobj, idpac, row_idprac, row_iduzi, datum, cas, casdo, typ, idcinnosti, info = row
        conflicts.append(
            {
                "idobj": int(idobj),
                "idpac": int(idpac) if idpac is not None else None,
                "idprac": int(row_idprac) if row_idprac is not None else None,
                "doctor_id": int(row_iduzi) if row_iduzi is not None else None,
                "date": datum.isoformat() if hasattr(datum, "isoformat") else _clean(datum),
                "start_time": cas.strftime("%H:%M") if hasattr(cas, "strftime") else _clean(cas),
                "end_time": casdo.strftime("%H:%M") if hasattr(casdo, "strftime") else _clean(casdo),
                "typ": int(typ) if typ is not None else None,
                "idcinnosti": int(idcinnosti) if idcinnosti is not None else None,
                "info": _clean(info),
            }
        )
    return conflicts


def _insert_appointment(
    cursor,
    *,
    idpac: int,
    idprac: int,
    doctor_id: int,
    target_date: date,
    start_time: time,
    end_time: time,
    idcinnosti: int | None,
    info: str,
    created_by: int,
) -> dict[str, Any]:
    conflicts = _find_conflicts(cursor, idprac, doctor_id, target_date, start_time, end_time)
    if conflicts:
        raise ValueError(f"slot conflict before insert: {conflicts}")

    cursor.execute(
        """
        INSERT INTO OBJOBJ (
            IDPAC,
            IDPRAC,
            DATUM,
            CAS,
            TYP,
            PRISEL,
            INFO,
            IDUZI,
            DATUMDO,
            CASDO,
            DATZAPIS,
            CREATEDBY,
            IDCINNOSTI
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_DATE, ?, ?)
        RETURNING IDOBJ
        """,
        (
            idpac,
            idprac,
            target_date,
            start_time,
            DEFAULT_TYPE,
            DEFAULT_PRISEL,
            info,
            doctor_id,
            target_date,
            end_time,
            created_by,
            idcinnosti,
        ),
    )
    return {
        "idobj": int(cursor.fetchone()[0]),
        "idpac": idpac,
        "idprac": idprac,
        "doctor_id": doctor_id,
        "date": target_date.isoformat(),
        "start_time": _format_time(start_time),
        "end_time": _format_time(end_time),
        "typ": DEFAULT_TYPE,
        "prisel": DEFAULT_PRISEL,
        "idcinnosti": idcinnosti,
        "info": info,
    }


def _create_appointments(cursor, request: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    _require_patient_verified(request)
    idpac = int(request["idpac"])
    option = _find_exact_bookable_option(cursor, request)
    if option.get("error"):
        status = str(option["error"])
        return {
            "ok": False,
            "status": status,
            "message": "Requested appointment cannot be written according to live availability rules.",
            "availability": option["availability_response"],
        }

    service = str(option["service"])
    target_date = _parse_date(option["date"], "date")
    start_time = _parse_time(option["start_time"], "start_time")
    end_time = _parse_time(option["end_time"], "end_time")
    doctor_id = int(option["doctor_id"])
    idprac = int(option["idprac"])
    created_by = _created_by(config)

    inserted_rows: list[dict[str, Any]] = []
    inserted_rows.append(
        _insert_appointment(
            cursor,
            idpac=idpac,
            idprac=idprac,
            doctor_id=doctor_id,
            target_date=target_date,
            start_time=start_time,
            end_time=end_time,
            idcinnosti=option.get("idcinnosti"),
            info=_service_info(service, option, request, config),
            created_by=created_by,
        )
    )

    if service == "skin" and _service_followup_enabled(service):
        followup = option.get("followup_dermatoscope_slot") or {}
        if not followup:
            raise ValueError("skin availability option did not include followup_dermatoscope_slot")
        follow_start = _parse_time(followup.get("start_time"), "followup.start_time")
        follow_end = _parse_time(followup.get("end_time"), "followup.end_time")
        inserted_rows.append(
            _insert_appointment(
                cursor,
                idpac=idpac,
                idprac=idprac,
                doctor_id=doctor_id,
                target_date=target_date,
                start_time=follow_start,
                end_time=follow_end,
                idcinnosti=_skin_followup_idcinnosti(config),
                info=_skin_followup_info(config),
                created_by=created_by,
            )
        )

    return {
        "ok": True,
        "status": "created",
        "service": service,
        "appointment_ids": [row["idobj"] for row in inserted_rows],
        "appointments": inserted_rows,
        "availability_option": option,
    }


def _cancel_appointments(cursor, request: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    _require_patient_verified(request)
    if not _cancel_enabled(config):
        return {
            "ok": False,
            "status": "cancel_not_enabled",
            "message": "Appointment cancellation is disabled in local API config.",
        }

    appointment_ids = _appointment_ids(request)
    rows_before = _fetch_appointment_rows(cursor, appointment_ids)
    found_ids = {row["idobj"] for row in rows_before}
    missing_ids = [idobj for idobj in appointment_ids if idobj not in found_ids]
    if missing_ids:
        return {
            "ok": False,
            "status": "appointment_not_found",
            "missing_ids": missing_ids,
            "appointments": rows_before,
        }

    if _bool(request.get("include_related", True)):
        appointment_ids = _expand_related_appointment_ids(cursor, appointment_ids, rows_before, config)
        rows_before = _fetch_appointment_rows(cursor, appointment_ids)

    idpac = int(request["idpac"])
    mismatched = [row for row in rows_before if row["idpac"] != idpac]
    if mismatched:
        return {
            "ok": False,
            "status": "appointment_patient_mismatch",
            "appointments": rows_before,
        }

    placeholders = ", ".join("?" for _ in appointment_ids)
    cursor.execute(f"DELETE FROM OBJOBJ WHERE IDOBJ IN ({placeholders})", tuple(appointment_ids))
    return {
        "ok": True,
        "status": "cancelled",
        "appointment_ids": appointment_ids,
        "appointments_before_cancel": rows_before,
    }


def write_appointment(cursor, request: dict[str, Any] | None, config: dict[str, Any]) -> dict[str, Any]:
    request = request or {}
    action = _clean(request.get("action") or "create").lower()
    if action not in SUPPORTED_ACTIONS:
        raise ValueError("action must be one of: create, cancel, reschedule")
    if not _write_enabled(config):
        return {
            "ok": False,
            "status": "writes_not_enabled",
            "message": "Appointment writes are disabled in local API config.",
        }

    if action == "create":
        return _create_appointments(cursor, request, config)

    if action == "cancel":
        return _cancel_appointments(cursor, request, config)

    cancelled = _cancel_appointments(cursor, request, config)
    if not cancelled.get("ok"):
        return cancelled
    created = _create_appointments(cursor, request, config)
    if not created.get("ok"):
        return created
    return {
        "ok": True,
        "status": "rescheduled",
        "cancelled": cancelled,
        "created": created,
    }
