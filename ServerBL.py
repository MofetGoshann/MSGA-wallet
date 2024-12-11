from select import select
import threading
from protocol import *

class Session: #session class
    def __init__(self, ip:str, port: str, sock: socket):
        self.__type = None
        self.__ip = ip
        self.__port = port
        self.__username = None
        self.__socket = None
    
    
    def connectupdate(self, username:str, type:int):
        self.__type = type
        self.__username = username
    
    def gettype(self):
        return self.__type
    
    def getsocket(self):
        return self.__socket
    
    def getusername(self):
        return self.__username


class CServerBL:
    def __init__(self, ip: str, port: int, receive_callback, cltable_callback):

        self.__ip: str = ip

        self._clientstablecallback = cltable_callback
        
        
        self._sessionlist: Session = {}
        self._server_socket: socket = None
        self.__server_running_flag: bool = False

        self._client_list: dict = {}
        self._minerlist: dict = {}
        self._receive_callback = receive_callback
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
                    # Start a new thread for a new client
                    firstmessage: str = receive_buffer(connected_socket)

                    typeuser = firstmessage.split('>')
                    connectedsession.connectupdate(typeuser[0], typeuser[1])
                        
                    if connectedsession.gettype()==1:
                        new_client_thread = threading.Thread(target=self.__handle_client, args=(connectedsession))
                        new_client_thread.start()
                    
                    if connectedsession.gettype()==2:
                        new_miner_thread = threading.Thread(target=self.__handle_miner, args=(connectedsession))
                        new_miner_thread.start()

                    

                    write_to_log(f"  Server    · active connection {threading.active_count() - 2}")

            # Close server socket on server end
            self._server_socket.close()
            write_to_log("  Server    · closed")

            # Everything went without any problems
            self._server_socket = None

            return True

        except Exception as e:

            # Handle failure
            write_to_log(f"  Server    · failed to set up server {e}")

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



    def __handle_client(self, client_session: Session):
        
        user = client_session.getusername()
        sock = client_session.getsocket()
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

                self._mutex.acquire()
                try:
                    if self._receive_callback is not None:
                        if not msg.startswith("LOGIN"):
                            self._receive_callback(f"{user} - {msg}")    
                        else:
                            self._receive_callback(f"{user} - LOGIN > Username, Password")

                except Exception as e:
                    write_to_log(f"  Server    · some error occurred : {e}")
                finally:
                    self._mutex.release()

                # Parse from buffer
                #cmd, args = convert_data(msg)

                # If the client wants to disconnect
                if msg == DISCONNECT_MSG:
                    connected = False
                else:
                    write_to_log(f"  Server    · client sent a transaction :  -{msg} ")
                    
                    for session in self._sessionlist:
                        
                        if(session.gettype==2):
                            #retransmit the transacion to the miners
                            session.getsocket().send(format_data(msg).encode())
                    
    
    def __handle_miner(self, miner_session: Session):
        
        user = miner_session.getusername()
        sock = miner_session.getsocket()
        
        write_to_log(f"  Server   new client : {user} connected")
        
        connected = True
        
        while connected:
            
            (success,  msg) = receive_buffer(sock)

            if success:
                # if we managed to get the message :
                write_to_log(f"  Server    · received from miner : {user} - {msg}")    
                
                
                
                
                
            
            

                    


    
    
    
    
    
        

