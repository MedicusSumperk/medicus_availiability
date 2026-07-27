import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from patient_lookup import (  # noqa: E402
    _name_fallback_request,
    _normalize_text,
    _patient_matches_requested_names,
    lookup_patient,
)


class FakeLookupCursor:
    def __init__(self, query_results=None):
        self._results = []
        self._query_results = list(query_results or [])
        self.patient_queries = []

    def execute(self, query, params=()):
        if "RDB$RELATION_FIELDS" in query:
            self._results = [
                ("IDPAC", 8, 4),
                ("PRIJMENI", 14, 80),
                ("JMENO", 14, 80),
                ("TITUL", 14, 20),
                ("RODCIS", 14, 20),
                ("DATNAR", 12, 8),
                ("POJ", 14, 10),
                ("TELEFON", 14, 40),
            ]
            return

        self.patient_queries.append((query, params))
        self._results = self._query_results.pop(0) if self._query_results else []

    def fetchall(self):
        return self._results


class PatientLookupNameMatchingTests(unittest.TestCase):
    patient_row = (52166, "Jan\u010da", "Vladim\u00edr", "", "1512230401", "2015-12-23", "205", "777 111 222")
    fuzzy_patient_row = (52167, "Nov\u00e1k", "Kry\u0161tof", "", "9001011234", "1990-01-01", "205", "777 333 444")

    def test_normalize_text_removes_diacritics(self):
        self.assertEqual(_normalize_text("Vladim\u00edr Jan\u010da"), "vladimir janca")

    def test_patient_name_match_is_accent_insensitive(self):
        patient = {"first_name": "Vladim\u00edr", "last_name": "Jan\u010da"}
        request = {"first_name": "Vladimir", "last_name": "Janca"}

        self.assertTrue(_patient_matches_requested_names(patient, request))

    def test_patient_name_match_keeps_like_semantics(self):
        patient = {"first_name": "Vladim\u00edr", "last_name": "Jan\u010da"}
        request = {"first_name": "Vlad", "last_name": "Jan"}

        self.assertTrue(_patient_matches_requested_names(patient, request))

    def test_name_fallback_requires_stable_anchor(self):
        self.assertIsNone(_name_fallback_request({"first_name": "Vladimir", "last_name": "Janca"}))
        self.assertEqual(
            _name_fallback_request(
                {
                    "first_name": "Vladimir",
                    "last_name": "Janca",
                    "birth_date": "2015-12-23",
                }
            ),
            {
                "birth_date": "2015-12-23",
                "limit": 20,
            },
        )

    def test_lookup_patient_falls_back_to_accent_insensitive_name_match(self):
        cursor = FakeLookupCursor(query_results=[[], [self.patient_row]])

        response = lookup_patient(
            cursor,
            {
                "first_name": "Vladimir",
                "last_name": "Janca",
                "birth_date": "2015-12-23",
                "include_appointments": False,
            },
        )

        self.assertEqual(response["status"], "found")
        self.assertEqual(response["name_match"], "accent_insensitive_fallback")
        self.assertTrue(response["verification"]["verified"])
        self.assertEqual(response["verification"]["method"], "name_birth_date_unique")
        self.assertEqual(response["patients"][0]["idpac"], 52166)
        self.assertEqual(len(cursor.patient_queries), 2)

    def test_lookup_patient_phone_unique_verifies_without_last4(self):
        cursor = FakeLookupCursor(query_results=[[self.patient_row]])

        response = lookup_patient(cursor, {"phone": "777111222", "include_appointments": False})

        self.assertEqual(response["status"], "found")
        self.assertTrue(response["verification"]["verified"])
        self.assertEqual(response["verification"]["method"], "phone_unique")
        self.assertEqual(response["appointments"], [])

    def test_lookup_patient_last_name_and_birth_date_verifies_without_last4(self):
        cursor = FakeLookupCursor(query_results=[[self.patient_row]])

        response = lookup_patient(
            cursor,
            {
                "last_name": "Jan\u010da",
                "birth_date": "2015-12-23",
                "include_appointments": False,
            },
        )

        self.assertEqual(response["status"], "found")
        self.assertTrue(response["verification"]["verified"])
        self.assertEqual(response["verification"]["method"], "name_birth_date_unique")

    def test_lookup_patient_fuzzy_name_with_birth_date_verifies_without_last4(self):
        cursor = FakeLookupCursor(query_results=[[], [], [self.fuzzy_patient_row]])

        response = lookup_patient(
            cursor,
            {
                "first_name": "Kristof",
                "last_name": "Novak",
                "birth_date": "1990-01-01",
                "include_appointments": False,
            },
        )

        self.assertEqual(response["status"], "found")
        self.assertEqual(response["name_match"], "fuzzy_fallback")
        self.assertTrue(response["verification"]["verified"])
        self.assertEqual(response["verification"]["method"], "fuzzy_name_birth_date_unique")
        self.assertEqual(response["patients"][0]["idpac"], 52167)

    def test_lookup_patient_multiple_matches_asks_for_missing_first_name(self):
        cursor = FakeLookupCursor(query_results=[[self.patient_row, self.fuzzy_patient_row]])

        response = lookup_patient(cursor, {"last_name": "Nov", "birth_date": "1990-01-01"})

        self.assertEqual(response["status"], "multiple_matches")
        self.assertFalse(response["verification"]["verified"])
        self.assertEqual(response["appointments"], [])
        self.assertIn("first name", response["agent_next_step"])

    def test_lookup_patient_not_found_asks_for_surname_and_birth_date(self):
        cursor = FakeLookupCursor(query_results=[[]])

        response = lookup_patient(cursor, {"phone": "000000000"})

        self.assertEqual(response["status"], "not_found")
        self.assertFalse(response["verification"]["verified"])
        self.assertIn("surname and date of birth", response["agent_next_step"])

    def test_lookup_patient_deprecated_last4_does_not_gate_success(self):
        cursor = FakeLookupCursor(query_results=[[self.patient_row]])

        response = lookup_patient(
            cursor,
            {
                "last_name": "Jan\u010da",
                "birth_date": "2015-12-23",
                "birth_number_last4": "9999",
                "include_appointments": False,
            },
        )

        self.assertEqual(response["status"], "found")
        self.assertTrue(response["verification"]["verified"])


if __name__ == "__main__":
    unittest.main()
