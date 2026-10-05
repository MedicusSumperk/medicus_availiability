import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import availability_engine as engine
from agent_context import build_skin_options, build_dermatoscope_options, build_simple_service_options


class MixedScheduleIntervalTests(unittest.TestCase):
    def context(self, blocks, appointments=()):
        with (patch.object(engine, 'find_schedule_contexts', return_value=[{'idprac': 1, 'typtyd': 4, 'dentyd': 4}]),
              patch.object(engine, 'load_schedule_blocks', return_value=blocks),
              patch.object(engine, 'load_appointments', return_value=appointments)):
            day = engine.compute_day_availability(None, {'doctor_id': 2}, date(2026, 10, 8))
        return day['contexts'][0]

    def test_each_service_uses_actual_cell(self):
        context = self.context([('09:00', 20, 10), ('13:00', 30, 15)])
        config = {'use_schedule_interval': True, 'create_followup_dermatoscope': False}
        results = [build_skin_options(context, [], config, 10, 10)[0],
                   build_dermatoscope_options(context, [], config, 10, 10)[0],
                   build_simple_service_options(context, config, 10, 10)[0]]
        for options in results:
            with self.subTest(service_options=options):
                self.assertEqual([(o['start_time'], o['end_time']) for o in options],
                                 [('09:00','09:10'), ('09:10','09:20'), ('13:00','13:15'), ('13:15','13:30')])

    def test_fixed_duration_can_span_adjacent_different_cells(self):
        context = self.context([('09:00', 10, 10), ('09:10', 15, 15)])
        options, _ = build_simple_service_options(context, {'appointment_duration_minutes': 25}, 10, 10)
        self.assertEqual([(o['start_time'], o['end_time']) for o in options], [('09:00','09:25')])

    def test_fixed_duration_cannot_bridge_gap(self):
        context = self.context([('09:00', 10, 10), ('09:15', 15, 15)])
        options, _ = build_simple_service_options(context, {'appointment_duration_minutes': 25}, 10, 10)
        self.assertEqual(options, [])

    def test_overlap_in_last_five_minutes_blocks_whole_cell(self):
        context = self.context([('09:00', 10, 10), ('13:00', 15, 15)], [('13:10','13:15')])
        options, _ = build_skin_options(context, [], {'create_followup_dermatoscope': False}, 10, 10)
        self.assertEqual([o['start_time'] for o in options], ['09:00'])
