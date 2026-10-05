import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from approval_store import ApprovalStore, ProposalConflict, ProposalNotFound


class ApprovalStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.path=Path(self.directory.name)/'requests.sqlite3'
        self.store=ApprovalStore(self.path)
        self.card=self.store.submit('tenant','call:create:1',{'action':'create','idpac':123},{'action':'create'})

    def test_retries_survive_restart_without_exposing_payload(self):
        other=ApprovalStore(self.path)
        self.assertEqual(other.submit('tenant','call:create:1',{'action':'create','idpac':123},{'action':'create'}),self.card)
        self.assertNotIn('idpac',str(other.list('tenant')))
        with self.assertRaises(ProposalConflict):
            other.submit('tenant','call:create:1',{'action':'cancel'},{'action':'cancel'})

    def test_concurrent_exact_submissions_keep_first_derived_snapshot(self):
        def submit(index):
            return self.store.submit('tenant','same-request',
                {'request_digest':'server-generated-same-request','derived_snapshot':index},
                {'action':'create'})
        with ThreadPoolExecutor(max_workers=2) as pool:
            cards=list(pool.map(submit,range(2)))
        self.assertEqual(cards[0]['id'],cards[1]['id'])
        self.assertEqual(len(self.store.list('tenant')),2)  # includes setUp card
        with self.assertRaises(ProposalConflict):
            self.store.replay_submission('tenant','same-request','different-request')
        self.assertIsNone(self.store.replay_submission('other','same-request','server-generated-same-request'))

    def test_only_one_concurrent_approval_can_execute(self):
        def approve(_):
            try:return self.store.decide('tenant',self.card['id'],1,'staff',approve=True)[1]
            except ProposalConflict:return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(approve,range(2)))
        self.assertEqual(sum(r is not None for r in results),1)
        with self.assertRaises(ProposalConflict):
            ApprovalStore(self.path).decide('tenant',self.card['id'],1,'staff',approve=True)

    def test_reject_never_returns_execution_payload(self):
        card,payload=self.store.decide('tenant',self.card['id'],1,'staff',approve=False)
        self.assertEqual(card['state'],'rejected');self.assertIsNone(payload)

    def test_tenant_boundary_and_expiry(self):
        self.assertEqual(self.store.list('other'),[])
        with self.assertRaises(ProposalNotFound):self.store.decide('other',self.card['id'],1,'staff',approve=True)
        with patch('approval_store.time.time',return_value=self.card['expires_at']+1):
            with self.assertRaises(ProposalConflict):self.store.decide('tenant',self.card['id'],1,'staff',approve=True)
        self.assertEqual(self.store.list('tenant')[0]['state'],'expired')

    def test_uncertain_outcome_cannot_be_reapproved(self):
        card,_=self.store.decide('tenant',self.card['id'],1,'staff',approve=True)
        done=self.store.finish('tenant',card['id'],card['version'],'needs_reconciliation',{'code':'commit_uncertain'})
        with self.assertRaises(ProposalConflict):self.store.decide('tenant',done['id'],done['version'],'staff',approve=True)


if __name__=='__main__':unittest.main()
