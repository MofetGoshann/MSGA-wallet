import sqlite3
from datetime import datetime

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
    SELECT * FROM blocks WHERE block_id = {1}
                ''')

result:tuple = cursor.fetchall()[0]

b = list(result)
s = ">".join(map(str, b))
print(datetime.now().strftime(f"%d.%m.%Y ; %H:%M:%S.%f")[:-3])
