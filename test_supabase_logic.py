import os, sys
os.environ['APP_MODE']='local'
sys.path.insert(0, os.path.dirname(__file__))
from supabase_store import SupabaseStore
import json

# Verify the production insert payload never sends the invalid legacy value `pending`.
class Probe(SupabaseStore):
    def __init__(self):
        os.environ['SUPABASE_URL']='https://example.supabase.co'
        os.environ['SUPABASE_SERVICE_ROLE_KEY']='test-only'
        super().__init__()
        self.seen=[]
    def insert(self, table, row, returning=True):
        self.seen.append((table,row))
        return dict(row, ticket_status='En attente')

p=Probe()
p.create_ticket({'ref':'UCS-TEST0001','first':'A','last':'B','phone':'1','email':'a@b.test','type':'Public','qty':1,'delivery':'email','created_at':'2026-11-10T00:00:00+00:00'})
table,row=p.seen[0]
assert table=='ticket_requests'
assert 'ticket_status' not in row
assert 'pending' not in json.dumps(row, ensure_ascii=False).lower()
assert p.status_pending == 'En attente'
assert p.status_proof == 'Paiement à vérifier'
assert p.status_validated == 'Validé'
assert p.status_rejected == 'Refusé'
print('SUPABASE LOGIC PASS: initial insert delegates status to DB default; no pending value is sent.')
