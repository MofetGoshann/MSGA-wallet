from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from ClientBL import ClientBL
from protocol import *
from PIL import Image, ImageTk
import PyQt5
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import Qt
import sys
#  endregion


#  region Constants

DEFAULT_IP: str = "127.0.0.1"

FONT_TITLE: tuple = ("Calibri", 20)
FONT_BUTTON: tuple = ("Calibri", 14)

COLOR_BLACK: str = "#000000"
COLOR_DARK_GRAY: str = "#808080"
COLOR_LIGHT_GRAY: str = "#c0c0c0"

START_IMAGE: str = "C:/Users/User/Documents/MSGA-wallet-main/Images/start_button.png"
BACKGROUND_IMAGE = "C:/Users/User/Documents/MSGA-wallet-main/Images/Bliss.png"


class ClientGUI:

    def __init__(self):
        self._client = None

        self._window = None
        self._login_obj = None

        self._back_img = None
        self._start_img = None

        self._back_img_size = [0, 0]
        self._btn_img_size = [0, 0]

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
        
        self._app = QApplication([])
        self._window = QMainWindow()

        self._window.setWindowTitle("MSGA Wallet")
        

        self.__setup_images()
        # Disable resize to fit with the background image
        self._window.setGeometry(100, 100, self._back_img_size[0], self._back_img_size[1]+30)  # Set window size and position
        self._window.setFixedSize(self._back_img_size[0], self._back_img_size[1]+30)
        
        # Now we need to set up the background of our window with
        # our background image

        self._back_label = QLabel(self._window)
        
        pixmap = QPixmap(BACKGROUND_IMAGE)
        
        # Resize the image
        resized_pixmap = pixmap.scaled(self._back_img_size[0], self._back_img_size[1], Qt.KeepAspectRatio)
        self._back_label.setPixmap(resized_pixmap)
        self._back_label.setAlignment(Qt.AlignCenter)
        
        self._back_label.setGeometry(0,0,self._back_img_size[0], self._back_img_size[1])
        # In-Application title

        # Create the ui elements
        self.__create_elements()
    

    def __setup_images(self):
        """
        Setup client gui images and save their data
        """
        # Load images
        self._back_img:QImage = QImage(BACKGROUND_IMAGE)
        self._start_img = QImage(START_IMAGE)
        
        
        self._start_icon = QIcon(START_IMAGE)

        # Save their vectors
        self._back_img_size = [int(self._back_img.width()/2.5), int(self._back_img.height()/2.5)]
        self._start_img_size = [self._start_img.width(), self._start_img.height()]
        
        #self._btn_img_size = [self._btn_img.width(), self._btn_img.height()]

    def __create_elements(self):
        """
        Create the ui elements in the window
        """

        # Buttons
        
        # Start 
        
        self._start_button = QPushButton(self._window)
        self._start_button.setIcon()  # Set icon size to default button size
        self._start_button.setGeometry(0, 560, self._start_img_size[0], self._start_img_size[1])  # Set button position and size
        
        # Connect


        # Send data

    
    def draw(s):
        s._window.show()
        sys.exit(s._app.exec_())
    
    
    def __connect_event(self):


        try:
            # Handle failure on casting from string to int

            self._client: ClientBL= ClientBL(DEFAULT_IP ,13333, "qwe", "zxc")

            # check if we successfully created socket
            # and ready to go
            if not self._client.get_success():
                raise Exception("failed to create and setup client bl")
            else:

                # Handle gui elements

                self._connect_button.config(state="disabled")
                self._send_button.config(state="normal")
                

        except Exception as e:
            # If our problem occurred before the client
            # mean that our client will be None
            error = self._client and self._client.get_last_error() or e

            write_to_log(f" 路 Client GUI 路 an error has occurred : {error}")
            messagebox.showerror("Error on Connect", error)
    
    def __send_data_event(self):
        self._client.send_transaction("SNC", 14.88, "qwe")

def main():
    n = ClientGUI()
    n.draw()

if __name__ == "__main__":
    main()
    

        