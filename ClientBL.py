
import threading 
from protocol import *

class ClientBL:

    def __init__(self, ip: str, port: int, recv_callback):
        # Here will be not only the init process of data
        # but also the connect event

        self._socket_obj: socket = None

        self.__recieved_message = None
        self._last_error = ""
        self._balance = {}
        self._recvfunc = recv_callback
        self._success = self.__connect(ip, port)

    def __connect(self, ip: str, port: int) -> bool:
        #connect client on start init returns success of connection

        try:
            # Create and connect socket
            self._socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket_obj.connect((ip, port))

            #always recieve data from server to know if kicked
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
            self.send_data(DISCONNECT_MSG, "")

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

    def assemble_transaction(self, send_address: str, token: str, amount: float, rec_address: str) -> str:

        transaction = send_address + ">" + amount + ">" + token + ">" + rec_address
        return transaction

    def send_transaction(self, send_address: str, token: str, amount: float, rec_address: str) -> bool:
        """
        Send transaction to the hub and after that to the miner pool
        :param args_string: arguments of the transaction string to send
        :return: True / False on success
        """
        try:

            # If our command is not related to protocol 2.7 at all

            # we will use protocol 2.6
            message: str = self.assemble_transaction(send_address, token, amount, rec_address)
            encoded_msg: bytes = message.encode(FORMAT)

            self._socket_obj.send(encoded_msg)

            write_to_log(f" 路 Client 路 send to server : {message}")

            return True

        except Exception as e:

            # Handle failure
            write_to_log(f" 路 Client 路 failed to send to server {e}")
            self._last_error = f"An error occurred in client bl [send_data function]\nError : {e}"

            return False








    
        
    






    def __always_listen(self):
        """always recieve messages from server primarily to get kick message"""

        connected = True
        while connected:
            self._socket_obj.settimeout(3) # set a timeout for recievedata

            self.__recieved_message = self.receive_data() # update 

            if self.__recieved_message and self.__recieved_message.startswith(REG_MSG):

                key = self.__recieved_message[REG_MSG.__len__():]

                if key:
                    with open("ClientBLregkeys.txt", 'a') as file: # save the key in a textfile
                        file.write(key + "\n")

                    self._recvfunc(REG_MSG) #insert the message into the gui
                else:
                    write_to_log(" 路 Client 路 Failed to save to text file, key not identified")

            else:
                self._recvfunc(self.__recieved_message) #insert the message into the gui
            

            if self.__recieved_message==KICK_MSG:
                discsuccess = self.disconnect() # disconnect the client from server
                
                if discsuccess: # confirm diconnect
                    write_to_log(f" 路 Client 路 You have been been kicked")

                else: # if doesnt diconnect
                    self._last_error = f"Error in client bl [always_listen function], failed to diconnect client when kicked by server"
                    write_to_log(f" 路 Client 路 Failed to diconnect the client when kicked by server")

                connected = False # close loop
    
