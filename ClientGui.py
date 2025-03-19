from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from ClientBL import ClientBL
from protocol import *
from PIL import Image, ImageTk
import PyQt5
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import Qt, QSize, QPoint
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
class DraggableTitleBar(QLabel):
    
    def __init__(s, parent=None):
        super().__init__(parent)
        s.setMouseTracking(True)
        s.dragging = False
        s.offset = QPoint()

    def mousePressEvent(s, event):
        """Start dragging when the left mouse button is pressed."""
        if event.button() == Qt.LeftButton:
            s.dragging = True
            s.offset = event.globalPos() - s.window().pos()  # Calculate offset
        super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(s, event):
        """Move the entire window when dragging."""
        if s.dragging:
            s.window().move(event.globalPos() - s.offset)  # Move the parent window
        super().mouseMoveEvent(event)
        event.accept()

    def mouseReleaseEvent(s, event):
        """Stop dragging when the left mouse button is released."""
        s.dragging = False

class DesktopShortcut(QWidget):
    def __init__(self, icon_path, app_name, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.app_name = app_name
        self.initUI()

    def initUI(self):
        # Create a vertical layout
        layout = QVBoxLayout()

        # Create a button with an icon
        self.button = QPushButton(self)
        self.button.setIcon(QIcon(self.icon_path))
        self.button.setIconSize(QSize(48, 48))  # Set icon size
        self.button.setFixedSize(64, 64)  # Set button size
        self.button.setStyleSheet("""
            QPushButton {
                border: 1px solid transparent;
                background-color: transparent;
            }
            QPushButton:hover {
                border: 1px solid #0078d7;
                background-color: rgba(0, 120, 215, 0.1);
            }
            QPushButton:pressed {
                border: 1px solid #005499;
                background-color: rgba(0, 84, 153, 0.2);
            }
        """)

        # Create a label for the app name
        self.label = QLabel(self.app_name, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-family: "Tahoma";
            }
        """)

        # Add the button and label to the layout
        layout.addWidget(self.button, 0, Qt.AlignCenter)
        layout.addWidget(self.label, 0, Qt.AlignCenter)

        # Set the layout to the widget
        self.setLayout(layout)

        # Set the widget background to transparent
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)

    def mousePressEvent(self, event):
        # Emit a signal or perform an action when the shortcut is clicked
        print(f"{self.app_name} shortcut clicked!")

class ClientGUI:

    def __init__(s):
        s._client = None

        s._window = None
        s._login_obj = None

        s._back_img = None
        s._start_img = None

        s._back_img_size = [0, 0]
        s._btn_img_size = [0, 0]

        s._back_canvas = None

        # UI
        s._connect_button = None
        s._disconnect_button = None
        s._send_button = None
        s._login_button = None

        s._ip_entry = None
        s._port_entry = None
        s._cmd_entry = None
        s._args_entry = None

        s._receive_field = None

        s.__setup_window()

    def __setup_window(s):
        
        s._app = QApplication([])
        s._window = QMainWindow()

        s._window.setWindowTitle("MSGA Wallet")
        
        s._window.setWindowFlags(Qt.FramelessWindowHint)

        s._central_widget = QWidget(s._window)
        s._window.setCentralWidget(s._central_widget)

        s.__setup_images()
        # Disable resize to fit with the background image
        s._window.setGeometry(150, 50, s._back_img_size[0], s._back_img_size[1]+s._start_img_size[1]+28)  # Set window size and position
        #s._window.setFixedSize(s._back_img_size[0], s._back_img_size[1]+s._start_img_size[1]+30)
        
        # Now we need to set up the background of our window with
        # our background image

        s._window.setStyleSheet("""
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
            QMainWindow {
                background-color: #ece9d8;
                border: 4px solid #000080;
                border-radius: 8px;                
            }
        """)



        
        s._back_label = QLabel(s._central_widget)
        
        pixmap = QPixmap(BACKGROUND_IMAGE)
        
        # Resize the image
        resized_pixmap = pixmap.scaled(s._back_img_size[0], s._back_img_size[1], Qt.KeepAspectRatio)
        s._back_label.setPixmap(resized_pixmap)
        s._back_label.setAlignment(Qt.AlignCenter)
        
        s._back_label.setGeometry(0,30,s._back_img_size[0], s._back_img_size[1])
        # In-Application title
        
        # Create the ui elements
        s.__create_elements()
    

    def __setup_images(s):
        """
        Setup client gui images and save their data
        """
        # Load images
        s._back_img:QImage = QImage(BACKGROUND_IMAGE)
        s._start_img = QImage(START_IMAGE)
        
        
        s._start_icon = QIcon(START_IMAGE)

        # Save their vectors
        s._back_img_size = [int(s._back_img.width()/2.5), int(s._back_img.height()/2.5)]
        s._start_img_size = [s._start_img.width(), s._start_img.height()]
        
        #s._btn_img_size = [s._btn_img.width(), s._btn_img.height()]

    def __create_elements(s):
        """
        Create the ui elements in the window
        """

        # Buttons
        
        # Start 
        
        s._start_button = QPushButton(s._central_widget)
        s._start_button.setIcon(s._start_icon)  # Set icon size to default button size
        s._start_button.setGeometry(2, s._back_img_size[1]+28, s._start_img_size[0], s._start_img_size[1])  # Set button position and size
        s._start_button.setIconSize(QSize(s._start_img_size[0],s._start_img_size[1]))
        s._start_button.setStyleSheet("background-color: transparent; border:none;")
        
        s._taskbar = QLabel(s._central_widget)
        s._taskbar.setStyleSheet("background-color: #003580; border:none")
        
        s._task_layout = QHBoxLayout(s._taskbar)
        s._task_layout.setContentsMargins(5, 0, 5, 0)
        
        s.title_bar = DraggableTitleBar(s._central_widget)
        s.title_bar.setStyleSheet("background-color: #000080; border-radius: 2 2 0 0")
        

        # Title bar layout
        title_layout = QHBoxLayout(s.title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)

        # Title label
        s.title_label = QLabel("My XP-Style App")
        s.title_label.setStyleSheet("color: white; font: bold 14px;")
        title_layout.addWidget(s.title_label)
        

        # Minimize button
        s.minimize_button = QPushButton("─")
        s.minimize_button.setFixedSize(25, 25)
        s.minimize_button.setStyleSheet("color: white")
        s.minimize_button.clicked.connect(s.__minimize)
        title_layout.addWidget(s.minimize_button)

        s.maximize_button = QPushButton("□")
        s.maximize_button.setStyleSheet("color: white")
        s.maximize_button.setFixedSize(25, 25)
        s.maximize_button.clicked.connect(s.__maximize)
        title_layout.addWidget(s.maximize_button)

        # Close button
        s.close_button = QPushButton("✕")
        s.close_button.setFixedSize(25, 25)
        s.close_button.setStyleSheet("color: white")
        s.close_button.clicked.connect(s.__close_main)
        title_layout.addWidget(s.close_button)
        
        s.title_bar.setGeometry(0,0,s._back_img_size[0],30)
        s.title_bar.raise_()
        s._taskbar.setGeometry(0,s._back_img_size[1]+28,s._back_img_size[0],s._start_img_size[1])

        s._start_button.raise_()
        
        s._login_cut = DesktopShortcut("")
        # Main layout
        #main_layout = QVBoxLayout(s._central_widget)
        #main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        #main_layout.setSpacing(0)

        #main_layout.addWidget(s.title_bar)
        
        #main_layout.addWidget(s._taskbar)
        #main_layout.addStretch()

















        # Connect


        # Send data

    def __minimize(s):
        s._window.showMinimized()
    
    def __maximize(s):
        if s._window.isMaximized():
            s._window.showNormal()  # Restore to normal size

        else:
            s._window.showMaximized()  # Maximize the window

    
    def __close_main(s):
        s._window.close()
    
    def draw(s):
        s._window.show()
        sys.exit(s._app.exec_())
    
    
    def __connect_event(s):


        try:
            # Handle failure on casting from string to int

            s._client: ClientBL= ClientBL(DEFAULT_IP ,13333, "qwe", "zxc")

            # check if we successfully created socket
            # and ready to go
            if not s._client.get_success():
                raise Exception("failed to create and setup client bl")
            else:

                # Handle gui elements

                s._connect_button.config(state="disabled")
                s._send_button.config(state="normal")
                

        except Exception as e:
            # If our problem occurred before the client
            # mean that our client will be None
            error = s._client and s._client.get_last_error() or e

            write_to_log(f" 路 Client GUI 路 an error has occurred : {error}")
            messagebox.showerror("Error on Connect", error)
    
    def __send_data_event(s):
        s._client.send_transaction("SNC", 14.88, "qwe")

def main():
    n = ClientGUI()
    n.draw()



if __name__ == "__main__":
    main()
    

        