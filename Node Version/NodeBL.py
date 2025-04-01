from select import select
import threading
from protocol import *
from Node_protocol import *
class Session: #session class
    def __init__(self, ip:str, port: str, sock: socket):
        self.__type = None
        self.__ip = ip
        self.__port = port
        self.__username = None
        self.__socket = sock
    
    
    def connectupdate(self, username:str, type:int):
        self.__type = type
        self.__username = username
    
    def gettype(self):
        '''Get the type of connecttion, 1 is client 2 is miner'''
        return self.__type
    
    def getsocket(self):
        return self.__socket
    
    def getusername(self):
        return self.__username
    
    
    
    def __iter__(s):
        s.l =  [s.__type, s.__ip, s.__port, s.__username, s.__socket]
        s.i = 0
        return s
    
    def __next__(s):
        if s.i == len(s.l):
            s.i+=1
            return s.l[s.i-1]
        else:
            raise StopIteration
    

    
    



class NodeBL:
    def __init__(self, ip: str, port: int):

        self.__ip: str = ip
        
        self._sessionlist: list[Session]= []
        self._Node_socket: socket = None
        self.__Node_running_flag: bool = False
        self._receive_callback = None
        self._mutex = threading.Lock()
        self.__lastb = 0
        self.tokenlist = ["NTL", "TAL", "SAN", "PEPE", "MNSR", "COLR", "MSGA", "52C", "GMBL", "MGR", "RR"]
        self.__timedict = {"blocks": 0 ,"sum": 0.0, "diff":0}
        
        with open("timesum.json", "r") as json_file:
            loaded_data = json.load(json_file)

        self.__timedict.update(loaded_data)

        self._conn = None
        

        with open('LogFile.log', 'w') as file: # open the log file\
            file.truncate(0)
            pass


        self._last_error = ""
        self._success = self.__start_Node(ip, port)
        
    def __start_Node(self, ip: str, port: int) -> bool:

        write_to_log(" Node / starting")

        try:
            # Create and connect socket
            self._Node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._Node_socket.bind((ip, port))

            # Return on success
            return True

        except Exception as e:

            # Handle failure
            self._Node_socket = None
            write_to_log(f" Node / Failed to start up sever : {e}")

            self._last_error = f"An error occurred in Node bl [start_Node function]\nError : {e}"

            return False
    
    
    def Node_process(self) -> bool:

        try:
            self._conn = sqlite3.connect(f'databases/Node/blockchain.db')
            self.__on_start() # update the chain
            self.__Node_running_flag = True

            self._Node_socket.listen()  # listen for clients

            write_to_log(f" Node / listening on {self.__ip}")

            while self.__Node_running_flag:

                # Use time_out function for .accept() to close thread on no need
                connected_socket, client_addr = self.__time_accept(0.3)
                logreg: str = receive_buffer(connected_socket)[1]
                miner = False
                res =False
                if logreg.startswith("REG"):
                    res = self.register(logreg, connected_socket)

                if logreg.startswith("LOG"):
                    res = self.login(logreg, connected_socket)
                
                if logreg.startswith("Miner user:"):
                    cursor = self._conn.cursor()
                    cursor.execute('''
                        SELECT uId FROM users WHERE username = ?
                        ''', (logreg.split(">")[1], ))
                    c = cursor.fetchone()
                    if c:
                        cursor.execute('''
                        SELECT address FROM balances WHERE uId = ? LIMIT 1
                        ''', (c[0], )) 

                        send("Valid>"+cursor.fetchone()[0], connected_socket)
                        miner = True
                        res = True
                    else:
                        send("Not registered", connected_socket)
                    cursor.close()
                    
                self._conn.commit()
                # Check if we didn't time out
                if connected_socket and res==True:
                    connectedsession: Session = Session(client_addr[0], client_addr[1], connected_socket)
                    self._sessionlist.append(connectedsession)

                    firstmessage: str = receive_buffer(connected_socket)[1]
                    typeuser = str(firstmessage).split('>')
                    connectedsession.connectupdate(typeuser[0], int(typeuser[1])) #get the username and type
                        
                    if connectedsession.gettype()==1 and miner==False: # if client
                        new_client_thread = threading.Thread(target=self.__handle_client, args=(connectedsession, ))
                        new_client_thread.start() # Start a new thread for a new client
                    
                    if connectedsession.gettype()==2 and miner: # if miner
                        new_miner_thread = threading.Thread(target=self.__handle_miner, args=(connectedsession, ))
                        new_miner_thread.start() # Start a new thread for a new miner

                    

                    write_to_log(f" Node / Active connection {threading.active_count() - 2}")

            # Close Node socket on Node end
            self._Node_socket.close()
            write_to_log(" Node / Closed")

            # Everything went without any problems
            self._Node_socket = None

            return True

        except Exception as e:

            # Handle failure
            traceback.print_exc()
            write_to_log(f" Node / Failed to handle a message; {e}")

            self._last_error = f"An error occurred in Node bl [Node_process function]\nError : {e}"

            return False
    
    
    def __time_accept(self, time: int):
    

        try:
            self._Node_socket.settimeout(time)

            ready, _, _ = select([self._Node_socket], [], [], time)

            if ready:
                return self._Node_socket.accept()

            return None, None
        except Exception as e:
            return None, None

    def register(s, msg:str, skt:socket):
        '''
        Create a new user and add into the databases also broadcast the addres to update everyone
        '''
        spl = msg.split(">")

        user = spl[1]
        pas = spl[2]
        address = spl[3]
        cursor = s._conn.cursor()

        # check if already in
        cursor.execute('''
            SELECT 1 FROM users WHERE username = ?
        ''', (user,))
        
        check = cursor.fetchone()
        if check: 
            send("Error, already registered", skt)
            write_to_log("Denied register of "+user)
            return False
        
        cursor.execute('''
            INSERT INTO users (username, pass) VALUES (?, ?)
        ''', (user,pas))

        # get the uid
        cursor.execute('''
            SELECT uId FROM users WHERE username = ?
        ''', (user, ))

        id = cursor.fetchone()[0]


        if not check_address(address): # validate address
            send("Error, invalid address", skt)
            write_to_log("Denied register of "+user)
            return False
        
        for token in s.tokenlist: # adding to the balances db

            cursor.execute('''
                INSERT INTO balances (uId, address, balance, token, nonce) VALUES (?, ?, ?, ?, ?)
            ''', (id, address, 0, token, 1))

        s._conn.commit() # commit changes
        # broadcast 
        if s._sessionlist:
            for session in s._sessionlist:
                send(NEW_USER + f">{address}", session.getsocket())
        
        send(REG_MSG, skt)
        return True

    def login(s, msg:str, skt:socket):
        spl = msg.split(">")

        user = spl[1]
        pas = spl[2]
        cursor = s._conn.cursor()

        cursor.execute('''
            SELECT uId FROM users WHERE username = ? AND pass = ?
        ''', (user, pas))
        
        id = cursor.fetchone()

        if id:
            cursor.execute('''
            SELECT address FROM balances WHERE uId = ?
            ''', (id[0], ))

            adr = cursor.fetchone()[0]

            send(LOG_MSG+">"+adr, skt)
            return True
        send("Error, wrong username or password", skt)
        return False



    def __handle_client(self, clientsession: Session):
        user = clientsession.getusername()
        sock = clientsession.getsocket()
        conn = sqlite3.connect('databases/Node/blockchain.db')
        conn.execute('PRAGMA journal_mode=WAL')

        # This code run in separate for every client
        write_to_log(f" Node / New client : {user} connected")
        
        connected = True
        
        while connected:
            # Get message from  client
            (success,  msg) = receive_buffer(sock)

            if success:
                # if we managed to get the message :
                write_to_log(f" Node / Received from client : {user} - {msg}")
                
                if msg.startswith(TRANS):
                    # the msg is transaction
                    trans = msg.split("|")[1]
                    suc, ermsg = verify_transaction(trans, conn)
                    if suc==False:
                        send(ermsg, sock)
                    else:

                        for session in self._sessionlist:
                            if(session.gettype()==2):
                                #retransmit the transacion to the miners
                                send(msg+"|"+user, session.getsocket())
                        write_to_log("Node / Broadcasted transaction")
                    
                if msg.startswith(CHAINUPDATEREQUEST):
                    if self.__sendupdatedchain(sock, msg, conn)==True:
                        write_to_log(" Node / Updated: " + user)  
                
                if msg.startswith("Is address valid"):
                    adr = msg.split(">")[1]
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1 FROM balances WHERE address = ? ", (adr, ))
                    if cursor.fetchone():
                        sock.send(format_data("Valid").encode())
                    else:
                        send("No such address in the blockchain", sock)
                
                if msg==DISCONNECT_MSG:
                    connected = False
                    write_to_log(f" Node / User {user} was disconnected")

                    for i, u in enumerate(self._sessionlist):
                        if u.getusername()==user:
                            self._sessionlist.pop(i)
                    
                    
    
    def __handle_miner(self, miner_session: Session):
        
        user = miner_session.getusername()
        sock = miner_session.getsocket()
        conn = sqlite3.connect('databases/Node/blockchain.db', timeout=5)
        

        write_to_log(f"Node / New miner : {user} connected")
        
        connected = True

        while connected:
            time.sleep(0.05)
            msg = receive_buffer(sock)[1]

            if msg!="" :

                # if we managed to get the message :
                write_to_log(f" Node / received from miner : {user} - {msg}")    

                if msg.startswith(MINEDBLOCKSENDMSG): # if miner is sending a block
                    res = msg.split(">") # minedblocksend, header, time

                    (suc,  bl_id) =  recieve_block(res[1], sock)
                    if suc: # if recieved block successfully
                        self.__timedict["blocks"]+=1
                        self.__timedict["sum"]+=float(res[2])

                        if self.__timedict["blocks"]%5==0: # adjust the difficulty
                            avg = self.__timedict["sum"]/5
                            self.calculate_diff(avg)
                            #reset the counters for difficulty
                            self.__timedict["blocks"]= 0 
                            self.__timedict["sum"]= 0.0                     
                        
                        with open("timesum.json", "w") as json_file:# update the json
                            json.dump(self.__timedict, json_file, indent=4)

                        self.__lastb = self.__lastb + 1
                        self.calculate_balik(self.__lastb, conn)
                        
                        send(SAVEDBLOCK + ">" + str(self.__timedict["diff"]), sock)

                        
                        for session in self._sessionlist:
                            #retransmit the block to all
                            skt=session.getsocket()
                            if session.gettype()==2 and session.getusername()!=user: # to the miners
                                send_to_miner(msg, self.__timedict['diff'], skt, conn)
                                write_to_log(f" Node / sent the block to {session.getusername()}")

                            elif session.gettype()==1: # to clients
                                send_block(bl_id, skt, conn)
                                write_to_log(f" Node / sent the block to {session.getusername()}")
                            
                    else:
                        write_to_log(f' Node / Couldnt recieve block from {user}; {bl_id}')

                elif msg.startswith(CHAINUPDATEREQUEST):
                    if self.__sendupdatedchain(sock, msg, conn)==True:
                        write_to_log(" Node / Updated: " + user)  

                if msg.startswith(GOOD_TRANS_MSG): # send the confirmation to the client(sender)
                    user_to_send = msg.split(">")[1]    

                    for session in self._sessionlist:
                        #retransmit to the sender
                        us=session.getusername()
                        typ = session.gettype()
                        if(us==user_to_send and typ==1):
                            send(GOOD_TRANS_MSG, session.getsocket())
                            write_to_log(f" Node / Sent confirmation to: {user_to_send}")

                if msg.startswith(BAD_TRANS_MSG):
                    er = msg.split(">")[1]
                    user_to_send = msg.split(">")[2]
                    for session in self._sessionlist:
                        #retransmit to the sender
                        us=session.getusername()
                        if(us==user_to_send):
                            send(BAD_TRANS_MSG+">"+er, session.getsocket())
                            write_to_log(f" Node / Sent error to: {user_to_send}")

                if msg==DISCONNECT_MSG:
                    connected = False
                    write_to_log(f" Node / Miner {user} was disconnected")
                    
                    for i, u in enumerate(self._sessionlist):
                        if u.getusername()==user:
                            self._sessionlist.pop(i)
                msg=""
                
    
    
    def __sendupdatedchain(s, skt: socket, msg: str, conn):
        '''
        updates a connected members blockchain from the block id
        returns True if sent everything and the member saved it 
        False if not
        '''
        
        id = msg.split(">")[1]
        cursor = conn.cursor()

        try:
            cursor.execute(f'''
            SELECT block_id FROM blocks WHERE block_id > {int(id)-1} 
            ''')

            id_list = cursor.fetchall() # get all the blocks needed to send

            if id_list: # if valid 
                
                

                if len(id_list)==1: # if the senders last block is the actual last block send confirmation

                    if int(id)==id_list[0][0]: # if last block the same
                        send("UPDATED" + f">{id}>{s.__timedict['diff']}", skt)
                        return True
                    
                    # if its the only block
                    send(CHAINUPDATING+f">{len(id_list)}", skt)

                    if send_block(id_list[0][0], skt, conn)==False:  # send the only block
                        s._last_error = " NodeBL / Couldnt update blockhain"
                        write_to_log("Failed to update chain")
                        return False

                    send("UPDATED" + ">" + str(id_list[0][0])+f">{s.__timedict['diff']}", skt)
                    return True
                if int(id)!=0:
                    print("NIGGER")
                    id_list = id_list[1:]

                send(CHAINUPDATING+f">{len(id_list)}>{s.__timedict['diff']}", skt)

                for b_id in id_list: # send all the blocks the member is missing 
                    
                    if send_block(b_id[0], skt, conn)==False:
                        s._last_error = " NodeBL / Couldnt update blockhain"
                        return False
                
                send("UPDATED" + ">" + str(b_id[0]) + f">{s.__timedict['diff']}", skt)
                cursor.close()
                return True
            else: # if sent if is wrong
                cursor.close()
                send("UPDATED>" +"0"+">"+str(s.__timedict['diff']), skt)
                return False

        except Exception as e:
            traceback.print_exc()
            write_to_log(f" NodeBL / failed to update blockchain; {e}")
            s._last_error = f"Failed to update blockchain; {e}"
            return False
                    


    
    def _send_block(s, id:int, skt:socket):
        send_block(id, skt, "Node")
        
    def get_success(s):
        return s._success
    
    def get_last_error(s):
        return s._last_error
    
    def calculate_balik(s, b_id: int, conn):
        cursor = conn.cursor()
        try:
            cursor.execute(f'''
            SELECT sender, reciever, amount, token FROM transactions WHERE block_id={b_id}
            ''')

            transes = cursor.fetchall()

            for trans in transes:
                
                cursor.execute(f'''
                UPDATE balances SET balance = balance + {trans[2]} WHERE address='{trans[1]}' AND token = '{trans[3]}'
                ''')
                if trans[0]!="0"*64:
                    cursor.execute(f'''
                    UPDATE balances SET balance = balance - {trans[2]} WHERE address='{trans[0]}' AND token = '{trans[3]}'
                    ''') 
                    cursor.execute(f"UPDATE balances SET nonce = nonce + 1 WHERE address='{trans[0]}' AND token = '{trans[3]}'")   
                    
                conn.commit()
            
            return True
        except Exception as e:
            traceback.print_exc()
            write_to_log("Failed to calculate balance ; " +e)
            s._last_error = "Failed to calculate balance"
            return False

    def calculate_diff(s, m_time):
        
        if m_time>120:
            s.__timedict["diff"]-=1
        
        if m_time<20:
            s.__timedict["diff"]+=1
    
    def __on_start(s):




        cursor = s._conn.cursor()
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
            uId INT NOT NULL,
            address VARCHAR(64) NOT NULL,
            balance REAL NOT NULL,
            token VARCHAR(12) NOT NULL,
            nonce INT NOT NULL
            )
            ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
            uId INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(16) NOT NULL,
            pass VARCHAR(16) NOT NULL
            )
            ''')
        
        s._conn.commit()
        cursor.execute('''
        SELECT block_id FROM blocks ORDER BY block_id DESC LIMIT 1
        ''')
        
        res = cursor.fetchone()
        if res:
            s.__lastb = res[0]
            write_to_log(f" Node / Current block is {s.__lastb}, with the difficulty of {s.__timedict['diff']}")
            return
        write_to_log(f"Node / No blocks in the chain, starting difficulty is {s.__timedict['diff']}")
        

        
        
        
                











    



                
                
                
                
                
            
            

                    


    
    
    
    
    
        

