import hashlib 
import shutil
import logging
import socket
from hashlib import sha256
from hashlib import blake2s
from ecdsa import ecdsa, VerifyingKey, NIST256p
from ecdsa.util import sigencode_string
import traceback
import binascii
import base64
import sqlite3
import time 
import ast
from protocol import *



NEW_USER = "New user just registered, address: "
DEFAULT_IP: str = "0.0.0.0"
DEFAULT_PORT =12222

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

DEFAULT_IP: str = "0.0.0.0"
BUFFER_SIZE: int = 1024
HEADER_SIZE = 4

def send(msg, skt: socket):
    write_to_log(" Miner / Sending message: "+msg)
    skt.send(format_data(msg).encode())

def check_address(address):

    if not address.startswith("RR") or len(address) != 38:
        return False
    
    extracted_checksum = address[-4:]  # Last 4 characters
    address_without_checksum = address[:-4]  # Everything except the last 4 characters
    

    secdhash_part = address_without_checksum[2:]  # Remove "RR" prefix
    
    secdhash_bytes = bytes.fromhex(secdhash_part)  # Convert hex to bytes
    recomputed_checksum = hashlib.sha256(secdhash_bytes).hexdigest()[:4]
    
    # Step 5: Compare the checksums
    return extracted_checksum == recomputed_checksum


def simple_verify(transmsg_full: str, conn: sqlite3.Connection):
    try:
        transaction_tuple: tuple = ast.literal_eval(transmsg_full)
        # str to tuple
        if not len(transaction_tuple)==8: # if wrong len
            return False, "Wrong transaction format"
        
        hexedpublickey = transaction_tuple[6]
        public_key:VerifyingKey = VerifyingKey.from_string(binascii.unhexlify(hexedpublickey),NIST256p) # extracting he key

        if address_from_key(public_key)!=transaction_tuple[2]:
            return False, "Address not connected to public key"
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
        
        hexedsignature = transaction_tuple[7]


        transaction: tuple = transaction_tuple[:-2] #transaction without the scriptsig
        st_transaction = str(transaction)
        
        signature: bytes = binascii.unhexlify(hexedsignature)
    
        is_valid = public_key.verify(signature, st_transaction.encode(),sha256,sigdecode=sigdecode_string) # verifying the signature
        if is_valid:
            return True, ""
        else:
            return False, "Signature failed verification"
    
    except Exception as e: # failure
        write_to_log(" protocol / Failed to verify transaction; "+e)
        return False, "Failed to verify transaction; "+e



def recieve_block(header:str,conn:sqlite3.Connection ,skt:socket)->bool:
    '''
    saves the block and the transactions in the database
    '''
    success = True
    #try:
        #create cursor
    cursor = conn.cursor()

    head_str = header # get the string version of the header data
    header_tuple  = ast.literal_eval(head_str)
    id = header_tuple[0] 
    
    # verify the block
    cursor.execute('''
        SELECT block_id, previous_block_hash FROM blocks ORDER BY block_id DESC LIMIT 1
        ''')
    res = cursor.fetchone() # get the last block

    if res == None and id!=1: # if the chain is empty and not getting the first block
        return False, "Block id is invalid", []

    if res: # if not empty
        lastb_id, prev_hash = res
        if lastb_id and id!=lastb_id+1: # check the block_id
            return False, "Block id is invalid", []
    
    head_no_hash = "(" +str(id) +", " +str(header_tuple[2:])[1:]

    if hashex(hashex(head_no_hash))!=header_tuple[1] : # check the hash or header_tuple[2]!=prev_hash
        return False, "Header hash is invalid", []

    #store it in the db
    cursor.execute(f'''
            INSERT INTO blocks 
            VALUES {head_str}
            ''')
    conn.commit()
    
    success, tr_list =  recieve_trs(skt, conn) # store the transactions of the block
    if success:
        write_to_log(f"Successfully saved the block {id} and its transactions") # log 
        return True, id, tr_list# if all saved successfully
    
    else: #if all saved unsuccessfully
        #delete all the wrong saved data
        
        cursor.execute(f''' 
        DELETE FROM blocks WHERE block_id = {id} ''')

        cursor.execute(f'''
        DELETE FROM transactions WHERE block_id = {id} ''')
        conn.commit()
        conn.close()
        return False, "Miner error", []
    
  
def recieve_trs(skt: socket, conn: sqlite3.Connection):
    '''
    recieves a blocks transactions
    returns true if all are saved 
    returns false if had errors saving
    '''
    cursor = conn.cursor()
    tr_list = []
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
                tr_list.append(transaction)

        return True, tr_list
    except Exception as e:
        #handle failure
        write_to_log(f" protocol / error in recieving the transactions of the block ; {e}")
        return False




def verify_transaction(transmsg_full: str, conn: sqlite3.Connection, connp: sqlite3.Connection):
    '''
    takes the full transaction message with signature transaction and public key
    returns true if transaction is valid or returns false and error
    '''
    try:
        (ver, msg) = simple_verify(transmsg_full, conn)

        if ver==False:
            return (ver, msg)
        
        cursor = conn.cursor()
        cursorp = connp.cursor()
        
        transaction_tuple = ast.literal_eval(transmsg_full)
        tr_nonce = transaction_tuple[0]
        amount_spent = transaction_tuple[4]
        token = transaction_tuple[5]
        cursorp.execute(f'''
        SELECT balance FROM balances WHERE nonce={tr_nonce} AND address='{transaction_tuple[3]}' AND token='{token}'
        ''')
        if cursorp.fetchone()==None: # update the recvs balance
            cursor.execute(f'''
            SELECT * FROM balances WHERE address='{transaction_tuple[3]}' AND token='{token}'
            ''')
            balances = cursor.fetchone()
            if balances==None: # if reciever not in database
                cursor.execute(f'''
                INSERT INTO balances VALUES (?, ?, ?, ?)
                ''', (transaction_tuple[3], 0, token, 1))
                conn.commit()
            
            cursorp.execute(f'''
            INSERT INTO balances VALUES (?, ?, ?, ?)
                
            ''', (transaction_tuple[3], 0, token, 1))
            connp.commit()
        
        # prove that nonce is valid to ensure no double spending
        cursorp.execute(f'''
        SELECT balance FROM balances WHERE nonce={tr_nonce} AND address='{transaction_tuple[2]}' AND token='{token}'
        ''')
        nonce = cursorp.fetchone()
        if nonce==None: # no balance in the mempool
            cursor.execute(f'''
            SELECT * FROM balances WHERE nonce={tr_nonce} AND address='{transaction_tuple[2]}' AND token='{token}'
            ''')
            balances = cursor.fetchone()
            if balances==None: # if the nonce wrong
                return False , "Error, your account is not registered in the chain / wrong nonce"
            
            # insert the balance of this user in this block
            cursorp.execute(f'''
            INSERT INTO balances VALUES {str(balances)}
            ''')
            connp.commit()
            return True, ""

        else:
            cursorp.execute(f'''
            SELECT nonce, balance FROM balances WHERE address='{transaction_tuple[2]}' AND token='{token}'
            ''')
            nonce, pend_balance = cursorp.fetchone()

            if pend_balance<amount_spent: # if trying to spend more then having
                return False, "Error, your account balance is lower then the amount you are trying to spend"
            
            if not nonce==transaction_tuple[0]:
                return False, "Error, wrong nonce"
            
            return True, "" # if didnt fail then verified
    
    except Exception as e: # failure
        write_to_log(" MinerBL / Failed to verify transaction; "+e)
        return False, f"Error, failed to verify transaction; {e}"

def calculate_balik_one(trans, connp:sqlite3.Connection): # update balances in the chain
    cursorp = connp.cursor()
    try:
        trans_tuple = ast.literal_eval(trans)
        #get the before addresses for handling failure
        # trans ()
        amount_spent = trans_tuple[5]
        token = trans_tuple[6]
        sender = trans_tuple[3]
        recv = trans_tuple[4]
        print(recv)

        cursorp.execute('''
            SELECT 1 FROM balances WHERE token = ? AND address = ?
            ''', (token, recv))

        if cursorp.fetchone()==None:
            print("No mine address")
            cursorp.execute('''
            INSERT INTO balances VALUES (?, ?, ?, ?)
            ''', (recv, 0, token, 1))
        connp.commit()
        
        # update senders balance and nonce if not miners reward
        if sender!="0"*64:
            cursorp.execute(f'''
            UPDATE balances SET balance = balance - {amount_spent} WHERE address = '{sender}' AND token = '{token}'
            ''') 
            cursorp.execute(f'''
            UPDATE balances SET nonce = nonce + 1 WHERE address = '{sender}' AND token = '{token}'
            ''') 
        # update the recievers
        cursorp.execute(f'''
        UPDATE balances SET balance = balance + {amount_spent} WHERE address = '{recv}' AND token = '{token}'
        ''')
        connp.commit()

        return True, trans_tuple[4] # if no errors return the sender address
    except Exception as e: # reset the addreses and return error

        write_to_log(f" MinerP / Failed to update balance after transaction ; {e}")
        return False, f" Error, failed to update balance after transaction ; {e}"

def calculate_balik_raw(trans, connp:sqlite3.Connection): # update balances in the mempool
    cursorp = connp.cursor()
    try:
        trans_tuple = ast.literal_eval(trans)
        #get the before addresses for handling failure
        # trans ()
        amount_spent = trans_tuple[4]
        token = trans_tuple[5]
        sender = trans_tuple[2]
        recv = trans_tuple[3]

        cursorp.execute('''
            SELECT 1 FROM balances WHERE token = ? AND address = ?
            ''', (token, recv))

        if cursorp.fetchone()==None:
            print("No mine address")
            cursorp.execute('''
            INSERT INTO balances VALUES (?, ?, ?, ?)
            ''', (recv, 0, token, 1))
        connp.commit()
        
        # update senders balance and nonce if not miners reward
        if sender!="0"*64:
            cursorp.execute(f'''
            UPDATE balances SET balance = balance - {amount_spent} WHERE address = '{sender}' AND token = '{token}'
            ''') 
            cursorp.execute(f'''
            UPDATE balances SET nonce = nonce + 1 WHERE address = '{sender}' AND token = '{token}'
            ''') 
        # update the recievers
        cursorp.execute(f'''
        UPDATE balances SET balance = balance + {amount_spent} WHERE address = '{recv}' AND token = '{token}'
        ''')
        connp.commit()

        return True, trans_tuple[4] # if no errors return the sender address
    except Exception as e: # reset the addreses and return error

        write_to_log(f" MinerP / Failed to update balance after transaction ; {e}")
        return False, f" Error, failed to update balance after transaction ; {e}"
    
def address_from_key(public_key: VerifyingKey):
    hexedpub = binascii.hexlify(public_key.to_string("compressed"))
    
    firsthash = hashlib.sha256(hexedpub).digest()
    secdhash = hashlib.blake2s(firsthash, digest_size=16)

    checksum = hashlib.sha256(secdhash.digest()).hexdigest()[:4] #grabbing the dirst 4 bytes of the address

    return "RR" + secdhash.hexdigest() + checksum

def update_mined_block(conn:sqlite3.Connection,connp:sqlite3.Connection, block_header:str):
    cursor = conn.cursor()
    cursorp = connp.cursor()
    # insert the header int local chain
    header_tuple = ast.literal_eval(block_header)


    # get all transactions
    cursor.execute(f'''
    INSERT INTO blocks VALUES {block_header}
    ''') 
    cursorp.execute(f'''
    SELECT * FROM transactions
    ''')     
    
    translist = cursorp.fetchall()
    if len(translist)==0: # if no transactions
        conn.commit()
        return 
    translist = [(header_tuple[0],) + row for row in translist] # aDdiNg tHe BloCk Id xDdDD


    cursor.executemany(f"INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?)", translist) # insert the transactions into the local blockchain 
    
    #delete all the values from the pending database
    cursorp.execute(f'''
    DELETE FROM transactions
    ''') 
    cursorp.execute(f'''
    DELETE FROM balances
    ''') 

    # commit everything
    conn.commit()
    connp.commit()

def send_mined(header: str, skt :socket, pend_conn, lastb) -> bool:
    '''
    sends a mined blocks transactions
    returns true if sent all without problems
    false if failed to send
    '''
    cursor:sqlite3.Cursor = pend_conn.cursor()
    #getting the block header
    try:
        b_id = ast.literal_eval(header)[0]

        cursor.execute(f'''
        SELECT * FROM transactions 
        ''')
        trans_list = cursor.fetchall()
        print(trans_list)

        if len(trans_list)!=0: # if valid
            for tr in trans_list: # sending all the transactions
                #tr in tuple type
                t = f"({lastb}, " + str(tr)[1:] # adding the block id to the start of all transactions
                skt.send(format_data(t).encode())
            send(BLOCKSTOPMSG, skt)

            return True, ""
            
        else:
            #the block mined has no transactions
            write_to_log(f" protocol / Sent a block with no header")
            return True, ""
        
    except Exception as e:
            write_to_log(f" protocol / Failed to send a block; {e}")
            return False, f"Failed to send a block; {e}"


def saveblockchain(msg, skt:socket, conn):
    loops = msg.split(">")[1]
    count = 0
    trans_list = []
    cursor = conn.cursor()
    try:
        while count<int(loops): # recieve multiple blocks
        
            skt.settimeout(3) # exception after 3 seconds of no answer
            (success, header) = receive_buffer(skt) # getting the header of the block
            if success:
                header = header.split(">")[1]
                (suc,  bl_id, tr_list) =  recieve_block(header, conn, skt)
                if suc==True:
                    count+=1
                    trans_list.extend(tr_list)
                else:
                    write_to_log(bl_id)
                    skt.send(format_data(FAILEDTOSAVEBLOCK).encode())
                    return False
        
        for tr in trans_list:
            trans_tuple = ast.literal_eval(tr)

            token = trans_tuple[6]
            recv = trans_tuple[4]
            cursor.execute('''
            SELECT 1 FROM balances WHERE token = ? AND address = ?
            ''', (token, recv))

            if cursor.fetchone()==None:
                print("No mine address")
                cursor.execute('''
                INSERT INTO balances VALUES (?, ?, ?, ?)
                ''', (recv, 0, token, 1))
            
            conn.commit()
            calculate_balik_one(tr, conn)
            




        return bl_id, tr_list
    except Exception as e:
        write_to_log(f" Miner / Failed to save block {bl_id} when updating chain")
        return False


def miner_on_start(skt:socket, conn, connp):
    cursor = conn.cursor()
    cursorp = connp.cursor()

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
            address VARCHAR(64) NOT NULL,
            balance REAL NOT NULL,
            token VARCHAR(12) NOT NULL,
            nonce INT NOT NULL
        )
        ''')
    
    cursorp.execute('''
    CREATE TABLE IF NOT EXISTS balances (
            address VARCHAR(64) NOT NULL,
            balance REAL NOT NULL,
            token VARCHAR(12) NOT NULL,
            nonce INT NOT NULL
    )
    ''')

    cursorp.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
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
    
    conn.commit() 
    connp.commit()

    cursorp.execute(f"SELECT 1 FROM transactions")

    if cursorp.fetchone():
        cursorp.execute(f"DELETE FROM transactions")
        connp.commit()
    
    cursor.execute('''
        SELECT block_id FROM blocks ORDER BY block_id DESC LIMIT 1
        ''')

    lastb_id= cursor.fetchone() # get the last block
    cursor.close()
    cursorp.close()
    if lastb_id:
        skt.send(format_data(CHAINUPDATEREQUEST + f">{lastb_id[0]}").encode())
        return lastb_id
    else:
        send(CHAINUPDATEREQUEST + f">{1}", skt)
        return 0


    


