from protocol import *
import socket
import sqlite3

def send_block(blockid: int, skt :socket, conn:sqlite3.Connection) -> bool:
    '''
    sends a block with a specific index to a socket
    returns true if sent all without problems
    false if failed to retrieve from the tables
    '''
    
    cursor = conn.cursor()
    #getting the block header
    cursor.execute(f'''
            SELECT * FROM blocks WHERE block_id = {blockid}
            ''')
    
    block_header = cursor.fetchone()[0] # retrieve the block header to send first
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

def send_mined(skt :socket):
    '''
    sends a mined block 
    returns true if sent all without problems
    false if failed to retrieve from the tables
    '''
    conn = sqlite3.connect(f"databases/Node/blockchain.db")
    cursor = conn.cursor()
    #getting the block header
    cursor.execute(f'''
            SELECT * FROM blocks ORDER BY block_id DESC LIMIT 1
            ''')
    
    block_header = cursor.fetchone()[0] # retrieve the block header to send first
    block_id = ast.literal_eval(block_header)[0]
    if block_header: # if valid
        # getting the transaction list
        cursor.execute(f'''
        SELECT * FROM transactions WHERE block_id = {block_id}
                    ''')
        # sending all the transactions
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
            write_to_log(f" protocol / failed to send a block with index {block_id}")
            return False    