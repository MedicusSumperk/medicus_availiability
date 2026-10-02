"""Clinic closures under Czech holiday rules, independent of Medicus schedules.

Source: https://ppropo.mpsv.cz/zakon_245_2000 (sections 1 and 2).
No replacement Monday is added when a fixed holiday falls on a weekend.
"""
from datetime import date, timedelta
from functools import lru_cache


@lru_cache(maxsize=32)
def public_holidays(year: int) -> frozenset[date]:
    # Gregorian computus (Meeus/Jones/Butcher).
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day_zero = divmod(h + l - 7 * m + 114, 31)
    easter = date(year, month, day_zero + 1)
    fixed = ((1, 1), (5, 1), (5, 8), (7, 5), (7, 6), (9, 28),
             (10, 28), (11, 17), (12, 24), (12, 25), (12, 26))
    return frozenset({date(year, month, day) for month, day in fixed}
                     | {easter - timedelta(days=2), easter + timedelta(days=1)})


def is_clinic_workday(day: date) -> bool:
    return day.weekday() < 5 and day not in public_holidays(day.year)
