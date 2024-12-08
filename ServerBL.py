from select import select
import threading
from protocol import *

class CServerBL:
    def __init__(self, ip: str, port: int, receive_callback):

        self.__ip: str = ip


        self._session_list = {}

        self._server_socket: socket = None
        self.__server_running_flag: bool = False

        self._clint_list: list = {}

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
                client_socket, client_addr = self.__time_accept(0.3)

                # Check if we didn't time out
                if client_socket:

                    self.__update_client_list(client_addr, client_socket)
                    # Start a new thread for a new client
                    

                    new_client_thread = threading.Thread(target=self.__handle_client, args=(client_socket, client_addr))
                    new_client_thread.start()

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


    def __handle_client(self, client_socket, client_addr):

        # This code run in separate for every client
        write_to_log(f"  Server    · new connection : {client_addr} connected")
        


        if self._clientstablecallback is not None: # insert client to gui table
            self._clientstablecallback(client_addr[0], client_addr[1], True, False)
        
        connected = True

        while connected:

            # Get message from  client
            (success,  msg) = receive_buffer(client_socket)

            if success:
                # if we managed to get the message :
                write_to_log(f"  Server    · received from client : {client_addr} - {msg}")

                self._mutex.acquire()
                try:
                    if self._receive_callback is not None:
                        if not msg.startswith("LOGIN"):
                            self._receive_callback(f"{client_addr} - {msg}")
                        else:
                            self._receive_callback(f"{client_addr} - LOGIN > Username, Password")

                except Exception as e:
                    write_to_log(f"  Server    · some error occurred : {e}")
                finally:
                    self._mutex.release()

                # Parse from buffer
                cmd, args = convert_data(msg)

                # If the client wants to disconnect
                if cmd == DISCONNECT_MSG:
                    connected = False
                else:
                    write_to_log(f"  Server    · client requested : {cmd} - {args}")

                    type_cmd = check_cmd(cmd)

                    if type_cmd == 2:
                        # Protocol 2.7

                        return_msg = self.__protocol_27.create_response(cmd, args, client_socket)

                        if return_msg[4:] == LOG_MSG:
                            self._clientstablecallback(client_addr[0], client_addr[1], False, False) # remove client not logged in
                            self._clientstablecallback(client_addr[0], client_addr[1], True, True) # insert client that ist shows that it changed

                        if cmd != "SEND_PHOTO":
                            # We don't want to send something while sending photo
                            # It will interrupt the data

                            write_to_log(f"  Server    · send to client : {return_msg}")

                            # Send the response
                            client_socket.send(return_msg.encode(FORMAT))

                    else:
                        #Protocol 2.6
                        return_msg = self.__protocol_26.create_response(cmd)

                        write_to_log(f"  Server    · send to client : {return_msg}")

                        # Send the response
                        client_socket.send(return_msg.encode(FORMAT))

        # Close client socket and delete client from list
                        
        self.__delete_client(client_addr)

        if self._clientstablecallback is not None: # Remove the client from the gui table
            self._clientstablecallback(client_addr[0], client_addr[1], False, False) 
        
        client_socket.close()
        write_to_log(f"  Server    · closed client {client_addr}")