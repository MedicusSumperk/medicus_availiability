"""Read-only availability calculation helpers for Firebird schedule data."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any


TIME_FORMAT = "%H:%M"


def to_time(value: Any) -> time:
    """Convert a database time-like value to datetime.time."""
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(text, fmt).time()
            except ValueError:
                continue
    raise ValueError(f"Unsupported time value: {value!r}")


def format_time(value: time) -> str:
    """Format a slot time for CLI and export output."""
    return value.strftime(TIME_FORMAT)


def generate_slots(start_time: time, duration_minutes: int, interval_minutes: int) -> list[time]:
    """Generate slot starts in [start_time, start_time + duration)."""
    base_day = date(2000, 1, 1)
    current = datetime.combine(base_day, start_time)
    end_time = current + timedelta(minutes=int(duration_minutes))
    step = timedelta(minutes=int(interval_minutes))

    slots: list[time] = []
    while current < end_time:
        slots.append(current.time())
        current += step

    return slots


def load_doctors(cursor) -> list[dict[str, Any]]:
    """Load doctors from UZIVATEL."""
    cursor.execute(
        """
        SELECT IDUZI,
               JMENO,
               PRIJMENI
        FROM UZIVATEL
        ORDER BY IDUZI
        """
    )

    doctors: list[dict[str, Any]] = []
    for doctor_id, first_name, last_name in cursor.fetchall():
        first_name_text = (first_name or "").strip()
        last_name_text = (last_name or "").strip()
        display_name = f"{first_name_text} {last_name_text}".strip() or "<no name>"
        doctors.append(
            {
                "doctor_id": int(doctor_id),
                "doctor_name": display_name,
            }
        )

    return doctors


def find_schedule_contexts(cursor, doctor_id: int, target_date: date) -> list[dict[str, int]]:
    """Find active appointment-enabled schedule contexts for one doctor/day."""
    day_of_week = target_date.isoweekday()  # Monday=1 ... Sunday=7
    cursor.execute(
        """
        SELECT DISTINCT IDPRAC, TYPTYD
        FROM OBSPRAC
        WHERE IDUZI = ?
          AND OBJED = 'A'
          AND DENTYD = ?
          AND PLATIOD <= ?
          AND (PLATIDO >= ? OR PLATIDO IS NULL)
        ORDER BY IDPRAC, TYPTYD
        """,
        (doctor_id, day_of_week, target_date, target_date),
    )

    return [
        {
            "idprac": int(row[0]),
            "typtyd": int(row[1]),
            "dentyd": day_of_week,
        }
        for row in cursor.fetchall()
    ]


def load_schedule_blocks(cursor, target_date: date, typtyd: int, day_of_week: int, idprac: int, doctor_id: int):
    """Load daily scheduling blocks using OBSDNE_PRAVODLIS_SEL."""
    cursor.execute(
        """
        SELECT CAS, DOBA, INTERVAL
        FROM OBSDNE_PRAVODLIS_SEL(?, ?, ?, ?)
        WHERE IDUZI = ?
        ORDER BY CAS
        """,
        (target_date, typtyd, day_of_week, idprac, doctor_id),
    )
    return cursor.fetchall()


def load_appointments(cursor, idprac: int, doctor_id: int, target_date: date):
    """Load existing appointments from OBJOBJ for a doctor/date/schedule."""
    cursor.execute(
        """
        SELECT CAS, CASDO
        FROM OBJOBJ
        WHERE IDPRAC = ?
          AND IDUZI = ?
          AND DATUM = ?
        ORDER BY CAS
        """,
        (idprac, doctor_id, target_date),
    )
    return cursor.fetchall()


def compute_slots(schedule_blocks, appointments) -> tuple[list[time], list[time], list[time]]:
    """Compute theoretical, occupied, and free slot starts."""
    theoretical_slots: list[time] = []
    for cas, doba, interval in schedule_blocks:
        theoretical_slots.extend(generate_slots(to_time(cas), int(doba), int(interval)))

    occupied_slots: list[time] = []
    free_slots: list[time] = []

    for slot in theoretical_slots:
        is_occupied = False
        for app_start, app_end in appointments:
            start_time = to_time(app_start)
            end_time = to_time(app_end)
            if slot >= start_time and slot < end_time:
                is_occupied = True
                break

        if is_occupied:
            occupied_slots.append(slot)
        else:
            free_slots.append(slot)

    return theoretical_slots, occupied_slots, free_slots


def compute_day_availability(cursor, doctor: dict[str, Any], target_date: date) -> dict[str, Any]:
    """Compute read-only availability details for one doctor and date."""
    doctor_id = int(doctor["doctor_id"])
    contexts = find_schedule_contexts(cursor, doctor_id, target_date)

    context_results: list[dict[str, Any]] = []
    all_theoretical: list[time] = []
    all_occupied: list[time] = []
    all_free: list[time] = []

    for context in contexts:
        idprac = int(context["idprac"])
        typtyd = int(context["typtyd"])
        dentyd = int(context["dentyd"])

        schedule_blocks = load_schedule_blocks(cursor, target_date, typtyd, dentyd, idprac, doctor_id)
        appointments = load_appointments(cursor, idprac, doctor_id, target_date)
        theoretical_slots, occupied_slots, free_slots = compute_slots(schedule_blocks, appointments)

        all_theoretical.extend(theoretical_slots)
        all_occupied.extend(occupied_slots)
        all_free.extend(free_slots)

        context_results.append(
            {
                "idprac": idprac,
                "typtyd": typtyd,
                "dentyd": dentyd,
                "schedule_block_count": len(schedule_blocks),
                "appointment_count": len(appointments),
                "total_slots": len(theoretical_slots),
                "occupied_slots_count": len(occupied_slots),
                "free_slots_count": len(free_slots),
                "free_slots": [format_time(slot) for slot in free_slots],
            }
        )

    unique_free_slots = sorted({slot for slot in all_free})

    return {
        "date": target_date.isoformat(),
        "weekday": target_date.strftime("%A"),
        "has_schedule": bool(contexts),
        "total_slots": len(all_theoretical),
        "occupied_slots_count": len(all_occupied),
        "free_slots_count": len(all_free),
        "free_slots": [format_time(slot) for slot in unique_free_slots],
        "contexts": context_results,
    }


def compute_week_availability(cursor, week_start: date, week_end: date) -> dict[str, Any]:
    """Compute Monday-Friday availability for all doctors."""
    doctors = load_doctors(cursor)
    days = [week_start + timedelta(days=offset) for offset in range((week_end - week_start).days + 1)]

    doctor_results: list[dict[str, Any]] = []
    for doctor in doctors:
        day_results = [compute_day_availability(cursor, doctor, target_date) for target_date in days]
        total_free_slots = sum(day["free_slots_count"] for day in day_results)
        total_slots = sum(day["total_slots"] for day in day_results)
        occupied_slots = sum(day["occupied_slots_count"] for day in day_results)

        doctor_results.append(
            {
                "doctor_id": doctor["doctor_id"],
                "doctor_name": doctor["doctor_name"],
                "total_slots": total_slots,
                "occupied_slots_count": occupied_slots,
                "free_slots_count": total_free_slots,
                "days": day_results,
            }
        )

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "days_included": [day.isoformat() for day in days],
        "doctor_count": len(doctors),
        "doctors": doctor_results,
    }
