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
from protocol import *



def simple_verify(transmsg_full: str, conn: sqlite3.Connection):
    try:
        if not transmsg_full.startswith("(") and not transmsg_full.endswith(")"):
            return False, "Wrong transaction format"
        transaction_tuple = ast.literal_eval(transmsg_full) # str to tuple
        if not len(transaction_tuple)==9: # if wrong len
            return False, "Wrong transaction format"

        cursor = conn.cursor()

        amount_spent = transaction_tuple[6]
        token = transaction_tuple[7]
        cursor.execute(f'''
        SELECT balance, nonce FROM balances WHERE address={transaction_tuple[4]} AND token={token}
        ''')
        result = cursor.fetchone()
        balance = result[0]
        nonce = result[1]

        if result==None:
            return False, "No account with the address"
        if balance<amount_spent: # spending nonexistant money
            return False, "Your account balance is lower then the amount you are trying to spend"
        if nonce>transaction_tuple[1]:
            return False, "Wrong nonce"
        
        hexedsignature = transaction_tuple[9]
        hexedpublickey = transaction_tuple[8]

        transaction: tuple = transaction_tuple[:-2] #transaction without the scriptsig


        public_key:VerifyingKey = VerifyingKey.from_string(binascii.unhexlify(hexedpublickey),NIST256p) # extracting he key
        signature: bytes = binascii.unhexlify(hexedsignature)
    
        is_valid = public_key.verify(signature, str(transaction).encode(),sha256,sigencode=sigencode_string) # verifying the signature
    
        if is_valid:
            return True, ""
        else:
            return False, "Signature failed verification"
    
    except Exception as e: # failure
        write_to_log(" protocol / Failed to verify transaction; "+e)
        return False, "Failed to verify transaction; "+e








def verify_transaction(transmsg_full: str, conn: sqlite3.Connection, connp: sqlite3.Connection):
    '''
    takes the full transaction message with signature transaction and public key
    returns true if transaction is valid or returns false and error
    '''
    try:
        (ver, msg) = simple_verify(transmsg_full)

        if ver==False:
            return (ver, msg)
        
        cursor = conn.cursor()
        cursorp = connp.cursor()
        
        transaction_tuple = ast.literal_eval(transmsg_full)
        tr_nonce = transaction_tuple[2]
        amount_spent = transaction_tuple[6]
        token = transaction_tuple[7]

        # prove that nonce is valid to ensure no double spending
        cursorp.execute(f'''
        SELECT balance FROM balances WHERE {tr_nonce}=nonce AND address={transaction_tuple[4]} AND token={token}
        ''')
        nonce = cursorp.fetchone()
        if nonce==None: # no balance in the mempool
            cursor.execute(f'''
            SELECT balance FROM balances WHERE {tr_nonce}=nonce AND address={transaction_tuple[4]} AND token={token}
            ''')
            balance = cursor.fetchone()
            if balance==None: # if the nonce wrong
                return False , "Error, your account is not registered in the chain / wrong nonce"
            
            # inserting to the mempool, its valid
            cursor.execute(f'''
            SELECT * FROM balances WHERE address={transaction_tuple[5]} AND token={transaction_tuple[7]}
            ''')
            # get the balance from the local chain
            balances = cursorp.fetchone()
            # insert the balance of this user in this block
            cursorp.execute(f'''
            INSERT INTO balances VALUES {str(balances)}
            ''')
            return True

        else:
            cursorp.execute(f'''
            SELECT nonce, balance FROM balances WHERE address={transaction_tuple[4]} AND token={token}
            ''')
            nonce, pend_balance = cursor.fetchone()

            if pend_balance<amount_spent: # if trying to spend more then having
                return False, "Error, your account balance is lower then the amount you are trying to spend"
            
            if not nonce==transaction_tuple[1]:
                return False, "Error, your account balance is lower then the amount you are trying to spend"
            
            return True, "" # if didnt fail then verified
    
    except Exception as e: # failure
        write_to_log(" MinerBL / Failed to verify transaction; "+e)
        return False, f"Error, failed to verify transaction; {e}"

def calculate_balik_one(trans, connp:sqlite3.Connection): # update balances in the mempool
    cursorp = connp.cursor()
    try:
        trans_tuple = ast.literal_eval(trans)
        #get the before addresses for handling failure
        # trans ()
        cursorp.execute(f'''
        SELECT balance FROM balances WHERE address={trans_tuple[5]} AND token={trans_tuple[7]}
        ''')
        send_bal = cursorp.fetchone()[0]
        cursorp.execute(f'''
        SELECT balance FROM balances WHERE address={trans_tuple[4]} AND token={trans_tuple[7]}
        ''')
        recv_bal = cursorp.fetchone()[0]
        # update senders 
        cursorp.execute(f'''
        UPDATE balances SET balance = balance - {trans_tuple[6]} WHERE address={trans_tuple[4]} AND token={trans_tuple[7]}
        ''') 
        # update the recievers
        cursorp.execute(f'''
        UPDATE balances SET balance = balance + {trans_tuple[6]} WHERE address={trans_tuple[5]} AND token={trans_tuple[7]}
        ''')
        return True, trans_tuple[4] # if no errors return the sender address
    except Exception as e: # reset the addreses and return error
        cursorp.execute(f'''
        UPDATE balances SET balance = {recv_bal} WHERE address={trans_tuple[4]} AND token={trans_tuple[7]}
        ''') 
        cursorp.execute(f'''
        UPDATE balances SET balance = {send_bal} WHERE address={trans_tuple[5]} AND token={trans_tuple[7]}
        ''') 
        write_to_log(" MinerP / Failed to update balance after transaction ; "+e)
        return False, trans_tuple[4], " Error, failed to update balance after transaction ; "+e
    
def update_mined_block(conn:sqlite3.Connection, block_header:str):
    cursor = conn.cursor()
    connp = sqlite3.connect(f'databases/Miner/pending.db')
    cursorp = connp.cursor()
    # insert the header int local chain
    header_tuple = ast.literal_eval(block_header)
    # get all transactions
    cursorp.execute(f'''
    SELECT * FROM transactions WHERE block_id={header_tuple[0]}
    ''')     
    
    translist = cursorp.fetchall()
    translist = [(header_tuple[0],) + row for row in translist] # aDdiNg tHe BloCk Id xDdDD
    cursor.executemany(f"INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?)", translist) # insert the transactions into the local blockchain 
    # commit everything
    
    cursorp.execute(f'''
    DELETE FROM transactions
    ''') 
    cursorp.execute(f'''
    DELETE FROM balances
    ''') 
    conn.commit()
    conn.close()
    connp.commit()
    connp.close()





def miner_on_start(skt:socket):
    conn = sqlite3.connect(f'databases/Miner/blockchain.db')
    cursor = conn.cursor()
    connp = sqlite3.connect(f'databases/Miner/pending.db')
    cursorp = connp.cursor()

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
            block_id INT NOT NULL,
            nonce INT NOT NULL,
            timestamp DATETIME NOT NULL,
            sender VARCHAR(64) NOT NULL,
            reciever TEXT NOT NULL,
            amount REAL NOT NULL,
            token TEXT NOT NULL,
            hex_pub_key TEXT NOT NULL,
            hex_signature TEXT NOT NULL
        )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            address VARCHAR(64) NOT NULL,
            balance INT NOT NULL,
            token TEXT NOT NULL,
            nonce INT NOT NULL
        )
        ''')
    
    cursorp.execute('''
    CREATE TABLE IF NOT EXISTS balances (
        address VARCHAR(64) NOT NULL,
        balance INT NOT NULL,
        token TEXT NOT NULL,
        nonce INT NOT NULL
    )
    ''')

    cursorp.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            nonce INT NOT NULL,
            timestamp DATETIME NOT NULL,
            sender VARCHAR(64) NOT NULL,
            reciever TEXT NOT NULL,
            amount REAL NOT NULL,
            token TEXT NOT NULL,
            hex_pub_key TEXT NOT NULL,
            hex_signature TEXT NOT NULL
        )
        ''')
    


    cursor.execute('''
        SELECT block_id FROM blocks ORDER BY block_id DESC LIMIT 1
        ''')

    lastb_id= cursor.fetchone()[0] # get the last block

    #if lastb_id:
    #    skt.send(format_data(CHAINUPDATEREQUEST + f">{lastb_id}").encode())
    #    return lastb_id
    #else:
    #    skt.send(format_data(CHAINUPDATEREQUEST + f">{0}").encode())
    #    return 0


    


