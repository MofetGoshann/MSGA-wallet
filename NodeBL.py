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
        self.__updated = False
    
    
    def connectupdate(self, username:str, type:int):
        self.__type = type
        self.__username = username
    
    def gettype(self):
        return self.__type
    
    def getsocket(self):
        return self.__socket
    
    def getusername(self):
        return self.__username
    


    def setu(s, up:bool):
        s.__updated = up
    
    def getu(s):
        return s.__updated
    
    def __iter__(s):
        s.l =  [s.__type, s.__ip, s.__port, s.__username, s.__socket, s.__updated]
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
        
        self._sessionlist: list= []
        self._Node_socket: socket = None
        self.__Node_running_flag: bool = False
        self._receive_callback = None
        self._mutex = threading.Lock()
        self._diff = 0
        self.__lastb = 0
        self.__timedict = {"blocks": 0 ,"sum": 0.0, "diff":0}
        
        with open("timesum.json", "r") as json_file:
            loaded_data = json.load(json_file)

        self.__timedict.update(loaded_data)

        self._conn = sqlite3.connect(f'databases/Node/blockchain.db')
        self.__on_start() # update the 

        with open('LogFile.log', 'w'): # open the log file
            pass

        self._last_error = ""
        self._success = self.__start_Node(ip, port)
        
    def __start_Node(self, ip: str, port: int) -> bool:

        write_to_log("  Node    · starting")

        try:
            # Create and connect socket
            self._Node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._Node_socket.bind((ip, port))

            # Return on success
            return True

        except Exception as e:

            # Handle failure
            self._Node_socket = None
            write_to_log(f"  Node    · failed to start up sever : {e}")

            self._last_error = f"An error occurred in Node bl [start_Node function]\nError : {e}"

            return False
    
    
    def Node_process(self) -> bool:

        try:

            self.__Node_running_flag = True

            self._Node_socket.listen()  # listen for clients

            write_to_log(f"  Node    · listening on {self.__ip}")

            while self.__Node_running_flag:

                # Use time_out function for .accept() to close thread on no need
                connected_socket, client_addr = self.__time_accept(0.3)

                # Check if we didn't time out
                if connected_socket:
                    connectedsession: Session = Session(client_addr[0], client_addr[1], connected_socket)
                    self._sessionlist.append(connectedsession)

                    firstmessage: str = receive_buffer(connected_socket)[1]
                    typeuser = str(firstmessage).split('>')
                    connectedsession.connectupdate(typeuser[0], int(typeuser[1])) #get the username and type
                        
                    if connectedsession.gettype()==1: # if client
                        new_client_thread = threading.Thread(target=self.__handle_client, args=(connectedsession, ))
                        new_client_thread.start() # Start a new thread for a new client
                    
                    if connectedsession.gettype()==2: # if miner
                        new_miner_thread = threading.Thread(target=self.__handle_miner, args=(connectedsession, ))
                        new_miner_thread.start() # Start a new thread for a new miner

                    

                    write_to_log(f"  Node    · active connection {threading.active_count() - 2}")

            # Close Node socket on Node end
            self._Node_socket.close()
            write_to_log("  Node    · closed")

            # Everything went without any problems
            self._Node_socket = None

            return True

        except Exception as e:

            # Handle failure
            write_to_log(f"  Node    · failed to handle a message; {e}")

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



    def __handle_client(self, clientsession: Session):
        
        user = clientsession.getusername()
        sock = clientsession.getsocket()
        conn = sqlite3.connect(f'databases/Node/blockchain.db')

        # This code run in separate for every client
        write_to_log(f"  Node   new client : {user} connected")
        

        #if self._clientstablecallback is not None: # insert client to gui table
        #    self._clientstablecallback(client_addr[0], client_addr[1], True, False)
        
        connected = True

        while connected:
            # Get message from  client
            (success,  msg) = receive_buffer(sock)

            if success:
                # if we managed to get the message :
                write_to_log(f"  Node    · received from client : {user} - {msg}")

                #self._mutex.acquire()
                #try:
                #    if self._receive_callback is not None:
                #        if not msg.startswith("LOGIN"):
                #            self._receive_callback(f"{user} - {msg}")    
                #        else:
                #            self._receive_callback(f"{user} - LOGIN > Username, Password")

                #except Exception as e:
                #    write_to_log(f"  Node    · some error occurred : {e}")
                #finally:
                #    self._mutex.release()
                    
                # If the client wants to disconnect
                if msg == DISCONNECT_MSG:
                    connected = False
                    self._sessionlist.remove(clientsession) # remove the client from session list
                
                if msg.startswith(TRANS):
                    # the msg is transaction
                    trans = msg.split("|")[1]
                    suc, ermsg = verify_transaction(trans, conn)
                    if suc==False:
                        sock.send(format_data(ermsg).encode())
                    else:

                        for session in self._sessionlist:
                            if(session.gettype()==2):
                                #retransmit the transacion to the miners
                                print("sent")
                                session.getsocket().send(format_data(msg+"|"+user).encode())
                    
    
    def __handle_miner(self, miner_session: Session):
        
        user = miner_session.getusername()
        sock = miner_session.getsocket()
        conn = sqlite3.connect(f'databases/Node/blockchain.db')


        write_to_log(f"  Node   new miner : {user} connected")
        
        connected = True

        while connected:
            time.sleep(0.05)
            (success,  msg) = receive_buffer(sock)

            if success :

                #if miner_session.getu()==False:
                #    write_to_log("Not ")
                #    raise Exception


                # if we managed to get the message :
                write_to_log(f" Node / received from miner : {user} - {msg}")    

                if msg.startswith(MINEDBLOCKSENDMSG): # if miner is sending a block
                    res = msg.split(">") # minedblocksend, header, time

                    ist = res[3]
                    (suc,  bl_id) =  recieve_block(res[1], conn, sock, ist)
                    if suc: # if recieved block successfully
                        self.__timedict["blocks"]+=1
                        self.__timedict["sum"]+=res[2]

                        if self.__timedict["blocks"]%5==0: # adjust the difficulty
                            avg = self.__timedict["sum"]/5
                            self.calculate_diff(avg)
                            #reset the counters for difficulty
                            self.__timedict["blocks"]= 0 
                            self.__timedict["sum"]= 0.0                     
                        
                        with open("timesum.json", "w") as json_file:# update the json
                            json.dump(self.__timedict, json_file, indent=4)

                        
                        self.calculate_balik(self.__lastb, conn)
                        
                        sock.send(format_data(SAVEDBLOCK + ">" + str(self._diff)).encode())

                        self.__lastb = self.__lastb + 1
                        for session in self._sessionlist:
                            #retransmit the block to all
                            skt=session.getsocket()
                            if session.gettype()==2 and session.getusername()!=user: # to the miners
                                send_to_miner(msg, self._diff,sock, conn)

                            elif session.gettype()==1: # to clients
                                send_block(bl_id, sock, conn)
                            
                            write_to_log(f" Node / sent the block to {session.getusername()}")
                    else:
                        write_to_log(f' Node / Couldnt recieve block from {user}; {bl_id}')

                elif msg.startswith(CHAINUPDATEREQUEST):
                    self.__sendupdatedchain(sock, msg, conn)     

                if msg.startswith(GOOD_TRANS_MSG): # send the confirmation to the client(sender)
                    user_to_send = msg.split(">")[1]    

                    for session in self._sessionlist:
                        #retransmit to the sender
                        us=session.getusername()
                        if(us==user_to_send):
                            session.getsocket().send(format_data(GOOD_TRANS_MSG).encode())
                            write_to_log(f" Node / sent confirmation to: {user_to_send}")
                

            else:
                self._last_error = f"miners {user} socket is wrong "
                write_to_log(" Node / miners {user} socket is wrong")
                return
                            #push the error in gui
    
    
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
                        skt.send(format_data("UPDATED" + ">" + id).encode())
                        return True
                    
                    # if its the only block
                    skt.send(format_data(CHAINUPDATING+f">{len(id_list)}").encode())

                    if send_block(id_list[0][0], skt, conn)==False:  # send the only block
                        s._last_error = " NodeBL / Couldnt update blockhain"
                        write_to_log("Failed to update chain")
                        return False

                    skt.send(format_data("UPDATED" + ">" + str(id_list[0][0])).encode())
                    return True
                
                id_list = id_list[1:]
                skt.send(format_data(CHAINUPDATING+f">{len(id_list)}").encode())

                for b_id in id_list: # send all the blocks the member is missing 
                    
                    if send_block(b_id[0], skt, conn)==False:
                        s._last_error = " NodeBL / Couldnt update blockhain"
                        return False
                    '''
                    skt.settimeout(1.5) # if in 1.5 seconds no answer end raise esception
                    while True:
                        (suc, msg) = receive_buffer(skt)
                        if suc and msg==SAVEDBLOCK+b_id:
                            break
                        elif msg==FAILEDTOSAVEBLOCK:
                            raise Exception
                    '''
                skt.send(format_data("UPDATED" + ">" + str(b_id[0])).encode())
                print("aufff")
                return True
            else: # if sent if is wrong
                print("afffffffffffffs")
                
                skt.send(format_data(WRONGID).encode())
                return False

        except Exception as e:
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
            print(transes)
            if len(transes)==0:
                return True

            for trans in transes:
                cursor.execute(f'''
                UPDATE balances SET amount = amount + {trans[2]} WHERE address='{trans[3]}' AND token = '{trans[5]}'
                ''')

                cursor.execute(f'''
                UPDATE balances SET amount = amount - {trans[4]} WHERE address='{trans[2]}' AND token = '{trans[5]}'
                ''')    
            conn.commit()
            return True
        except Exception as e:
            write_to_log("Failed to calculate balance ; " +e)
            s._last_error = "Failed to calculate balance"
            return False

    def calculate_diff(s, m_time):
        if m_time>300:
            s.__timedict["diff"]-=2
        
        if m_time>90:
            s.__timedict["diff"]-=1
        
        if m_time<40:
            s.__timedict["diff"]+=1
    
    def __on_start(s):
        cursor = s._conn.cursor()
        cursor.execute('''
        SELECT block_id, difficulty FROM blocks ORDER BY block_id DESC LIMIT 1
        ''')
        
        res = cursor.fetchone()
        if res:
            s.__lastb, s._diff= res 
            write_to_log(f"Current block is {s.__lastb}, with the difficulty of {s._diff}")
        

        
        
        
                











    



                
                
                
                
                
            
            

                    


    
    
    
    
    
        

