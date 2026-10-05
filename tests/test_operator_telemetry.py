import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import operator_telemetry  # noqa: E402


class OperatorTelemetryTests(unittest.TestCase):
    def test_staff_request_uses_durable_identity_instead_of_process_sequence(self):
        config = {'operator_ingest_url': 'https://operator.example.test',
                  'operator_ingest_token': 'token', 'operator_tenant_key': 'test'}
        with patch.object(operator_telemetry._EXECUTOR, 'submit') as submit:
            operator_telemetry.emit_tool_event(
                config, conversation_id='conv_test', tool_name='appointment_write',
                endpoint='/staff/proposals/{proposal_id}/approve', started_monotonic=0,
                request_payload={}, response_payload={'ok': True}, http_status=200,
                business_ok=True, request_id='staff:proposal_test')
        tool = submit.call_args.args[2]['tool_call']
        self.assertEqual(tool['request_id'], 'staff:proposal_test')
        self.assertIsNone(tool['sequence_no'])

    def test_move_evidence_keeps_calendar_but_redacts_notes(self):
        result = operator_telemetry._sanitize({'appointments_before_move': [
            {'idobj': 11, 'idpac': 123, 'database': 'MAIN', 'info': 'private clinical note'}]})
        row = result['appointments_before_move'][0]
        self.assertEqual(row['database'], 'MAIN')
        self.assertEqual(row['idobj'], 11)
        self.assertEqual(row['info'], '[REDACTED]')
        self.assertEqual(row['idpac'], '[REDACTED]')

    def test_scheduling_failure_never_escapes_or_logs_sensitive_details(self):
        with (patch.object(operator_telemetry, '_emit_tool_event', side_effect=RuntimeError('secret-patient-content')),
              self.assertLogs(operator_telemetry.LOGGER, level='WARNING') as logs):
            operator_telemetry.emit_tool_event()
        self.assertNotIn('secret-patient-content', str(logs.output))

    def test_delivery_failure_does_not_log_response_or_credentials(self):
        with (patch.object(operator_telemetry, 'urlopen', side_effect=OSError('secret-patient-content')),
              self.assertLogs(operator_telemetry.LOGGER, level='WARNING') as logs):
            operator_telemetry._post_event({'url':'https://example.test','token':'secret-token','timeout':1}, {})
        self.assertNotIn('secret-patient-content', str(logs.output))
        self.assertNotIn('secret-token', str(logs.output))

    def test_patient_identity_is_removed_from_nested_json_without_losing_slots(self):
        payload={'first_name':'Sensitive','last_name':'Patient','birth_date':'1990-01-01',
                 'options_json':json.dumps([{'patient_verification_token':'private-token',
                                            'date':'2026-10-07','start_time':'13:20',
                                            'doctor_name':'Test doctor'}])}
        safe=operator_telemetry._sanitize(payload)
        self.assertEqual(safe['first_name'],'[REDACTED]')
        self.assertEqual(safe['last_name'],'[REDACTED]')
        self.assertEqual(safe['birth_date'],'[REDACTED]')
        option=json.loads(safe['options_json'])[0]
        self.assertEqual(option['patient_verification_token'],'[REDACTED]')
        self.assertEqual(option['start_time'],'13:20')
        self.assertEqual(option['doctor_name'],'Test doctor')

    def test_disabled_telemetry_does_not_schedule_delivery(self):
        with patch.object(operator_telemetry._EXECUTOR, "submit") as submit:
            operator_telemetry.emit_tool_event(
                {},
                conversation_id="conv_1",
                tool_name="patient_lookup",
                endpoint="/patient-lookup",
                started_monotonic=0,
                request_payload={},
                response_payload={"ok": True},
                http_status=200,
                business_ok=True,
            )
        submit.assert_not_called()

    def test_payload_is_redacted_before_background_delivery(self):
        config = {
            "operator_ingest_url": "https://operator.example.test",
            "operator_ingest_token": "token",
            "operator_tenant_key": "laser_medicus",
        }
        with patch.object(operator_telemetry._EXECUTOR, "submit") as submit:
            operator_telemetry.emit_tool_event(
                config,
                conversation_id="conv_1",
                tool_name="patient_lookup",
                endpoint="/patient-lookup",
                started_monotonic=0,
                request_payload={"phone": "+420777123456", "birth_number": "1234567890", "idpac": 42},
                response_payload={"ok": True},
                http_status=200,
                business_ok=True,
                trace_id="trace_1",
            )
        submit.assert_called_once()
        payload = submit.call_args.args[2]
        request_safe = payload["tool_call"]["request_safe"]
        self.assertEqual(request_safe["birth_number"], "[REDACTED]")
        self.assertEqual(request_safe["idpac"], "[REDACTED]")
        self.assertTrue(request_safe["phone"].endswith("456"))


if __name__ == "__main__":
    unittest.main()
