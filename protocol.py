import hashlib 
import shutil
import logging
import socket
from socket import socket
from hashlib import sha256
from hashlib import blake2s
import base64
import sqlite3

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
BLOCKSTOPMSG = "Stop recieving transactions"
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
                skt.send(format_data(str(tr)).encode())
            
            return True
            
        else:
            #the block id is false
            write_to_log(f" protocol / failed to send a block with index {blockid}")
            return False

def recieve_trs(skt: socket, typpe:str)-> (bool, int):
    '''
    recieves a blocks transactions
    returns true if all are saved 
    '''
    conn = sqlite3.connect(f'databases/{typpe}/blockchain.db')
    cursor = conn.cursor()

    skt.settimeout(5)
    recieving =True
    try:
        while recieving: # while loop to get all the transactions
            buffer_size = int(skt.recv(HEADER_SIZE).decode())
            transaction = skt.recv(buffer_size).decode()
            if transaction == BLOCKSTOPMSG:
                break
            cursor.execute(f'''
            INSERT INTO transactions (tr_hash, block_id, previous_tr_hash, timestamp, sender, reciever, amount, token)
            VALUES {str(transaction)}
            ''')
            conn.commit()
        
        return True
    except Exception as e:
        #handle failure
        write_to_log(f" protocol / error in saving/recieving the transactions of the block ; exception: {e}")
        return False

def recieve_block(header:str, typpe:str, skt:socket)->bool:
    '''
    saves the block header in the database
    '''
    success = True
    try:
        conn = sqlite3.connect(f'databases/{typpe}/blockchain.db')
        cursor = conn.cursor()

        head_str = ">".split(header)[1]
        cursor.execute(f'''
                INSERT INTO blocks (block_id,
                    block_hash,
                    previous_block_hash,
                    timestamp,
                    nonce)
                VALUES {head_str}
                ''')
        
        return recieve_trs(skt, typpe)
    except Exception as e:
        
        write_to_log(f" protocol / couldnt save the block header,type {typpe}; {e}")
        return False
    
    

    




class ShevahBlock:
    def __init__(self, previous_block_hash, transaction_list):
        self.previous_block_hash = previous_block_hash
        self.transaction_list = transaction_list
        self.block_data = "-" + previous_block_hash + "-".join(transaction_list)
        self.block_hash = hashlib.sha256(self.block_data.encode()).hexdigest()
    def __str__(self) -> str:
        return None
    

t1 = "Tal>1488>NC>Misha"
t2 = "Misha sent 1337 SNC to Trump"
t3 = "Biden  sent 0.1 TLC to Tal"
t4 = "Ariel sent 1 SNC to Natali"

FirstB =  ShevahBlock("1488", [t1,t2])

SecondB = ShevahBlock(FirstB.block_hash, [t3,t4])
