import hashlib 
import shutil
import logging
import socket


LOG_FILE = "LogFile.log"
FORMAT: str = "utf-8"
PORT: int = 12345
BUFFER_SIZE: int = 1024
HEADER_SIZE = 4
DISCONNECT_MSG = "EXIT"


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


def format_data(data: str) -> str:
#adds header accounting the header size

    data_length = len(data)
    num_str = str(data_length)
    padding = "0" * (HEADER_SIZE - len(num_str))

    return f"{padding + num_str}{data}"

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

        buffer = my_socket.recv(buffer_size).decode()
        logging.info("  Protocol  · Buffer data : {}".format(buffer))

        return True, buffer
    except Exception as e:
        
        # On buffer size convert fail
        return False, "Error"    


class ShevahBlock:
    def __init__(self, previous_block_hash, transaction_list):
        self.previous_block_hash = previous_block_hash
        self.transaction_list = transaction_list
        self.block_data = "-" + previous_block_hash ++ "-".join(transaction_list)
        self.block_hash = hashlib.sha256(self.block_data.encode()).hexdigest()
    def __str__(self) -> str:
        return None
    

t1 = "Tal>1488>NC>Misha"
t2 = "Misha sent 1337 SNC to Trump"
t3 = "Biden  sent 0.1 TLC to Tal"
t4 = "Ariel sent 1 SNC to Natali"

FirstB =  ShevahBlock("1488", [t1,t2])

SecondB = ShevahBlock(FirstB.block_hash, [t3,t4])
#asdfasdasdasdasdsdad