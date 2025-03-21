
import threading 
from protocol import *
from Client_protocol import *
from hashlib import sha256
import hashlib
import ecdsa
from ecdsa import SigningKey, NIST256p
from ecdsa.util import sigencode_string
import sqlite3
import binascii
from datetime import datetime
import socket

class ClientBL:

    def __init__(self, ip: str, port: int, username:str, pas:str, skt:socket):
        # Here will be not only the init process of data
        # but also the connect event

        self._socket_obj: socket = None
        self.__user = username
        self.__pass = pas
        self.__recieved_message:str = None
        self._last_error = ""
        self.__nonce = {'SNC': 1}
        self.tokenlist = ["NTL", "TAL", "SAN", "PEPE", "MNSR", "COLR", "MSGA", "52C", "GMBL", "MGR", "RR"]
        self._recvfunc =None #recv_callback
        self._success = self.__connect(ip, port, skt)

    def __connect(self, ip: str, port: int, skt) -> bool:
        #connect client on start init returns success of connection

        try:
            # Create and connect socket
            self._socket_obj = skt
            # let the node know im a client. 1 is client type
            # self.__lastb = chain_on_start("Client", self._socket_obj)
            send(self.__user + ">1", self._socket_obj)
            #always recieve data from node
            self.__always_recieve()
            # Log the data
            write_to_log(f" 路 Client 路 {self._socket_obj.getsockname()} connected")

            # Return on success
            return True

        except Exception as e:

            # Handle failure
            self._socket_obj = None
            write_to_log(f" 路 Client 路 failed to connect client; ex:{e}")

            self._last_error = f"An error occurred in client bl [connect function]\nError : {e}"

            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect the client from server

        :return: True / False on success
        """

        try:
            # Start the disconnect process
            write_to_log(f" 路 Client 路 {self._socket_obj.getsockname()} closing")

            # Alert the server we're closing this client
            send(DISCONNECT_MSG, self._socket_obj)

            self._recvfunc("Disconnected.")
            # Close client socket
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

    def assemble_transaction(self, token: str, amount: float, rec_address: str): # , private_key: SigningKey
        '''gets the transaction info and assembles transaction ready to send
        (time, sender, reciever, amount, token, hexedsignature, hexedpublickey)'''
        time = datetime.now().strftime(f"%d.%m.%Y %H:%M:%S")
        
        
        
        try:
            with open(self.__user+".bin", "rb") as file: # save the phrase encypted
                enc_phrase = file.read()
            
            phrase = decrypt_data(enc_phrase, self.__pass)
            seed = bip39.phrase_to_seed(phrase)

            private_key_bytes = hashlib.sha256(seed).digest()
            private_key = SigningKey.from_string(private_key_bytes, NIST256p)

            public_key: ecdsa.VerifyingKey = private_key.get_verifying_key()
            addres = address_from_key(public_key)
            
            transaction = f"({self.__nonce[token]}, '{str(time)}', '{addres}', '{rec_address}', {amount}, '{token}')"
            signature = private_key.sign_deterministic(transaction.encode(), hashfunc=sha256 ,sigencode=sigencode_string)
            hexedpub = binascii.hexlify(public_key.to_string("compressed")).decode() # hexed public key
            hexedsig = binascii.hexlify(signature).decode() # hexed signature

            wholetransaction = f"({self.__nonce[token]}, '{time}', '{self.__c_address}', '{rec_address}', {amount}, '{token}', '{hexedsig}', '{hexedpub}')"

            return wholetransaction

        except Exception as e:
            write_to_log(f" 路 Client 路 failed to assemble transaction {e}")
            self._last_error = f"An error occurred in client bl [assemble_transaction function]\nError : {e}"

            return False
    
    def send_transaction(self, token: str, amount: float, rec_address: str) -> bool:#, private_key: SigningKey
        """
        Send transaction to the hub and after that to the miner pool
        :return: True / False on success
        """
        try:

            message: str = self.assemble_transaction(token, amount, rec_address)
            if message==False:
                return False
            send(TRANS+"|"+message, self._socket_obj)

            write_to_log(f" 路 Client 路 send to server : {message}")

            return True

        except Exception as e:

            # Handle failure
            write_to_log(f" 路 Client 路 failed to send to server {e}")
            self._last_error = f"An error occurred in client bl [send_data function]\nError : {e}"

            return False

    def __receive_data(self):
        try:
            success, message = receive_buffer(self._socket_obj)
            if not success:
                self._last_error = "didn`t recieve a message"
                return
            return message
        except Exception as e:

            # Handle failure
            write_to_log(f" Client / failed to receive from server : {e}")
            self._last_error = f"An error occurred in client bl [receive_data function]\nError : {e}"
            return ""




    def __always_recieve(self, *args):
        """setup a thread to always recieve messages"""
        try:
            listening_thread = threading.Thread(target=self.__always_listen, args=())
            listening_thread.start()
        except Exception as e:
            self._last_error = f"Error in client bl [always recieve function]\nError : {e}"
            write_to_log(f" 路 Client 路 always recieve thread not working; {e}")

    
        
    def send_blockk(s, id:int):
        send_block(id, s._socket_obj, "Client")
        


    def __always_listen(s):
        """always recieve messages from server primarily to get kick message"""

        connected = True
        while connected:
            s._socket_obj.settimeout(3) # set a timeout for recievedata

            s.__recieved_message = s.__receive_data() # update 
            msg = s.__recieved_message
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
            if not msg==None:
                if msg==KICK_MSG:
                    discsuccess = s.disconnect() # disconnect the client from server
                    
                    if discsuccess: # confirm diconnect
                        write_to_log(f" 路 Client 路 You have been been kicked")

                    else: # if doesnt diconnect
                        s._last_error = f"Error in client bl [always_listen function], failed to diconnect client when kicked by server"
                        write_to_log(f" 路 Client 路 Failed to diconnect the client when kicked by server")

                    connected = False # close loop
                
                if msg==BAD_TRANS_MSG:
                    #faulty transaction
                    s._last_error = f"Error in client bl the transaction sent is invalid "
                
                if msg.startswith(MINEDBLOCKSENDMSG):
                    header = msg.split(">")[1]
                    (suc,  bl_id) =  recieve_block(header, "Client", s._socket_obj)
                    if suc:
                        s.__lastb = bl_id
                    #got a block from the miner
                
                if msg==GOOD_TRANS_MSG:
                    print("qweqweqweqweqweqwe")


    


    
    def get_success(s):
        return s._success
    
    def getsocket(self):
        return self._socket_obj
    
    def get_last_error(s):
        return s._last_error
        
                
                
            
            
    
