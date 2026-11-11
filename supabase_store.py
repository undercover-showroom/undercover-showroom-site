import os, json, urllib.request, urllib.parse, urllib.error, secrets
from datetime import datetime, timezone

class SupabaseError(RuntimeError):
    pass

class SupabaseStore:
    """Small PostgREST/Storage adapter. No schema recreation; only CRUD against existing tables."""
    def __init__(self):
        self.url = os.environ.get('SUPABASE_URL','').rstrip('/')
        self.key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY','')
        if not self.url or not self.key:
            raise SupabaseError('SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis en production.')
        self.rest = self.url + '/rest/v1'
        self.storage = self.url + '/storage/v1'
        self.ticket_table = os.environ.get('SUPABASE_TICKET_TABLE','ticket_requests')
        self.table_table = os.environ.get('SUPABASE_TABLE_RESERVATIONS_TABLE','table_reservations')
        self.event_table = os.environ.get('SUPABASE_EVENT_LOG_TABLE','event_log')
        self.proof_bucket = os.environ.get('SUPABASE_PROOF_BUCKET','undercover-proofs')
        self.ticket_bucket = os.environ.get('SUPABASE_TICKET_BUCKET','undercover-tickets')
        # These four values are the validated workflow labels used by the application.
        self.status_pending = os.environ.get('TICKET_STATUS_INITIAL','En attente')
        self.status_proof = os.environ.get('TICKET_STATUS_PROOF','Paiement à vérifier')
        self.status_validated = os.environ.get('TICKET_STATUS_VALIDATED','Validé')
        self.status_rejected = os.environ.get('TICKET_STATUS_REJECTED','Refusé')

    def _request(self, method, url, payload=None, headers=None, query=None):
        if query:
            url += ('&' if '?' in url else '?') + urllib.parse.urlencode(query, doseq=True)
        h={'apikey':self.key,'Authorization':'Bearer '+self.key,'Content-Type':'application/json','Accept':'application/json'}
        if headers: h.update(headers)
        if payload is None:
            data=None
        elif isinstance(payload,(bytes,bytearray)):
            data=bytes(payload)
        else:
            data=json.dumps(payload, ensure_ascii=False).encode()
        req=urllib.request.Request(url,data=data,headers=h,method=method)
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                raw=r.read(); return json.loads(raw.decode()) if raw else None
        except urllib.error.HTTPError as e:
            detail=e.read().decode('utf-8','replace')[:1200]
            raise SupabaseError(f'{method} {url}: HTTP {e.code}: {detail}') from e

    def insert(self, table, row, returning=True):
        headers={'Prefer':'return=representation' if returning else 'return=minimal'}
        out=self._request('POST',f'{self.rest}/{table}',row,headers=headers)
        return out[0] if isinstance(out,list) and out else out

    def update(self, table, values, filters):
        query={k:'eq.'+str(v) for k,v in filters.items()}
        return self._request('PATCH',f'{self.rest}/{table}',values,headers={'Prefer':'return=representation'},query=query)

    def select(self, table, filters=None, order=None, limit=None):
        query={'select':'*'}
        if filters:
            for k,v in filters.items(): query[k]='eq.'+str(v)
        if order: query['order']=order
        if limit: query['limit']=str(limit)
        return self._request('GET',f'{self.rest}/{table}',query=query) or []

    def get_ticket(self, ref):
        rows=self.select(self.ticket_table,{'reference':ref},limit=1)
        return rows[0] if rows else None

    def get_table(self, ref):
        rows=self.select(self.table_table,{'reference':ref},limit=1)
        return rows[0] if rows else None

    def list_tickets(self):
        return self.select(self.ticket_table,order='created_at.desc')

    def list_tables(self):
        return self.select(self.table_table,order='created_at.desc')

    def create_ticket(self, data):
        # Deliberately omit ticket_status on initial insert. The DB default remains authoritative.
        row={
            'reference':data['ref'],'first_name':data['first'],'last_name':data['last'],
            'phone':data['phone'],'email':data['email'],'ticket_type':data['type'],
            'quantity':data['qty'],'delivery_method':data['delivery'],'adult_confirmed':True,
            'created_at':data['created_at']
        }
        return self.insert(self.ticket_table,row)

    def create_table_reservation(self,data):
        row={'reference':data['ref'],'first_name':data['first'],'last_name':data['last'],
             'phone':data['phone'],'email':data['email'],'people_count':data['people'],
             'appointment':data['appointment'],'notes':data['notes'],'created_at':data['created_at']}
        return self.insert(self.table_table,row)

    def upload_file(self,bucket, path, content, content_type):
        url=f'{self.storage}/object/{bucket}/{urllib.parse.quote(path,safe="/")}'
        headers={'Content-Type':content_type,'x-upsert':'true'}
        return self._request('POST',url,content,headers=headers)

    def signed_url(self,bucket,path,expires=600):
        url=f'{self.storage}/object/sign/{bucket}/{urllib.parse.quote(path,safe="/")}'
        return self._request('POST',url,{'expiresIn':expires}).get('signedURL')

    def update_ticket_proof(self, ref, proof_url):
        return self.update(self.ticket_table,{'payment_proof_url':proof_url,'ticket_status':self.status_proof},{'reference':ref})

    def update_ticket_validated(self, ref, ticket_url, qr_url, validated_at):
        return self.update(self.ticket_table,{'ticket_status':self.status_validated,'validated_at':validated_at,'ticket_url':ticket_url,'qr_url':qr_url},{'reference':ref})

    def update_ticket_rejected(self, ref):
        return self.update(self.ticket_table,{'ticket_status':self.status_rejected},{'reference':ref})

    def update_send_status(self, ref, value):
        return self.update(self.ticket_table,{'send_status':value},{'reference':ref})

    def log(self,kind,ref,detail):
        try:
            self.insert(self.event_table,{'kind':kind,'reference':ref,'detail':detail,'created_at':datetime.now(timezone.utc).isoformat()},returning=False)
        except SupabaseError:
            # Logging must not break the ticket workflow if the optional event log table is absent.
            pass

    def ensure_buckets(self):
        # Idempotent: creates private buckets only if they do not already exist.
        for name in (self.proof_bucket,self.ticket_bucket):
            try:
                self._request('POST',f'{self.storage}/bucket',{'id':name,'name':name,'public':False})
            except SupabaseError as e:
                if 'already exists' not in str(e).lower() and 'duplicate' not in str(e).lower():
                    raise

def normalize_ticket(r):
    if not r: return None
    return {
        'ref': r.get('reference',r.get('ref','')), 'first':r.get('first_name',r.get('first','')), 'last':r.get('last_name',r.get('last','')),
        'phone':r.get('phone',''), 'email':r.get('email',''), 'type':r.get('ticket_type',r.get('type','')),
        'qty':r.get('quantity',r.get('qty',1)), 'delivery':r.get('delivery_method',r.get('delivery','')),
        'adult':r.get('adult_confirmed',r.get('adult',True)), 'proof':r.get('payment_proof_url',r.get('proof','')),
        'status':r.get('ticket_status',r.get('status','')), 'created_at':r.get('created_at',''),
        'validated_at':r.get('validated_at',''), 'ticket_pdf':r.get('ticket_url',r.get('ticket_pdf','')),
        'qr_path':r.get('qr_url',r.get('qr_path','')), 'send_status':r.get('send_status',r.get('send_status','Non envoyé')),
        '_raw':r
    }

def normalize_table(r):
    if not r:return None
    return {'ref':r.get('reference',r.get('ref','')), 'first':r.get('first_name',r.get('first','')), 'last':r.get('last_name',r.get('last','')),
            'phone':r.get('phone',''),'email':r.get('email',''),'people':r.get('people_count',r.get('people',1)),
            'appointment':r.get('appointment',''),'notes':r.get('notes',''),'status':r.get('status',''),'created_at':r.get('created_at',''),'_raw':r}

class LocalStore:
    """Deterministic local test store. Production never uses this unless APP_MODE=local is explicit."""
    def __init__(self, db_path):
        import sqlite3
        self.sqlite3=sqlite3; self.db_path=db_path
        con=self.sqlite3.connect(db_path); con.row_factory=self.sqlite3.Row
        con.executescript('''CREATE TABLE IF NOT EXISTS ticket_requests(
          id INTEGER PRIMARY KEY AUTOINCREMENT, reference TEXT UNIQUE, first_name TEXT,last_name TEXT,phone TEXT,email TEXT,
          ticket_type TEXT,quantity INTEGER,delivery_method TEXT,adult_confirmed INTEGER,ticket_status TEXT DEFAULT 'En attente',
          payment_proof_url TEXT,ticket_url TEXT,qr_url TEXT,created_at TEXT,validated_at TEXT,send_status TEXT DEFAULT 'Non envoyé');
          CREATE TABLE IF NOT EXISTS table_reservations(
          id INTEGER PRIMARY KEY AUTOINCREMENT,reference TEXT UNIQUE,first_name TEXT,last_name TEXT,phone TEXT,email TEXT,
          people_count INTEGER,appointment TEXT,notes TEXT,status TEXT DEFAULT 'En attente',created_at TEXT);
          CREATE TABLE IF NOT EXISTS event_log(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT,reference TEXT,detail TEXT,created_at TEXT);''')
        con.commit();con.close()
        self.status_pending='En attente'; self.status_proof='Paiement à vérifier'; self.status_validated='Validé'; self.status_rejected='Refusé'
        self.proof_bucket='local'; self.ticket_bucket='local'
    def _con(self):
        c=self.sqlite3.connect(self.db_path); c.row_factory=self.sqlite3.Row; return c
    def insert(self,table,row,returning=True):
        c=self._con(); keys=list(row); vals=[row[k] for k in keys]; qs=','.join('?' for _ in keys)
        cur=c.execute(f'INSERT INTO {table} ({",".join(keys)}) VALUES ({qs})',vals); c.commit();
        if returning:
            r=c.execute(f'SELECT * FROM {table} WHERE id=?',(cur.lastrowid,)).fetchone(); c.close(); return dict(r)
        c.close(); return None
    def get_ticket(self,ref):
        c=self._con(); r=c.execute('SELECT * FROM ticket_requests WHERE reference=?',(ref,)).fetchone(); c.close(); return normalize_ticket(dict(r)) if r else None
    def get_table(self,ref):
        c=self._con(); r=c.execute('SELECT * FROM table_reservations WHERE reference=?',(ref,)).fetchone(); c.close(); return normalize_table(dict(r)) if r else None
    def list_tickets(self):
        c=self._con(); rows=c.execute('SELECT * FROM ticket_requests ORDER BY id DESC').fetchall(); c.close(); return [normalize_ticket(dict(r)) for r in rows]
    def list_tables(self):
        c=self._con(); rows=c.execute('SELECT * FROM table_reservations ORDER BY id DESC').fetchall(); c.close(); return [normalize_table(dict(r)) for r in rows]
    def create_ticket(self,data):
        r=self.insert('ticket_requests',{'reference':data['ref'],'first_name':data['first'],'last_name':data['last'],'phone':data['phone'],'email':data['email'],'ticket_type':data['type'],'quantity':data['qty'],'delivery_method':data['delivery'],'adult_confirmed':1,'created_at':data['created_at']})
        return normalize_ticket(r)
    def create_table_reservation(self,data):
        r=self.insert('table_reservations',{'reference':data['ref'],'first_name':data['first'],'last_name':data['last'],'phone':data['phone'],'email':data['email'],'people_count':data['people'],'appointment':data['appointment'],'notes':data['notes'],'created_at':data['created_at']}); return normalize_table(r)
    def update_ticket_proof(self,ref,proof_url):
        c=self._con(); c.execute('UPDATE ticket_requests SET payment_proof_url=?,ticket_status=? WHERE reference=?',(proof_url,self.status_proof,ref)); c.commit(); c.close()
    def update_ticket_validated(self,ref,ticket_url,qr_url,validated_at):
        c=self._con(); c.execute('UPDATE ticket_requests SET ticket_status=?,validated_at=?,ticket_url=?,qr_url=? WHERE reference=?',(self.status_validated,validated_at,ticket_url,qr_url,ref)); c.commit(); c.close()
    def update_ticket_rejected(self,ref):
        c=self._con(); c.execute('UPDATE ticket_requests SET ticket_status=? WHERE reference=?',(self.status_rejected,ref)); c.commit(); c.close()
    def update_send_status(self,ref,value):
        c=self._con(); c.execute('UPDATE ticket_requests SET send_status=? WHERE reference=?',(value,ref)); c.commit(); c.close()
    def log(self,kind,ref,detail):
        c=self._con(); c.execute('INSERT INTO event_log(kind,reference,detail,created_at) VALUES(?,?,?,?)',(kind,ref,detail,datetime.now(timezone.utc).isoformat())); c.commit(); c.close()
    def upload_file(self,bucket,path,content,content_type):
        return path
    def signed_url(self,bucket,path,expires=600): return path
    def ensure_buckets(self): pass
