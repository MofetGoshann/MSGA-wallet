import sqlite3

conn = sqlite3.connect('blockchain_db')
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


