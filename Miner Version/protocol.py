import hashlib 
import shutil
import logging
import socket
import json
from hashlib import sha256
from hashlib import blake2s
from ecdsa import ecdsa, VerifyingKey, NIST256p
from ecdsa.util import sigencode_string, sigdecode_string
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import binascii
import base64
import sqlite3
import time 
import ast


    #helpinginfo
    # < divider of the transactioninfo
    # > divider of the transaction
    # - divider of the block
    # = divider of the transactionlist

DISCONNECT_MSG = "EXIT"
KICK_MSG = "You have been kicked."
LOG_FILE: str = "LogFile.log"
FORMAT: str = "utf-8"
LOG_MSG = "Successfully logged in."
REG_MSG = "Successfully registered, enjoy!"
BAD_TRANS_MSG = "Transaction you sent has failed verification"
byte_decode_error = "'utf-8' codec can't decode byte"
BLOCKSENDMSG = "Sending block..."
MINEDBLOCKSENDMSG = "Sending mined block"
BLOCKSTOPMSG = "Stop recieving transactions"
CHAINUPDATEREQUEST = "Can you send me the blockchain from block"
CHAINUPDATING = "Sending the blocks"
SAVEDBLOCK = "Saved the whole block"
ALREADYUPDATED = "You have the whole blockchain"
WRONGID = "There is no blocks after this id"
FAILEDTOSAVEBLOCK = "Could not save the block"
GOOD_TRANS_MSG = "Transaction verified"
TRANS = "Transaction:"
PORT: int = 12345

DEFAULT_IP: str = "0.0.0.0"
BUFFER_SIZE: int = 1024
HEADER_SIZE = 4



logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def convert_data(buffer: str) -> (str, list):
    #converts a command(separator)>args to
    #string of the command, list of the arguments

    try:
        data = buffer.split(">")
        return data
    except Exception as e:

        # In case our data is only a message without arguments
        return buffer, None


def format_data(data) -> str:
#adds header accounting the header size

    data_length = len(data)
    num_str = str(data_length)
    padding = "0" * (HEADER_SIZE - len(num_str))

    return f"{padding + num_str}{data}"
'''
def format_data(data:bytes) ->bytes:

    data_length = len(data)
    num_str = str(data_length)
    padding = "0" * (HEADER_SIZE - len(num_str))

    return f"{(padding + num_str).encode()}{data}"
'''

def write_to_log(data):
    """
    Print and write to log data
    """
    logging.info(data)
    print(data)

def receive_buffer(my_socket: socket) -> tuple[bool,str]:
    """
    Extracts a message from the socket and handles potential errors.
    """

    try:
        buffer_size = int(my_socket.recv(HEADER_SIZE).decode())
        logging.info("  Protocol  · Buffer size : {}".format(buffer_size))

        buffer = my_socket.recv(buffer_size)
        logging.info("  Protocol  · Buffer data : {}".format(buffer.decode()))

        return True, buffer.decode()
    except Exception as e:
        # On buffer size convert fail
        return False, "Error"    
    



def address_from_key(public_key: VerifyingKey):
    hexedpub = binascii.hexlify(public_key.to_string("compressed"))
    
    firsthash = hashlib.sha256(hexedpub).digest()
    secdhash = hashlib.blake2s(firsthash, digest_size=16)

    checksum = hashlib.sha256(secdhash.digest()).hexdigest()[:4] #grabbing the dirst 4 bytes of the address

    return "RR" + secdhash.hexdigest() + checksum





    



def chain_on_start(type: str, skt:socket):
    try:
        conn = sqlite3.connect(f'databases/{type}/blockchain.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
            block_id INT PRIMARY KEY NOT NULL,
            block_hash VARCHAR(64) NOT NULL,
            previous_block_hash VARCHAR(64),
            merkle_root VARCHAR(64) NOT NULL,
            timestamp VARCHAR(24) NOT NULL,
            difficulty INT NOT NULL,
            nonce INT NOT NULL
            )
            ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
            block_id INT NOT NULL,
            nonce INT NOT NULL,
            timestamp VARCHAR(24) NOT NULL,
            sender VARCHAR(64) NOT NULL,
            reciever VARCHAR(64) NOT NULL,
            amount REAL NOT NULL,
            token VARCHAR(12) NOT NULL,
            hex_pub_key VARCHAR(256) NOT NULL,
            hex_signature VARCHAR(256) NOT NULL
            )
            ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balances (
            uId INT NOT NULL,
            address VARCHAR(64) NOT NULL,
            balance REAL NOT NULL,
            token VARCHAR(12) NOT NULL,
            nonce INT NOT NULL
            )
            ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
            uId INT NOT NULL,
            username VARCHAR(16) NOT NULL,
            pass VARCHAR(16) NOT NULL
            )
            ''')
        
        
        
        cursor.execute('''
            SELECT block_id FROM blocks ORDER BY block_id DESC LIMIT 1
            ''')

        lastb_id= cursor.fetchone()[0] # get the last block
        conn.commit()
        conn.close()

        if lastb_id: # get the chain from last block
            skt.send(format_data(CHAINUPDATEREQUEST + f">{lastb_id}").encode())
            return lastb_id
        else:  # get the whole chain
            skt.send(format_data(CHAINUPDATEREQUEST + f">{0}").encode())
    except Exception as e:
        write_to_log(" protocol / Failed to start chain; "+e)
        return "Failed to start chain; "+e
        
        
def hashex(data:str):
    '''returns the hash of data hexed'''
    return hashlib.sha256(data.encode(FORMAT)).hexdigest()

def verify_transaction(transmsg_full: str):
    #try:
        transaction_tuple: tuple = ast.literal_eval(transmsg_full)
        # str to tuple
        if not len(transaction_tuple)==8: # if wrong len
            return False, "Wrong transaction format"
        
        conn = sqlite3.connect(f'databases/Node/blockchain.db')
        cursor = conn.cursor()
        amount_spent = float(transaction_tuple[4])
        token = transaction_tuple[5]
        cursor.execute(f'''
        SELECT balance, nonce FROM balances WHERE address='{transaction_tuple[2]}' AND token='{token}'
        ''')
        result = cursor.fetchone()


        if result==None:
            return False, "No account with the address"
        balance = float(result[0])
        nonce = result[1]
        if balance<amount_spent: # spending nonexistant money
            return False, "Your account balance is lower then the amount you are trying to spend"
        if nonce>int(transaction_tuple[0]):
            return False, "Wrong nonce"
        
        hexedsignature = transaction_tuple[6]
        hexedpublickey = transaction_tuple[7]

        transaction: tuple = transaction_tuple[:-2] #transaction without the scriptsig
        st_transaction = str(transaction)
        public_key:VerifyingKey = VerifyingKey.from_string(binascii.unhexlify(hexedpublickey),NIST256p) # extracting he key
        signature: bytes = binascii.unhexlify(hexedsignature)
    
        is_valid = public_key.verify(signature, st_transaction.encode(),sha256,sigdecode=sigdecode_string) # verifying the signature
        if is_valid:
            return True, ""
        else:
            return False, "Signature failed verification"
    
    #except Exception as e: # failure
    #    write_to_log(" protocol / Failed to verify transaction; "+str(e))
    #    return False, "Failed to verify transaction; "+str(e)




        


    




