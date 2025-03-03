from hashlib import sha256
import hashlib
import base64
import ecdsa
from ecdsa import SigningKey, NIST256p, VerifyingKey
from ecdsa.util import sigencode_string
import socket
from select import select
import binascii
from datetime import datetime
import threading
import json
import os
import sqlite3
from protocol import *
'''
key = SigningKey.generate(curve=NIST256p)
public = key.get_verifying_key()
#"""  """
transaction = "Tal>1488>NC>Misha>19:19/"
#enc_transaction = hashlib.sha256(transaction)
#encc = key.sign_deterministic(transaction, hashfunc=sha256,sigencode=sigencode_string)
def time_accept(time: int, server_socket):
    try:
        server_socket.settimeout(time)
        ready, _, _ = select([server_socket], [], [], time)

        if ready:
            return server_socket.accept()

        return None, None

    except Exception as e:
        return None, None
        
    

#print(public.to_string())
#print(encc)
#print(enc_transaction)
print("sdfsdf")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('127.0.0.1', 22222))
server_socket.listen()

conn, addr = server_socket.accept()

while conn == None:
    pass


data = conn.recv(1024)

print(data.decode())


t1 = hashlib.sha256("qqqq".encode()).digest()
t2 = hashlib.sha256("eeee".encode()).digest()
e1 = base64.b32encode(t1)
e2 = base64.b32encode(t2)

print(e1)
print(e2)
'''
'''
priv = ecdsa.SigningKey.generate()
pub :ecdsa.VerifyingKey = priv.get_verifying_key()
sign = priv.sign_deterministic("q".encode(), hashfunc=sha256 ,sigencode=sigencode_string)
pubs = pub.to_string("compressed")
hexpubs = binascii.hexlify(sign)
h = hashlib.sha256("q".encode())
q= "q".encode()
c = True
nonce = str(0).encode()
count = 0
while c:
    if hashlib.sha256(q+nonce).hexdigest().startswith("0000"):
        c = False
        print(hashlib.sha256(q+nonce).hexdigest())
        break
    count+=1
    nonce = str(count).encode()
    print(count)

di = {"age":2, "country":"russia"}
dic = json.dumps(di, indent=3)
with open("asd.json", "a") as f:
    f.write(dic+ "\n")
'''


'''
num = 5

print(pubs + ">".encode())

try:
    print()
except Exception as e:
    print(e)

print(len(pubs))
print(len(pubs + ">".encode()))
print(num.encode())
'''


conn = sqlite3.connect(f'databases/Node/blockchain.db')
cursor = conn.cursor()
cursor.execute(f'''
SELECT block_hash from blocks WHERE block_id={1}
''')

print(hashex("ed53dd9da999e70e0e34e064194b559fddd85c5a603b5b21ba720d9fd3784513"))






'''
trial = ""
sum=0
for i in range(10):
    time.sleep(2)
    nonce=0
    start_time = time.time()
    while True:
        
        if nonce>100000000:
            trial += "NO \n"
            break
        if nonce%100000==0:
            headers = strheader + datetime.now().strftime("%d.%m.%Y %H:%M:%S") + ", "
        header = headers + str(nonce)+ ")" # header with no hash

        hash = hashex(hashex(header)) # sha256 *2 the header with the nonce

        if hash.startswith(diff*"0"): # if the hash is good mine the block
            mining_time = time.time()-start_time
            trial = trial +str(mining_time) + "\n"
            sum += mining_time
            print(mining_time)
            break
        

        else:
            nonce+=1 # increase the nonce

print(trial)
print(sum/10)
'''

