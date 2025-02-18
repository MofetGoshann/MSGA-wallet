from select import select
import threading
from protocol import *
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
        self._server_socket: socket = None
        self.__server_running_flag: bool = False
        self._receive_callback = None
        self._mutex = threading.Lock()

        with open('LogFile.log', 'w'):
            pass

        self._last_error = ""
        self._success = self.__start_server(ip, port)
        
    def __start_server(self, ip: str, port: int) -> bool:

        write_to_log("  Server    · starting")

        try:
            # Create and connect socket
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.bind((ip, port))



            # Return on success
            return True

        except Exception as e:

            # Handle failure
            self._server_socket = None
            write_to_log(f"  Server    · failed to start up sever : {e}")

            self._last_error = f"An error occurred in server bl [start_server function]\nError : {e}"

            return False
    
    
    def server_process(self) -> bool:

        try:
            self.__server_running_flag = True

            self._server_socket.listen()  # listen for clients

            write_to_log(f"  Server    · listening on {self.__ip}")

            while self.__server_running_flag:

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

                    

                    write_to_log(f"  Server    · active connection {threading.active_count() - 2}")

            # Close server socket on server end
            self._server_socket.close()
            write_to_log("  Server    · closed")

            # Everything went without any problems
            self._server_socket = None

            return True

        except Exception as e:

            # Handle failure
            write_to_log(f"  Server    · failed to handle a message; {e}")

            self._last_error = f"An error occurred in server bl [server_process function]\nError : {e}"

            return False
    
    
    def __time_accept(self, time: int):
    

        try:
            self._server_socket.settimeout(time)

            ready, _, _ = select([self._server_socket], [], [], time)

            if ready:
                return self._server_socket.accept()

            return None, None
        except Exception as e:
            return None, None



    def __handle_client(self, clientsession: Session):
        
        user = clientsession.getusername()
        sock = clientsession.getsocket()

        # This code run in separate for every client
        write_to_log(f"  Server   new client : {user} connected")
        

        #if self._clientstablecallback is not None: # insert client to gui table
        #    self._clientstablecallback(client_addr[0], client_addr[1], True, False)
        
        connected = True

        while connected:
            # Get message from  client
            (success,  msg) = receive_buffer(sock)

            if success:
                # if we managed to get the message :
                write_to_log(f"  Server    · received from client : {user} - {msg}")

                #self._mutex.acquire()
                #try:
                #    if self._receive_callback is not None:
                #        if not msg.startswith("LOGIN"):
                #            self._receive_callback(f"{user} - {msg}")    
                #        else:
                #            self._receive_callback(f"{user} - LOGIN > Username, Password")

                #except Exception as e:
                #    write_to_log(f"  Server    · some error occurred : {e}")
                #finally:
                #    self._mutex.release()
                    
                # If the client wants to disconnect
                if msg == DISCONNECT_MSG:
                    connected = False
                    self._sessionlist.remove(clientsession) # remove the client from session list
                
                if msg.startswith(TRANS):
                    # the msg is transaction
                    suc, ermsg = verify_transaction(msg[1])
                    if suc==False:
                        sock.send(format_data(ermsg).encode())

                    for session in self._sessionlist:
                        if(session.gettype()==2):
                            #retransmit the transacion to the miners
                            session.getsocket().send(format_data(msg).encode())
                    
    
    def __handle_miner(self, miner_session: Session):
        
        user = miner_session.getusername()
        sock = miner_session.getsocket()

        write_to_log(f"  Server   new miner : {user} connected")
        
        connected = True

        while connected:
            
            (success,  msg) = receive_buffer(sock)

            if success :

                #if miner_session.getu()==False:
                #    write_to_log("Not ")
                #    raise Exception


                # if we managed to get the message :
                write_to_log(f"  Server    · received from miner : {user} - {msg}")    

                if msg.startswith(MINEDBLOCKSENDMSG): # if miner is sending a block
                    (suc,  bl_id) =  recieve_block(msg, "Node", sock)
                    if suc: # if recieved block successfully
                        for session in self._sessionlist:
                            #retransmit the block to all
                            skt=session.getsocket()
                            send_block(bl_id, skt, "Node")
                            write_to_log(f" Server / sent the block to {session.getusername()}")
                    else:
                        miner_session.setu(False)

                elif msg==CHAINUPDATEREQUEST:
                    self.__sendupdatedchain(sock, msg)             
                

            else:
                self._last_error = f"clients {session.getusername()} socket is wrong "
                write_to_log(" Server / ")
                            #push the error in gui
    
    
    
    def __sendupdatedchain(s, skt: socket, msg: str):
        '''
        updates a connected members blockchain from the block id
        returns True if sent everything and the member saved it 
        False if not
        '''
        id = msg.split(">")[1]

        conn = sqlite3.connect(f"databases/Node/blockchain.db") # client/node/miner
        cursor = conn.cursor()
        try:
            cursor.execute(f'''
            SELECT block_id FROM blocks WHERE block_id > {id-1} 
            ''')
            id_list = cursor.fetchall() # get all the blocks needed to send

            if id_list: # if valid 
                skt.send(format_data(CHAINUPDATING+f">{len(id_list)}").encode())
                
                for b_id in id_list: # send all the blocks the member is missing 
                    
                    send_block(b_id, skt, conn) 
                    '''
                    skt.settimeout(1.5) # if in 1.5 seconds no answer end raise esception
                    while True:
                        (suc, msg) = receive_buffer(skt)
                        if suc and msg==SAVEDBLOCK+b_id:
                            break
                        elif msg==FAILEDTOSAVEBLOCK:
                            raise Exception
                    '''
                return True
            else: # if sent if is wrong
                skt.send(format_data(WRONGID).encode())
                return False

        except Exception as e:
            write_to_log(" NodeBL / failed to update blockchain")
            s._last_error = "Failed to update blockchain"
            return False
                    


    
    def _send_block(s, id:int, skt:socket):
        send_block(id, skt, "Node")
        
    def get_success(s):
        return s._success
    
    def get_last_error(s):
        return s._last_error
    
    def calculate_balik(s, b_id: int):
        conn = sqlite3.connect(f"databases/Node/blockchain.db") # client/node/miner
        cursor = conn.cursor()
        try:
            cursor.execute(f'''
            SELECT sender, reciever, amount, token FROM transactions WHERE block_id={b_id}
            ''')

            transes = cursor.fetchall()

            for trans in transes:
                cursor.execute(f'''
                UPDATE balances SET amount = amount + {trans[2]} WHERE address={trans[1]}
                ''')

                cursor.execute(f'''
                UPDATE balances SET amount = amount - {trans[2]} WHERE address={trans[0]}
                ''')    
        
            return True
        except Exception as e:
            write_to_log("Failed to calculate balance ; " +e)
            s._last_error = "Failed to calculate balance"
            return False

                











    



                
                
                
                
                
            
            

                    


    
    
    
    
    
        

