from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from ClientBL import ClientBL
from protocol import *
from PIL import Image, ImageTk
import PyQt5
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import Qt, QSize
import sys
#  endregion


#  region Constants

DEFAULT_IP: str = "127.0.0.1"

FONT_TITLE: tuple = ("Calibri", 20)
FONT_BUTTON: tuple = ("Calibri", 14)

COLOR_BLACK: str = "#000000"
COLOR_DARK_GRAY: str = "#808080"
COLOR_LIGHT_GRAY: str = "#c0c0c0"

START_IMAGE: str = "Images/start_button.png"
BACKGROUND_IMAGE = "Images/Bliss.png"


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
        
        self._window.setWindowFlags(Qt.FramelessWindowHint)

        self._central_widget = QWidget(self._window)
        self._window.setCentralWidget(self._central_widget)

        self.__setup_images()
        # Disable resize to fit with the background image
        self._window.setGeometry(100, 100, self._back_img_size[0], self._back_img_size[1]+self._start_img_size[1]+30)  # Set window size and position
        self._window.setFixedSize(self._back_img_size[0], self._back_img_size[1]+self._start_img_size[1]+30)
        
        # Now we need to set up the background of our window with
        # our background image

        self._window.setStyleSheet("""
            QWidget {
                background-color: #ece9d8;
                border: 2px solid #000080;
                border-radius: 4px;
            }
            QLabel {
                font: bold 12px;
                color: #000080;
            }
            QPushButton {
                background-color: #ece9d8;
                border: 1px solid #000080;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c0c0c0;
            }
        """)



        
        self._back_label = QLabel(self._window)
        
        pixmap = QPixmap(BACKGROUND_IMAGE)
        
        # Resize the image
        resized_pixmap = pixmap.scaled(self._back_img_size[0], self._back_img_size[1], Qt.KeepAspectRatio)
        self._back_label.setPixmap(resized_pixmap)
        self._back_label.setAlignment(Qt.AlignCenter)
        
        self._back_label.setGeometry(0,30,self._back_img_size[0], self._back_img_size[1])
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
        
        self._start_button = QPushButton(self._central_widget)
        self._start_button.setIcon(self._start_icon)  # Set icon size to default button size
        self._start_button.setGeometry(2, self._back_img_size[1]+28, self._start_img_size[0], self._start_img_size[1])  # Set button position and size
        self._start_button.setIconSize(QSize(self._start_img_size[0],self._start_img_size[1]))
        

        self.title_bar = QWidget(self._central_widget)
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("background-color: #000080;")

        # Title bar layout
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)

        # Title label
        self.title_label = QLabel("My XP-Style App")
        self.title_label.setStyleSheet("color: white; font: bold 14px;")
        title_layout.addWidget(self.title_label)

        # Minimize button
        self.minimize_button = QPushButton("─")
        self.minimize_button.setFixedSize(25, 25)
        self.minimize_button.setStyleSheet("color: white")
        title_layout.addWidget(self.minimize_button)

        self.maximize_button = QPushButton("□")
        self.maximize_button.setStyleSheet("color: white")
        self.maximize_button.setFixedSize(25, 25)
        title_layout.addWidget(self.maximize_button)

        # Close button
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(25, 25)
        self.close_button.setStyleSheet("color: white")
        title_layout.addWidget(self.close_button)

        # Main layout
        main_layout = QVBoxLayout(self._central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        main_layout.setSpacing(0)

        main_layout.addWidget(self.title_bar)
        main_layout.addStretch()

















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
    

        