"""Interactive CLI for checking free appointment slots for a doctor and date."""

from __future__ import annotations

import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from db import connect_to_db


DATE_FORMAT = "%Y-%m-%d"


def _to_time(value) -> time:
    """Convert DB value to datetime.time."""
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


def _generate_slots(start_time: time, duration_minutes: int, interval_minutes: int) -> list[time]:
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


def _load_doctors(cursor) -> list[tuple[int, str]]:
    """Load doctors from UZIVATEL and return (IDUZI, display_name)."""
    cursor.execute(
        """
        SELECT IDUZI,
               JMENO,
               PRIJMENI
        FROM UZIVATEL
        ORDER BY IDUZI
        """
    )

    doctors: list[tuple[int, str]] = []
    for doctor_id, first_name, last_name in cursor.fetchall():
        first_name_text = (first_name or "").strip()
        last_name_text = (last_name or "").strip()
        display_name = f"{first_name_text} {last_name_text}".strip() or "<no name>"
        doctors.append((int(doctor_id), display_name))

    return doctors


def _select_doctor(doctors: list[tuple[int, str]]) -> tuple[int, str]:
    """Prompt user to choose a doctor by number."""
    if not doctors:
        raise ValueError("No doctors found in UZIVATEL")

    print("Available doctors:")
    for index, (doctor_id, doctor_name) in enumerate(doctors, start=1):
        print(f"{index}. {doctor_name} (IDUZI={doctor_id})")

    while True:
        raw_input_value = input("Select doctor number: ").strip()
        if not raw_input_value.isdigit():
            print("Invalid input. Enter a number from the list.")
            continue

        selected_index = int(raw_input_value)
        if 1 <= selected_index <= len(doctors):
            return doctors[selected_index - 1]

        print(f"Invalid doctor number. Enter a value between 1 and {len(doctors)}.")


def _read_target_date() -> date:
    """Prompt user for target date in YYYY-MM-DD format."""
    while True:
        raw_input_value = input("Enter target date (YYYY-MM-DD): ").strip()
        try:
            return datetime.strptime(raw_input_value, DATE_FORMAT).date()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")


def _find_schedule_context(cursor, doctor_id: int, target_date: date, day_of_week: int):
    """Find active scheduling context (IDPRAC, TYPTYD) from OBSPRAC."""
    cursor.execute(
        """
        SELECT FIRST 1 IDPRAC, TYPTYD
        FROM OBSPRAC
        WHERE IDUZI = ?
          AND OBJED = 'A'
          AND DENTYD = ?
          AND PLATIOD <= ?
          AND (PLATIDO >= ? OR PLATIDO IS NULL)
        ORDER BY PLATIOD DESC
        """,
        (doctor_id, day_of_week, target_date, target_date),
    )
    return cursor.fetchone()


def _load_schedule_blocks(cursor, target_date: date, typtyd: int, day_of_week: int, idprac: int, doctor_id: int):
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


def _load_appointments(cursor, idprac: int, doctor_id: int, target_date: date):
    """Load appointments for selected doctor/date from OBJOBJ."""
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


def _compute_free_slots(schedule_blocks, appointments) -> tuple[list[time], list[time], list[time]]:
    """Compute theoretical, occupied, and free slot starts."""
    theoretical_slots: list[time] = []
    for cas, doba, interval in schedule_blocks:
        theoretical_slots.extend(_generate_slots(_to_time(cas), int(doba), int(interval)))

    occupied_slots: list[time] = []
    free_slots: list[time] = []

    for slot in theoretical_slots:
        is_occupied = False
        for app_start, app_end in appointments:
            start_time = _to_time(app_start)
            end_time = _to_time(app_end)
            if slot >= start_time and slot < end_time:
                is_occupied = True
                break

        if is_occupied:
            occupied_slots.append(slot)
        else:
            free_slots.append(slot)

    return theoretical_slots, occupied_slots, free_slots


def main() -> None:
    """Run interactive doctor/date availability lookup."""
    connection = None

    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        doctors = _load_doctors(cursor)
        doctor_id, doctor_name = _select_doctor(doctors)

        target_date = _read_target_date()
        day_of_week = target_date.isoweekday()  # Monday=1 ... Sunday=7

        context_row = _find_schedule_context(cursor, doctor_id, target_date, day_of_week)
        if not context_row:
            print("No valid schedule found for this doctor and date")
            return

        idprac, typtyd = int(context_row[0]), int(context_row[1])

        schedule_blocks = _load_schedule_blocks(cursor, target_date, typtyd, day_of_week, idprac, doctor_id)
        appointments = _load_appointments(cursor, idprac, doctor_id, target_date)

        theoretical_slots, occupied_slots, free_slots = _compute_free_slots(schedule_blocks, appointments)

        fmt = "%H:%M"
        print("\nDoctor:", f"{doctor_name} (IDUZI={doctor_id})")
        print("Date:", target_date.isoformat())
        print("Total slots:", len(theoretical_slots))
        print("Occupied slots:", len(occupied_slots))
        print("Free slots:", len(free_slots))

        if free_slots:
            print("Free slot times:", ", ".join(slot.strftime(fmt) for slot in free_slots))
        else:
            print("No free slots available")

    except Exception as error:  # noqa: BLE001
        print(f"Error: {error}")
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
