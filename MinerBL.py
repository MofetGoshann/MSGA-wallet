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
import traceback

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


tm_format = "%d.%m.%Y %H:%M:%S"




class Miner:




    def __init__(self, ip:str, port: int, username:str):
    
        self._socket_obj: socket = None
        self.__recieved_message = ""
        self.__user = username
        self.__lastb = None
        self.__mining = False
        self.__diff = 0
        self.__connected = False
        self._conn = sqlite3.connect(f'databases/Miner/blockchain.db')
        self._pend_conn  = sqlite3.connect(f'databases/Miner/pending.db')
        suc = self.__connect(ip, port)
        
    
    def __connect(self, ip:str, port:int):
        #connect the miner to the hub/server

        try:
            # Create and connect socket to the hub
            self._socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket_obj.connect((ip, port))

            
            # let the hub know im a miner and give the block id to update
            self._socket_obj.send(format_data(self.__user + ">2").encode())
            #always recieve data from server to know if kicked
            self.__always_recieve()
            self.__lastb = miner_on_start(self._socket_obj, self._conn, self._pend_conn)

            #stalling until chain is updated
            start_time = time.time()
            stall_time = time.time() - start_time
            while(stall_time<3 and self.__recieved_message.startswith("UPDATED")==False):
                time.sleep(0.1)
                stall_time = time.time() - start_time
            if stall_time>3:
                write_to_log(" Miner / Timed out on chainupdate")
                self.disconnect()
                return False
            self.__lastb = self.__recieved_message.split(">")[1]
            print("gutt")

        
            listening_thread = threading.Thread(target=self._always_mine(), args=())
            listening_thread.start()
            
            # Log the data
            write_to_log(f" 路 Miner 路 {self._socket_obj.getsockname()} connected")

            # Return on success
            return True

        except Exception as e:

            # Handle failure
            self._socket_obj = None
            write_to_log(f" 路 Miner 路 failed to connect miner; ex:{e}")
            traceback.print_exc()
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
            self._socket_obj.send(format_data(DISCONNECT_MSG).encode())
            self.__connected= False
            #self._recvfunc("Disconnected.")
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
        conn = sqlite3.connect(f'databases/Miner/blockchain.db')
        self.__connected = True

        while self.__connected:
            self._socket_obj.settimeout(3) # set a timeout for recievedata

            self.__recieved_message = self.__receive_data() # update 
            
            msg = self.__recieved_message

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

            if msg==KICK_MSG:
                discsuccess = self.disconnect() # disconnect the client from server
                
                if discsuccess: # confirm diconnect
                    write_to_log(f" 路 Client 路 You have been been kicked")

                else: # if doesnt diconnect
                    self._last_error = f"Error in client bl [always_listen function], failed to diconnect client when kicked by server"
                    write_to_log(f" 路 Client 路 Failed to diconnect the client when kicked by server")

                connected = False # close loop
            
            if msg.startswith(MINEDBLOCKSENDMSG): # if got a mined block

                msg_list = self.__recieved_message.split(">")
                header = msg_list[1]
                self.__diff =msg_list[2]
                (suc,  msg) =  recieve_block(header, conn, self._socket_obj)
                if suc:
 
                    self.__lastb =+1
                    self.__mining = False
                    self.update_balances(conn)
                else:
                    self._socket_obj.send((format_data(msg).encode()))
                
            if msg.startswith(CHAINUPDATING): # if updating the local chain
                print("dsfsdf")
                result = saveblockchain(msg, self._socket_obj, conn)
                if result!=False:
                    self.__lastb = result
                    print("gutttt")
                
                else:
                    self._last_error = "Cannot connect to blockchain"
                    print("nono")
                    self.disconnect()

            if msg.startswith(TRANS): # if got a transaction from a client
                print("miner got trans")
                transplit = self.__recieved_message.split("|")
                transaction = transplit[1]
                res, ermsg = self.__operate_transaction(transaction, conn)
                
                if res==True: # if transaction good
                    self._socket_obj.send(format_data(GOOD_TRANS_MSG+">"+transplit[2]).encode())
                    print("trans allgut")

                else:
                    # handle if faulted transaction
                    print("trans nogut")
                    self._socket_obj.send(format_data(ermsg + ">" + transplit[2]).encode())
            

            
    def update_balances(s, conn):
        cursor:sqlite3.Cursor = conn.cursor()
        cursor.execute(f'''
        SELECT * FROM transactions WHERE block_id = {s.__lastb} 
        ''')

        trans_list :list[tuple]= cursor.fetchall()

        for t in trans_list:
            if calculate_balik_one(str(t), s._conn)[0]==False:
                break


    def build_merkle_tree(s, connp):

        cursor = connp.cursor()
        cursor.execute(f'''
                        SELECT * FROM transactions 
                    ''')      
        trs = cursor.fetchall()
        if trs==None: # if no transactions
            return hashex("0"*64)
        hashes = [hashex(hashex(str(t))) for t in trs]

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
    
    def __operate_transaction(s, trans, conn):
        connp = sqlite3.connect(f'databases/Node/pending.db')
        cursorp = connp.cursor()
        try:

            success, msg = verify_transaction(trans, conn, connp) # verify transaction
            if not success:
                return False, msg

            success, msgg = calculate_balik_one(trans, connp) # update the balance
            if not success:
                return False, msgg
            
            trans_tuple = ast.literal_eval(trans)
            #include transaction in mempool
            cursorp.execute(f'''
                    INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', trans_tuple)
            cursorp.execute(f'''
            UPDATE balances SET nonce = nonce + 1 WHERE address='{trans_tuple[2]}' AND token='{trans_tuple[5]}'
            ''')
            connp.commit()

            connp.close()
            return True, msgg
        except Exception as e:
            write_to_log(f" Miner / Problem with including the transactions into pending table; {msg or msgg}")
            s._last_error = f"Error in __operate_transaction() func ; {e}"
            
            
    def __start_mining(s, conn, connp):
        chaincursor = conn.cursor()
        
        try:

            diff = s.__diff
            merkle_root = s.build_merkle_tree(connp) # build the root

            chaincursor.execute(f'''
            SELECT block_hash from blocks WHERE block_id={s.__lastb}
            ''')
            p_hash = chaincursor.fetchone() # previous hash of the next block
            if p_hash==None: # if the first block
                p_hash="0"*64
            s.__mining = True
            nonce = 0
            start_time = time.time()
            while s.__mining:
                if nonce%100000==0: # every 100000 calculations update the time
                    timestamp = datetime.now().strftime(tm_format)
                    strheader = f"({s.__lastb+1}, {p_hash}, {merkle_root}, {timestamp}, {diff}, "
                
                header = strheader + str(nonce)+ ")" # header with no hash

                hash = hashex(hashex(header)) # sha256 *2 the header with the nonce

                if hash.startswith(diff*"0"): # if the hash is good mine the block
                    # mining=False
                    full_block_header = f"({s.__lastb+1}, '{hash}', '{p_hash}', '{merkle_root}', '{timestamp}', {diff}, {nonce})"
                    mine_time = time.time() - start_time

                    return full_block_header, mine_time # return the header with the hash

                else:
                    nonce+=1 # increase the nonce

            return False, "Not mined fast enough"
        except Exception as e: # failure handling
            write_to_log(f" MinerBL / Failed to mine block {str(s.__lastb+1)}")
            s._last_error = f"Failed to mine block {str(s.__lastb+1)}"

            return False,f"{e}"
    
    def _always_mine(s):
        conn = sqlite3.connect(f'databases/Miner/blockchain.db')
        pend_conn = sqlite3.connect(f'databases/Miner/pending.db')
        while s.__connected:
            result = s.__start_mining(conn, pend_conn) #  header, time
            if result[0]==False: # if block came earlier
                ermsg = result[1]
            
            else: # mined successfully
                s._socket_obj.send(format_data(MINEDBLOCKSENDMSG +">"+result[0]+">"+result[1]).encode()) # broadcast to everyone
                #stall till got confirmation
                if send_mined==True:
                    start_time = time.time()

                    while time.time() - start_time < 3:
                        if s.__recieved_message.startswith(SAVEDBLOCK):
                            s.__diff = s.__recieved_message.split(">")[1]
                            break
                        time.sleep(0.1)

                    if time.time() - start_time >3:
                        write_to_log(" Miner / Didnt recieve confirmation from node on mined block")
                        s._last_error = " Error in _always_mine func; Didnt recieve confirmation from node on mined block"
                        raise Exception()
                    
                    update_mined_block(conn, pend_conn,result[0]) # update the transactions in local chain

                    s.update_balances() # update the balances
    
   


                

                
            
            
            
            
            


    








        




        
        
    
                        
                
                
    
    
        
    
    
            
    
        
        
        

    

