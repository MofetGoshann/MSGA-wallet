import hashlib 
import socket
from hashlib import sha256
from hashlib import blake2s
from ecdsa import ecdsa, VerifyingKey, NIST256p, SigningKey
from ecdsa.util import sigencode_string, sigdecode_string
import os
import binascii
import base64
import sqlite3
import bip39
import ast
from protocol import *
import traceback
import PyQt5
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QMessageBox, QGridLayout, QSpacerItem, QSizePolicy, QToolTip, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QGraphicsDropShadowEffect, QScrollArea
from PyQt5.QtGui import QPixmap, QIcon, QImage, QPainter, QPen, QColor, QBrush, QCursor, QMouseEvent
from PyQt5.QtCore import Qt, QSize, QPoint, QRect, QTimer, QObject, pyqtSignal, pyqtSlot, QPropertyAnimation
import time


NEW_USER = "New user just registered, address: "
DEFAULT_IP: str = "0.0.0.0"
DEFAULT_PORT =12222
tm_format = "%Y-%m-%d %H:%M:%S"

def send(msg, skt: socket):
    write_to_log(" Client / Sending message: "+msg)
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

def is_valid_amount(amount_str):
    try:
        float(amount_str)
        return float(amount_str) > 0  # Also checks positive value
    except ValueError:
        return False

def address_from_key(public_key: VerifyingKey):
    hexedpub = binascii.hexlify(public_key.to_string("compressed"))
    
    firsthash = hashlib.sha256(hexedpub).digest()
    secdhash = hashlib.blake2s(firsthash, digest_size=16)

    checksum = hashlib.sha256(secdhash.digest()).hexdigest()[:4] #grabbing the dirst 4 bytes of the address

    return "RR" + secdhash.hexdigest() + checksum

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

def send_block(blockid: int, skt :socket) -> bool:
    '''
    sends a block with a specific index to a socket
    returns true if sent all without problems
    false if failed to retrieve from the tables
    '''
    

    conn = sqlite3.connect(f"databases/Client/blockchain.db") # client/node/miner
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
            write_to_log(f" ClientP / failed to send a block with index {blockid}")
            return False

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
        write_to_log(f" ClientP / Error in recieving the transactions of the block ; {e}")
        return False

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
        return False, "Client error", []

def add_his(tr_list, address):
    my_tr_list = []
    for tr in tr_list:
        trans_tuple = ast.literal_eval(tr)

        token = str(trans_tuple[6])
        recv = str(trans_tuple[4])
        sender = str(trans_tuple[3])
        time = str(trans_tuple[2])
        amount = str(trans_tuple[5])

        if sender==address or recv==address:
            my_tr_list.append([time, sender, recv, token, amount])
    
    return my_tr_list

def add_hiss(tr_list):
    my_tr_list = []
    for tr in tr_list:
        trans_tuple = ast.literal_eval(tr)

        token = str(trans_tuple[6])
        recv = str(trans_tuple[4])
        sender = str(trans_tuple[3])
        time = str(trans_tuple[2])
        amount = str(trans_tuple[5])


        my_tr_list.append([time, sender, recv, token, amount])
    
    return my_tr_list


def saveblockchain(msg, skt:socket, conn, address):
    loops = msg.split(">")[1]
    count = 0
    trans_list = []
    my_tr_list = [[]]
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

            token = str(trans_tuple[6])
            recv = str(trans_tuple[4])
            sender = str(trans_tuple[3])
            time = str(trans_tuple[2])
            amount = str(trans_tuple[5])
            cursor.execute('''
            SELECT 1 FROM balances WHERE token = ? AND address = ?
            ''', (token, recv))

            if cursor.fetchone()==None:
                cursor.execute('''
                INSERT INTO balances VALUES (?, ?, ?, ?)
                ''', (recv, 0, token, 1))
            
            conn.commit()
            calculate_balik_one(tr, conn)

            if sender==address or recv==address:
                my_tr_list.append([time, sender, recv, token, amount])


        return bl_id, my_tr_list
    except Exception as e:
        write_to_log(f" Miner / Failed to save block {bl_id} when updating chain")
        return False


def calculate_balik_one(trans, connp:sqlite3.Connection): # update balances in the mempool
    cursorp = connp.cursor()
    try:
        trans_tuple = ast.literal_eval(trans)
        #get the before addresses for handling failure
        # trans ()
        amount_spent = trans_tuple[5]
        token = trans_tuple[6]
        sender = trans_tuple[3]
        recv = trans_tuple[4]

        cursorp.execute('''
            SELECT 1 FROM balances WHERE token = ? AND address = ?
            ''', (token, recv))

        if cursorp.fetchone()==None:

            cursorp.execute('''
            INSERT INTO balances VALUES (?, ?, ?, ?)
            ''', (recv, 0, token, 1))
        connp.commit()
        
        # update senders if not miners reward
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

        write_to_log(f" ClientP / Failed to update balance after transaction ; {e}")
        return False, f" Error, failed to update balance after transaction ; {e}"


    



