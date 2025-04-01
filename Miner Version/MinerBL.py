from protocol import *
from Miner_protocol import *
import select
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
import random







class Miner:




    def __init__(self, username:str, address, skt):
    
        self._socket_obj: socket = skt
        self.__recieved_message = ""
        self.__user = username
        self.__address = address
        self.__lastb = None
        self.tokenlist = ["NTL", "TAL", "SAN", "PEPE", "MNSR", "MSGA", "52C", "GMBL", "MGR", "RR"]
        self.__mining = False
        self.__diff = 0
        self.__connected = False
        with open('LogFile.log', 'w') as file: # open the log file\
            file.truncate(0)
            pass
        self._conn = sqlite3.connect(f'databases/Miner/blockchain.db')
        self._pend_conn  = sqlite3.connect(f'databases/Miner/pending.db')
        self.suc = self.__connect()
        
    
    def __connect(self):
        #connect the miner to the hub/server

        try:
            # Create and connect socket to the hub
            
            # let the hub know im a miner and give the block id to update
            send(self.__user + ">2", self._socket_obj)
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
            
            self.__lastb = int(self.__recieved_message.split(">")[1])
            self.__diff = int(self.__recieved_message.split(">")[2])
            print(f" Miner / Starting difficulty is {self.__diff}")
            #self.__diff = self.__recieved_message.split(">")[2]


        
            mining_thread = threading.Thread(target=self._always_mine, args=())
            mining_thread.start()
            
            # Log the data
            write_to_log(f" Miner / {self._socket_obj.getsockname()} connected")

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
            write_to_log(f" Miner / {self._socket_obj.getsockname()} closing")

            # Alert the server we're closing this miner
            self._socket_obj.send(format_data(DISCONNECT_MSG).encode())
            self.__connected= False
            self.__mining = False
            self._socket_obj.close()

            write_to_log(f" Miner / The miner closed application")

            self._socket_obj = None

            # Return on success
            return True

        except Exception as e:

            # Handle failure
            write_to_log(f" Miner / Failed to disconnect : {e}")
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
        
    def __time_recieve(self, time: int):
        try:
            self._socket_obj.settimeout(time)

            ready, _, _ = select.select([self._socket_obj], [], [], time)

            if ready:
                return self.__receive_data()

            return ""
        except Exception as e:
            return str(e)
    
    def __always_listen(self):
        """always recieve messages from server primarily to get kick message"""
        conn = sqlite3.connect(f'databases/Miner/blockchain.db')
        self.__connected = True

        while self.__connected:
            time.sleep(0.05)
            self.__recieved_message = self.__receive_data() # update 
              
            msg = self.__recieved_message # for simplicity
            if msg!="":
                write_to_log(f" Miner / Received from Node : {msg}")  
            # log in stuff
            
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
                self.__diff = msg.split(">")[2]
                result = saveblockchain(msg, self._socket_obj, conn)
                if result[0]!=False:
                    self.__lastb = result[0]

                    write_to_log(f" Miner / Updated chain, diff: {self.__diff}")
                
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
                    send(BAD_TRANS_MSG+">" + ermsg + ">" + transplit[2], self._socket_obj)
            

            
    def update_balances(s, conn):
        cursor:sqlite3.Cursor = conn.cursor()
        cursor.execute(f'''
        SELECT * FROM transactions WHERE block_id = {s.__lastb} 
        ''')

        trans_list :list[tuple]= cursor.fetchall()

        for t in trans_list:
            
            if calculate_balik_one(str(t), conn)[0]==False:
                write_to_log("Couldnt calculate balances of block:" + str(s.__lastb))
                break


    def build_merkle_tree(s, connp):

        cursor = connp.cursor()
        cursor.execute(f'''
                        SELECT * FROM transactions 
                    ''')      
        trs = cursor.fetchall()
        
        mined_time = datetime.fromtimestamp(time.time() + 1).strftime("%Y-%m-%d %H:%M:%S")
        hashes = [hashex(hashex(str(t))) for t in trs]

        # If only one transaction, the Merkle Root is its hash
        if len(hashes) == 1:
            return hashes[0], mined_time
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
        return hashes[0], mined_time
    
    def __operate_transaction(s, trans, conn):
        connp = sqlite3.connect(f'databases/Miner/pending.db')
        cursorp = connp.cursor()
        try:

            success, msg = verify_transaction(trans, conn) # verify transaction
            if not success:
                return False, msg
            
            trans_tuple = ast.literal_eval(trans)
            #include transaction in mempool
            cursorp.execute(f'''
                    INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', trans_tuple)
            connp.commit()

            connp.close()
            return True, msg
        except Exception as e:
            write_to_log(f" Miner / Problem with including the transactions into pending table; {msg}")
            s._last_error = f"Error in __operate_transaction() func ; {e}"
            
            
    def __start_mining(s, conn : sqlite3.Connection, connp):
        
        chaincursor = conn.cursor()
        cursorp = connp.cursor()

        token = s.tokenlist[random.randint(0,9)] # get a random token
        print(f" Miner / Mining block {s.__lastb+1}, reward in {token}", end="", flush=True)
        try:
            mined_time = datetime.now().strftime(tm_format)
            diff = s.__diff # set the diff
            # insert the reward transaction
            cursorp.execute(f'''
            INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (0, mined_time, "0"*64, s.__address, 100, token, "0"*64, "0"*64))
            connp.commit()

            merkle_root, mined_time = s.build_merkle_tree(connp) # build the root

            chaincursor.execute(f'''
            SELECT block_hash from blocks WHERE block_id={s.__lastb}
            ''')
            p_hash = chaincursor.fetchone() # previous hash of the next block
            
            
            if p_hash==None: # if the first block
                p_hash=tuple("0"*64, )

            s.__mining = True
            nonce = 0
            thisb = s.__lastb+1

            start_time = time.time()
            while s.__mining:
                if nonce%500000==0: # every 100000 calculations update the time
                    print(".", end="", flush=True)
                    timestamp = datetime.now().strftime(tm_format) #  
                    strheader = f"({str(thisb)}, '{str(p_hash[0])}', '{str(merkle_root)}', '{str(timestamp)}', {str(diff)}, "
                
                header = strheader + str(nonce)+ ")" # header with no hash

                hash = hashex(hashex(header)) # sha256 *2 the header with the nonce

                if hash.startswith(diff*"0"): # if the hash is good mine the block
                    # mining=False
                    full_block_header = f"({thisb}, '{hash}', '{p_hash[0]}', '{merkle_root}', '{timestamp}', {diff}, {nonce})"
                    mine_time = time.time() - start_time
                    print("\n")
                    return full_block_header, str(round(mine_time, 2)), mined_time # return the header with the hash

                else: 
                    nonce+=1 # increase the nonce

            return False, "Not mined fast enough"
        except Exception as e: # failure handling
            write_to_log(f" MinerBL / Failed to mine block {str(s.__lastb+1)}; {e}")
            s._last_error = f"Failed to mine block {str(s.__lastb+1)}"
            s.disconnect()
            traceback.print_exc()
            return False,f"{e}"
    
    def _always_mine(s):
        conn = sqlite3.connect(f'databases/Miner/blockchain.db')
        pend_conn = sqlite3.connect(f'databases/Miner/pending.db')

        while s.__connected:

            result = s.__start_mining(conn, pend_conn) #  header, time, mined_time
            if result[0]!=False: # if block came earlier
                write_to_log(f" Miner / Sent the block {s.__lastb+1} to node ")
                header, mining_time, mined_time = result

                send(MINEDBLOCKSENDMSG +">"+header+">"+mining_time, s._socket_obj) # broadcast to everyone
                #stall till got confirmation
                res = send_mined(header, s._socket_obj, pend_conn, s.__lastb+1, mined_time)
                if res[0]==True:
                    # wait for confirmation from server , then save the block
                    start_time = time.time()

                    while time.time() - start_time < 3:
                        if s.__recieved_message.startswith(SAVEDBLOCK):
                            s.__diff = int(s.__recieved_message.split(">")[1])
                            break
                        time.sleep(0.1)

                    if time.time() - start_time >3: 
                        write_to_log(" Miner / Didnt recieve confirmation from node on mined block")
                        s._last_error = " Error in _always_mine func; Didnt recieve confirmation from node on mined block"
                        raise Exception(TimeoutError)
                    
                    s.__recieved_message = ""
                    update_mined_block(conn, pend_conn,header, mined_time) # update the transactions in local chain
                    s.__lastb=s.__lastb+1 # update the last block

                    s.update_balances(conn) # update the balances
                        
                    
                    write_to_log(f"Miner / Successully mined and broadcasted the block {s.__lastb}") # log
                else: # delete the miners transaction on error
                    cursorp = pend_conn.cursor()
                    cursorp.execute("""
                    DELETE FROM transactions WHERE sender = ?                  
                      """, ('0'*64, ))
                    
                    cursorp.commit()
                    cursorp.close()
                    conn.close()
                    pend_conn.close()
                    write_to_log(" Miner / Failed to send mined block")
                    s.disconnect()
            else: # if bad delete 
                cursorp = pend_conn.cursor()
                cursorp.execute(f"SELECT 1 FROM transactions")

                if cursorp.fetchone(): # delete miner trasanctions
                    cursorp.execute(f"DELETE FROM transactions WHERE sender = ?", ('0'*64, ) )
                    pend_conn.commit()
                cursorp.close()
                pend_conn.close()
                write_to_log("Miner / Failed to mine; "+result[1])
    
    def get_success(s):
        return s.suc
    



                

                
            
            
            
            
            


    








        




        
        
    
                        
                
                
    
    
        
    
    
            
    
        
        
        

    

