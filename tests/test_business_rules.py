import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import availability_search  # noqa: E402
import appointment_write  # noqa: E402
from business_rules import (  # noqa: E402
    afternoon_bucket_for_time,
    agent_capabilities,
    agent_context_overlay,
    load_business_rules,
    service_followup_enabled,
    validate_business_rules,
)
from handoff_summary import build_handoff_summary  # noqa: E402
from render_business_rules import render_business_rules  # noqa: E402


class BusinessRulesTests(unittest.TestCase):
    def test_business_rules_are_valid_and_renderable(self):
        rules = load_business_rules()

        self.assertEqual(validate_business_rules(rules), [])
        rendered = render_business_rules(rules)
        self.assertIn("Current Business Rules", rendered)
        self.assertIn("Rule Matrix", rendered)
        self.assertIn("Config path", rendered)
        self.assertIn("How to change", rendered)
        self.assertIn("Before-time emergency gate", rendered)
        self.assertIn("operational_rules.before_time_requires_emergency.enabled", rendered)
        self.assertIn("Set false to return early slots normally", rendered)
        self.assertIn("Rostislav Bednar", rendered)

    def test_rules_overlay_uses_business_doctor_exclusions(self):
        rules = load_business_rules()
        overlay = agent_context_overlay(rules)

        self.assertIn(4, overlay["system_excluded_doctor_ids"])
        self.assertIn("skin", overlay["services"])
        self.assertEqual(overlay["services"]["plasma"]["appointment_duration_minutes"], 30)

    def test_render_output_can_be_written_for_review(self):
        rules = load_business_rules()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "rules.md"
            output_path.write_text(render_business_rules(rules), encoding="utf-8")

            self.assertIn("Services", output_path.read_text(encoding="utf-8"))

    def test_handoff_summary_callback(self):
        summary = build_handoff_summary(
            {
                "mode": "callback",
                "caller_phone": "777111222",
                "reason": "new_patient",
                "conversation_summary": "Caller needs a new card.",
            }
        )

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["mode"], "callback")
        self.assertIn("777111222", summary["summary_for_staff"])
        self.assertIsNone(summary["transfer_target"])

    def test_handoff_summary_live_transfer(self):
        summary = build_handoff_summary(
            {"mode": "live_transfer", "reason": "medical_question"},
            {"handoff_phone": "+420123456789"},
        )

        self.assertEqual(summary["transfer_target"], "+420123456789")

    def test_agent_capabilities_split_bookable_and_handoff_services(self):
        capabilities = agent_capabilities(
            {
                "version": "test",
                "services": {
                    "skin": {
                        "label": "Kozni vysetreni",
                        "agent_can_offer_availability": True,
                        "agent_can_book_finally": True,
                        "followup": {"create": True},
                    },
                    "plasma": {
                        "label": "Plazma",
                        "agent_can_offer_availability": False,
                        "agent_can_book_finally": False,
                    },
                },
            }
        )

        self.assertEqual([service["key"] for service in capabilities["bookable_services"]], ["skin"])
        self.assertEqual([service["key"] for service in capabilities["handoff_services"]], ["plasma"])
        self.assertTrue(capabilities["bookable_services"][0]["followup_enabled"])
        self.assertIn("Kozni vysetreni", capabilities["voice_answer_cs"])

    def test_service_followup_enabled_helper(self):
        self.assertTrue(service_followup_enabled({"services": {"skin": {"followup": {"create": True}}}}, "skin"))
        self.assertFalse(service_followup_enabled({"services": {"skin": {"followup": {"create": False}}}}, "skin"))

    def test_afternoon_bucket_can_be_limited_by_weekday(self):
        rules = {
            "operational_rules": {
                "afternoon_arrival_buckets": [
                    {
                        "enabled": True,
                        "service": "skin",
                        "weekdays": [3],
                        "time_from": "15:00",
                        "time_to": "16:00",
                        "spoken_time_label": "15:00",
                    }
                ]
            }
        }

        self.assertIsNone(afternoon_bucket_for_time(rules, "skin", "15:10", weekday_iso=2))
        self.assertEqual(
            afternoon_bucket_for_time(rules, "skin", "15:10", weekday_iso=3)["spoken_time_label"],
            "15:00",
        )

    def test_write_revalidation_prefers_technical_start_time(self):
        captured_request = {}

        def fake_search(_cursor, request):
            captured_request.update(request)
            return {
                "filters": {"doctor": {"match_type": "partial"}},
                "options": [
                    {
                        "date": "2026-07-27",
                        "service": "skin",
                        "start_time": "15:20",
                        "end_time": "15:30",
                        "doctor_id": 2,
                        "doctor_name": "Rostislav Bednar",
                        "idprac": 1,
                        "idcinnosti": None,
                    }
                ],
            }

        with patch.object(appointment_write, "search_availability", side_effect=fake_search):
            option = appointment_write._find_exact_bookable_option(
                object(),
                {
                    "service": "skin",
                    "date": "2026-07-27",
                    "time": "15:00",
                    "start_time": "15:20",
                    "doctor_name": "Bednar",
                },
            )

        self.assertNotIn("error", option)
        self.assertEqual(captured_request["time_from"], "15:20")
        self.assertEqual(captured_request["time_to"], "15:20")

    def test_skin_followup_disabled_creates_single_row(self):
        inserted = []

        def fake_insert(_cursor, **kwargs):
            row = {"idobj": len(inserted) + 1, **kwargs}
            inserted.append(row)
            return row

        with (
            patch.object(
                appointment_write,
                "load_business_rules",
                return_value={"services": {"skin": {"followup": {"create": False}}}},
            ),
            patch.object(
                appointment_write,
                "_find_exact_bookable_option",
                return_value={
                    "service": "skin",
                    "date": "2026-07-27",
                    "start_time": "15:20",
                    "end_time": "15:30",
                    "doctor_id": 2,
                    "idprac": 1,
                    "idcinnosti": None,
                },
            ),
            patch.object(appointment_write, "_insert_appointment", side_effect=fake_insert),
        ):
            response = appointment_write._create_appointments(
                object(),
                {
                    "service": "skin",
                    "idpac": 123,
                    "patient_verified": True,
                    "date": "2026-07-27",
                    "start_time": "15:20",
                    "doctor_id": 2,
                },
                {"appointment_created_by": 10},
            )

        self.assertTrue(response["ok"])
        self.assertEqual(len(inserted), 1)


class AvailabilityRulesTests(unittest.TestCase):
    def setUp(self):
        self.base_config = {
            "slot_interval_minutes": 10,
            "services": {
                "skin": {"label": "Skin", "use_schedule_interval": True, "idcinnosti": None},
                "plasma": {"label": "Plasma", "appointment_duration_minutes": 30, "idcinnosti": 3},
            },
            "dermatoscope_blocking_idcinnosti": [],
            "allowed_doctor_ids": [],
            "system_excluded_doctor_ids": [],
            "excluded_doctor_ids": [],
        }
        self.doctors = [
            {"doctor_id": 2, "doctor_name": "Rostislav Bednar"},
            {"doctor_id": 4, "doctor_name": "Rostislav Bednar duplicate"},
            {"doctor_id": 8, "doctor_name": "Maria Bartonova"},
        ]

    def _availability(self, _cursor, doctor, _target_date):
        if int(doctor["doctor_id"]) == 4:
            self.fail("globally excluded doctor should not be searched")
        return {
            "has_schedule": True,
            "contexts": [
                {
                    "idprac": 1,
                    "slot_interval_minutes": 10,
                    "free_slots": [
                        "07:50",
                        "08:00",
                        "08:10",
                        "15:00",
                        "15:10",
                        "15:20",
                        "15:30",
                        "15:40",
                        "15:50",
                        "16:00",
                    ],
                }
            ],
        }

    def test_before_8_slots_are_hidden_without_emergency(self):
        with (
            patch.object(availability_search, "load_doctors", return_value=self.doctors),
            patch.object(availability_search, "compute_day_availability", side_effect=self._availability),
            patch.object(availability_search, "load_dermatoscope_blockers", return_value=[]),
        ):
            response = availability_search.search_availability(
                object(),
                {
                    "service": "skin",
                    "date_from": "2026-07-27",
                    "date_to": "2026-07-27",
                    "time_from": "07:00",
                    "time_to": "08:00",
                    "limit": 3,
                },
                self.base_config,
            )

        self.assertNotIn("07:50", [option["start_time"] for option in response["options"]])
        self.assertIn("08:00", [option["start_time"] for option in response["options"]])

    def test_before_8_slots_are_returned_with_emergency(self):
        with (
            patch.object(availability_search, "load_doctors", return_value=self.doctors),
            patch.object(availability_search, "compute_day_availability", side_effect=self._availability),
            patch.object(availability_search, "load_dermatoscope_blockers", return_value=[]),
        ):
            response = availability_search.search_availability(
                object(),
                {
                    "service": "skin",
                    "date_from": "2026-07-27",
                    "date_to": "2026-07-27",
                    "time_from": "07:00",
                    "time_to": "08:00",
                    "limit": 3,
                    "emergency": True,
                },
                self.base_config,
            )

        self.assertIn("07:50", [option["start_time"] for option in response["options"]])

    def test_afternoon_option_has_technical_and_spoken_times(self):
        with (
            patch.object(availability_search, "load_doctors", return_value=self.doctors),
            patch.object(availability_search, "compute_day_availability", side_effect=self._availability),
            patch.object(availability_search, "load_dermatoscope_blockers", return_value=[]),
        ):
            response = availability_search.search_availability(
                object(),
                {
                    "service": "skin",
                    "date_from": "2026-07-27",
                    "date_to": "2026-07-27",
                    "time_from": "15:20",
                    "time_to": "15:20",
                    "limit": 1,
                },
                self.base_config,
            )

        option = response["options"][0]
        self.assertEqual(option["start_time"], "15:20")
        self.assertEqual(option["technical_start_time"], "15:20")
        self.assertEqual(option["spoken_time_label"], "15:00")

    def test_afternoon_bucket_options_are_deduplicated_by_spoken_time(self):
        with (
            patch.object(availability_search, "load_doctors", return_value=self.doctors),
            patch.object(availability_search, "compute_day_availability", side_effect=self._availability),
            patch.object(availability_search, "load_dermatoscope_blockers", return_value=[]),
        ):
            response = availability_search.search_availability(
                object(),
                {
                    "service": "skin",
                    "date_from": "2026-07-27",
                    "date_to": "2026-07-27",
                    "time_from": "15:00",
                    "time_to": "16:00",
                    "doctor_id": 2,
                    "limit": 3,
                },
                self.base_config,
            )

        spoken_times = [option["spoken_time_label"] for option in response["options"]]
        self.assertEqual(spoken_times.count("15:00"), 1)

    def test_first_available_extends_short_default_window(self):
        def delayed_availability(_cursor, _doctor, target_date):
            if target_date.isoformat() != "2026-07-31":
                return {"has_schedule": True, "contexts": [{"idprac": 1, "slot_interval_minutes": 10, "free_slots": []}]}
            return {
                "has_schedule": True,
                "contexts": [{"idprac": 1, "slot_interval_minutes": 10, "free_slots": ["09:00", "09:10"]}],
            }

        with (
            patch.object(availability_search, "load_doctors", return_value=[self.doctors[0]]),
            patch.object(availability_search, "compute_day_availability", side_effect=delayed_availability),
            patch.object(availability_search, "load_dermatoscope_blockers", return_value=[]),
        ):
            response = availability_search.search_availability(
                object(),
                {
                    "service": "skin",
                    "date_from": "2026-07-27",
                    "days_ahead": 2,
                    "max_days_ahead": 7,
                    "limit": 1,
                },
                self.base_config,
            )

        self.assertEqual(response["date_range"]["searched_days_ahead"], 7)
        self.assertEqual(response["options"][0]["date"], "2026-07-31")

    def test_plasma_service_is_not_in_first_production_availability_scope(self):
        with (
            patch.object(availability_search, "load_doctors", return_value=self.doctors),
            patch.object(availability_search, "compute_day_availability", side_effect=self._availability),
            patch.object(availability_search, "load_dermatoscope_blockers", return_value=[]),
        ):
            with self.assertRaisesRegex(ValueError, "not agent-facing"):
                availability_search.search_availability(
                    object(),
                    {
                        "service": "plasma",
                        "date_from": "2026-07-27",
                        "date_to": "2026-07-27",
                        "limit": 1,
                    },
                    self.base_config,
                )

    def test_skin_options_do_not_require_followup_when_disabled(self):
        options, rejections = availability_search.build_skin_options(
            {
                "idprac": 1,
                "slot_interval_minutes": 10,
                "free_slots": ["09:00"],
            },
            [],
            {
                "label": "Skin",
                "use_schedule_interval": True,
                "idcinnosti": None,
                "create_followup_dermatoscope": False,
            },
            10,
            3,
        )

        self.assertEqual(len(options), 1)
        self.assertNotIn("followup_dermatoscope_slot", options[0])
        self.assertEqual(rejections, [])


if __name__ == "__main__":
    unittest.main()
