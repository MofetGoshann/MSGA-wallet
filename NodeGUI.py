
from tkinter import *
from protocol import *
from tkinter import messagebox

from NodeBL import *
import threading


FONT_TITLE: tuple = ("Calibri", 20)
FONT_BUTTON: tuple = ("Calibri", 14)

COLOR_BLACK: str = "#000000"
COLOR_DARK_GRAY: str = "#808080"
COLOR_LIGHT_GRAY: str = "#c0c0c0"





class NodeGUI:
    def __init__(self):
        self._node = None  # node_node bl obj

        self._window = None

        self._back_img = None
        self._btn_img = None

        self._back_canvas = None

        # UI
        self._start_button = None
        self._stop_button = None
        self._kick_button = None
        self._ip_entry = None
        self._port_entry = None
        self._receive_field = None
        self._table = None

        
        self._back_img_size = [500, 400]
        self._btn_img_size = [100, 10]        
        self.__setup_window()
        
    def __setup_window(self):
        self._window = Tk()

        self._window.title("Node GUI")

        self._window.resizable(True, True)

        self._window.geometry(f"{self._back_img_size[0]}x{self._back_img_size[1]}")

        # Now we need to set up the background of our window with
        # our background image
        self._back_canvas = Canvas(self._window, width=self._back_img_size[0], height=self._back_img_size[1])
        self._back_canvas.pack(fill='both', expand=True)
        #self._back_canvas.create_image(0, 0, anchor="nw", image=self._back_img)

        # In-Application title
        self._back_canvas.create_text(20, 30, text="Node", font=FONT_TITLE, fill=COLOR_DARK_GRAY, anchor="nw")

        self.__create_elements()
    
    def __create_elements(self):
        """
        Create the ui elements in the window
        """

        # Buttons
        self._start_button = Button(self._back_canvas,
                                    text="Start", command=self.__start_event,
                                    width=40, height=20,
                                    background="grey"
                                    )
        
        self._start_button.place(x=100, y=40)
        self._window.mainloop()

    def __start_event(self):
        """Start the node_node, create a node_node bl object, handle gui elements"""

        self._start_button.config(state="disabled")
        
        ip = DEFAULT_IP
        port = DEFAULT_PORT

        self._node = NodeBL(ip, port)
        
        if self._node:
            if self._node.get_success():
                node_node_handle_thread = threading.Thread(target=self._node.Node_process)
                node_node_handle_thread.start()
            else:
                messagebox.showerror("Error on Start", self._node.get_last_error())
n = NodeGUI()
        


