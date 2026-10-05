"""Read projection filter checks; fixture substitutes only the Firebird procedure."""
import sqlite3
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from availability_engine import load_appointments, compute_slots


class ProjectionCursor:
    def __init__(self, db):
        self.db = db

    def execute(self, sql, args):
        assert args[:4] == (1, 8, date(2027, 1, 4), date(2027, 1, 4))
        sql = sql.replace('OBJOBJ_SEL(NULL, NULL, ?, ?, ?, ?)', 'projection')
        self.rows = self.db.execute(sql, args[4:]).fetchall()

    def fetchall(self):
        return self.rows


def test_excludes_only_selected_id_retains_same_time_other_booking_and_null_id():
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE projection(IDOBJ,CAS,CASDO)')
        db.executemany('INSERT INTO projection VALUES (?,?,?)', [
            (11, '09:30', '09:40'), (12, '09:30', '09:40'), (None, '09:40', '09:50')])
        cursor = ProjectionCursor(db)
        appointments = load_appointments(cursor, 1, 8, date(2027, 1, 4), exclude_ids=(11,))
        assert appointments == [('09:30', '09:40'), ('09:40', '09:50')]
        assert compute_slots([('09:30', 20, 10)], appointments)[2] == []
        assert db.execute('SELECT COUNT(*) FROM projection').fetchone()[0] == 3


@pytest.mark.parametrize('ids', [('11',), (True,), (-1,), tuple(range(1, 12))])
def test_invalid_exclusion_is_rejected_before_query(ids):
    with pytest.raises(ValueError):
        load_appointments(None, 1, 8, date(2027, 1, 4), exclude_ids=ids)
