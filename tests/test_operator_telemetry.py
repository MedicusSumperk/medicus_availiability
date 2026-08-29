import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import operator_telemetry  # noqa: E402


class OperatorTelemetryTests(unittest.TestCase):
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
