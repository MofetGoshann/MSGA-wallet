from protocol import *
from Miner_protocol import *
import socket
import ecdsa
from ecdsa import SigningKey, NIST256p
from ecdsa.util import sigencode_string
from hashlib import sha256
from datetime import datetime
import threading
import binascii
import json
import os
import ast

class Block:

    def __init__(self, previous_block_hash, transaction_list, id: int):
        self.previous_block_hash = previous_block_hash
        self.transaction_list = transaction_list
        self.__nonce = 0
        self.block_data =  previous_block_hash +"-"+ datetime.datetime.now() + "-" + self.__nonce
        self.block_hash = hashlib.sha256(self.block_data.encode()).hexdigest()
        self.__block_id = id
    
    def gethash(self):
        return self.block_hash
    def getdata(self):
        return self.block_data
    
    def getid(s):
        return s.__block_id
    
    def mine(s):
        pass    


    




class Miner:




    def __init__(self, ip:str, port: int, username:str):
    
        self._socket_obj: socket = None
        self.__recieved_message = None 
        self.__user = username
        self.__lastb = None
        self.__mining = False
        self.__diff = 0
        self.__connected = False
        self.__connect()
        
    
    def __connect(self, ip:str, port:int):
        #connect the miner to the hub/server

        try:
            # Create and connect socket to the hub
            self._socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket_obj.connect((ip, port))

            
            # let the hub know im a miner and give the block id to update
            self._socket_obj.send(format_data(self.__user + ">2").encode())
            self.__lastb = chain_on_start("Miner", self._socket_obj)
            #always recieve data from server to know if kicked
            self.__always_recieve()
            # Log the data
            write_to_log(f" 路 Miner 路 {self._socket_obj.getsockname()} connected")

            # Return on success
            return True

        except Exception as e:

            # Handle failure
            self._socket_obj = None
            write_to_log(f" 路 Miner 路 failed to connect miner; ex:{e}")

            self._last_error = f"An error occurred in miner bl [connect function]\nError : {e}"

            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect the client from server
        :return: True / False on success
        """

        try:
            # Start the disconnect process
            write_to_log(f" 路 Client 路 {self._socket_obj.getsockname()} closing")

            # Alert the server we're closing this miner
            self.send_data(DISCONNECT_MSG)

            self._recvfunc("Disconnected.")
            # Close miner socket
            self._socket_obj.close()

            write_to_log(f" 路 Client 路 the client closed")

            self._socket_obj = None

            # Return on success
            return True

        except Exception as e:

            # Handle failure
            write_to_log(f" 路 Client 路 failed to disconnect : {e}")
            self._last_error = f"An error occurred in client bl [disconnect function]\nError : {e}"

            return False
    

        
        
    
    def __always_recieve(self, *args):
        """setup a thread to always recieve messages"""
        try:
            listening_thread = threading.Thread(target=self.__always_listen, args=())
            listening_thread.start()
        except Exception as e:
            self._last_error = f"Error in client bl [always recieve function]\nError : {e}"
            write_to_log(f" 路 Client 路 always recieve thread not working; {e}")
    
    
        
    def __receive_data(self):
        try:
            success, message = receive_buffer(self._socket_obj)
            if not success:
                self._last_error = "didn`t recieve a message"
                return ""
            return message
        except Exception as e:

            # Handle failure
            write_to_log(f" Miner / failed to receive from server : {e}")
            self._last_error = f"An error occurred in miner bl [receive_data function]\nError : {e}"
            return ""
            
            
    
    def __always_listen(self):
        """always recieve messages from server primarily to get kick message"""

        self.__connected = True
        while connected:
            self._socket_obj.settimeout(3) # set a timeout for recievedata

            self.__recieved_message = self.__receive_data() # update 
                
            """
            if self.__recieved_message and self.__recieved_message.startswith(REG_MSG):

                key = self.__recieved_message[REG_MSG.__len__():]

                if key:
                    with open("ClientBLregkeys.txt", 'a') as file: # save the key in a textfile
                        file.write(key + "\n")

                    self._recvfunc(REG_MSG) #insert the message into the gui
                else:
                    write_to_log(" 路 Client 路 Failed to save to text file, key not identified")

            else: 
            #    self._recvfunc(self.__recieved_message) #insert the message into the gui
            """

            if self.__recieved_message==KICK_MSG:
                discsuccess = self.disconnect() # disconnect the client from server
                
                if discsuccess: # confirm diconnect
                    write_to_log(f" 路 Client 路 You have been been kicked")

                else: # if doesnt diconnect
                    self._last_error = f"Error in client bl [always_listen function], failed to diconnect client when kicked by server"
                    write_to_log(f" 路 Client 路 Failed to diconnect the client when kicked by server")

                connected = False # close loop
            
            if self.__recieved_message.startswith(MINEDBLOCKSENDMSG):
                msg_list = self.__recieved_message.split(">")
                header = msg_list[1]
                diff =msg_list[2]
                (suc,  msg) =  recieve_block(header, "Miner", self._socket_obj)
                if suc:
                    self.__lastb =+1
                    self.__mining = False
                    listening_thread = threading.Thread(target=self.start_mining(), args=(diff,))
                    listening_thread.start()
                else:
                    self._socket_obj.send((format_data(msg).encode()))
                

                
                
            if self.__recieved_message.startswith(CHAINUPDATING):
                result = saveblockchain(self.__recieved_message, "Miner", self._socket_obj)
                if not result==False:
                    self.__lastb = result

            if self.__recieved_message.startswith(TRANS):
                transaction = self.__recieved_message.split(">")[1]
                success = verify_transaction(self.__recieved_message) # verify the transaction
                
                if success==True:
                    self.__operate_transaction(transaction)
                    
                    
                else:
                    # handle if faulted transaction
                    self._socket_obj.send(format_data(BAD_TRANS_MSG).encode())
    

    def _send_block(s):
        send_block(1, s._socket_obj, "Miner")

    def build_merkle_tree(s):
        conn = sqlite3.connect(f'databases/Miner/pending.db')
        cursor = conn.cursor()
        cursor.execute(f'''
                        SELECT tr_hash FROM transactions ORDER BY block_id DESC LIMIT 1
                    ''')      
        hashes = cursor.fetchall()
        conn.close()
        # Base case: If no transactions are provided, return None
        if len(hashes)==0:
            return hashex("0"*64)
        # If only one transaction, the Merkle Root is its hash
        if len(hashes) == 1:
            return hashes[0]
        try:
        # Hash all transactions

        # Build the tree until there is only one hash (the root)
            while len(hashes) > 1:
                # If the number of hashes is odd, duplicate the last hash
                if len(hashes) % 2 == 1:
                    hashes.append(hashes[-1])

                # Pairwise combine and hash
                temp_hashes = []
                for i in range(0, len(hashes), 2):
                    combined = hashes[i] + hashes[i + 1]
                    temp_hashes.append(hashex(combined))

                hashes = temp_hashes  # Move up to the next level
        except Exception as e:
            write_to_log(" MinerBL / Failed to build a merkle tree ; "+e)
            s._last_error = "Problem in BL, failed to build a merkle tree" + e
        # The final hash is the Merkle Root
        return hashes[0]
    
    def __operate_transaction(s, trans):
        conn = sqlite3.connect(f'databases/Miner/pending.db')
        cursor = conn.cursor()
        try:
            success, msg = verify_transaction(trans) # verify transaction
            if not success:
                return False, msg

            success, msgg = calculate_balik_one(trans, msg[1], msg[2]) # update the balance
            if not success:
                return False, msgg
            #include transaction in mempool
            cursor.execute(f'''
                    INSERT INTO transactions VALUES {trans}
                ''')
            return True
        except Exception as e:
            write_to_log(f" Miner / Problem with including the transactions into pending table; {e}")
            
            
    def __start_mining(s):
        conn2 = sqlite3.connect(f'databases/Miner/blockchain.db')
        chaincursor = conn2.cursor()
        
        try:

            # chaincursor.executemany(f"INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?)", translist) # insert the transactions into the local blockchain 
            diff = s.__diff
            merkle_root = s.build_merkle_tree() # build the root

            chaincursor.execute(f'''
            SELECT block_hash from blocks WHERE block_id={s.__lastb}
            ''')
            p_hash = chaincursor.fetchone() # previous hash of the nest block is the current hash

            s.__mining = True
            nonce = 0
            start_time = time.time()
            while mining:
                if nonce%100000==0: # every 100000 calculations update the time
                    timestamp = datetime.now().strftime(f"%d.%m.%Y %H:%M:%S")
                    strheader = f"({s.__lastb+1}, {p_hash}, {merkle_root}, {timestamp}, {diff}, "
                
                header = strheader + str(nonce)+ ")" # header with no hash

                hash = hashex(hashex(header)) # sha256 *2 the header with the nonce

                if hash.startswith(diff*"0"): # if the hash is good mine the block
                    mining=False
                    full_block_header = f"({s.__lastb+1}, {hash}, {p_hash}, {merkle_root}, {timestamp}, {diff}, {nonce})"
                    mine_time = time.time() - start_time
                    chaincursor.execute(f'''
                    INSERT INTO blocks VALUES {full_block_header}
                    ''')
                    conn2.commit()
                    return conn2, full_block_header, mine_time # return the header with the hash

                else:
                    nonce+=1 # increase the nonce
            conn2.close()
            return False
        except Exception as e: # failure handling
            write_to_log(f" MinerBL / Failed to mine block {s.__lastb+1}")
            s._last_error = "Failed to mine block {s.__lastb+1}"
            conn2.close()
            return False
    
    def _always_mine(s):
        while s.__connected:
            result = s.__start_mining(s) # full header
            if result ==False:
                return
            # mined successfully

            update_mined_block(result) # update the transactions in local chain
            s._socket_obj.send(format_data(MINEDBLOCKSENDMSG +">"+result[1]+">"+result[2]).encode())
            
            
            
            
            


    








        




        
        
    
                        
                
                
    
    
        
    
    
            
    
        
        
        

    

