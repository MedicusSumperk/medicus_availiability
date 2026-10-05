import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from business_rules import agent_capabilities
from availability_search import compact_options


class ReviewVoiceContractTests(unittest.TestCase):
    def test_review_mode_never_advertises_direct_booking(self):
        # Use actual configured schema rather than hand-crafted flag aliases.
        import json
        rules=json.loads((Path(__file__).resolve().parents[1]/'config/business_rules.example.json').read_text(encoding='utf-8-sig'))
        result=agent_capabilities(rules,staff_review=True)
        self.assertEqual(result['booking_mode'],'staff_review')
        self.assertEqual(result['bookable_services'],[])
        self.assertTrue(result['review_services'])
        self.assertTrue(all(not s['agent_can_book_finally'] for s in result['review_services']))
        self.assertIn('personál',result['voice_answer_cs'])

    def test_compact_offer_preserves_earliest_arrival_and_token(self):
        response={'ok':True,'service':'dermatoscope_first','options':[{
            'date':'2026-10-07','doctor_name':'Test doctor','start_time':'15:20',
            'spoken_time_label':'15:00','scan_slot':{'start_time':'15:05','end_time':'15:20'},'offer_token':'opaque'}]}
        result=compact_options(response)
        self.assertEqual(result['options'][0]['arrival_time'],'15:00')
        self.assertEqual(result['options'][0]['scan_start_time'],'15:05')
        self.assertEqual(result['options'][0]['offer_token'],'opaque')
