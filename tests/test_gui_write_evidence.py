import copy
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('gui_evidence', Path(__file__).resolve().parents[1] /
                                            'tools/diagnostics/gui_write_evidence.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class GuiEvidenceTests(unittest.TestCase):
    def snapshot(self):
        row = audit.protect_row({'IDOBJ': 1, 'DATUM': '2026-10-07',
                                 'IDPAC': 123456, 'POZNAMKA': 'private patient text'}, b'k' * 32)
        return {'schema_version': 1, 'key_id': 'key', 'dates': ['2026-10-07'],
                'captured_at_utc': 'now', 'databases': {
                    'MAIN': {'columns': list(row['fingerprints']), 'rows': {'1': row}}}}

    def test_patient_data_not_exposed_but_changes_detected(self):
        before = self.snapshot()
        serialized = json.dumps(before)
        self.assertNotIn('123456', serialized)
        self.assertNotIn('private patient text', serialized)
        after = copy.deepcopy(before)
        after['databases']['MAIN']['rows']['1']['fingerprints']['IDPAC'] = 'changed'
        diff = audit.compare(before, after)
        self.assertEqual(diff['databases']['MAIN']['changed'][0]['fields'], ['IDPAC'])

    def test_added_removed_and_unchanged(self):
        before = self.snapshot()
        self.assertEqual(audit.compare(before, before)['databases']['MAIN']['changed'], [])
        after = copy.deepcopy(before)
        row = after['databases']['MAIN']['rows'].pop('1')
        row['values']['IDOBJ'] = 2
        after['databases']['MAIN']['rows']['2'] = row
        diff = audit.compare(before, after)['databases']['MAIN']
        self.assertEqual(diff['removed_from_scope'][0]['IDOBJ'], 1)
        self.assertEqual(diff['added_to_scope'][0]['IDOBJ'], 2)

    def test_related_history_preserves_multiplicity_without_patient_text(self):
        row = audit.protect_row({'IDOBJ': 1, 'AKCE': 'D', 'PACIENT': 'private name'}, b'k'*32)
        old = {'OBJHIST': {'columns': list(row['fingerprints']), 'rows': [row]}}
        new = copy.deepcopy(old)
        new['OBJHIST']['rows'].append(row)
        diff = audit.related_delta(old, new)
        self.assertEqual(diff['OBJHIST']['added'][0]['count'], 1)
        self.assertEqual(diff['OBJHIST']['removed'], [])
        self.assertNotIn('private name', json.dumps(diff))
        with self.assertRaises(ValueError):
            audit.related_delta(old, {})

    def test_incompatible_evidence_rejected(self):
        for field, value in [('key_id', 'other'), ('dates', ['2026-10-08']),
                             ('schema_version', 2)]:
            before = self.snapshot()
            after = copy.deepcopy(before)
            after[field] = value
            with self.assertRaises(ValueError):
                audit.compare(before, after)


if __name__ == '__main__':
    unittest.main()
