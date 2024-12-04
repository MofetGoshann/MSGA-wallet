from protocol import *
import threading





class CServerBL:
    def __init__(self, ip: str, port: int, receive_callback, cltable_callback):

        self.__ip: str = ip

        self._clientstablecallback = cltable_callback

        self._server_socket: socket = None
        self.__server_running_flag: bool = False

        self._clint_list: list = {}

        self._receive_callback = receive_callback
        self._mutex = threading.Lock()

        with open('LogFile.log', 'w'):
            pass

        self._last_error = ""
        self._success = self.__start_server(ip, port)