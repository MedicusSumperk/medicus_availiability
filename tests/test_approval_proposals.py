import sys
import tempfile
import unittest
from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from approval_store import ApprovalStore,ProposalConflict
import approval_proposals as proposals


class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=ApprovalStore(Path(self.tmp.name)/'db.sqlite')
        self.cursor=Mock();self.cursor.fetchone.return_value=(123,'Test','Patient','2000-01-01')
        self.patient={'idpac':123,'fingerprint':proposals.patient_fingerprint(self.cursor,123)}
        self.proof=self.store.issue_grant('t','c','patient',self.patient)
        self.offer=proposals.offer_snapshot({'service':'skin','date':'2030-01-07','start_time':'09:00','end_time':'09:10','doctor_id':2,'doctor_name':'Test doctor','idprac':1})
        self.token=self.store.issue_grant('t','c','offer',self.offer)
        self.request={'action':'create','caller_confirmed':True,'request_id':'one','patient_verification_token':self.proof,'offer_token':self.token}

    def test_create_only_persists_review_card(self):
        with patch.object(proposals,'validate_offer'):
            result=proposals.submit_proposal(self.store,self.cursor,'t','c',self.request)
            again=proposals.submit_proposal(self.store,self.cursor,'t','c',self.request)
        self.assertEqual(result,again)
        self.assertEqual(result['status'],'pending_staff_review')
        self.assertFalse(result['booking_confirmed'])
        self.assertEqual(len(self.store.list('t')),1)
        self.assertNotIn('idpac',str(self.store.list('t')))
        for call in self.cursor.execute.call_args_list:self.assertTrue(call.args[0].startswith('SELECT'))

    def test_retry_after_expiry_and_availability_change_returns_saved_state(self):
        with patch.object(proposals,'validate_offer'):
            first=proposals.submit_proposal(self.store,self.cursor,'t','c',self.request)
        card=self.store.get('t',first['proposal_id'])
        self.store.decide('t',card['id'],card['version'],'staff',approve=False)
        with (patch.object(self.store,'resolve_grant',side_effect=AssertionError('expired grant must not be read')),
              patch.object(proposals,'validate_offer',side_effect=AssertionError('availability must not be read')),
              patch.object(proposals,'patient_fingerprint',side_effect=AssertionError('patient must not be read'))):
            again=proposals.submit_proposal(self.store,self.cursor,'t','c',self.request)
        self.assertEqual(again['proposal_id'],first['proposal_id'])
        self.assertEqual(again['status'],'rejected')
        self.assertFalse(again['booking_confirmed'])
        self.assertEqual(len(self.store.list('t')),1)

    def test_changed_request_with_same_key_rejected_before_validation(self):
        with patch.object(proposals,'validate_offer'):
            proposals.submit_proposal(self.store,self.cursor,'t','c',self.request)
        with patch.object(self.store,'resolve_grant',side_effect=AssertionError('must reject first')):
            with self.assertRaises(ProposalConflict):
                proposals.submit_proposal(self.store,self.cursor,'t','c',{**self.request,'offer_token':'other'})

    def test_legacy_card_does_not_create_duplicate(self):
        self.store.submit('t','c:one',{'action':'create'},{})
        with self.assertRaises(ProposalConflict):
            proposals.submit_proposal(self.store,self.cursor,'t','c',self.request)
        self.assertEqual(len(self.store.list('t')),1)

    def test_model_cannot_change_offer_or_forge_verification_flag(self):
        with self.assertRaises(ProposalConflict):
            proposals.submit_proposal(self.store,self.cursor,'t','c',{**self.request,'start_time':'13:20'})
        with self.assertRaises(ProposalConflict):
            proposals.submit_proposal(self.store,self.cursor,'t','c',{**self.request,'patient_verification_token':None,'patient_verified':True})
        self.assertEqual(self.store.list('t'),[])

    def test_grants_cannot_cross_conversation_tenant_or_purpose(self):
        for tenant,conversation,purpose in [('other','c','patient'),('t','other','patient'),('t','c','offer')]:
            with self.assertRaises(ProposalConflict):self.store.resolve_grant(tenant,conversation,purpose,self.proof)

    def test_identity_reference_requires_dob_and_nonfuzzy_name(self):
        result={'status':'found','patients':[{'idpac':123}],'filters':['idpac'],'name_match':'sql'}
        self.assertIsNone(proposals.issue_patient_reference(self.store,self.cursor,'t','c',{},result))
        result['filters']=['birth_date','last_name'];result['name_match']='fuzzy_fallback'
        self.assertIsNone(proposals.issue_patient_reference(self.store,self.cursor,'t','c',{'birth_date':'2000-01-01'},result))
        result['name_match']='sql'
        self.assertIsNone(proposals.issue_patient_reference(self.store,self.cursor,'t','c',{'birth_date':'2000-01-01'},result))
        result['filters']=['first_name','last_name','birth_date']
        result['patients']=[{'idpac':123,'first_name':'Test','last_name':'Patient','birth_date':'2000-01-01'}]
        self.assertTrue(proposals.issue_patient_reference(self.store,self.cursor,'t','c',{'first_name':'Test','last_name':'Patient','birth_date':'2000-01-01'},result))

    def test_cancel_and_reschedule_are_only_proposals(self):
        source=[{'idobj':77,'idpac':123,'date':'2030-01-08','start_time':'10:00'}]
        with patch.object(proposals,'source_snapshot',return_value=source),patch.object(proposals,'validate_offer'),patch.object(proposals,'staff_original_summary',return_value=[]):
            for action in ['cancel','reschedule']:
                result=proposals.submit_proposal(self.store,self.cursor,'t','c',{**self.request,'request_id':action,'action':action,'appointment_ids':[77]})
                self.assertEqual(result['status'],'pending_staff_review')
        self.assertEqual(len(self.store.list('t')),2)

    def test_changed_arrival_invalidates_existing_offer(self):
        option={'service':'skin','date':'2030-01-07','start_time':'15:20','end_time':'15:30',
                'doctor_id':2,'doctor_name':'Test doctor','idprac':1,'spoken_time_label':'15:00'}
        offer=proposals.offer_snapshot(option)
        with patch.object(proposals,'search_availability',return_value={'options':[{**option,'spoken_time_label':'15:15'}]}):
            with self.assertRaises(ProposalConflict):
                proposals.validate_offer(self.cursor,offer)

    def test_changed_rules_require_new_offer(self):
        option={'service':'skin','date':'2030-01-07','start_time':'09:00','end_time':'09:10',
                'doctor_id':2,'doctor_name':'Test doctor','idprac':1}
        with patch.object(proposals,'load_business_rules',return_value={'revision':1}):
            offer=proposals.offer_snapshot(option)
        with patch.object(proposals,'load_business_rules',return_value={'revision':2}),\
             patch.object(proposals,'search_availability',return_value={'options':[option]}):
            with self.assertRaises(ProposalConflict):
                proposals.validate_offer(self.cursor,offer)

    def test_snapshot_does_not_share_mutable_scan_with_option(self):
        option={'start_time':'15:20','spoken_time_label':'15:00','scan_slot':{'start_time':'15:05','end_time':'15:20'}}
        snapshot=proposals.offer_snapshot(option)
        option['scan_slot']['start_time']='14:00'
        self.assertEqual(snapshot['scan_slot']['start_time'],'15:05')
        self.assertEqual(snapshot['arrival_time'],'15:00')

    def test_conflicting_spoken_time_is_rejected_before_submission(self):
        with self.assertRaises(ProposalConflict):
            proposals.submit_proposal(self.store,self.cursor,'t','c',{**self.request,'spoken_time_label':'08:30'})
        self.assertEqual(self.store.list('t'),[])

    def test_original_summary_uses_verified_pair_without_private_fields(self):
        import paired_appointments
        import laser_calendar
        row = {'idobj':77, 'idpac':123, 'doctor_id':8, 'idprac':1,
               'date':'2030-01-07', 'start_time':'09:30', 'end_time':'09:40',
               'typ':1, 'idcinnosti':1}
        before = deepcopy(row)
        calendar = Mock(calendar_id=5, workplace_id=1)
        scanner = {'start_time':'09:15', 'end_time':'09:30', 'info':'private note'}
        self.cursor.fetchone.return_value = ('Test', 'Doctor')
        with patch.object(laser_calendar, 'open_scan_calendar', return_value=nullcontext(calendar)), \
             patch.object(paired_appointments, 'load_pair', return_value=(dict(row,info='private'),scanner,'private-token')):
            result = proposals.staff_original_summary(self.cursor,123,[row])[0]
        self.assertEqual(result['doctor_name'],'Test Doctor')
        self.assertEqual(result['service'],'dermatoscope_first')
        self.assertEqual(result['scan_slot'],{'start_time':'09:15','end_time':'09:30'})
        self.assertIsNone(result['arrival_time'])
        self.assertEqual(row,before)
        self.assertNotIn('private',str(result))
        self.assertNotIn('idpac',result)
        self.assertNotIn('idobj',result)

    def test_source_change_or_missing_pair_cannot_produce_trusted_scan_summary(self):
        import paired_appointments
        import laser_calendar
        row = {'idobj':77,'doctor_id':8,'idcinnosti':1,'start_time':'09:30'}
        self.cursor.fetchone.return_value = ('Test','Doctor')
        for changed in (False,True):
            with self.subTest(changed=changed), \
                 patch.object(laser_calendar,'open_scan_calendar',return_value=nullcontext(Mock(calendar_id=5,workplace_id=1))), \
                 patch.object(paired_appointments,'load_pair',side_effect=None if changed else ValueError('missing pair'),
                              return_value=(dict(row,start_time='10:00'),{},'token')):
                with self.assertRaises(ValueError):
                    proposals.staff_original_summary(self.cursor,123,[row])

    def test_single_summary_does_not_invent_scan_or_arrival(self):
        self.cursor.fetchone.return_value = ('Test','Doctor')
        result = proposals.staff_original_summary(self.cursor,123,[{'doctor_id':8,'idcinnosti':None}])[0]
        self.assertEqual(result['service'],'skin')
        self.assertIsNone(result['scan_slot'])
        self.assertIsNone(result['arrival_time'])


if __name__=='__main__':unittest.main()
