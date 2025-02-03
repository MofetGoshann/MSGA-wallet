import sqlite3
from datetime import datetime
import socket
conn = sqlite3.connect('blockchain.db')
cursor = conn.cursor()

cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                block_id INT PRIMARY KEY,
                block_hash VARCHAR(64) NOT NULL,
                previous_block_hash VARCHAR(64),
                timestamp DATETIME,
                nonce INT
            )
            ''')

cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                tr_hash VARCHAR(64) NOT NULL,
                block_id INT PRIMARY KEY,
                previous_tr_hash VARCHAR(64),
                timestamp DATETIME,
                sender VARCHAR(64) NOT NULL,
                reciever TEXT NOT NULL,
                amount REAL NOT NULL,
                token TEXT NOT NULL
            )
            ''')

cursor.execute(f'''
                SELECT block_id FROM blocks ORDER BY block_id DESC LIMIT 1
                ''')

#result= cursor.fetchone()[0]

#b = list(result)
#s = ">".join(map(str, b))
print(datetime.now().strftime(f"%d.%m.%Y %H:%M:%S"))
#print(result)
class Session: #session class
    def __init__(self, ip:str, port: str):
        self.__type = None
        self.__ip = ip
        self.__port = port
        self.__username = None
        self.__updated = False
    
    def getu(s):
        return s.__updated
s = Session("123", "22")
#print(s.getu())


#print(s.getu())