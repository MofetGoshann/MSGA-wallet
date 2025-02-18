from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from MinerBL import Miner
from protocol import *
#  endregion


#  region Constants

DEFAULT_IP: str = "127.0.0.1"

FONT_TITLE: tuple = ("Calibri", 20)
FONT_BUTTON: tuple = ("Calibri", 14)

COLOR_BLACK: str = "#000000"
COLOR_DARK_GRAY: str = "#808080"
COLOR_LIGHT_GRAY: str = "#c0c0c0"

BUTTON_IMAGE: str = "Images\\gui_button.png"
BACKGROUND_IMAGE: str = "Images\\gui_bg_small.png"


class MinerGUI:

    def __init__(self):
        self._miner = None

        self._window = None
        self._login_obj = None

        self._back_img = None
        self._btn_img = None

        self._back_img_size = [1000, 500]
        self._btn_img_size = [100, 40]

        self._back_canvas = None

        # UI
        self._connect_button = None
        self._disconnect_button = None
        self._send_button = None
        self._login_button = None

        self._ip_entry = None
        self._port_entry = None
        self._cmd_entry = None
        self._args_entry = None

        self._receive_field = None

        self.__setup_window()

    def __setup_window(self):

        self._window = Tk()

        self._window.title("Client GUI")

        # Disable resize to fit with the background image
        self._window.resizable(False, False)
        self._window.geometry(f"{self._back_img_size[0]}x{self._back_img_size[1]}")

        # Now we need to set up the background of our window with
        # our background image
        self._back_canvas = Canvas(self._window, width=self._back_img_size[0], height=self._back_img_size[1])
        self._back_canvas.pack(fill='both', expand=True)

        # In-Application title
        self._back_canvas.create_text(20, 30, text="Miner", font=FONT_TITLE, fill=COLOR_DARK_GRAY, anchor="nw")

        # Create the ui elements
        self.__create_elements()
    

    def __create_elements(self):
        """
        Create the ui elements in the window
        """

        # Buttons
        # Connect
        self._connect_button = Button(self._back_canvas,
                                      text="Connect",  command=self.__connect_event,
                                      )
        self._connect_button.place(x=100, y=50)

        # Send data

    
    def draw(s):
        s._window.mainloop()
    
    
    def __connect_event(self):


        try:
            # Handle failure on casting from string to int

            self._miner: Miner= Miner(DEFAULT_IP ,13333, "asd")

            # check if we successfully created socket
            # and ready to go

            self._connect_button.config(state="disabled")
                

        except Exception as e:
            # If our problem occurred before the client
            # mean that our client will be None
            error = self._miner and self._miner.get_last_error() or e

            write_to_log(f" 路 Client GUI 路 an error has occurred : {error}")
            messagebox.showerror("Error on Connect", error)
    

def main():
    n = MinerGUI()
    n.draw()

if __name__ == "__main__":
    main()