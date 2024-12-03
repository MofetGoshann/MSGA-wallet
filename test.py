from hashlib import sha256
import hashlib
import ecdsa
from ecdsa import SigningKey, NIST256p
from ecdsa.util import sigencode_string

key = SigningKey.generate(curve=NIST256p)
public = key.get_verifying_key()

transaction = "Tal>1488>NC>Misha".encode()
enc_transaction = hashlib.sha256(transaction).hexdigest()
encc = key.sign_deterministic(transaction, hashfunc=sha256,sigencode=sigencode_string)

print(transaction)
print(encc)
print(enc_transaction)