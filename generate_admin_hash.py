import base64, hashlib, secrets, getpass
p=getpass.getpass('Admin password: ')
s=secrets.token_bytes(16)
d=hashlib.scrypt(p.encode(),salt=s,n=2**14,r=8,p=1,dklen=64)
print('ADMIN_PASSWORD_HASH=scrypt$16384$8$1$'+base64.urlsafe_b64encode(s).decode()+'$'+base64.urlsafe_b64encode(d).decode())
