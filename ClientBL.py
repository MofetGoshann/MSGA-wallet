
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

    def __init__(self, username:str, private_key: SigningKey, skt:socket, show_err):
        # Here will be not only the init process of data
        # but also the connect event
        self.show_error = show_err
        self._socket_obj: socket = None
        self.__user = username
        self.__private_key = private_key
        self.__address = address_from_key(self.__private_key.get_verifying_key())
        print(self.__address)
        self.__recieved_message:str = None
        self._last_error = ""
        self.tokenlist = ["NTL", "TAL", "SAN", "PEPE", "MNSR", "MSGA", "52C", "GMBL", "MGR", "RR"]
        self._recvfunc =None #recv_callback
        
        self._success = self.__connect(skt)

    def __connect(self, skt) -> bool:
        #connect client on start init returns success of connection

        try:
            # Create and connect socket
            self._socket_obj = skt
            # let the node know im a client. 1 is client type
            # self.__lastb = chain_on_start("Client", self._socket_obj)
            send(self.__user + ">1", self._socket_obj)
            
            #always recieve data from node
            self.__always_recieve()
            self._lastb = chain_on_start(self._socket_obj)
            # Log the data
            write_to_log(f" 路 Client 路 {self._socket_obj.getsockname()} connected")

            # Return on success
            return True

        except Exception as e:

            # Handle failure
            self._socket_obj = None
            self.show_error("Error in __conect func", f"failed to connect client; ex:{e}")
            write_to_log(f" 路 Client 路 failed to connect client; ex:{e}")
            traceback.print_exc
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
            self.show_error("Error in disconect func", self._last_error)
            return False

    def assemble_transaction(self, token: str, amount: float, rec_address: str): # 
        '''gets the transaction info and assembles transaction ready to send
        (time, sender, reciever, amount, token, hexedsignature, hexedpublickey)'''
        time = datetime.now().strftime(f"%d.%m.%Y %H:%M:%S")
        
        
        
        try:
            private_key = self.__private_key
            public_key: ecdsa.VerifyingKey = private_key.get_verifying_key()
            addres = address_from_key(public_key)

            conn = sqlite3.connect(f'databases/Client/blockchain.db')
            cursor = conn.cursor()

            cursor.execute(f'''
            SELECT nonce from balances WHERE token = ? AND address = ?
            ''', (token, addres))
            nonce = cursor.fetchone()[0]
            conn.close()

            transaction = f"({nonce}, '{str(time)}', '{addres}', '{rec_address}', {amount}, '{token}')"

            signature = private_key.sign_deterministic(transaction.encode(), hashfunc=sha256 ,sigencode=sigencode_string)
            hexedpub = binascii.hexlify(public_key.to_string("compressed")).decode() # hexed public key
            hexedsig = binascii.hexlify(signature).decode() # hexed signature

            wholetransaction = f"({nonce}, '{time}', '{addres}', '{rec_address}', {amount}, '{token}', '{hexedpub}', '{hexedsig}')"

            return wholetransaction

        except Exception as e:
            write_to_log(f" 路 Client 路 failed to assemble transaction {e}")
            self._last_error = f"An error occurred in client bl [assemble_transaction function]\nError : {e}"
            self.show_error("Error in assemble_transaction func", self._last_error)

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

            return True

        except Exception as e:

            # Handle failure
            write_to_log(f" 路 Client 路 failed to send to server {e}")
            self._last_error = f"An error occurred in client bl [send_data function]\nError : {e}"
            self.show_error("Error in send_transaction func", self._last_error)

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
            self.show_error("Error in recieve_data func", self._last_error)
            return ""




    def __always_recieve(self, *args):
        """setup a thread to always recieve messages"""
        try:
            listening_thread = threading.Thread(target=self.__always_listen, args=())
            listening_thread.start()
        except Exception as e:
            self._last_error = f"Error in client bl [always recieve function]\nError : {e}"
            self.show_error("Error in __always_recieve func", self._last_error)
            write_to_log(f" 路 Client 路 always recieve thread not working; {e}")

    
        
    def send_blockk(s, id:int):
        send_block(id, s._socket_obj, "Client")
        


    def __always_listen(s):
        """always recieve messages from server primarily to get kick message"""

        connected = True
        while connected:
            s._socket_obj.settimeout(3) # set a timeout for recievedata
            conn = sqlite3.connect("databases/Client/blockchain.db")

            s.__recieved_message = s.__receive_data() # update 
            msg = s.__recieved_message

            if not msg==None:
                write_to_log(" Client / Received from Node : " + msg)
                if msg==KICK_MSG:
                    discsuccess = s.disconnect() # disconnect the client from server
                    
                    if discsuccess: # confirm diconnect
                        write_to_log(f" Client / You have been been kicked")

                    connected = False # close loop
                
                if msg==BAD_TRANS_MSG:
                    #faulty transaction
                    s._last_error = f"Error in client bl the transaction sent is invalid "
                
                if msg.startswith(BLOCKSENDMSG):
                    header = msg.split(">")[1]
                    (suc,  bl_id, g) =  recieve_block(header, conn, s._socket_obj)
                    if suc:
                        s._lastb +=1
                        s.update_balances(conn)
                    else:
                        send(bl_id, s._socket_obj)
                    #got a block from the miner
                
                if msg==GOOD_TRANS_MSG:
                    print("qweqweqweqweqweqwe")
                
                if msg.startswith(CHAINUPDATING): # if updating the local chain
                    result = saveblockchain(msg, s._socket_obj, conn)
                    if result!=False:
                        s._lastb = result
                        write_to_log(f" Client / Updated chain, last block: {s._lastb}")
                    
                    else:
                        s._last_error = "Cannot connect to blockchain"
                        print("nono")
                        s.disconnect()

    def update_balances(s, conn):
        cursor:sqlite3.Cursor = conn.cursor()
        cursor.execute(f'''
        SELECT * FROM transactions WHERE block_id = {s._lastb} 
        ''')

        trans_list :list[tuple]= cursor.fetchall()

        for t in trans_list:
            
            if calculate_balik_one(str(t), conn)[0]==False:
                write_to_log("Couldnt calculate balances of block:" + str(s._lastb))
                break
    


    
    def get_success(s):
        return s._success
    
    def getsocket(self):
        return self._socket_obj
    
    def get_last_error(s):
        return s._last_error

    def get_private(s):
        return s.__private_key
    
    def get_address(s):
        return s.__address

    def get_message(s):
        return s.__recieved_message
    
def chain_on_start(skt:socket):

    conn = sqlite3.connect(f'databases/Client/blockchain.db')
    cursor = conn.cursor()


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            block_id INT PRIMARY KEY NOT NULL,
            block_hash VARCHAR(64) NOT NULL,
            previous_block_hash VARCHAR(64),
            merkle_root VARCHAR(64) NOT NULL,
            timestamp VARCHAR(24) NOT NULL,
            difficulty INT NOT NULL,
            nonce INT NOT NULL
        )
        ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
            block_id INT NOT NULL,
            nonce INT NOT NULL,
            timestamp VARCHAR(24) NOT NULL,
            sender VARCHAR(64) NOT NULL,
            reciever VARCHAR(64) NOT NULL,
            amount REAL NOT NULL,
            token VARCHAR(12) NOT NULL,
            hex_pub_key VARCHAR(256) NOT NULL,
            hex_signature VARCHAR(256) NOT NULL
        )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            address VARCHAR(64) NOT NULL,
            balance REAL NOT NULL,
            token VARCHAR(12) NOT NULL,
            nonce INT NOT NULL
        )
        ''')  

    conn.commit()
    cursor.execute('''
        SELECT block_id FROM blocks ORDER BY block_id DESC LIMIT 1
        ''')

    lastb_id = cursor.fetchone() # get the last block

    if lastb_id:
        send(CHAINUPDATEREQUEST + f">{lastb_id[0]}", skt)
        return lastb_id[0]
    else:
        send(CHAINUPDATEREQUEST + f">{1}", skt)
        return 1
                
                
            
            
    
