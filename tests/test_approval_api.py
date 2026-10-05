import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from fastapi.testclient import TestClient
import api_server as api
from operator_telemetry import _sanitize


class ApprovalApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        config={'enable_staff_approval':True,'approval_store_path':str(Path(self.tmp.name)/'cards.sqlite'),
                'operator_tenant_key':'tenant','staff_approval_token':'s'*40}
        for name,value in [('API_CONFIG',config),('API_TOKEN','agent-token')]:
            p=patch.object(api,name,value);p.start();self.addCleanup(p.stop)
        api.approval_store()  # Deployment provisions the protected durable store.
        self.client=TestClient(api.app)

    def test_agent_token_cannot_access_staff_cards(self):
        self.assertEqual(self.client.get('/staff/proposals',headers={'Authorization':'Bearer agent-token'}).status_code,401)
        self.assertEqual(self.client.get('/staff/proposals',headers={'X-Staff-Token':'agent-token'}).status_code,401)
        self.assertEqual(self.client.get('/staff/proposals',headers={'X-Staff-Token':'s'*40}).json(),{'items':[], 'next_cursor': None})

    def test_staff_detail_history_requires_staff_and_never_connects_to_medicus(self):
        card=api.approval_store().submit('tenant','history',{'idpac':123},{'action':'create'})
        path='/staff/proposals/'+card['id']
        with patch.object(api,'connect_to_db') as connect:
            self.assertEqual(self.client.get(path,headers={'Authorization':'Bearer agent-token'}).status_code,401)
            result=self.client.get(path,headers={'X-Staff-Token':'s'*40})
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.json()['history'][0]['state'],'pending_staff_review')
            self.assertNotIn('idpac',result.text)
            api.API_CONFIG['operator_tenant_key']='other'
            self.assertEqual(self.client.get(path,headers={'X-Staff-Token':'s'*40}).status_code,404)
        connect.assert_not_called()

    def test_tool_never_calls_old_write_path_in_review_mode(self):
        connection=Mock()
        with patch.object(api,'connect_to_db',return_value=connection),patch.object(api,'submit_proposal',return_value={'status':'pending_staff_review','booking_confirmed':False}) as submit,patch.object(api,'write_appointment') as write:
            r=self.client.post('/book-appointment',headers={'Authorization':'Bearer agent-token','X-Conversation-Id':'c'},json={'action':'create','caller_confirmed':True,'request_id':'one','approved':True})
        self.assertEqual(r.status_code,200);self.assertFalse(r.json()['booking_confirmed'])
        write.assert_not_called();connection.commit.assert_not_called();connection.rollback.assert_called_once()
        self.assertEqual(submit.call_args.args[3],'c')

    def test_accepted_request_replays_over_http_during_database_outage(self):
        from approval_proposals import submission_identity
        request={'action':'create','caller_confirmed':True,'request_id':'retry',
                 'patient_verification_token':'expired-proof','offer_token':'expired-offer'}
        key,digest=submission_identity('c',request)
        card=api.approval_store().submit('tenant',key,{'request_digest':digest},{'action':'create'})
        with patch.object(api,'connect_to_db',side_effect=OSError('private database path')) as connect:
            response=self.client.post('/book-appointment',
                headers={'Authorization':'Bearer agent-token','X-Conversation-Id':'c'},json=request)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['proposal_id'],card['id'])
        self.assertEqual(response.json()['status'],'pending_staff_review')
        self.assertFalse(response.json()['booking_confirmed'])
        connect.assert_not_called()

    def test_new_request_during_outage_cannot_claim_success_or_leak_error(self):
        with patch.object(api,'connect_to_db',side_effect=OSError('private database path')),patch.object(api,'emit_tool_event'):
            response=self.client.post('/book-appointment',
                headers={'Authorization':'Bearer agent-token','X-Conversation-Id':'c'},
                json={'action':'create','caller_confirmed':True,'request_id':'new'})
        self.assertEqual(response.status_code,500)
        self.assertNotIn('private database path',response.text)
        self.assertEqual(api.approval_store().list('tenant'),[])

    def test_staff_rejection_does_not_connect_to_medicus(self):
        card=api.approval_store().submit('tenant','key',{'idpac':123},{'action':'create'})
        with patch.object(api,'connect_to_db') as connect:
            r=self.client.post('/staff/proposals/'+card['id']+'/reject',headers={'X-Staff-Token':'s'*40},json={'version':1,'actor_user_id':'verified-operator-user'})
        self.assertEqual(r.json()['state'],'rejected');connect.assert_not_called()
        self.assertNotIn('idpac',r.text)

    def test_all_review_returns_emit_state_without_tokens_or_free_text(self):
        from approval_store import ProposalConflict
        pending={'ok':True,'status':'pending_staff_review','booking_confirmed':False,'proposal_id':'card'}
        for mode in ('new','replay','replay_conflict','submit_conflict'):
            with self.subTest(mode=mode):
                connection=Mock()
                request={'action':'create','caller_confirmed':True,'request_id':'one',
                         'patient_verification_token':'private-proof','offer_token':'private-offer',
                         'note':'private text'}
                replay_error=ProposalConflict('private conflict') if mode=='replay_conflict' else None
                submit_error=ProposalConflict('private conflict') if mode=='submit_conflict' else None
                with patch.object(api,'replay_proposal',return_value=pending if mode=='replay' else None,side_effect=replay_error), \
                     patch.object(api,'submit_proposal',return_value=pending,side_effect=submit_error), \
                     patch.object(api,'connect_to_db',return_value=connection) as connect, \
                     patch.object(api,'write_appointment') as write, patch.object(api,'emit_tool_event') as emit:
                    response=self.client.post('/book-appointment',headers={'Authorization':'Bearer agent-token','X-Conversation-Id':'c'},json=request)
                self.assertEqual(response.status_code,200)
                emit.assert_called_once()
                event=emit.call_args.kwargs
                self.assertEqual(event['response_payload']['status'],response.json()['status'])
                self.assertFalse(event['response_payload']['booking_confirmed'])
                self.assertEqual(event['business_ok'],mode in ('new','replay'))
                self.assertNotIn('private',str(event))
                write.assert_not_called();connection.commit.assert_not_called()
                if mode in ('replay','replay_conflict'):
                    connect.assert_not_called()
                else:
                    connection.rollback.assert_called_once()

    def test_telemetry_redacts_references_inside_json_string(self):
        result=_sanitize({'offer_token':'secret-a','patient_verification_token':'secret-b','options_json':'[{"offer_token":"secret-c"}]'})
        self.assertNotIn('secret-',str(result))

    def test_handoff_persists_before_reporting_success_without_logging_text(self):
        with patch.object(api,'emit_tool_event') as emit:
            r=self.client.post('/handoff-summary',headers={'Authorization':'Bearer agent-token','X-Conversation-Id':'c'},
                json={'mode':'callback','request_id':'handoff-1','conversation_summary':'Private context'})
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json()['stored'])
        self.assertEqual(r.json()['delivery_status'],'pending')
        self.assertNotIn('Private context',str(emit.call_args))
        with api.approval_store().connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM handoffs').fetchone()[0],1)

    def test_handoff_storage_error_cannot_claim_success(self):
        from approval_store import ApprovalStore
        with patch.object(ApprovalStore,'store_handoff',side_effect=OSError('private path')),patch.object(api,'emit_tool_event'):
            r=self.client.post('/handoff-summary',headers={'Authorization':'Bearer agent-token','X-Conversation-Id':'c'},
                json={'mode':'callback','request_id':'handoff-1'})
        self.assertEqual(r.status_code,500)
        self.assertNotIn('private path',r.text)


if __name__=='__main__':unittest.main()
