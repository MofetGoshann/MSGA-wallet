import hashlib 
import shutil
import logging
import socket
from hashlib import sha256
from hashlib import blake2s
from ecdsa import ecdsa, VerifyingKey, NIST256p
from ecdsa.util import sigencode_string, sigdecode_string
import binascii
import base64
import sqlite3
import time 
import ast
from protocol import *










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
            skt.send(format_data("Block id is invalid").encode())
            return False
        head_no_hash = "(" +id +str(header_tuple[2:])[1:]
        if hashex(head_no_hash)!=header_tuple[1] and header_tuple[2]!=prev_hash: # check the hash
            skt.send(format_data("Header hash is invalid").encode())
            return False
        
        
        #store it in the db
        cursor.execute(f'''
                INSERT INTO blocks 
                VALUES {head_str}
                ''')
        conn.commit()

        success =  recieve_trs(skt, typpe, conn) # store the transactions of the block
        if success:
            skt.send(format_data(SAVEDBLOCK).encode())
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
            skt.send(format_data("Already have the block").encode())
        #log the exception
        write_to_log(f" protocol / couldnt save the block header,type {typpe}; {e}")
        return False