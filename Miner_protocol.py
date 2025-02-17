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

def verify_transaction(transmsg_full: str):
    '''
    takes the full transaction message with signature transaction and public key
    returns true if transaction is valid or returns false and error
    '''
    try:
        conn = sqlite3.connect(f"databases/Miner/blockchain.db") # connect to db
        cursor = conn.cursor()

        connp = sqlite3.connect(f"databases/Miner/pending.db") # connect to db
        cursorp = connp.cursor()
        if not transmsg_full.startswith("(") and not transmsg_full.endswith(")"):
            return False, "Error, wrong format"
        transaction_tuple = ast.literal_eval(transmsg_full)
        # prove that nonce is valid to ensure no double spending
        cursorp.execute(f'''
        SELECT nonce FROM balances WHERE {nonce}=nonce AND address={transaction_tuple[4]} AND token={token}
        ''')
        nonce = cursorp.fetchone()
        #grabbing the balance of the sender in chain and mempool chain
        cursor.execute(f'''
        SELECT balance FROM balances WHERE address={transaction_tuple[4]} AND token={token}
        ''')
        cursorp.execute(f'''
        SELECT balance FROM balances WHERE address={transaction_tuple[4]} AND token={token}
        ''')
        balance = cursor.fetchone()[0]
        pend_balance = cursorp.fetchone()[0]
        # no updates so just close
        conn.close()
        connp.close()
        if len(nonce)==0:
            return False, "Error, wrong nonce"
        nonce = transaction_tuple[2]

        amount_spent = transaction_tuple[6]
        token = transaction_tuple[7]

        if balance<amount_spent or pend_balance<amount_spent: # if trying to spend more then having
            return False, "Error, your account balance is lower then the amount you are trying to spend"

        return True, conn, connp # if didnt fail then veified
    
    except Exception as e: # failure
        write_to_log(" MinerBL / Failed to verify transaction; "+e)
        return False, f"Error, failed to verify transaction; {e}"

def calculate_balik_one(trans, conn: sqlite3.Connection, connp:sqlite3.Connection): # update balances in the mempool
    cursor = connp.cursor()
    cursorp = conn.cursor()
    try:
        trans_tuple = ast.literal_eval(trans)
        #get the before addresses for handling failure
        # trans ()
        cursor.execute(f'''
        SELECT balance FROM balances WHERE address={trans_tuple[5]} AND token={trans_tuple[7]}
        ''')
        send_bal = cursor.fetchone()
        if len(send_bal)==0: # if no such balance in the mempool
            cursorp.execute(f'''
            SELECT balance FROM balances WHERE address={trans_tuple[5]} AND token={trans_tuple[7]}
            ''')
            # get the balance from the local chain
            send_bal = cursorp.fetchone()[0]
            # insert the balance of this user in this block
            cursor.execute(f'''
            INSERT INTO balances VALUES ({trans_tuple[4]}, {send_bal-trans_tuple[6]}, {trans_tuple[7]}, {trans_tuple[2]+1})
            ''')
        else:
            # update the senders address
            cursor.execute(f'''
            UPDATE balances SET balance = balance - {trans_tuple[6]} WHERE address={trans_tuple[4]} AND token={trans_tuple[7]}
            ''') 
        cursor.execute(f'''
        SELECT balance FROM balances WHERE address={trans_tuple[4]} AND token={trans_tuple[7]}
        ''')
        recv_bal = cursor.fetchone()[0] 
        if len(recv_bal)==0: # if no such balance in the mempool
            cursorp.execute(f'''
            SELECT balance FROM balances WHERE address={trans_tuple[5]} AND token={trans_tuple[7]}
            ''')
            # get the balance from the local chain
            recv_bal = cursorp.fetchone()[0]
            # insert the balance of this user in this block
            cursor.execute(f'''
            INSERT INTO balances VALUES ({trans_tuple[4]}, {send_bal-trans_tuple[6]})
            ''')
        else:
        # update the recievers address if already in the mempool
            cursor.execute(f'''
            UPDATE balances SET balance = balance + {trans_tuple[6]} WHERE address={trans_tuple[5]} AND token={trans_tuple[7]}
            ''')


        conn.commit()
        conn.close() 
        return True # if no errors
    except Exception as e: # reset the addreses and return error
        cursor.execute(f'''
        UPDATE balances SET balance = {recv_bal} WHERE address={trans_tuple[4]} AND token={trans_tuple[7]}
        ''') 
        cursor.execute(f'''
        UPDATE balances SET balance = {send_bal} WHERE address={trans_tuple[5]} AND token={trans_tuple[7]}
        ''') 
        conn.commit()
        conn.close()
        write_to_log(" MinerP / Failed to update balance after transaction ; "+e)
        return False, " MinerP / Failed to update balance after transaction ; "+e
    
def update_mined_block(conn:sqlite3.Connection, block_header:str):
    cursor = conn.cursor()
    connp = sqlite3.connect(f'databases/Miner/pending.db')
    cursorp = connp.cursor()

    cursor.execute(f'''
    SELECT * FROM blocks ORDER BY block_id DESC LIMIT 1
    ''')     

    block_header = cursor.fetchone()[0]
    # insert the header int local chain
    header_tuple = ast.literal_eval(block_header)
    # get all transactions
    cursorp.execute(f'''
    SELECT * FROM transactions WHERE block_id={header_tuple[0]}
    ''')     

    translist = cursorp.fetchall()
    cursor.executemany(f"INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?)", translist) # insert the transactions into the local blockchain 
    # commit everything
    
    cursorp.execute(f'''
    DELETE FROM transactions
    ''') 
    conn.commit()
    conn.close()
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
            tr_hash VARCHAR(64) NOT NULL,
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
            uId INT NOT NULL,
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
            tr_hash VARCHAR(64) NOT NULL,
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

    if lastb_id:
        skt.send(format_data(CHAINUPDATEREQUEST + f">{lastb_id}").encode())
        return lastb_id
    else:
        skt.send(format_data(CHAINUPDATEREQUEST + f">{0}").encode())
        return 0


    


