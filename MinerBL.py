import socket
import protocol
from protocol import *
import ecdsa
from ecdsa import SigningKey, NIST256p
from ecdsa.util import sigencode_string



class Miner:
    def __init__(self, ip:str, port: int, username:str):
    
        self.__btransactions = 0
        self._socket_obj: socket= None
        self.__recieved_message = None
        self.__user = username

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
    
    def __verify_transaction(self, transmsg_full: str):
        try:
        
            trans_list: list = transmsg_full.split(">")
        
            public_key = ecdsa.VerifyingKey.from_string(trans_list[2],NIST256p)
        
            enc_transaction = trans_list[0]
        
            byte_signature = trans_list[1].encode()
        
            is_valid = public_key.verify(byte_signature, enc_transaction,None)
        
            return is_valid
        except Exception as e:
            write_to_log(f" Miner / failed to verify a transaction ; {e}")
            
            self._last_error = "failed to verify a transaction"
            
            return False
    
    
            
    
        
        
        

    

