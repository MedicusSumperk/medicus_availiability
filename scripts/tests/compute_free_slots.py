"""Read-only script to compute exact free appointment slots for a known test case."""

import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db import connect_to_db


DOCTOR_ID = 1
TARGET_DATE = "2026-04-10"
IDPRAC = 1
TYPTYD = 4
DENTYD = 5


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
    """Generate slot starts from [start_time, start_time + duration)."""
    base_day = date(2000, 1, 1)
    start_dt = datetime.combine(base_day, start_time)
    end_dt = start_dt + timedelta(minutes=int(duration_minutes))
    step = timedelta(minutes=int(interval_minutes))

    slots: list[time] = []
    current = start_dt
    while current < end_dt:
        slots.append(current.time())
        current += step

    return slots


def compute_free_slots() -> None:
    """Compute theoretical, occupied, and free slots for the known schedule case."""
    connection = None

    try:
        connection = connect_to_db()
        cursor = connection.cursor()

        target_date = date.fromisoformat(TARGET_DATE)

        cursor.execute(
            """
            SELECT CAS, DOBA, INTERVAL
            FROM OBSDNE_PRAVODLIS_SEL(?, ?, ?, ?)
            WHERE IDUZI = ?
            ORDER BY CAS
            """,
            (target_date, TYPTYD, DENTYD, IDPRAC, DOCTOR_ID),
        )
        schedule_blocks = cursor.fetchall()

        theoretical_slots: list[time] = []
        for cas, doba, interval in schedule_blocks:
            block_slots = _generate_slots(_to_time(cas), int(doba), int(interval))
            theoretical_slots.extend(block_slots)

        cursor.execute(
            """
            SELECT CAS, CASDO
            FROM OBJOBJ
            WHERE IDPRAC = ?
              AND IDUZI = ?
              AND DATUM = ?
            ORDER BY CAS
            """,
            (IDPRAC, DOCTOR_ID, target_date),
        )
        appointments = cursor.fetchall()

        occupied_slots: list[time] = []
        free_slots: list[time] = []

        for slot in theoretical_slots:
            slot_occupied = False
            for app_cas, app_casdo in appointments:
                app_start = _to_time(app_cas)
                app_end = _to_time(app_casdo)
                if slot >= app_start and slot < app_end:
                    slot_occupied = True
                    break

            if slot_occupied:
                occupied_slots.append(slot)
            else:
                free_slots.append(slot)

        fmt = "%H:%M"
        theoretical_text = [slot.strftime(fmt) for slot in theoretical_slots]
        occupied_text = [slot.strftime(fmt) for slot in occupied_slots]
        free_text = [slot.strftime(fmt) for slot in free_slots]

        print(f"Doctor ID: {DOCTOR_ID}")
        print(f"Target date: {TARGET_DATE}")
        print(f"IDPRAC: {IDPRAC}, TYPTYD: {TYPTYD}, DENTYD: {DENTYD}")

        print("\nTheoretical slots:")
        print(", ".join(theoretical_text) if theoretical_text else "<none>")

        print("\nOccupied slots:")
        print(", ".join(occupied_text) if occupied_text else "<none>")

        print("\nFree slots:")
        print(", ".join(free_text) if free_text else "<none>")

        print("\nSummary")
        print(f"Total theoretical slots: {len(theoretical_slots)}")
        print(f"Total occupied slots: {len(occupied_slots)}")
        print(f"Total free slots: {len(free_slots)}")
        print("Expected for this test case: theoretical=24, free=0")

    except Exception as error:  # noqa: BLE001
        print(f"Failed to compute free slots: {error}")
    finally:
        if connection is not None:
            connection.close()


def main() -> None:
    """Entry point for direct script execution."""
    compute_free_slots()


if __name__ == "__main__":
    main()
