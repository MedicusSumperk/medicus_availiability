import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import paired_recovery as recovery
from paired_appointments import marker


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.token = 'a' * 32
        self.rows = [dict(database=role, idobj=i, idpac=1 if role == 'MAIN' else None,
                          idprac=1, doctor_id=i, date='2027-01-04', start_time='09:30',
                          end_time='09:40', typ=1, prisel='N', idcinnosti=i,
                          info=marker(self.token, role) + 'private patient note')
                     for role, i in [('MAIN', 1), ('LASER', 2)]]
        self.attempt = {'state': 'commit_started', 'result': {'ok': True, 'status': 'created',
                        'pair_id': self.token, 'appointments': self.rows}}

    def inspect(self, rows):
        with patch.object(recovery, '_fetch_appointment_rows', side_effect=rows):
            return recovery.inspect_attempt(self.attempt, object(), object())

    def test_complete_visible_pair_is_not_automatic_retry_permission(self):
        report = self.inspect([[self.rows[0]], [self.rows[1]]])
        self.assertEqual(report['observation'], 'both_expected_rows_visible')
        self.assertFalse(report['safe_to_retry'])
        self.assertFalse(report['journal_changed'])
        self.assertNotIn('private patient note', json.dumps(report))
        self.assertNotIn('idpac', json.dumps(report))

    def test_partial_pair_needs_manual_reconciliation(self):
        report = self.inspect([[self.rows[0]], []])
        self.assertEqual(report['observation'], 'partial_or_modified_pair')

    def test_changed_time_or_marker_never_matches(self):
        for change in ({'start_time': '10:00'}, {'info': 'edited'}, {'idpac': 999}):
            with self.subTest(change=change):
                report = self.inspect([[dict(self.rows[0], **change)], [self.rows[1]]])
                self.assertEqual(report['observation'], 'partial_or_modified_pair')

    def test_missing_both_does_not_prove_rollback(self):
        report = self.inspect([[], []])
        self.assertEqual(report['observation'], 'neither_expected_row_visible')
        self.assertFalse(report['safe_to_retry'])

    def test_cancel_absence_does_not_silently_unlock_journal(self):
        self.attempt['result']['status'] = 'cancelled'
        report = self.inspect([[], []])
        self.assertEqual(report['observation'], 'both_rows_absent')
        self.assertFalse(report['automatic_resolution'])

    def test_started_without_result_does_not_query_medicus(self):
        with patch.object(recovery, '_fetch_appointment_rows') as fetch:
            report = recovery.inspect_attempt({'state': 'started', 'result': None}, None, None)
        fetch.assert_not_called()
        self.assertEqual(report['observation'], 'no_recorded_commit_intent')

    def test_journal_read_is_read_only_and_missing_path_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'journal.sqlite'
            with self.assertRaises(ValueError):
                recovery.read_attempt(path, 'one')
            self.assertFalse(path.exists())
            db = sqlite3.connect(path)
            db.execute('CREATE TABLE attempts (key TEXT,state TEXT,result TEXT)')
            db.execute('INSERT INTO attempts VALUES (?,?,?)', ('one', 'commit_started', json.dumps(self.attempt['result'])))
            db.commit(); db.close()
            before = path.read_bytes()
            self.assertEqual(recovery.read_attempt(path, 'one'), self.attempt)
            self.assertEqual(before, path.read_bytes())

    def live_inspection(self, main, laser, inspect_error=None, connect_error=None):
        from contextlib import ExitStack
        with ExitStack() as stack:
            stack.enter_context(patch.object(recovery, 'read_attempt', return_value=self.attempt))
            stack.enter_context(patch('laser_calendar.CONFIG_PATH', Mock(
                read_text=Mock(return_value=json.dumps({'enabled': True, 'database': 'synthetic'})))))
            stack.enter_context(patch('db._load_db_config', return_value={
                'host': 'test', 'port': 3050, 'username': 'test', 'password': 'test'}))
            stack.enter_context(patch('db.connect_to_db', return_value=main))
            stack.enter_context(patch.object(recovery.fdb, 'connect', return_value=laser,
                                            side_effect=connect_error))
            stack.enter_context(patch.object(recovery, 'inspect_attempt', return_value={},
                                            side_effect=inspect_error))
            return recovery.inspect_live('unused', 'synthetic')

    def test_cleanup_failure_still_releases_both_connections(self):
        for method in ('rollback', 'close'):
            with self.subTest(method=method):
                main, laser = Mock(), Mock()
                getattr(laser, method).side_effect = RuntimeError('cleanup failed')
                with self.assertRaisesRegex(RuntimeError, 'cleanup failed'):
                    self.live_inspection(main, laser)
                for connection in (main, laser):
                    connection.rollback.assert_called_once_with()
                    connection.close.assert_called_once_with()
                    connection.commit.assert_not_called()

    def test_original_inspection_failure_survives_cleanup_failure(self):
        main, laser = Mock(), Mock()
        laser.rollback.side_effect = RuntimeError('cleanup failed')
        with self.assertRaisesRegex(ValueError, 'inspection failed'):
            self.live_inspection(main, laser, inspect_error=ValueError('inspection failed'))
        main.close.assert_called_once_with()
        laser.close.assert_called_once_with()

    def test_second_connection_failure_releases_first(self):
        main, laser = Mock(), Mock()
        with self.assertRaisesRegex(RuntimeError, 'connect failed'):
            self.live_inspection(main, laser, connect_error=RuntimeError('connect failed'))
        main.rollback.assert_called_once_with()
        main.close.assert_called_once_with()
        laser.begin.assert_not_called()


if __name__ == '__main__':
    unittest.main()
