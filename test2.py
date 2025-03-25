from Client_protocol import *


conn = sqlite3.connect('databases/Client/blockchain.db')
cursor = conn.cursor()
address = "RRdcff92bc9ff4aa60e3cafe147e197d9ac46f"
cursor.execute('SELECT balance, token from balances WHERE address = ?', (address,))
balances = cursor.fetchall()


balance_dict = {}
for b in balances:
    balance_dict[b[1]] = b[0]
    print(balance_dict[b[1]])