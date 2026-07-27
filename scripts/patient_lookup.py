"""Read-only patient lookup helpers for API/tool calls."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date, timedelta
from typing import Any


PATIENT_TABLE = "KAR"
TEXT_FIELD_TYPES = {14, 37}  # CHAR, VARCHAR
DATE_FIELD_TYPES = {12, 35}  # DATE, TIMESTAMP
NUMERIC_FIELD_TYPES = {7, 8, 16, 27}

OUTPUT_COLUMN_CANDIDATES = [
    "IDPAC",
    "PRIJMENI",
    "JMENO",
    "TITUL",
    "RODCIS",
    "DATNAR",
    "POJ",
    "TELEFON",
    "TELEFON1",
    "TELEFON2",
    "MOBIL",
    "MOBILNI",
    "TEL",
]
PHONE_COLUMN_CANDIDATES = [
    "TELEFON",
    "TELEFON1",
    "TELEFON2",
    "MOBIL",
    "MOBILNI",
    "TEL",
    "TEL1",
    "TEL2",
]
NAME_COLUMN_CANDIDATES = ["PRIJMENI", "JMENO"]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_text(value: Any) -> str:
    decomposed = unicodedata.normalize("NFKD", _clean(value).casefold())
    without_marks = "".join(character for character in decomposed if not unicodedata.combining(character))
    return re.sub(r"\s+", " ", without_marks).strip()


def _digits(value: Any) -> str:
    return re.sub(r"\D+", "", _clean(value))


def _last4(value: Any) -> str | None:
    digits = _digits(value)
    if len(digits) < 4:
        return None
    return digits[-4:]


def _date_iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "date"):
        value = value.date()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = _clean(value)
    return text or None


def _load_column_metadata(cursor, table_name: str) -> dict[str, dict[str, int | None]]:
    cursor.execute(
        """
        SELECT
            rf.RDB$FIELD_NAME,
            f.RDB$FIELD_TYPE,
            f.RDB$FIELD_LENGTH
        FROM RDB$RELATION_FIELDS rf
        JOIN RDB$FIELDS f ON f.RDB$FIELD_NAME = rf.RDB$FIELD_SOURCE
        WHERE rf.RDB$RELATION_NAME = ?
        ORDER BY rf.RDB$FIELD_POSITION
        """,
        (table_name,),
    )
    return {
        _clean(column_name).upper(): {
            "type": int(field_type),
            "length": int(field_length) if field_length is not None else None,
        }
        for column_name, field_type, field_length in cursor.fetchall()
    }


def _available_columns(metadata: dict[str, dict[str, int | None]], candidates: list[str]) -> list[str]:
    return [column for column in candidates if column in metadata]


def _is_text_column(metadata: dict[str, dict[str, int | None]], column: str) -> bool:
    return metadata.get(column, {}).get("type") in TEXT_FIELD_TYPES


def _build_patient_query(
    metadata: dict[str, dict[str, int | None]],
    request: dict[str, Any],
    limit: int,
) -> tuple[str, list[Any], list[str], list[str]]:
    output_columns = _available_columns(metadata, OUTPUT_COLUMN_CANDIDATES)
    if "IDPAC" not in output_columns and "IDPAC" in metadata:
        output_columns.insert(0, "IDPAC")
    if not output_columns:
        raise ValueError("KAR.IDPAC column was not found")

    where_parts: list[str] = []
    params: list[Any] = []
    applied_filters: list[str] = []

    if request.get("idpac") is not None and "IDPAC" in metadata:
        where_parts.append("IDPAC = ?")
        params.append(int(request["idpac"]))
        applied_filters.append("idpac")

    birth_number_digits = _digits(request.get("birth_number") or request.get("rodne_cislo") or request.get("rodcis"))
    if birth_number_digits and "RODCIS" in metadata:
        where_parts.append("CAST(RODCIS AS VARCHAR(20)) = ?")
        params.append(birth_number_digits)
        applied_filters.append("birth_number")

    phone_digits = _digits(request.get("phone") or request.get("phone_number") or request.get("caller_phone"))
    if phone_digits:
        phone_tail = phone_digits[-9:] if len(phone_digits) > 9 else phone_digits
        phone_groups = [phone_tail[index : index + 3] for index in range(0, len(phone_tail), 3)]
        phone_columns = [column for column in _available_columns(metadata, PHONE_COLUMN_CANDIDATES) if _is_text_column(metadata, column)]
        phone_parts = []
        for column in phone_columns:
            column_parts = []
            for group in phone_groups:
                column_parts.append(f"CAST({column} AS VARCHAR(80)) LIKE ?")
                params.append(f"%{group}%")
            phone_parts.append("(" + " AND ".join(column_parts) + ")")
        contact_parts = ["CAST(kk.TELEFON_ADJ AS VARCHAR(80)) LIKE ?"]
        contact_params: list[Any] = [f"%{phone_tail}%"]
        contact_group_parts = []
        for group in phone_groups:
            contact_group_parts.append("CAST(kk.KONTAKT AS VARCHAR(80)) LIKE ?")
            contact_params.append(f"%{group}%")
        contact_parts.append("(" + " AND ".join(contact_group_parts) + ")")
        phone_parts.append(
            "EXISTS ("
            "SELECT 1 FROM KARKONTAKT kk "
            "WHERE kk.IDPAC = KAR.IDPAC "
            "AND (" + " OR ".join(contact_parts) + ")"
            ")"
        )
        params.extend(contact_params)
        if phone_parts:
            where_parts.append("(" + " OR ".join(phone_parts) + ")")
            applied_filters.append("phone")

    last_name = _clean(request.get("last_name") or request.get("surname"))
    if last_name and "PRIJMENI" in metadata and _is_text_column(metadata, "PRIJMENI"):
        where_parts.append("UPPER(CAST(PRIJMENI AS VARCHAR(80))) LIKE ?")
        params.append(f"%{last_name.upper()}%")
        applied_filters.append("last_name")

    first_name = _clean(request.get("first_name") or request.get("name"))
    if first_name and "JMENO" in metadata and _is_text_column(metadata, "JMENO"):
        where_parts.append("UPPER(CAST(JMENO AS VARCHAR(80))) LIKE ?")
        params.append(f"%{first_name.upper()}%")
        applied_filters.append("first_name")

    birth_date = _clean(request.get("birth_date"))
    if birth_date and "DATNAR" in metadata:
        where_parts.append("DATNAR = ?")
        params.append(birth_date)
        applied_filters.append("birth_date")

    if not where_parts:
        raise ValueError("patient lookup requires phone, idpac, birth_number, name, surname, or birth_date")

    safe_limit = min(max(int(limit), 1), 20)
    query = f"""
        SELECT FIRST {safe_limit} {", ".join(output_columns)}
        FROM {PATIENT_TABLE}
        WHERE {" AND ".join(where_parts)}
        ORDER BY IDPAC DESC
    """
    return query, params, output_columns, applied_filters


def _requested_name_filters(request: dict[str, Any]) -> list[str]:
    filters: list[str] = []
    if _clean(request.get("last_name") or request.get("surname")):
        filters.append("last_name")
    if _clean(request.get("first_name") or request.get("name")):
        filters.append("first_name")
    return filters


def _has_stable_anchor(request: dict[str, Any]) -> bool:
    return any(
        [
            request.get("idpac") is not None,
            _digits(request.get("phone") or request.get("phone_number") or request.get("caller_phone")),
            _digits(request.get("birth_number") or request.get("rodne_cislo") or request.get("rodcis")),
            _clean(request.get("birth_date")),
        ]
    )


def _name_fallback_request(request: dict[str, Any]) -> dict[str, Any] | None:
    if not _requested_name_filters(request):
        return None

    if not _has_stable_anchor(request):
        return None

    fallback = dict(request)
    for key in ("first_name", "name", "last_name", "surname"):
        fallback.pop(key, None)
    fallback["limit"] = max(int(request.get("limit") or 5), 20)
    return fallback


def _text_contains_normalized(value: Any, requested: Any) -> bool:
    requested_normalized = _normalize_text(requested)
    if not requested_normalized:
        return True
    return requested_normalized in _normalize_text(value)


def _levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            insertion = current[right_index - 1] + 1
            deletion = previous[right_index] + 1
            substitution = previous[right_index - 1] + (left_char != right_char)
            current.append(min(insertion, deletion, substitution))
        previous = current
    return previous[-1]


def _text_fuzzy_matches(value: Any, requested: Any) -> bool:
    requested_normalized = _normalize_text(requested)
    if not requested_normalized:
        return True

    value_normalized = _normalize_text(value)
    if not value_normalized:
        return False
    if requested_normalized in value_normalized:
        return True

    max_distance = 1 if min(len(requested_normalized), len(value_normalized)) < 8 else 2
    return _levenshtein_distance(value_normalized, requested_normalized) <= max_distance


def _patient_matches_requested_names(patient: dict[str, Any], request: dict[str, Any]) -> bool:
    last_name = _clean(request.get("last_name") or request.get("surname"))
    first_name = _clean(request.get("first_name") or request.get("name"))
    return _text_contains_normalized(patient.get("last_name"), last_name) and _text_contains_normalized(
        patient.get("first_name"), first_name
    )


def _patient_fuzzy_matches_requested_names(patient: dict[str, Any], request: dict[str, Any]) -> bool:
    last_name = _clean(request.get("last_name") or request.get("surname"))
    first_name = _clean(request.get("first_name") or request.get("name"))
    return _text_fuzzy_matches(patient.get("last_name"), last_name) and _text_fuzzy_matches(
        patient.get("first_name"), first_name
    )


def _verification_method(applied_filters: list[str], name_match: str) -> str:
    if "idpac" in applied_filters:
        return "idpac_unique"
    if "birth_number" in applied_filters:
        return "birth_number_unique"
    if "phone" in applied_filters and len(applied_filters) == 1:
        return "phone_unique"
    if "birth_date" in applied_filters and ("last_name" in applied_filters or "first_name" in applied_filters):
        return "name_birth_date_unique" if name_match != "fuzzy_fallback" else "fuzzy_name_birth_date_unique"
    if "phone" in applied_filters:
        return "phone_refined_unique"
    return "unique_match"


def _next_step_for_multiple_matches(applied_filters: list[str]) -> str:
    if "birth_date" not in applied_filters:
        return "Ask the caller for date of birth, then call patient lookup again."
    if "first_name" not in applied_filters:
        return "Ask the caller for first name, then call patient lookup again."
    if "last_name" not in applied_filters:
        return "Ask the caller for surname, then call patient lookup again."
    return "Ask the caller for one more identifying detail and hand off to staff if the match remains ambiguous."


def _patient_from_row(columns: list[str], row: tuple[Any, ...]) -> dict[str, Any]:
    values = dict(zip(columns, row, strict=False))
    rodcis = values.get("RODCIS")
    phones = {
        column.lower(): _clean(values.get(column))
        for column in PHONE_COLUMN_CANDIDATES
        if column in values and _clean(values.get(column))
    }
    return {
        "idpac": int(values["IDPAC"]) if values.get("IDPAC") is not None else None,
        "first_name": _clean(values.get("JMENO")),
        "last_name": _clean(values.get("PRIJMENI")),
        "title": _clean(values.get("TITUL")),
        "birth_date": _date_iso(values.get("DATNAR")),
        "insurance_code": _clean(values.get("POJ")),
        "_birth_number_last4": _last4(rodcis),
        "phones": phones,
    }


def _sanitize_patient(patient: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in patient.items() if not key.startswith("_")}


def _appointment_row_to_dict(row: tuple[Any, ...]) -> dict[str, Any]:
    idobj, datum, cas, casdo, iduzi, jmeno, prijmeni, idprac, idcinnosti, activity_name, info = row
    doctor_name = " ".join(part for part in [_clean(jmeno), _clean(prijmeni)] if part)
    return {
        "idobj": int(idobj),
        "date": _date_iso(datum),
        "start_time": cas.strftime("%H:%M") if hasattr(cas, "strftime") else _clean(cas),
        "end_time": casdo.strftime("%H:%M") if hasattr(casdo, "strftime") else _clean(casdo),
        "doctor_id": int(iduzi) if iduzi is not None else None,
        "doctor_name": doctor_name,
        "idprac": int(idprac) if idprac is not None else None,
        "idcinnosti": int(idcinnosti) if idcinnosti is not None else None,
        "activity_name": _clean(activity_name),
        "info": _clean(info),
    }


def _load_appointments(cursor, idpac: int, date_from: date, date_to: date, sort_desc: bool = False) -> list[dict[str, Any]]:
    order_direction = "DESC" if sort_desc else "ASC"
    cursor.execute(
        f"""
        SELECT FIRST 20
            o.IDOBJ,
            o.DATUM,
            o.CAS,
            o.CASDO,
            o.IDUZI,
            u.JMENO,
            u.PRIJMENI,
            o.IDPRAC,
            o.IDCINNOSTI,
            c.NAZEV,
            o.INFO
        FROM OBJOBJ o
        LEFT JOIN UZIVATEL u ON u.IDUZI = o.IDUZI
        LEFT JOIN CINNOSTI c ON c.ID = o.IDCINNOSTI
        WHERE o.IDPAC = ?
          AND o.DATUM >= ?
          AND o.DATUM <= ?
          AND o.TYP NOT IN (9, 10)
        ORDER BY o.DATUM {order_direction}, o.CAS {order_direction}
        """,
        (idpac, date_from, date_to),
    )
    return [_appointment_row_to_dict(row) for row in cursor.fetchall()]


def _load_future_appointments(cursor, idpac: int, days_ahead: int) -> list[dict[str, Any]]:
    date_from = date.today()
    date_to = date_from + timedelta(days=max(int(days_ahead), 1) - 1)
    return _load_appointments(cursor, idpac, date_from, date_to)


def _load_past_appointments(cursor, idpac: int, days_back: int) -> list[dict[str, Any]]:
    date_to = date.today() - timedelta(days=1)
    date_from = date_to - timedelta(days=max(int(days_back), 1) - 1)
    return _load_appointments(cursor, idpac, date_from, date_to, sort_desc=True)


def lookup_patient(cursor, request: dict[str, Any] | None = None) -> dict[str, Any]:
    request = request or {}
    limit = min(max(int(request.get("limit") or 5), 1), 20)
    include_appointments = bool(request.get("include_appointments", True))
    include_past_appointments = bool(request.get("include_past_appointments", False))
    appointment_days_ahead = min(max(int(request.get("appointment_days_ahead") or 365), 1), 730)
    past_appointment_days = min(max(int(request.get("past_appointment_days") or 365), 1), 1825)

    metadata = _load_column_metadata(cursor, PATIENT_TABLE)
    query, params, output_columns, applied_filters = _build_patient_query(metadata, request, limit)
    cursor.execute(query, tuple(params))

    raw_patients = [_patient_from_row(output_columns, row) for row in cursor.fetchall()]
    name_match = "sql"
    if not raw_patients:
        fallback_request = _name_fallback_request(request)
        if fallback_request:
            fallback_query, fallback_params, fallback_columns, fallback_filters = _build_patient_query(
                metadata, fallback_request, int(fallback_request.get("limit") or 20)
            )
            cursor.execute(fallback_query, tuple(fallback_params))
            fallback_patients = [_patient_from_row(fallback_columns, row) for row in cursor.fetchall()]
            raw_patients = [
                patient for patient in fallback_patients if _patient_matches_requested_names(patient, request)
            ]
            if raw_patients:
                applied_filters = fallback_filters + _requested_name_filters(request)
                name_match = "accent_insensitive_fallback"

    if not raw_patients and _requested_name_filters(request) and _has_stable_anchor(request):
        fallback_request = _name_fallback_request(request)
        if fallback_request:
            fallback_query, fallback_params, fallback_columns, fallback_filters = _build_patient_query(
                metadata, fallback_request, int(fallback_request.get("limit") or 20)
            )
            cursor.execute(fallback_query, tuple(fallback_params))
            fallback_patients = [_patient_from_row(fallback_columns, row) for row in cursor.fetchall()]
            raw_patients = [
                patient for patient in fallback_patients if _patient_fuzzy_matches_requested_names(patient, request)
            ]
            if raw_patients:
                applied_filters = fallback_filters + _requested_name_filters(request)
                name_match = "fuzzy_fallback"

    response: dict[str, Any] = {
        "ok": True,
        "status": "not_found" if not raw_patients else "multiple_matches" if len(raw_patients) > 1 else "found",
        "filters": applied_filters,
        "name_match": name_match,
        "verification": {
            "required": False,
            "verified": len(raw_patients) == 1,
            "method": _verification_method(applied_filters, name_match) if len(raw_patients) == 1 else None,
        },
        "patients": [_sanitize_patient(patient) for patient in raw_patients],
        "appointments": [],
        "past_appointments": [],
        "appointments_json": "[]",
        "past_appointments_json": "[]",
        "agent_next_step": None,
    }

    if not raw_patients:
        response["agent_next_step"] = "Ask the caller for surname and date of birth, then call patient lookup again."
        return response

    if len(raw_patients) > 1:
        response["agent_next_step"] = _next_step_for_multiple_matches(applied_filters)
        return response

    patient = raw_patients[0]
    if include_appointments and patient.get("idpac") is not None:
        response["appointments"] = _load_future_appointments(cursor, int(patient["idpac"]), appointment_days_ahead)
    if include_past_appointments and patient.get("idpac") is not None:
        response["past_appointments"] = _load_past_appointments(cursor, int(patient["idpac"]), past_appointment_days)
    response["appointments_json"] = json.dumps(response["appointments"], ensure_ascii=False, separators=(",", ":"))
    response["past_appointments_json"] = json.dumps(
        response["past_appointments"], ensure_ascii=False, separators=(",", ":")
    )
    response["agent_next_step"] = "Patient identity verified. Use appointments to answer questions about existing bookings."
    return response
