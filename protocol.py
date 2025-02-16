import hashlib 
import shutil
import logging
import socket
from hashlib import sha256
from hashlib import blake2s
from ecdsa import ecdsa, VerifyingKey, NIST256p
from ecdsa.util import sigencode_string
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

def receive_buffer(my_socket: socket) -> (bool, str):
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
    



def address_from_key(public_key:bytes):
    firsthash = hashlib.sha256(public_key).digest()
    secdhash = hashlib.blake2s(firsthash).digest()

    checksum = hashlib.sha256(secdhash).digest()[:4] #grabbing the dirst 4 bytes of the address

    full_address = "RR".encode() + base64.b32encode(secdhash) + checksum


def check_address(address:bytes):
    pass


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
            skt.send(format_data(BLOCKSENDMSG+">"+str(block_header)).encode()) # sending the starter
            for tr in trans_list: # sending all the transactions
                #tr in tuple type
                t= str(tr)
                skt.send(format_data(t).encode())
            skt.send(format_data(BLOCKSTOPMSG).encode())

            return True
            
        else:
            #the block id is false
            write_to_log(f" protocol / failed to send a block with index {blockid}")
            return False

def recieve_trs(skt: socket, typpe:str)-> (bool, int):
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
        write_to_log(f" protocol / error in saving/recieving the transactions of the block ; exception: {e}")
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
        #lil verification
        header_tuple = ast.literal_eval(head_str)
        cursor.execute('''
            SELECT block_id FROM blocks ORDER BY block_id DESC LIMIT 1
            ''')
        lastb_id= cursor.fetchone()[0] # get the last block

        if header_tuple[0]!=lastb_id+1:
            skt.send(format_data("Block id is invalid").encode())
            return False
        head_no_hash = "(" +header_tuple[0] +str(header_tuple[2:])
        if hashex(head_no_hash)!=header_tuple[1]:
            skt.send(format_data("Header hash is invalid").encode())
            return False
        #store it in the db
        cursor.execute(f'''
                INSERT INTO blocks 
                VALUES {head_str}
                ''')
        conn.commit()

        id = head_str[0] 
        success =  recieve_trs(skt, typpe) # store the transactions of the block
        if success:
            skt.send(format_data(SAVEDBLOCK + str(id)).encode())
            write_to_log(f"Successfully saved the block {id} and its transactions") # log 
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
            skt.send(format_data("Already have the block").encode())
        #log the exception
        write_to_log(f" protocol / couldnt save the block header,type {typpe}; {e}")
        return False
    
def saveblockchain(msg, typpe:str, skt:socket):
    loops = msg.split(">")[1]
    count = 0
    try:
        while count<loops: # recieve multiple blocks
        
            skt.settimeout(3) # exception after 3 seconds of no answer
            (success, header) = receive_buffer(skt) # getting the header of the block
            if success:
                header = header.split(">")[1]
                (suc,  bl_id) =  recieve_block(header, typpe, skt)
                if suc:
                    skt.send(format_data(SAVEDBLOCK+f"{bl_id}").encode())
                    count+=1
                    
                else:
                    skt.send(format_data(FAILEDTOSAVEBLOCK).encode())
                    break
    except Exception as e:
        write_to_log(f" Miner / Failed to save block {bl_id} when updating chain")



def chain_on_start(type: str, skt:socket):
    try:
        conn = sqlite3.connect(f'databases/{type}/blockchain.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                block_id INT PRIMARY KEY NOT NULL,
                block_hash VARCHAR(64) NOT NULL,
                previous_block_hash VARCHAR(64),
                merkle_root VARCHAR(64) NOT NULL
                timestamp DATETIME NOT NULL,
                difficulty INT NOT NULL,
                nonce INT NOT NULL
            )
            ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                tr_hash VARCHAR(64) NOT NULL,
                block_id INT NOT NULL,
                nonce INT NOT NULL,
                timestamp DATETIME NOT NULL,
                sender VARCHAR(64) NOT NULL,
                reciever VARCHAR(64) NOT NULL,
                amount REAL NOT NULL,
                token TEXT NOT NULL,
                hex_pub_key TEXT NOT NULL,
                hex_signature TEXT NOT NULL
            )
            ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balances (
                uId INT NOT NULL
                address VARCHAR(64) NOT NULL,
                balance INT NOT NULL,
                token TEXT NOT NULL,
                nonce INT NOT NULL
            )
            ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                uId INT NOT NULL,
                address VARCHAR(64) NOT NULL,
                username TEXT NOT NULL,
                pass TEXT NOT NULL
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
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def verify_transaction(transmsg_full: str, typpe:str): # verify of node

    try:
        if not transmsg_full.startswith("(") and not transmsg_full.endswith(")"):
            return False, "Wrong transaction format"
        transaction_tuple = ast.literal_eval(transmsg_full) # str to tuple
        if not len(transaction_tuple)==9: # if wrong len
            return False, "Wrong transaction format"
        
        conn = sqlite3.connect(f"databases/{typpe}/blockchain.db") # client/node/miner
        cursor = conn.cursor()

        amount_spent = transaction_tuple[6]
        token = transaction_tuple[7]
        cursor.execute(f'''
        SELECT balance FROM balances WHERE address={transaction_tuple[4]} AND token={token}
        ''')
        balance = cursor.fetchone()[0]
        cursor.close()
        if not balance:
            return False, "No account with the address"
        if balance<amount_spent: # spending nonexistant money
            return False, "Your account balance is lower then the amount you are trying to spend"
        
        hexedsignature = transaction_tuple[9]
        hexedpublickey = transaction_tuple[8]

        transaction: tuple = transaction_tuple[:-2] #transaction without the scriptsig

        public_key:VerifyingKey = VerifyingKey.from_string(binascii.unhexlify(hexedpublickey),NIST256p) # extracting he key
        signature: bytes = binascii.unhexlify(hexedsignature)
    
        is_valid = public_key.verify(signature, str(transaction).encode(),sha256,sigencode=sigencode_string) # verifying the signature
    
        if is_valid:
            return True
        else:
            return False, "Signature failed verification"
    
    except Exception as e: # failure
        write_to_log(" protocol / Failed to verify transaction; "+e)
        return False, "Failed to verify transaction; "+e


        


    




