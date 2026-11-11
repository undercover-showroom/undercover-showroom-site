#!/usr/bin/env python3
import os, re, html, json, secrets, string, mimetypes, smtplib, urllib.request, urllib.parse, urllib.error, hashlib, hmac, time, base64
from pathlib import Path
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from email.message import EmailMessage
from email.utils import formatdate
from io import BytesIO
from supabase_store import SupabaseStore, LocalStore, SupabaseError
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

ROOT=Path(__file__).resolve().parent
DATA_ROOT=Path(os.environ.get('DATA_ROOT', str(ROOT)))
DATA_ROOT.mkdir(parents=True, exist_ok=True)
DB=DATA_ROOT/'data.sqlite3'; UP=DATA_ROOT/'uploads'; TICK=DATA_ROOT/'tickets'; AS=ROOT/'assets'
UP.mkdir(exist_ok=True); TICK.mkdir(exist_ok=True)
ORANGE='+261 32 61 39 215'
EVENT_DATE='04 décembre 2026'; VENUE='LE FUN CLUB, Diego-Suarez'
ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD')
ADMIN_PASSWORD_HASH=os.environ.get('ADMIN_PASSWORD_HASH')
ADMIN_SESSION_SECRET=os.environ.get('ADMIN_SESSION_SECRET')
SESSION_COOKIE='ucs_admin'
SESSION_MAX_AGE=8*60*60
MAX_UPLOAD=8*1024*1024

HTML_HEAD='''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>UNDERCOVER_SHOWROOM — 04 décembre 2026</title><style>
:root{--black:#090909;--paper:#f4f2ed;--beige:#d8ccb9;--red:#a91616;--line:rgba(9,9,9,.18);--muted:#706d67}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--black);font-family:Arial,Helvetica,sans-serif}a{color:inherit;text-decoration:none}.wrap{max-width:1280px;margin:auto;padding:0 42px}header{position:sticky;top:0;z-index:10;background:rgba(244,242,237,.94);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}.nav{height:74px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{font-weight:900;letter-spacing:.13em;font-size:14px}.navlinks{display:flex;gap:28px;font-size:11px;letter-spacing:.11em;text-transform:uppercase}.navlinks a:hover{color:var(--red)}.hero{min-height:760px;background:var(--black);color:var(--paper);position:relative;overflow:hidden;display:flex;align-items:center}.hero:before{content:"";position:absolute;width:520px;height:520px;border:1px solid rgba(244,242,237,.28);border-radius:50%;right:-100px;top:-100px}.hero:after{content:"";position:absolute;width:1px;height:460px;background:var(--red);right:22%;top:20%}.hero .wrap{width:100%;position:relative;z-index:2}.kicker{font-size:12px;letter-spacing:.3em;color:var(--beige);text-transform:uppercase;margin-bottom:30px}h1{font-size:clamp(58px,11vw,156px);line-height:.83;margin:0;letter-spacing:-.07em;font-weight:900;max-width:900px}.hero-sub{margin-top:34px;max-width:650px;font-family:Georgia,serif;font-size:22px;line-height:1.45;color:#ddd8d0}.date{margin-top:50px;display:flex;align-items:flex-end;gap:20px;flex-wrap:wrap}.date strong{font-size:32px;letter-spacing:.06em}.date span{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--beige)}.actions{margin-top:42px;display:flex;gap:12px;flex-wrap:wrap}.btn{display:inline-block;padding:15px 20px;border:1px solid var(--paper);font-size:11px;letter-spacing:.15em;font-weight:800;background:transparent;color:inherit;cursor:pointer}.btn.primary{background:var(--red);border-color:var(--red);color:#fff}.section{padding:110px 0;border-bottom:1px solid var(--line)}.section.dark{background:var(--black);color:var(--paper);border-color:#292929}.eyebrow{font-size:10px;letter-spacing:.28em;text-transform:uppercase;color:var(--red);font-weight:800;margin-bottom:18px}.section h2{font-size:clamp(40px,6vw,76px);letter-spacing:-.05em;line-height:.9;margin:0 0 32px;font-weight:900}.intro{max-width:760px;font-family:Georgia,serif;font-size:21px;line-height:1.55;color:var(--muted)}.dark .intro{color:#c8c4bd}.split{display:grid;grid-template-columns:1fr 1.35fr;gap:80px;align-items:start}.program{display:grid;gap:0;border-top:1px solid currentColor}.act{display:grid;grid-template-columns:130px 1fr;gap:25px;padding:28px 0;border-bottom:1px solid currentColor}.actnum{font-size:12px;letter-spacing:.2em;color:var(--red);font-weight:900}.act h3{margin:0 0 12px;font-size:22px;text-transform:uppercase;letter-spacing:.03em}.act ul{margin:0;padding-left:18px;color:#c8c4bd;line-height:1.8}.partner-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.partner{min-height:220px;background:#fff;border:1px solid rgba(9,9,9,.13);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:26px;position:relative}.partner .logo{width:100%;height:135px;display:flex;align-items:center;justify-content:center;overflow:hidden}.partner img{max-width:100%;max-height:125px;width:auto;height:auto;object-fit:contain;display:block}.partner-name{margin-top:18px;font-size:10px;font-weight:900;letter-spacing:.16em;text-transform:uppercase;text-align:center}.partner.pending{background:transparent;border:1px dashed rgba(9,9,9,.38)}.pending-mark{width:62px;height:62px;border:1px solid rgba(9,9,9,.45);border-radius:50%;display:grid;place-items:center;font-size:24px;color:var(--red)}.pending small{margin-top:14px;color:var(--muted);font-size:9px;letter-spacing:.16em;text-transform:uppercase;text-align:center}.access{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:45px}.price{border:1px solid rgba(244,242,237,.25);padding:30px;background:#101010}.price .label{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--beige)}.price strong{display:block;font-size:34px;margin-top:20px}.price span{display:block;margin-top:8px;color:#aaa;font-size:11px}.note{margin-top:25px;font-size:11px;color:#aaa;line-height:1.7}.form{margin-top:35px;padding:30px;background:#fff;border:1px solid var(--line)}.dark .form{background:#111;border-color:#333}.fields{display:grid;grid-template-columns:1fr 1fr;gap:16px}.field{display:flex;flex-direction:column;gap:7px}.field.full{grid-column:1/-1}.field label{font-size:10px;letter-spacing:.13em;text-transform:uppercase;font-weight:800}.field input,.field select,.field textarea{width:100%;padding:13px 12px;border:1px solid #bbb;background:#fff;font:inherit}.dark .field input,.dark .field select,.dark .field textarea{background:#0b0b0b;color:#fff;border-color:#555}.paybox{margin:20px 0;padding:20px;border-left:3px solid var(--red);background:rgba(169,22,22,.07)}.paybox strong{font-size:24px;letter-spacing:.05em}.status{padding:14px 16px;background:#efe9df;border:1px solid var(--line);font-size:12px;line-height:1.6}.admin{background:#111;color:#eee;min-height:100vh;padding:45px}.admin .wrap{max-width:1200px}.admin h1{font-size:52px;max-width:none}.admin table{width:100%;border-collapse:collapse;margin-top:25px;font-size:12px}.admin th,.admin td{padding:12px;border-bottom:1px solid #333;text-align:left;vertical-align:top}.admin th{color:#cfc6b8;text-transform:uppercase;letter-spacing:.1em;font-size:9px}.admin a,.admin button{color:#fff}.badge{display:inline-block;padding:5px 8px;border:1px solid #555;font-size:9px;letter-spacing:.1em;text-transform:uppercase}.adminform{display:inline}.adminbtn{padding:7px 9px;border:1px solid #666;background:#222;cursor:pointer;margin:2px;font-size:10px}.adminbtn.ok{border-color:#8b9f83}.adminbtn.no{border-color:#a66}.small{font-size:10px;color:#aaa}.qr{width:130px;height:130px;background:#fff;padding:5px}.practical{display:grid;grid-template-columns:1fr 1fr;gap:20px}.info{padding:28px;background:#fff;border:1px solid var(--line)}.info span{display:block;font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}.info strong{font-size:22px}footer{background:var(--black);color:var(--paper);padding:50px 0}.footerline{display:flex;justify-content:space-between;gap:20px;align-items:center;font-size:10px;letter-spacing:.14em;text-transform:uppercase}@media(max-width:850px){.wrap{padding:0 20px}.navlinks{display:none}.hero{min-height:690px}.split,.partner-grid,.access,.practical{grid-template-columns:1fr}.act{grid-template-columns:1fr;gap:10px}h1{font-size:clamp(48px,15vw,90px)}.fields{grid-template-columns:1fr}.field.full{grid-column:auto}.admin{padding:20px}.admin h1{font-size:38px}.admin table{display:block;overflow:auto;white-space:nowrap}}
</style></head><body>'''


APP_MODE=os.environ.get('APP_MODE','supabase').lower()
if APP_MODE == 'local':
    STORE=LocalStore(str(DATA_ROOT/'test.sqlite3'))
else:
    STORE=SupabaseStore()

def log(kind,ref,detail):
    STORE.log(kind,ref,detail)

def refcode(prefix):
    alphabet='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    for _ in range(100):
        r=prefix+'-'+''.join(secrets.choice(alphabet) for _ in range(8))
        if not STORE.get_ticket(r) and not STORE.get_table(r):
            return r
    raise RuntimeError('Impossible de générer une référence unique.')

def esc(s): return html.escape(str(s or ''))
def parse_qs(body): return {k:v[0] for k,v in urllib.parse.parse_qs(body,keep_blank_values=True).items()}

def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return 'scrypt$16384$8$1$'+base64.urlsafe_b64encode(salt).decode()+ '$'+base64.urlsafe_b64encode(dk).decode()

def verify_password(password, encoded):
    try:
        scheme,n,r,p,salt_b64,hash_b64=encoded.split('$',5)
        if scheme!='scrypt': return False
        salt=base64.urlsafe_b64decode(salt_b64.encode())
        expected=base64.urlsafe_b64decode(hash_b64.encode())
        actual=hashlib.scrypt(password.encode('utf-8'), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def session_value():
    if not ADMIN_SESSION_SECRET: return None
    payload=f'{secrets.token_urlsafe(24)}|{int(time.time())+SESSION_MAX_AGE}'
    sig=hmac.new(ADMIN_SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode((payload+'|'+sig).encode()).decode().rstrip('=')

def verify_session(value):
    if not value or not ADMIN_SESSION_SECRET: return False
    try:
        raw=base64.urlsafe_b64decode(value+'='*((4-len(value)%4)%4)).decode()
        nonce,exp,sig=raw.split('|',2)
        payload=f'{nonce}|{exp}'
        if int(exp)<int(time.time()): return False
        expected=hmac.new(ADMIN_SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False

def csrf_token(session_value=None):
    nonce=secrets.token_urlsafe(18)
    if session_value:
        return nonce+'.'+hmac.new(ADMIN_SESSION_SECRET.encode(), (session_value+'|'+nonce).encode(), hashlib.sha256).hexdigest()
    return nonce

def csrf_ok(value, session_value=None):
    if not value: return False
    if session_value:
        try:
            nonce,sig=value.rsplit('.',1)
            expected=hmac.new(ADMIN_SESSION_SECRET.encode(), (session_value+'|'+nonce).encode(), hashlib.sha256).hexdigest()
            return hmac.compare_digest(sig,expected)
        except Exception:
            return False
    return bool(re.fullmatch(r'[A-Za-z0-9_-]{20,}', value))

def page(body): return HTML_HEAD+body+'</body></html>'
def nav(): return '<header><div class="wrap nav"><div class="brand">UNDERCOVER_SHOWROOM</div><nav class="navlinks"><a href="/#experience">Expérience</a><a href="/#programme">Programme</a><a href="/#partners">Partenaires</a><a href="/#tickets">Billetterie</a><a href="/#table">Table</a></nav></div></header>'

def homepage():
    return page(nav()+'''<main><section class="hero"><div class="wrap"><div class="kicker">04 DECEMBER 2026 · DIEGO-SUAREZ</div><h1>UNDERCOVER_<br>SHOWROOM</h1><p class="hero-sub">Réunir les mondes créatifs.</p><div class="date"><strong>04 décembre 2026</strong><span>LE FUN CLUB · Diego-Suarez</span></div><div class="actions"><a class="btn primary" href="#tickets">ACHETER UN BILLET</a><a class="btn" href="#table">RÉSERVER UNE TABLE</a></div></div></section>
<section class="section" id="experience"><div class="wrap split"><div><div class="eyebrow">L'expérience</div><h2>Une rencontre.<br>Une révélation.</h2></div><div class="intro">UNDERCOVER_SHOWROOM réunit mode, beauté, musique, performance, danse, image et autres expressions artistiques pour révéler des talents, créer des rencontres et ouvrir de nouvelles perspectives.<br><br><strong style="color:var(--black)">L’élégance se révèle. La nuit s’enflamme.</strong></div></div></section>
<section class="section dark" id="programme"><div class="wrap split"><div><div class="eyebrow">Programme</div><h2>Trois<br>parties.</h2></div><div class="program"><article class="act"><div class="actnum">01</div><div><h3>Première partie</h3><ul><li>SAKAV — première entrée et animation.</li><li>Boutique 1 — défilé par les mannequins de PCMA.</li><li>Boutique 2 — défilé par les mannequins de SM.</li><li>Transition DJ — 10 minutes.</li></ul></div></article><article class="act"><div class="actnum">02</div><div><h3>Deuxième partie</h3><ul><li>Boutique 3 — défilé par les mannequins de PCMA.</li><li>Boutique 4 — défilé par les mannequins de SM.</li><li>SAKAV — deuxième entrée et animation.</li><li>Transition DJ — 10 minutes.</li></ul></div></article><article class="act"><div class="actnum">03</div><div><h3>Troisième partie</h3><ul><li>PCMA — propres tenues et propre chorégraphie.</li><li>SM — propres tenues et propre chorégraphie.</li><li>SAKAV — troisième entrée et animation.</li><li>SAKAV invite les clients à danser avec le DJ.</li><li>La soirée se poursuit avec le DJ.</li></ul></div></article></div></div></section>
<section class="section" id="partners"><div class="wrap"><div class="eyebrow">Partenaires</div><h2>Les univers<br>qui se rencontrent.</h2><div class="partner-grid">'''+partner_cards()+'''</div></div></section>
<section class="section dark" id="tickets"><div class="wrap split"><div><div class="eyebrow">Billetterie</div><h2>Choisissez<br>votre accès.</h2><div class="access"><div class="price"><div class="label">Public</div><strong>5 000 Ar</strong><span>Billet public</span></div><div class="price"><div class="label">VIP</div><strong>20 000 Ar</strong><span>Billet VIP</span></div><div class="price"><div class="label">Table</div><strong>10 000 Ar</strong><span>Réservation de table</span></div></div></div><div><div class="form"><form method="post" action="/ticket" enctype="multipart/form-data"><div class="fields"><div class="field"><label>Prénom</label><input name="first" required></div><div class="field"><label>Nom</label><input name="last" required></div><div class="field"><label>Téléphone</label><input name="phone" required></div><div class="field"><label>E-mail</label><input type="email" name="email" required></div><div class="field"><label>Type de billet</label><select name="type" required><option value="Public">Public — 5 000 Ar</option><option value="VIP">VIP — 20 000 Ar</option></select></div><div class="field"><label>Quantité</label><input type="number" min="1" max="10" name="qty" value="1" required></div><div class="field"><label>Réception</label><select name="delivery" required><option value="email">E-mail</option><option value="whatsapp">WhatsApp</option></select></div><div class="field"><label>Confirmation</label><select name="adult" required><option value="1">Je confirme être majeur(e)</option><option value="0">Je ne confirme pas</option></select></div><div class="field full"><button class="btn primary" type="submit">ENVOYER LA DEMANDE</button></div></div></form></div><div class="note">Après l’envoi, une référence unique est créée et les instructions de paiement sont affichées. Le billet est généré après vérification administrative de la preuve de paiement.</div></div></div></section>
<section class="section" id="table"><div class="wrap split"><div><div class="eyebrow">Réservation de table</div><h2>Votre table,<br>votre espace.</h2></div><div><div class="intro">La réservation de table est proposée à <strong>10 000 Ar</strong>. Pour choisir votre table, contactez l’organisation, prenez rendez-vous et choisissez votre table. Les modalités de paiement sont communiquées ensuite.</div><div class="form"><form method="post" action="/table"><div class="fields"><div class="field"><label>Prénom</label><input name="first" required></div><div class="field"><label>Nom</label><input name="last" required></div><div class="field"><label>Téléphone</label><input name="phone" required></div><div class="field"><label>E-mail</label><input type="email" name="email" required></div><div class="field"><label>Nombre de personnes</label><input type="number" min="1" name="people" required></div><div class="field"><label>Prise de rendez-vous</label><input name="appointment" placeholder="Date / créneau souhaité" required></div><div class="field full"><label>Message</label><textarea name="notes" rows="3"></textarea></div><div class="field full"><button class="btn primary" type="submit">ENVOYER LA DEMANDE</button></div></div></form></div></div></div></section>
<section class="section"><div class="wrap"><div class="eyebrow">Informations pratiques</div><div class="practical"><div class="info"><span>Date</span><strong>04 décembre 2026</strong></div><div class="info"><span>Lieu</span><strong>LE FUN CLUB, Diego-Suarez</strong></div></div></div></section></main><footer><div class="wrap footerline"><span>UNDERCOVER_SHOWROOM</span><span>04.12.2026 · DIEGO-SUAREZ</span></div></footer>''')

def partner_cards():
    items=[('maki-company.jpg','MAKI Company'),('fitia-curly.jpg','Fitia Curly'),('diego-beaute.jpg','Diego Beauté'),('pcma.jpg','PCMA Diego-Suarez'),('orange.png','Orange')]
    s=''.join(f'<div class="partner"><div class="logo"><img src="/assets/{fn}" alt="{esc(nm)}"></div><div class="partner-name">{esc(nm)}</div></div>' for fn,nm in items)
    for nm in ['Diego Style','Self Modeling Agency','Boutique éphémère de LE FUN','SAKAV Studio','Akira']:
        s+=f'<div class="partner pending"><div class="pending-mark">+</div><div class="partner-name">{esc(nm)}</div><small>Logo à recevoir</small></div>'
    return s

def make_ticket(row):
    ref=row['ref']; qrfile=TICK/f'{ref}.png'; pdffile=TICK/f'{ref}.pdf'
    qr=qrcode.make(f'UNDERCOVER_SHOWROOM|{ref}|{row["type"]}|{row["qty"]}')
    qr.save(qrfile)
    c=canvas.Canvas(str(pdffile),pagesize=A4); w,h=A4
    c.setFillColorRGB(.035,.035,.035); c.rect(0,0,w,h,fill=1,stroke=0)
    c.setFillColorRGB(.96,.95,.93); c.setFont('Helvetica-Bold',30); c.drawString(24*mm,h-40*mm,'UNDERCOVER_SHOWROOM')
    c.setFont('Helvetica',12); c.drawString(24*mm,h-50*mm,'04 décembre 2026 · LE FUN CLUB, Diego-Suarez')
    c.setFillColorRGB(.66,.09,.09); c.rect(24*mm,h-68*mm,38*mm,1.2*mm,fill=1,stroke=0)
    c.setFillColorRGB(.96,.95,.93); c.setFont('Helvetica-Bold',22); c.drawString(24*mm,h-92*mm,row['type'].upper())
    c.setFont('Helvetica',12); c.drawString(24*mm,h-105*mm,f'Référence : {ref}')
    c.drawString(24*mm,h-115*mm,f'Titulaire : {row["first"]} {row["last"]}')
    c.drawString(24*mm,h-125*mm,f'Quantité : {row["qty"]}')
    c.drawImage(str(qrfile),w-75*mm,h-155*mm,width=48*mm,height=48*mm)
    c.setFont('Helvetica',9); c.drawString(24*mm,24*mm,'Billet généré après validation de la preuve de paiement.')
    c.save(); return pdffile,qrfile

def send_email(row,pdf):
    host=os.environ.get('SMTP_HOST'); port=int(os.environ.get('SMTP_PORT','587')); user=os.environ.get('SMTP_USER'); pw=os.environ.get('SMTP_PASSWORD'); sender=os.environ.get('SMTP_FROM',user or '')
    if not all([host,user,pw,sender,row['email']]): return False,'SMTP non configuré'
    msg=EmailMessage(); msg['Subject']=f'Votre billet UNDERCOVER_SHOWROOM — {row["ref"]}'; msg['From']=sender; msg['To']=row['email']
    msg.set_content(f'Votre billet UNDERCOVER_SHOWROOM est validé. Référence : {row["ref"]}. Billet en pièce jointe.')
    msg.add_attachment(pdf.read_bytes(),maintype='application',subtype='pdf',filename=pdf.name)
    with smtplib.SMTP(host,port,timeout=20) as s:
        s.starttls(); s.login(user,pw); s.send_message(msg)
    return True,'E-mail envoyé'

def send_whatsapp(row,pdf,media_url=None):
    token=os.environ.get('WHATSAPP_TOKEN'); phone_id=os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    if not token or not phone_id: return False,'API WhatsApp non configurée'
    # Cloud API requires an externally hosted media URL or upload flow; this implementation reports the missing public media URL.
    public_url=media_url or os.environ.get('WHATSAPP_PUBLIC_MEDIA_URL')
    if not public_url: return False,'URL de média WhatsApp non configurée'
    version=os.environ.get('WHATSAPP_GRAPH_VERSION','v21.0')
    url=f'https://graph.facebook.com/{version}/{phone_id}/messages'
    payload={'messaging_product':'whatsapp','to':row['phone'].replace(' ','').replace('+',''),'type':'document','document':{'link':public_url,'caption':f'Billet UNDERCOVER_SHOWROOM — {row["ref"]}','filename':pdf.name}}
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=20) as r: return True,'WhatsApp envoyé'
    except Exception as e: return False,'Échec WhatsApp: '+str(e)[:180]

def admin_page(handler):
    rows=STORE.list_tickets(); tables=STORE.list_tables()
    cookie=handler.headers.get('Cookie','')
    session_value=cookie.split(SESSION_COOKIE+'=',1)[1].split(';',1)[0] if SESSION_COOKIE+'=' in cookie else ''
    csrf=csrf_token(session_value)
    s='<div class="admin"><div class="wrap"><div class="small">ADMINISTRATION · UNDERCOVER_SHOWROOM</div><h1>Billetterie</h1><p>Orange Money : <strong>+261 32 61 39 215</strong></p><h2>Demandes de billets</h2><table><tr><th>Réf.</th><th>Client</th><th>Billet</th><th>Preuve</th><th>Statut</th><th>Action</th></tr>'
    for r in rows:
        proof=f'<a href="/proof/{esc(r["ref"])}" target="_blank">Voir preuve</a>' if r['proof'] else '—'
        acts=''
        if r['status']!=STORE.status_validated: acts+=f'<form class="adminform" method="post" action="/admin/validate"><input type="hidden" name="ref" value="{esc(r["ref"])}"><input type="hidden" name="csrf" value="{csrf}"><button class="adminbtn ok">VALIDER</button></form>'
        if r['status']!=STORE.status_rejected: acts+=f'<form class="adminform" method="post" action="/admin/reject"><input type="hidden" name="ref" value="{esc(r["ref"])}"><input type="hidden" name="csrf" value="{csrf}"><button class="adminbtn no">REFUSER</button></form>'
        if r['status']==STORE.status_validated: acts+=f'<a class="adminbtn" href="/ticket/{esc(r["ref"])}.pdf">BILLET</a><form class="adminform" method="post" action="/admin/send"><input type="hidden" name="ref" value="{esc(r["ref"])}"><input type="hidden" name="csrf" value="{csrf}"><button class="adminbtn">ENVOYER</button></form>'
        s+=f'<tr><td>{esc(r["ref"])}</td><td>{esc(r["first"])} {esc(r["last"])}<br>{esc(r["phone"])}<br>{esc(r["email"])}</td><td>{esc(r["type"])} × {r["qty"]}<br>{esc(r["delivery"])}</td><td>{proof}</td><td><span class="badge">{esc(r["status"])}</span><br><span class="small">{esc(r["send_status"])}</span></td><td>{acts}</td></tr>'
    s+='</table><h2>Réservations de table</h2><table><tr><th>Réf.</th><th>Client</th><th>Personnes</th><th>Rendez-vous</th><th>Message</th><th>Statut</th></tr>'
    for r in tables: s+=f'<tr><td>{esc(r["ref"])}</td><td>{esc(r["first"])} {esc(r["last"])}<br>{esc(r["phone"])}<br>{esc(r["email"])}<br></td><td>{r["people"]}</td><td>{esc(r["appointment"])}</td><td>{esc(r["notes"])}</td><td>{esc(r["status"])}</td></tr>'
    s+='</table><p class="small">Les preuves et billets sont stockés dans un stockage privé. Les envois e-mail/WhatsApp utilisent les services externes configurés.</p></div></div>'
    return HTML_HEAD+s+'</body></html>'

class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def send_html(self,body,status=200):
        b=body.encode('utf-8'); self.send_response(status); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('X-Frame-Options','DENY'); self.send_header('Referrer-Policy','no-referrer'); self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'"); self.end_headers(); self.wfile.write(b)
    def redirect(self,url): self.send_response(303); self.send_header('Location',url); self.end_headers()
    def redirect_external(self,url): self.send_response(302); self.send_header('Location',url); self.end_headers()
    def admin_ok(self):
        cookie=self.headers.get('Cookie','')
        value=cookie.split(SESSION_COOKIE+'=',1)[1].split(';',1)[0] if SESSION_COOKIE+'=' in cookie else ''
        return verify_session(value)
    def csrf_ok_request(self,d):
        cookie=self.headers.get('Cookie','')
        session_value=cookie.split(SESSION_COOKIE+'=',1)[1].split(';',1)[0] if SESSION_COOKIE+'=' in cookie else ''
        return csrf_ok(d.get('csrf',''), session_value)
    def do_GET(self):
        p=urllib.parse.urlparse(self.path).path
        if p=='/': self.send_html(homepage()); return
        if p.startswith('/assets/'):
            f=AS/p.split('/')[-1]
            if f.exists(): self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(f.name)[0] or 'application/octet-stream'); self.end_headers(); self.wfile.write(f.read_bytes()); return
        if p=='/admin/login':
            token=csrf_token()
            self.send_html(page(nav()+f'''<section class="section"><div class="wrap"><div class="eyebrow">Administration</div><h2>Connexion</h2><div class="form"><form method="post" action="/admin/login"><input type="hidden" name="csrf" value="{token}"><div class="field"><label>Mot de passe administrateur</label><input type="password" name="password" required></div><br><button class="btn primary">SE CONNECTER</button></form></div></div></section>''')); return
        if p=='/admin':
            if not self.admin_ok(): self.redirect('/admin/login'); return
            self.send_html(admin_page(self)); return
        if p.startswith('/proof/'):
            if not self.admin_ok(): self.send_response(403); self.end_headers(); return
            ref=p.split('/')[2] if len(p.split('/'))>2 else ''
            row=STORE.get_ticket(ref); path=row['proof'] if row else ''
            if not path: self.send_response(404); self.end_headers(); return
            if APP_MODE=='local':
                f=Path(path)
                if not f.exists(): self.send_response(404); self.end_headers(); return
                self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(f.name)[0] or 'application/octet-stream'); self.end_headers(); self.wfile.write(f.read_bytes()); return
            try:
                url=STORE.signed_url(STORE.proof_bucket,path,expires=600); self.redirect_external(url); return
            except Exception: self.send_response(404); self.end_headers(); return
        if p.startswith('/ticket/'):
            if not self.admin_ok(): self.send_response(403); self.end_headers(); return
            ref=p.split('/')[2].split('.')[0] if len(p.split('/'))>2 else ''
            row=STORE.get_ticket(ref); path=row['ticket_pdf'] if row else ''
            if not path: self.send_response(404); self.end_headers(); return
            if APP_MODE=='local':
                f=TICK/Path(path).name
                if not f.exists(): self.send_response(404); self.end_headers(); return
                self.send_response(200); self.send_header('Content-Type','application/pdf'); self.send_header('Content-Disposition',f'inline; filename="{f.name}"'); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(f.read_bytes()); return
            try:
                url=STORE.signed_url(STORE.ticket_bucket,path,expires=600); self.redirect_external(url); return
            except Exception: self.send_response(404); self.end_headers(); return
        self.send_response(404); self.end_headers()
    def do_POST(self):
        p=urllib.parse.urlparse(self.path).path
        ctype=self.headers.get('Content-Type',''); length=int(self.headers.get('Content-Length','0'))
        if length>12*1024*1024: self.send_html('<h1>Requête trop volumineuse</h1>',413); return
        body=self.rfile.read(length)
        if p=='/admin/login':
            d=parse_qs(body.decode());
            configured=bool(ADMIN_PASSWORD_HASH and ADMIN_SESSION_SECRET)
            valid_csrf=csrf_ok(d.get('csrf',''))
            password_ok=verify_password(d.get('password',''),ADMIN_PASSWORD_HASH) if ADMIN_PASSWORD_HASH else bool(ADMIN_PASSWORD and secrets.compare_digest(d.get('password',''),ADMIN_PASSWORD))
            if configured and valid_csrf and password_ok:
                sid=session_value(); secure='; Secure' if os.environ.get('PUBLIC_HTTPS')=='1' else ''
                self.send_response(303); self.send_header('Set-Cookie',f'{SESSION_COOKIE}={sid}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_MAX_AGE}{secure}'); self.send_header('Location','/admin'); self.end_headers(); return
            self.send_html(page(nav()+'<section class="section"><div class="wrap"><h2>Accès refusé</h2><p>Mot de passe incorrect ou administration non configurée.</p></div></section>'),403); return
        if p=='/ticket':
            if not ctype.startswith('application/x-www-form-urlencoded'): self.send_html('Format invalide',400); return
            d=parse_qs(body.decode()); first=d.get('first','').strip(); last=d.get('last','').strip(); phone=d.get('phone','').strip(); email=d.get('email','').strip(); typ=d.get('type',''); qty=int(d.get('qty','1') or 1); delivery=d.get('delivery',''); adult=d.get('adult','0')
            if not all([first,last,phone,email]) or typ not in ('Public','VIP') or not (1<=qty<=10) or delivery not in ('email','whatsapp') or adult!='1': self.send_html(page(nav()+'<section class="section"><div class="wrap"><h2>Demande non envoyée</h2><p>Veuillez vérifier les champs et confirmer la majorité.</p></div></section>'),400); return
            ref=refcode('UCS'); now=datetime.now(timezone.utc).isoformat(); row=STORE.create_ticket({'ref':ref,'first':first,'last':last,'phone':phone,'email':email,'type':typ,'qty':qty,'delivery':delivery,'created_at':now}); log('ticket',ref,'Demande créée')
            total=(5000 if typ=='Public' else 20000)*qty
            b=page(nav()+f'''<section class="section"><div class="wrap"><div class="eyebrow">Demande enregistrée</div><h2>Référence<br>{esc(ref)}</h2><div class="status">Votre demande est enregistrée. Conservez cette référence.</div><div class="paybox"><div class="eyebrow">Paiement Orange Money</div><p>Transférez <strong>{total:,} Ar</strong> vers le numéro officiel :</p><strong>{ORANGE}</strong><p class="note">Après le transfert, déposez votre preuve de paiement ci-dessous. La demande sera vérifiée par l’administrateur avant validation du billet.</p></div><div class="form"><form method="post" action="/proof" enctype="multipart/form-data"><input type="hidden" name="ref" value="{esc(ref)}"><div class="field"><label>Preuve de paiement</label><input type="file" name="proof" accept="image/*,application/pdf" required></div><br><button class="btn primary">DÉPOSER LA PREUVE</button></form></div></div></section>'''); self.send_html(b); return
        if p=='/proof':
            ref=next((x.strip() for x in re.findall(r'name="ref"\r\n\r\n([^\r\n]+)',body.decode('latin1'))),None)
            row=STORE.get_ticket(ref) if ref else None
            if not row: self.send_html('<h1>Référence introuvable</h1>',404); return
            boundary=ctype.split('boundary=',1)[-1].strip().strip('"')
            chunks=body.split(('--'+boundary).encode())
            saved=None; content=b''; ctype_file='application/octet-stream'
            for ch in chunks:
                if b'filename=' not in ch: continue
                header,data=ch.split(b'\r\n\r\n',1); data=data.rsplit(b'\r\n',1)[0]
                fn=re.search(br'filename="([^"]+)"',header)
                mt=re.search(br'Content-Type:\s*([^\r\n]+)',header,re.I)
                if fn:
                    original=fn.group(1).decode('utf-8','ignore'); safe=re.sub(r'[^A-Za-z0-9._-]','_',original)[:80]
                    saved=f'{ref}/{safe}'; content=data; ctype_file=(mt.group(1).decode() if mt else mimetypes.guess_type(safe)[0] or 'application/octet-stream'); break
            if not saved or not content: self.send_html('<h1>Preuve manquante</h1>',400); return
            try:
                if APP_MODE=='local':
                    local_path=UP/(ref+'_'+Path(saved).name); local_path.write_bytes(content); proof_url=str(local_path)
                else:
                    STORE.upload_file(STORE.proof_bucket,saved,content,ctype_file); proof_url=saved
                STORE.update_ticket_proof(ref,proof_url); log('proof',ref,'Preuve déposée')
            except Exception as e:
                self.send_html(page(nav()+f'<section class="section"><div class="wrap"><h2>Preuve non enregistrée</h2><div class="status">Erreur de stockage : {esc(str(e)[:300])}</div></div></section>'),500); return
            self.send_html(page(nav()+f'<section class="section"><div class="wrap"><div class="eyebrow">Preuve reçue</div><h2>Merci.</h2><div class="status">Votre preuve de paiement a été reçue. Elle sera vérifiée par l’administrateur. Référence : <strong>{esc(ref)}</strong>.</div></div></section>')); return
        if p=='/table':
            d=parse_qs(body.decode()); ref=refcode('TAB'); now=datetime.now(timezone.utc).isoformat(); STORE.create_table_reservation({'ref':ref,'first':d.get('first',''),'last':d.get('last',''),'phone':d.get('phone',''),'email':d.get('email',''),'people':int(d.get('people','1') or 1),'appointment':d.get('appointment',''),'notes':d.get('notes',''),'created_at':now}); log('table',ref,'Demande de réservation créée'); self.send_html(page(nav()+f'<section class="section"><div class="wrap"><div class="eyebrow">Réservation</div><h2>Demande enregistrée.</h2><div class="status">Référence : <strong>{esc(ref)}</strong>. L’organisation peut maintenant contacter le demandeur pour la prise de rendez-vous et le choix de la table.</div></div></section>')); return
        if p.startswith('/admin/'):
            if not self.admin_ok(): self.send_response(403); self.end_headers(); return
            d=parse_qs(body.decode())
            if not self.csrf_ok_request(d): self.send_response(403); self.end_headers(); return
            ref=d.get('ref',''); row=STORE.get_ticket(ref)
            if not row: self.send_html('<h1>Référence introuvable</h1>',404); return
            if p=='/admin/validate':
                if not row['proof']: self.send_html(page('<div class="admin"><div class="wrap"><h1>Impossible de valider</h1><p>Aucune preuve de paiement n’est déposée.</p></div></div>'),400); return
                try:
                    pdf,qr=make_ticket(row)
                    if APP_MODE=='local':
                        ticket_url=pdf.name; qr_url=qr.name
                    else:
                        STORE.upload_file(STORE.ticket_bucket,f'{ref}/{pdf.name}',pdf.read_bytes(),'application/pdf')
                        STORE.upload_file(STORE.ticket_bucket,f'{ref}/{qr.name}',qr.read_bytes(),'image/png')
                        ticket_url=f'{ref}/{pdf.name}'; qr_url=f'{ref}/{qr.name}'
                    STORE.update_ticket_validated(ref,ticket_url,qr_url,datetime.now(timezone.utc).isoformat())
                    log('validate',ref,'Billet généré et validé')
                    if row['delivery']=='email': ok,msg=send_email(row,pdf)
                    else:
                        media_url = STORE.signed_url(STORE.ticket_bucket,ticket_url,expires=900) if APP_MODE!='local' else None
                        ok,msg=send_whatsapp(row,pdf,media_url)
                    STORE.update_send_status(ref,msg if ok else 'Non envoyé — '+msg); log('send',ref,msg)
                except Exception as e:
                    self.send_html(page('<div class="admin"><div class="wrap"><h1>Validation interrompue</h1><p>'+esc(str(e)[:500])+'</p></div></div>'),500); return
                self.redirect('/admin'); return
            if p=='/admin/reject': STORE.update_ticket_rejected(ref); log('reject',ref,'Demande refusée'); self.redirect('/admin'); return
            if p=='/admin/send':
                pdf=TICK/Path(row['ticket_pdf']).name if row['ticket_pdf'] else None
                if not pdf or not pdf.exists():
                    # Regenerate locally from the current validated record when the PDF is not on the web instance.
                    pdf,_=make_ticket(row)
                if row['delivery']=='email': ok,msg=send_email(row,pdf)
                else:
                    media_url=STORE.signed_url(STORE.ticket_bucket,row['ticket_pdf'],expires=900) if APP_MODE!='local' else None
                    ok,msg=send_whatsapp(row,pdf,media_url)
                STORE.update_send_status(ref,msg if ok else 'Non envoyé — '+msg); log('send',ref,msg); self.redirect('/admin'); return
        self.send_response(404); self.end_headers()

def main():
    if APP_MODE!='local': STORE.ensure_buckets()
    port=int(os.environ.get('PORT','8080')); server=ThreadingHTTPServer(('0.0.0.0',port),H); print(f'UNDERCOVER_SHOWROOM running on http://127.0.0.1:{port}'); server.serve_forever()
if __name__=='__main__': main()
