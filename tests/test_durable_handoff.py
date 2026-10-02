import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from approval_store import ApprovalStore, ProposalConflict


class DurableHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'review.sqlite'
        self.store=ApprovalStore(self.path)
        self.payload={'ok':True,'mode':'callback','summary_for_staff':'Test request','created_at':'first'}

    def test_retry_and_reopen_keep_one_request(self):
        result=self.store.store_handoff('t','c','r',self.payload)
        again=ApprovalStore(self.path).store_handoff('t','c','r',{**self.payload,'created_at':'later'})
        self.assertEqual(result,again)
        self.assertTrue(result['stored'])
        self.assertEqual(result['delivery_status'],'pending')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM handoffs').fetchone()[0],1)

    def test_conflicting_retry_does_not_overwrite_context(self):
        self.store.store_handoff('t','c','r',self.payload)
        with self.assertRaises(ProposalConflict):
            self.store.store_handoff('t','c','r',{**self.payload,'summary_for_staff':'Changed request'})

    def test_identity_scoped_by_tenant_and_conversation(self):
        ids={self.store.store_handoff(t,c,'r',self.payload)['handoff_id']
             for t,c in [('t','c'),('other','c'),('t','other')]}
        self.assertEqual(len(ids),3)

    def test_missing_key_rejected(self):
        with self.assertRaises(ProposalConflict):
            self.store.store_handoff('t','c',None,self.payload)

    def test_unresolved_runtime_binding_cannot_merge_calls(self):
        for conversation, key in [('{{system__conversation_id}}', 'r'),
                                  ('system__conversation_id', 'r'), (' ', 'r'),
                                  ('c', '{{request_id}}'), ('c', ' ')]:
            with self.subTest(conversation=conversation, key=key):
                with self.assertRaises(ProposalConflict):
                    self.store.store_handoff('t', conversation, key, self.payload)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM handoffs').fetchone()[0], 0)
