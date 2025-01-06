import socket
from protocol import *
import ecdsa
from ecdsa import SigningKey, NIST256p
from ecdsa.util import sigencode_string
from hashlib import sha256
import datetime
import threading
import binascii
import json
import os

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

    def findprevblock(self):
        thisdir = os.path.dirname(os.path.abspath(__file__))
        blockdir = os.path.join(thisdir, "blocks")

        lastbfilepath = os.path.join(blockdir,os.listdir(blockdir)[-1])
        with open(lastbfilepath, 'r') as file:
            lastbdict = json.load(file)
        
        






    def __init__(self, ip:str, port: int, username:str):
    
        self.__transactioncap = 3 # how many transactions in one block
        self._socket_obj: socket = None
        self.__recieved_message = None 
        self.__user = username
        self.__transfile = {}
        self.__thisb: Block = Block("0"*64, )
        

        self.__connect()
        
    
    def __connect(self, ip:str, port:int):
        #connect the miner to the hub/server

        try:
            # Create and connect socket to the hub
            self._socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket_obj.connect((ip, port))

            # let the hub know im a miner. 2 is miner type
            self._socket_obj.send(format_data(self.__user + ">2").encode())

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
    
    def __verify_transaction(self, transmsg_full: str) -> (bool, dict):
        '''
        takes the full transaction message with signature transaction and public key
        returns true if transaction is valid and returns the transaction text
        '''
        try:
            transmsg_full:dict = json.loads(transmsg_full)
            trans_dict: dict = json.loads(transmsg_full["transaction"]) 

            hexedpublickey = trans_dict["public_key"]

            public_key:ecdsa.VerifyingKey = ecdsa.VerifyingKey.from_string(binascii.unhexlify(hexedpublickey),NIST256p) # extracting he key
        
            hexedsignature = trans_dict["signature"]
            signature: bytes = binascii.unhexlify(hexedsignature)
        
            is_valid = public_key.verify(signature, str(trans_dict).encode(),sha256,sigencode=sigencode_string) # verifying
        
            return is_valid, transmsg_full
        
        except Exception as e: # failure
            write_to_log(f" Miner / failed to verify a transaction ; {e}")
            self._last_error = "failed to verify a transaction"
            return False, ""
        
        
    
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
                return
            return message
        except Exception as e:

            # Handle failure
            write_to_log(f" Miner / failed to receive from server : {e}")
            self._last_error = f"An error occurred in miner bl [receive_data function]\nError : {e}"
            return ""
            
            
    
    def __always_listen(self):
        """always recieve messages from server primarily to get kick message"""

        connected = True
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
                
            else:
                success, full_trans_dict = self.__verify_transaction(self.__recieved_message) # verify the transaction
                
                if success:
                    with open(f"block_{str(thisb.getid())}.json", "a") as file: # store the transaction
                        file.write(full_trans_dict + "\n")
                    
                    if len(self.__translist)>= self.__transactioncap: # if the transaction is last
                        #create a block and start to mine
                        
                        thisb = Block(self.__last_block_hash, self.__translist)

                        self._socket_obj.send(format_data(BLOCKSENDMSG + thisb.getdata())).encode()

                        
                        self.__last_block_hash = thisb.gethash() # update the previous hash
                
                else:
                    # handle if faulted transaction
                    self._socket_obj.send(format_data(BAD_TRANS_MSG).encode())
                        
                        
                
                
    
    
        
    
    
            
    
        
        
        

    

