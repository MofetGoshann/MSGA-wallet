from protocol import *
import socket
import sqlite3
import traceback




NEW_USER = "New user just registered, address: "
DEFAULT_IP: str = "0.0.0.0"
DEFAULT_PORT = 12222

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
        return False, ""    
    

def send_block(blockid, skt :socket, conn:sqlite3.Connection) -> bool:
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
    
    block_header = cursor.fetchone() # retrieve the block header to send first

    if block_header: # if valid
        # getting the transaction list

        cursor.execute(f'''
        SELECT * FROM transactions WHERE block_id = {blockid}
                    ''')
        
        trans_list = cursor.fetchall()
        
        send(BLOCKSENDMSG+">"+str(block_header), skt) # sending the starter 
        if trans_list: # if block has transactions
            
            for tr in trans_list: # sending all the transactions
                #tr in tuple type
                t= str(tr)
                send(t ,skt)

        cursor.close()
        send(BLOCKSTOPMSG, skt)
        return True
        
def send_to_miner(starter:str, diff:int,skt :socket.socket, conn:sqlite3.Connection):
    '''
    sends a block with a specific index to a socket but without sending the header
    returns true if sent all without problems
    false if failed to retrieve from the tables
    '''
    
    cursor = conn.cursor()
    
    st_tuple = starter.split(">")
    block_header = st_tuple[1]
    # getting the transaction list
    cursor.execute(f'''
    SELECT * FROM transactions WHERE block_id = {block_header[1]}
                ''')
    
    trans_list = cursor.fetchall()
    if trans_list: # if valid
        send(MINEDBLOCKSENDMSG+">" +block_header + ">" + str(diff), skt) # sending the starter
        for tr in trans_list: # sending all the transactions
            #tr in tuple type
            t= str(tr)
            send(t,skt)
        send(BLOCKSTOPMSG, skt)
        cursor.close()
        return True
        
    else:
        #the block id is false
        write_to_log(f" protocol / failed to send a block with index {block_header[1]}")
        return False

def send(msg, skt: socket):
    write_to_log(" Node / Sending message: "+msg)
    skt.send(format_data(msg).encode())





    

def recieve_block(header:str ,skt:socket)->bool:
    '''
    saves the block and the transactions in the database
    '''
    success = True
    try:
        conn = sqlite3.connect('databases/Node/blockchain.db')

        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        
        head_str = header # get the string version of the header data
        header_tuple  = ast.literal_eval(head_str)
        id = header_tuple[0] 

        # verify the block
        cursor.execute('''
            SELECT block_id, block_hash FROM blocks ORDER BY block_id DESC LIMIT 1
            ''')
        c = cursor.fetchone()
        if c:
            lastb_id, prev_hash = c # get the last block
        
            if id!=lastb_id+1: # check the block_id
                send(format_data("Block id is invalid").encode(), skt)
                return False, "Block id is invalid"
            
            if  header_tuple[2]!=prev_hash:
                send(format_data("Block hash is invalid").encode(), skt)
                return False, "Block hash is invalid"
            
        head_no_hash = "(" +str(id) +", " +str(header_tuple[2:])[1:]

        if hashex(hashex(head_no_hash))!=header_tuple[1]: # check the hash
            send(format_data("Header hash is invalid").encode(), skt)
            return False, "Header hash is invalid"
        
        
        #store it in the db
        cursor.execute(f'''
                INSERT INTO blocks 
                VALUES {head_str}
                ''')
        conn.commit()

        
        success =  recieve_trs(skt, conn) # store the transactions of the block
        if success:
            write_to_log(f"Successfully saved the block {id} and its transactions") # log 
            conn.close()
            return True, id # if all saved successfully
        
        else: #if all saved unsuccessfully
            #delete all the wrong saved data
            cursor.execute(f''' 
            DELETE FROM blocks WHERE block_id = {id} ''')

            cursor.execute(f'''
            DELETE FROM transactions WHERE block_id = {id} ''')
            conn.commit()
            conn.close()
            return False, "did not save the transactions"
        
    except Exception as e:
        if str(e).startswith("UNIQUE constraint"): # if recieving a saved block
            send(format_data("Already have the block").encode(), skt)
        #log the exception
        write_to_log(f" protocol / couldnt save the block header; {e}")
        traceback.print_exc()
        return False, ""
  
def recieve_trs(skt: socket, conn: sqlite3.Connection):
    '''
    recieves a blocks transactions
    returns true if all are saved 
    returns false if had errors saving
    '''
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
        write_to_log(f" NodeP / Error in saving/recieving the transactions of the block ; {e}")
        return False

def verify_transaction(transmsg_full: str, conn):
    try:
        transaction_tuple: tuple = ast.literal_eval(transmsg_full)
        # str to tuple
        if not len(transaction_tuple)==8: # if wrong len
            return False, "Wrong transaction format"
        

        cursor = conn.cursor()
        amount_spent = float(transaction_tuple[4])
        token = transaction_tuple[5]
        cursor.execute(f'''
        SELECT balance, nonce FROM balances WHERE address='{transaction_tuple[2]}' AND token='{token}'
        ''')
        result = cursor.fetchone()
        
        cursor.close()
        conn.commit()
        if result==None:
            return False, "No account with the address"
        balance = float(result[0])
        nonce = result[1]
        if balance<amount_spent: # spending nonexistant money
            return False, "Your account balance is lower then the amount you are trying to spend"
        if nonce>int(transaction_tuple[0]):
            return False, "Wrong nonce"
        
        hexedsignature = transaction_tuple[7]
        hexedpublickey = transaction_tuple[6]

        transaction: tuple = transaction_tuple[:-2] #transaction without the scriptsig
        st_transaction = str(transaction)
        public_key:VerifyingKey = VerifyingKey.from_string(binascii.unhexlify(hexedpublickey),NIST256p) # extracting he key
        signature: bytes = binascii.unhexlify(hexedsignature)

        if transaction_tuple[2]!=address_from_key(public_key):
            return False, "Address not connected to public key"


        is_valid = public_key.verify(signature, st_transaction.encode(),sha256,sigdecode=sigdecode_string) # verifying the signature
        if is_valid:
            return True, ""
        else:
            return False, "Signature failed verification"
    
    except Exception as e: # failure
        write_to_log(" protocol / Failed to verify transaction; "+str(e))
        return False, "Failed to verify transaction; "+str(e)