import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import paired_appointments as p


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.journal = p.Journal(str(Path(self.tmp.name) / 'journal.sqlite'))

    def test_lost_response_replays_without_new_claim(self):
        request = {'idpac': 1, 'request_id': 'a'}
        self.assertIsNone(self.journal.claim('a', request))
        response = {'ok': True, 'appointment_ids': [10], 'laser_appointment_ids': [20]}
        self.journal.state('a', 'committed', response)
        self.assertEqual(self.journal.claim('a', request), response)
        with self.assertRaisesRegex(p.PairUnavailable, 'payload_conflict'):
            self.journal.claim('a', dict(request, idpac=2))

    def test_interrupted_attempt_blocks_other_request_ids(self):
        self.journal.claim('a', {})
        for state in ('started', 'commit_started'):
            self.journal.state('a', state)
            with self.assertRaisesRegex(p.PairUnavailable, 'reconciliation'):
                self.journal.claim('b', {})
        self.journal.state('a', 'rejected', {'ok': False})
        self.assertIsNone(self.journal.claim('b', {}))


class PairTests(unittest.TestCase):
    def setUp(self):
        self.token = 'a' * 32
        self.cfg = {'calendar_id': 5, 'workplace_id': 1, 'booking_activity_id': 28, 'created_by': 2}
        self.request = {'action': 'create', 'service': 'dermatoscope_first', 'idpac': 41738,
                        'patient_verified': True, 'request_id': 'test', 'info': 'test'}
        self.option = {'date': '2027-01-04', 'start_time': '09:30', 'end_time': '09:40',
                       'idcinnosti': 1, 'idprac': 1, 'doctor_id': 8,
                       'scan_slot': {'start_time': '09:15', 'end_time': '09:30'}}

    def test_both_insertions_anonymous_scanner_and_separate_authors(self):
        inserts = []
        def insert(cursor, **values):
            inserts.append(values)
            return {'idobj': len(inserts), **values}
        with patch.object(p, 'option_for_pair', return_value=self.option), patch.object(p, 'validate_info'), \
             patch.object(p.aw, '_insert_appointment', side_effect=insert):
            result = p.insert_pair(Mock(), Mock(), self.request, {'appointment_created_by': 10}, self.cfg)
        self.assertEqual(result['appointment_ids'], [1])
        self.assertEqual(result['laser_appointment_ids'], [2])
        self.assertEqual(inserts[0]['idpac'], 41738)
        self.assertIsNone(inserts[1]['idpac'])
        self.assertEqual(inserts[1]['idcinnosti'], 28)
        self.assertEqual([r['created_by'] for r in inserts], [10, 2])
        self.assertEqual(p.pair_token(inserts[0]['info'], 'MAIN'), p.pair_token(inserts[1]['info'], 'LASER'))

    def test_note_limit_preserves_marker_and_refuses_injection(self):
        text = p.info_text({'info': 'x' * 200}, self.token, 'LASER')
        self.assertEqual(len(text), 80)
        self.assertEqual(p.pair_token(text, 'LASER'), self.token)
        with self.assertRaises(p.PairUnavailable):
            p.info_text({'info': p.marker(self.token, 'MAIN')}, self.token, 'MAIN')

    def test_patient_mismatch_does_not_touch_scanner(self):
        scan = Mock()
        with patch.object(p.aw, '_fetch_appointment_rows', return_value=[{'idpac': 2}]):
            with self.assertRaisesRegex(p.PairUnavailable, 'patient_mismatch'):
                p.load_pair(Mock(), scan, {'appointment_id': 1, 'idpac': 1}, self.cfg)
        scan.execute.assert_not_called()

    def test_unmarked_legacy_booking_not_guessed_by_time(self):
        scan = Mock()
        with patch.object(p.aw, '_fetch_appointment_rows', return_value=[{'idpac': 1, 'info': 'old booking'}]):
            with self.assertRaisesRegex(p.PairUnavailable, 'unmanaged'):
                p.load_pair(Mock(), scan, {'appointment_id': 1, 'idpac': 1}, self.cfg)
        scan.execute.assert_not_called()

    def test_move_preserves_ids_without_temporary_deletions(self):
        group, main, scan = Mock(), Mock(), Mock()
        rows = ({'idobj': 11}, {'idobj': 22}, self.token)
        with patch.object(p, 'load_pair', return_value=rows), patch.object(p, 'option_for_pair', return_value=self.option) as find:
            result = p.change_pair(group, main, scan, dict(self.request, action='reschedule'), self.cfg)
        self.assertEqual(result['appointment_ids'], [11])
        self.assertEqual(result['laser_appointment_ids'], [22])
        group.rollback.assert_not_called()
        group.savepoint.assert_not_called()
        self.assertEqual(find.call_args.kwargs, {'exclude_main_ids': (11,), 'exclude_scan_ids': (22,)})
        for cursor, idobj in ((main, 11), (scan, 22)):
            self.assertEqual(cursor.execute.call_count, 1)
            sql, args = cursor.execute.call_args.args
            self.assertTrue(sql.startswith('UPDATE OBJOBJ'))
            self.assertEqual(args[-1], idobj)

    def test_invalid_move_restores_old_pair_without_update(self):
        group, main, scan = Mock(), Mock(), Mock()
        with patch.object(p, 'load_pair', return_value=({'idobj': 11}, {'idobj': 22}, self.token)), \
             patch.object(p, 'option_for_pair', side_effect=p.PairUnavailable('slot_not_bookable')):
            with self.assertRaises(p.PairUnavailable):
                p.change_pair(group, main, scan, dict(self.request, action='reschedule'), self.cfg)
        group.rollback.assert_not_called()
        main.execute.assert_not_called()
        scan.execute.assert_not_called()

    def test_scanner_capacity_is_read_in_same_transaction(self):
        main, scan = Mock(), Mock()
        with patch.object(p.aw, '_find_exact_bookable_option', return_value=self.option) as find:
            p.option_for_pair(main, scan, self.request, self.cfg)
        self.assertIs(find.call_args.kwargs['scan_calendar'].cursor, scan)


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = {'enable_paired_appointment_writes': True,
                       'paired_write_journal_path': str(Path(self.tmp.name) / 'journal.sqlite')}
        self.request = {'action': 'create', 'idpac': 1, 'patient_verified': True, 'request_id': 'test'}
        self.main, self.scan, self.group = Mock(), Mock(), Mock()
        self.main.cursor.return_value.fetchone.return_value = ('MAIN.FDB',)
        self.scan.cursor.return_value.fetchone.return_value = ('LASER.FDB',)
        self.journal = p.Journal(self.config['paired_write_journal_path'])
        for name, value in [('mapping', ({'database': 'LASER.FDB', 'created_by': 2, 'calendar_id': 5, 'workplace_id': 1}, {'host': 'h', 'port': 1, 'username': 'u', 'password': 'p'}))]:
            context = patch.object(p, name, return_value=value); context.start(); self.addCleanup(context.stop)
        for target, value in [('connect', self.scan), ('ConnectionGroup', self.group)]:
            context = patch.object(p.fdb, target, return_value=value); context.start(); self.addCleanup(context.stop)

    def state(self):
        with self.journal.connect() as db:
            return db.execute('SELECT state FROM attempts').fetchone()[0]

    def test_failure_after_first_insert_rolls_back_both(self):
        with patch.object(p, 'insert_pair', side_effect=RuntimeError('private SQL')):
            response = p.execute_pair(self.main, self.request, self.config)
        self.assertFalse(response['ok'])
        self.assertNotIn('private SQL', str(response))
        self.group.rollback.assert_called_once()
        self.group.commit.assert_not_called()
        self.assertEqual(self.state(), 'rejected')

    def test_uncertain_commit_never_returns_success_or_retries(self):
        self.group.commit.side_effect = OSError('connection lost')
        with patch.object(p, 'insert_pair', return_value={'ok': True}):
            with self.assertRaisesRegex(p.PairUnavailable, 'uncertain'):
                p.execute_pair(self.main, self.request, self.config)
        self.assertEqual(self.state(), 'commit_started')
        with self.assertRaisesRegex(p.PairUnavailable, 'reconciliation'):
            p.execute_pair(self.main, dict(self.request, request_id='new'), self.config)
        self.assertEqual(self.group.commit.call_count, 1)

    def test_success_replays_without_second_distributed_commit(self):
        with patch.object(p, 'insert_pair', return_value={'ok': True, 'appointment_ids': [11]}) as insert:
            first = p.execute_pair(self.main, self.request, self.config)
            self.assertEqual(p.execute_pair(self.main, self.request, self.config), first)
        self.assertEqual(self.state(), 'committed')
        self.group.commit.assert_called_once()
        insert.assert_called_once()

    def test_staff_first_pair_revalidates_without_reserving_gui_table(self):
        calls = []
        with patch.object(p, 'insert_pair', side_effect=lambda *a: calls.append('write') or {'ok': True}):
            p.execute_pair(self.main, self.request, self.config,
                           precondition=lambda *a: calls.append('revalidate'))
        self.assertEqual(calls, ['revalidate', 'write'])
        tpb = self.group.begin.call_args.args[0]
        self.assertEqual(len(tpb.table_reservation), 0)
        self.assertEqual(tpb.isolation_level, p.fdb.isc_tpb_concurrency)
        self.assertEqual(tpb.lock_resolution, p.fdb.isc_tpb_nowait)
        self.group.commit.assert_called_once()

    def test_staff_first_conflict_at_revalidation_never_inserts(self):
        with patch.object(p, 'insert_pair') as insert:
            response = p.execute_pair(self.main, self.request, self.config,
                precondition=Mock(side_effect=p.PairUnavailable('slot_not_bookable')))
        self.assertFalse(response['booking_confirmed'])
        self.assertEqual(response['status'], 'slot_not_bookable')
        insert.assert_not_called()
        self.group.commit.assert_not_called()
        self.group.rollback.assert_called_once()

    def test_staff_first_single_revalidates_without_reserving_gui_table(self):
        calls = []
        writer = Mock(side_effect=lambda *a: calls.append('write') or {'ok': True})
        with patch.object(p, 'is_pair_request', return_value=False):
            p.write_transaction(self.main, self.request, {'enable_appointment_writes': True},
                writer, precondition=lambda *a: calls.append('revalidate'))
        self.assertEqual(calls, ['revalidate', 'write'])
        self.assertEqual(len(self.main.begin.call_args.args[0].table_reservation), 0)
        self.main.commit.assert_called_once()

    def test_busy_medicus_fails_before_any_write(self):
        self.group.begin.side_effect = p.fdb.DatabaseError('lock conflict', -901, 335544345)
        with patch.object(p, 'insert_pair') as insert:
            response = p.execute_pair(self.main, self.request, self.config)
        self.assertEqual(response['status'], 'calendar_busy_retry_later')
        self.assertEqual(self.state(), 'rejected')
        insert.assert_not_called()
        self.group.commit.assert_not_called()

    def test_failed_journal_preparation_cannot_commit(self):
        with patch.object(p, 'insert_pair', return_value={'ok': True}), patch.object(p.Journal, 'state', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                p.execute_pair(self.main, self.request, self.config)
        self.group.commit.assert_not_called()
        self.group.rollback.assert_called_once()
        self.assertEqual(self.state(), 'started')

    def test_lost_local_ack_after_commit_stays_unresolved(self):
        original = p.Journal.state
        def state(journal, key, status, result=None):
            if status == 'committed':
                raise OSError('disk full')
            return original(journal, key, status, result)
        with patch.object(p, 'insert_pair', return_value={'ok': True}), patch.object(p.Journal, 'state', state):
            with self.assertRaisesRegex(p.PairUnavailable, 'uncertain'):
                p.execute_pair(self.main, self.request, self.config)
        self.group.commit.assert_called_once()
        self.assertEqual(self.state(), 'commit_started')

    def test_cancel_replay_routes_to_journal_after_rows_disappeared(self):
        request = dict(self.request, action='cancel', appointment_id=11)
        self.journal.claim('test', request)
        self.journal.state('test', 'committed', {'ok': True, 'status': 'cancelled'})
        with patch.object(p, 'is_pair_request', return_value=False), patch.object(p, 'execute_pair', return_value={'ok': True}) as execute:
            p.write_transaction(self.main, request, dict(self.config, enable_appointment_writes=True))
        execute.assert_called_once()


if __name__ == '__main__':
    unittest.main()
