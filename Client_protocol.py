import hashlib 
import shutil
import logging
import socket
from hashlib import sha256
from hashlib import blake2s
from ecdsa import ecdsa, VerifyingKey, NIST256p, SigningKey
from ecdsa.util import sigencode_string, sigdecode_string
import os
import ecdsa
import binascii
import base64
import sqlite3
import bip39
import time 
import ast
from protocol import *


NEW_USER = "New user just registered, address: "
DEFAULT_PORT =13333

def send(msg, skt: socket):
    skt.send(format_data(msg).encode())

def create_seed():
    '''creates a seed phrase and returns public_key'''
    entropy = os.urandom(16)
    mnemonic = bip39.encode_bytes(entropy)

    seed = bip39.phrase_to_seed(mnemonic)

    private_key_bytes = hashlib.sha256(seed).digest()
    private_key = SigningKey.from_string(private_key_bytes, NIST256p)
    pub_key = private_key.get_verifying_key()


    return mnemonic, address_from_key(pub_key)

def address_from_key(public_key: VerifyingKey):
    hexedpub = binascii.hexlify(public_key.to_string("compressed"))
    
    firsthash = hashlib.sha256(hexedpub).digest()
    secdhash = hashlib.blake2s(firsthash, digest_size=16)

    checksum = hashlib.sha256(secdhash.digest()).hexdigest()[:4] #grabbing the dirst 4 bytes of the address

    return "RR" + secdhash.hexdigest() + checksum


def add_new_user(address, tokenlist, conn):
    cursor = conn.cursor()
    for token in tokenlist: # adding to the balances db

        cursor.execute('''
            INSERT INTO balances (address, balance, token, nonce) VALUES (?, ?, ?, ?)
        ''', (address, 0, token, 1))

def encrypt_data(data: bytes, password: str) -> bytes:
    # Generate a salt (random data for key derivation)
    salt = os.urandom(16)

    # Derive a key from the password using PBKDF2HMAC
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

    # Create a Fernet object for encryption
    fernet = Fernet(key)

    # Encrypt the data
    encrypted_data = fernet.encrypt(data)

    # Return the salt and encrypted data (both are needed for decryption)
    print(salt + encrypted_data)
    return salt + encrypted_data

def decrypt_data(encrypted_data: bytes, password: str) -> bytes:
    # Extract the salt and encrypted data
    salt = encrypted_data[:16]
    encrypted_data = encrypted_data[16:]

    # Derive the key using the same password and salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

    # Create a Fernet object for decryption
    fernet = Fernet(key)

    # Decrypt the data
    decrypted_data = fernet.decrypt(encrypted_data)
    return decrypted_data

def send_block(blockid: int, skt :socket, type:str) -> bool:
    '''
    sends a block with a specific index to a socket
    returns true if sent all without problems
    false if failed to retrieve from the tables
    '''
    

    conn = sqlite3.connect(f"databases/{type}/blockchain.db") # client/node/miner
    cursor = conn.cursor()
    #getting the block header
    cursor.execute(f'''
            SELECT * FROM blocks WHERE block_id = {blockid}
            ''')
    
    block_header = cursor.fetchall()[0] # retrieve the block header to send first
    if block_header: # if valid
        # getting the transaction list
        cursor.execute(f'''
        SELECT * FROM transactions WHERE block_id = {blockid}
                    ''')
        
        trans_list = cursor.fetchall()
        if trans_list: # if valid
            send(BLOCKSENDMSG+">"+str(block_header), skt) # sending the starter
            for tr in trans_list: # sending all the transactions
                #tr in tuple type
                t= str(tr)
                send(t, skt)
            send(BLOCKSTOPMSG, skt)

            return True
            
        else:
            #the block id is false
            write_to_log(f" protocol / failed to send a block with index {blockid}")
            return False

def recieve_trs(skt: socket, typpe:str, conn: sqlite3.Connection):
    '''
    recieves a blocks transactions
    returns true if all are saved 
    returns false if had errors saving
    '''
    conn = sqlite3.connect(f'databases/{typpe}/blockchain.db')
    cursor = conn.cursor()

    recieving =True
    try:
        skt.settimeout(3) # set timeout and if no data is sent in this time will raise exception to not make endless loop
        while recieving: # while loop to get all the transactions
            (success, transaction) = receive_buffer(skt)

            if success: #when recieved a message
                if transaction==BLOCKSTOPMSG: #if all transactions are sent
                    break
                #store the transaction
                cursor.execute(f'''
                INSERT INTO transactions 
                VALUES {transaction}
                ''')
                conn.commit()

        return True
    except Exception as e:
        #handle failure
        write_to_log(f" protocol / error in saving/recieving the transactions of the block ; {e}")
        return False

def recieve_block(header:str, typpe:str, skt:socket)->bool:
    '''
    saves the block and the transactions in the database
    '''
    success = True
    try:
        #conncet to the database
        conn = sqlite3.connect(f'databases/{typpe}/blockchain.db')
        cursor = conn.cursor()

        head_str = header.split(">")[1] # get the string version of the header data
        header_tuple  = ast.literal_eval(head_str)
        id = header_tuple[0] 

        # verify the block
        cursor.execute('''
            SELECT block_id, previous_block_hash FROM blocks ORDER BY block_id DESC LIMIT 1
            ''')
        lastb_id, prev_hash = cursor.fetchone() # get the last block
        
        if id!=lastb_id+1: # check the block_id
            send("Block id is invalid",skt)
            return False
        head_no_hash = "(" +id +str(header_tuple[2:])[1:]
        if hashex(head_no_hash)!=header_tuple[1] and header_tuple[2]!=prev_hash: # check the hash
            send("Header hash is invalid",skt)
            return False
        
        
        #store it in the db
        cursor.execute(f'''
                INSERT INTO blocks 
                VALUES {head_str}
                ''')
        conn.commit()

        success =  recieve_trs(skt, typpe, conn) # store the transactions of the block
        if success:
            send(SAVEDBLOCK,skt)
            write_to_log(f"Successfully saved the block {id} and its transactions") # log 
            conn.close()
            return True # if all saved successfully
        
        else: #if all saved unsuccessfully
            #delete all the wrong saved data
            cursor.execute(f''' 
            DELETE FROM blocks WHERE block_id = {id} ''')

            cursor.execute(f'''
            DELETE FROM transactions WHERE block_id = {id} ''')
            conn.commit()
            conn.close()
            return False
    
    except Exception as e:
        if str(e).startswith("UNIQUE constraint"): # if recieving a saved block
            send("Already have the block", skt)
        #log the exception
        write_to_log(f" protocol / couldnt save the block header,type {typpe}; {e}")
        return False







    



