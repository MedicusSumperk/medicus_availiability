"""Read-only patient lookup helpers for API/tool calls."""

from __future__ import annotations

import re
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


def _load_future_appointments(cursor, idpac: int, days_ahead: int) -> list[dict[str, Any]]:
    date_from = date.today()
    date_to = date_from + timedelta(days=max(int(days_ahead), 1) - 1)
    cursor.execute(
        """
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
        ORDER BY o.DATUM, o.CAS
        """,
        (idpac, date_from, date_to),
    )

    appointments: list[dict[str, Any]] = []
    for idobj, datum, cas, casdo, iduzi, jmeno, prijmeni, idprac, idcinnosti, activity_name, info in cursor.fetchall():
        doctor_name = " ".join(part for part in [_clean(jmeno), _clean(prijmeni)] if part)
        appointments.append(
            {
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
        )
    return appointments


def lookup_patient(cursor, request: dict[str, Any] | None = None) -> dict[str, Any]:
    request = request or {}
    limit = min(max(int(request.get("limit") or 5), 1), 20)
    include_appointments = bool(request.get("include_appointments", True))
    appointment_days_ahead = min(max(int(request.get("appointment_days_ahead") or 365), 1), 730)
    birth_number_digits = _digits(request.get("birth_number") or request.get("rodne_cislo") or request.get("rodcis"))
    verification_last4 = _last4(
        request.get("birth_number_last4") or request.get("rodne_cislo_last4") or birth_number_digits
    )

    metadata = _load_column_metadata(cursor, PATIENT_TABLE)
    query, params, output_columns, applied_filters = _build_patient_query(metadata, request, limit)
    cursor.execute(query, tuple(params))

    raw_patients = [_patient_from_row(output_columns, row) for row in cursor.fetchall()]
    response: dict[str, Any] = {
        "ok": True,
        "status": "not_found" if not raw_patients else "multiple_matches" if len(raw_patients) > 1 else "found",
        "filters": applied_filters,
        "verification": {
            "required": True,
            "verified": False,
            "method": "birth_number_last4",
        },
        "patients": [_sanitize_patient(patient) for patient in raw_patients],
        "appointments": [],
        "agent_next_step": None,
    }

    if not raw_patients:
        response["agent_next_step"] = "Ask the caller for full name and date of birth, then call patient lookup again."
        return response

    if len(raw_patients) > 1:
        response["agent_next_step"] = "Ask the caller for additional identifying information, ideally date of birth and last 4 digits of birth number."
        return response

    patient = raw_patients[0]
    if verification_last4:
        response["verification"]["provided_last4"] = verification_last4
        response["verification"]["verified"] = patient.get("_birth_number_last4") == verification_last4
        if not response["verification"]["verified"]:
            response["status"] = "verification_failed"
            response["agent_next_step"] = "The provided last 4 digits do not match. Ask the caller to repeat the identifying information."
            return response
    else:
        response["status"] = "needs_verification"
        response["agent_next_step"] = "Ask the caller for the last 4 digits of their birth number before discussing existing appointments."
        return response

    if include_appointments and patient.get("idpac") is not None:
        response["appointments"] = _load_future_appointments(cursor, int(patient["idpac"]), appointment_days_ahead)
    response["agent_next_step"] = "Patient identity verified. Use appointments to answer questions about existing bookings."
    return response
