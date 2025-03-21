from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from ClientBL import ClientBL
from protocol import *
from Client_protocol import *
from PIL import Image, ImageTk
import PyQt5
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit
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
LOGIN_ICON = "Images/login.png"
REG_ICON = "Images/register.png"


class DraggableTitleBar(QLabel):
    
    def __init__(s, app_name:str,parent=None):
        super().__init__(parent)
        s.setMouseTracking(True)
        s.dragging = False
        s.offset = QPoint()

        title_login_layout = QHBoxLayout(s)
        title_login_layout.setContentsMargins(5, 0, 5, 0)

        # Title label
        s.title_label = QLabel(app_name)
        s.title_label.setStyleSheet("color: white; font: bold 14px;")
        title_login_layout.addWidget(s.title_label)
        

        # Minimize button
        s.minimize_button = QPushButton("─")
        s.minimize_button.setFixedSize(25, 25)
        s.minimize_button.setStyleSheet("color: white")
        s.minimize_button.clicked.connect(s.__minimize)
        title_login_layout.addWidget(s.minimize_button)
        # Maximize button
        s.maximize_button = QPushButton("□")
        s.maximize_button.setStyleSheet("color: white")
        s.maximize_button.setFixedSize(25, 25)
        s.maximize_button.clicked.connect(s.__maximize)
        title_login_layout.addWidget(s.maximize_button)

        # Close button
        s.close_button = QPushButton("✕")
        s.close_button.setFixedSize(25, 25)
        s.close_button.setStyleSheet("color: white")
        s.close_button.clicked.connect(s.__close_main)
        title_login_layout.addWidget(s.close_button)

    def mousePressEvent(s, event):
        """Start dragging when the left mouse button is pressed."""
        if event.button() == Qt.LeftButton:
            s.dragging = True
            s.offset = event.globalPos() - s.parent().pos()  # Calculate offset
        super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(s, event):
        """Move the entire window when dragging."""
        if s.dragging:
            s.parent().move(event.globalPos() - s.offset)  # Move the parent window
        super().mouseMoveEvent(event)
        event.accept()

    def mouseReleaseEvent(s, event):
        """Stop dragging when the left mouse button is released."""
        s.dragging = False

    
    def __minimize(s):
        s.parent().showMinimized()
    
    def __maximize(s):
        if s.parent().isMaximized():
            s.parent().showNormal()  # Restore to normal size

        else:
            s.parent().showMaximized()  # Maximize the window

    
    def __close_main(s):
        s.parent().close()


class DesktopShortcut(QWidget):
    def __init__(self, icon_path, app_name, on_clickback, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.app_name = app_name
        self.callback = on_clickback
        self.initUI()

    def initUI(self):
        # Create a vertical layout
        self.setStyleSheet("""
            QWidget {
                border: 1px solid transparent;
                background-color: transparent;
            }
            QWidget:hover {
                border: 1px solid #0078d7;
                background-color: rgba(0, 120, 215, 0.1);
            }
            QWidget:pressed {
                border: 1px solid #005499;
                background-color: rgba(0, 84, 153, 0.2);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2,2,2,2)
        
        # Create a button with an icon
        self.button = QPushButton(self)
        self.button.setIcon(QIcon(self.icon_path))
        self.button.setIconSize(QSize(48, 48))  # Set icon size
        self.button.setFixedSize(48, 48)  # Set button size
        """
        self.button.setStyleSheet(
            QPushButton {
                border: 1px solid transparent;
                background-color: transparent;
            }

            QPushButton:pressed {
                border: 1px solid #005499;
                background-color: rgba(0, 84, 153, 0.3);
            }
            )
        """

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

    def enterEvent(self, event):
        # Change the background color when the mouse enters the widget
        self.setStyleSheet("""
            QWidget {
                border: 1px solid #0078d7;
                border-radius: 2px;
                padding: 2px;
                background-color: rgba(0, 120, 215, 0.2);
            }
        """)

    def leaveEvent(self, event):
        # Reset the background color when the mouse leaves the widget
        self.setStyleSheet("""
            QWidget {
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 2px;
                background-color: transparent;
            }
        """)
    def mousePressEvent(self, event):
        # open th needed window when the shortcut is clicked
        self.callback()

        

class ClientGUI:

    def __init__(s):
        s._client = None
        s._login_layout = None
        s._window = None
        s._login_window = None
        s._login_window = None
        s._back_img = None
        s._start_img = None

        s._back_img_size = [0, 0]
        s._btn_img_size = [0, 0]


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
        s._window.setAttribute(Qt.WA_TranslucentBackground)
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
        
        s._task_login_layout = QHBoxLayout(s._taskbar)
        s._task_login_layout.setContentsMargins(5, 0, 5, 0)
        
        s.title_bar = DraggableTitleBar("XP Wallet", s._window)
        s.title_bar.setStyleSheet("background-color: #000080; border-radius: 2 2 0 0")
        
        '''
        # Title bar layout
        title_login_layout = QHBoxLayout(s.title_bar)
        title_login_layout.setContentsMargins(5, 0, 5, 0)

        # Title label
        s.title_label = QLabel("My XP-Style App")
        s.title_label.setStyleSheet("color: white; font: bold 14px;")
        title_login_layout.addWidget(s.title_label)
        

        # Minimize button
        s.minimize_button = QPushButton("─")
        s.minimize_button.setFixedSize(25, 25)
        s.minimize_button.setStyleSheet("color: white")
        s.minimize_button.clicked.connect(s.__minimize)
        title_login_layout.addWidget(s.minimize_button)

        s.maximize_button = QPushButton("□")
        s.maximize_button.setStyleSheet("color: white")
        s.maximize_button.setFixedSize(25, 25)
        s.maximize_button.clicked.connect(s.__maximize)
        title_login_layout.addWidget(s.maximize_button)

        # Close button
        s.close_button = QPushButton("✕")
        s.close_button.setFixedSize(25, 25)
        s.close_button.setStyleSheet("color: white")
        s.close_button.clicked.connect(s.__close_main)
        title_login_layout.addWidget(s.close_button)
        '''
        s.title_bar.setGeometry(0,0,s._back_img_size[0],30)
        s.title_bar.raise_()
        s._taskbar.setGeometry(0,s._back_img_size[1]+28,s._back_img_size[0],s._start_img_size[1])

        s._start_button.raise_()
        
        s._cut_login_layout = QVBoxLayout(s._back_label)
        s._cut_login_layout.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        s._cut_login_layout.setSpacing(10)
        s._cut_login_layout.setContentsMargins(0,10,0,10)
        s._login_cut = DesktopShortcut(LOGIN_ICON, "Login", s.openlogingui ,s._central_widget)
        s._login_cut.setFixedSize(72,72)

        s._reg_cut = DesktopShortcut(REG_ICON, "Register", s.openreggui, s._central_widget)
        s._reg_cut.setFixedSize(72,72)

        s._cut_login_layout.addWidget(s._login_cut)
        s._cut_login_layout.addWidget(s._reg_cut)      
        s._back_label.setLayout(s._cut_login_layout)
        
        # Main layout
        #main_login_layout = QVBoxLayout(s._central_widget)
        #main_login_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        #main_login_layout.setSpacing(0)

        #main_login_layout.addWidget(s.title_bar)
        
        #main_login_layout.addWidget(s._taskbar)
        #main_login_layout.addStretch()

    def openlogingui(s):
        s._login_window = QMainWindow() 
        s._login_window.setAttribute(Qt.WA_TranslucentBackground)
        s._login_window.setWindowTitle("Login")
        s._login_window.setWindowFlags(Qt.FramelessWindowHint|Qt.Window) # remove the title bar

        s._login_window.setStyleSheet(
            '''
                QLineEdit {
                background-color: black !important;
                border: 4px solid #000080;
                border-radius: 8px;     
                }
        ''')
        s._login_central_wid = QWidget(s._login_window)
        s._login_central_wid.setStyleSheet("background-color: #ece9d8; border: 4px solid #000080; border-radius: 2 2 0 0;")

        s._login_window.setGeometry(int(s._window.width() / 2)-200, int(s._window.height() /2)-100, 400,200)
        s._login_window.setFixedSize(400,250)

        s._login_central_wid.setGeometry(0,30,s._login_window.width(),s._login_window.height()-30)
        s._login_central_wid.setFixedSize(s._login_window.width(),s._login_window.height()-30)


        title_bar = DraggableTitleBar("Login",s._login_window) # add custom title bar
        title_bar.setStyleSheet("background-color: #000080; border-radius: 0 0 2 2")
        title_bar.raise_()

        title_bar.setGeometry(0,0,400,30)
        title_bar.setFixedSize(400,30)

        s._login_layout = QVBoxLayout()
        
        s._login_layout.setSpacing(5)
        s._login_layout.setAlignment(Qt.AlignCenter)

        username_label = QLabel("Username:",s._login_central_wid)
        username_label.setStyleSheet(" border: none; font: bold 20px;")
        username_label.setAlignment(Qt.AlignCenter)
        username_label.setFixedHeight(20)
        s._login_layout.addWidget(username_label)

        s._username_input = QLineEdit(s._login_central_wid)
        s._username_input.setStyleSheet("background-color: white")
        s._login_layout.addWidget(s._username_input)

        # Create and add the password label and input field
        password_label = QLabel("Password:", s._login_central_wid)
        password_label.setStyleSheet(" border: none; font: bold 20px;")
        password_label.setAlignment(Qt.AlignCenter)
        password_label.setFixedHeight(20)
        s._login_layout.addWidget(password_label)

        s._password_input = QLineEdit(s._login_central_wid)
        s._password_input.setStyleSheet("background-color: white")
        s._password_input.setEchoMode(QLineEdit.Password)  # Hide the password input
        s._login_layout.addWidget(s._password_input)

        # Create and add the login button
        login_button = QPushButton("Login")
        login_button.setFixedSize(100,30)
        login_button.setStyleSheet("background-color: #000080; color: white; ")

        login_button.clicked.connect(s.__login_on_click)
        s._login_layout.addWidget(login_button, alignment=Qt.AlignCenter)

        s._login_layout.insertSpacing(4, 10)
        s._login_layout.insertSpacing(6, 10)

        s._login_central_wid.setLayout(s._login_layout)
        s._login_window.show()


    def __login_on_click(s):

        if s._login_layout.count()==6: # if not needed seed
            s._skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s._skt.connect((DEFAULT_IP,DEFAULT_PORT))
            s.user = s._username_input.text()
            s.pas = s._password_input.text()

            send(f"LOGIN>{s.user}>{s.pas}", s._skt)

            result = receive_buffer(s._skt)
            if result==LOG_MSG:
                with open(s.user+".bin", "rb") as file: # check if seed is on this computer
                    enc_seed = file.read()
                if not enc_seed:
                    # add input for seed
                    seed_label = QLabel("Seed(12 words: word1 word2 ...):", s._login_central_wid)
                    s._login_layout.insertWidget(4,seed_label)

                    s._seed_input = QLineEdit(s._login_central_wid) 
                    s._login_layout.insertWidget(5,s._password_input)  
                    return      
                seed = decrypt_data(enc_seed, s.pas)

                private_key_bytes = hashlib.sha256(seed).digest()
                private_key  = SigningKey.from_string(private_key_bytes, NIST256p)
                public_key = private_key.get_verifying_key()

                s.__connect_event(s.user, public_key, s._skt)

                s._window.close() # close the login window
                return

            else:
                s._err_label = QLabel(result, s._login_central_wid)
                s._err_label.setStyleSheet("color: red; font-weight: bold;")
                s._login_layout.insertWidget(6,s._err_label)

        else: # if dealing with seed
            mnemonic = s._seed_input.text() # get the phrase seed
            if mnemonic.split(" ") !=11: # 12 words
                if s._seed_err_label==None:
                    s._seed_err_label = QLabel("Wrong seed", s._login_central_wid)
                    s._seed_err_label.setStyleSheet("color: red; font-weight: bold;")
                    s._login_layout.insertWidget(6,s._seed_err_label)
            try:
                seed = bip39.phrase_to_seed(mnemonic)

                private_key_bytes = hashlib.sha256(seed).digest()
                private_key  = SigningKey.from_string(private_key_bytes, NIST256p)
                public_key = private_key.get_verifying_key()

                s._window.close() # close the login window
                s.__connect_event(s.user, public_key, s._skt)

                return 
            except Exception:
                if s._seed_err_label==None:
                    s._seed_err_label = QLabel("Wrong seed", s._login_central_wid)
                    s._seed_err_label.setStyleSheet("color: red; font-weight: bold;")
                    s._login_layout.insertWidget(6,s._seed_err_label)

            
    def openreggui(s):
        s._reg_window = QMainWindow() 
        s._reg_window.setAttribute(Qt.WA_TranslucentBackground)
        s._reg_window.setWindowTitle("Register")
        s._reg_window.setWindowFlags(Qt.FramelessWindowHint|Qt.Window) # remove the title bar

        s._reg_window.setStyleSheet(
            '''
                QLineEdit {
                background-color: black !important;
                border: 4px solid #000080;
                border-radius: 8px;     
                }
        ''')
        s._reg_central_wid = QWidget(s._reg_window)
        s._reg_central_wid.setStyleSheet("background-color: #ece9d8; border: 4px solid #000080; border-radius: 2 2 0 0;")

        s._reg_window.setGeometry(int(s._window.width() / 2)-200, int(s._window.height() /2)-100, 400,200)
        s._reg_window.setFixedSize(400,220)

        s._reg_central_wid.setGeometry(0,30,s._reg_window.width(),s._reg_window.height()-30)
        s._reg_central_wid.setFixedSize(s._reg_window.width(),s._reg_window.height()-30)


        title_bar = DraggableTitleBar("Register",s._reg_window) # add custom title bar
        title_bar.setStyleSheet("background-color: #000080; border-radius: 0 0 2 2")
        title_bar.raise_()

        title_bar.setGeometry(0,0,400,30)
        title_bar.setFixedSize(400,30)

        s._reg_layout = QVBoxLayout()
        
        s._reg_layout.setSpacing(5)
        s._reg_layout.setAlignment(Qt.AlignCenter)

        username_label = QLabel("Username:",s._reg_central_wid)
        username_label.setStyleSheet(" border: none; font: bold 20px;")
        username_label.setAlignment(Qt.AlignCenter)
        username_label.setFixedHeight(20)
        s._reg_layout.addWidget(username_label)

        s._username_input = QLineEdit(s._reg_central_wid)
        s._username_input.setStyleSheet("background-color: white")
        s._reg_layout.addWidget(s._username_input)

        # Create and add the password label and input field
        password_label = QLabel("Password:", s._reg_central_wid)
        password_label.setStyleSheet(" border: none; font: bold 20px;")
        password_label.setAlignment(Qt.AlignCenter)
        password_label.setFixedHeight(20)
        s._reg_layout.addWidget(password_label)

        s._password_input = QLineEdit(s._reg_central_wid)
        s._password_input.setStyleSheet("background-color: white")
        s._password_input.setEchoMode(QLineEdit.Password)  # Hide the password input
        s._reg_layout.addWidget(s._password_input)

        # Create and add the login button
        reg_button = QPushButton("Register")
        reg_button.setFixedSize(100,30)
        reg_button.setStyleSheet("background-color: #000080; color: white; ")

        reg_button.clicked.connect(s.__reg_on_click)
        s._reg_layout.addWidget(reg_button, alignment=Qt.AlignCenter)

        s._reg_layout.insertSpacing(4, 10)
        s._reg_layout.insertSpacing(6, 10)
        s._reg_central_wid.setLayout(s._reg_layout)
        s._reg_window.show()
            
    def __reg_on_click(s):
            s._skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s._skt.connect((DEFAULT_IP,DEFAULT_PORT))
            s.user = s._username_input.text()
            s.pas = s._password_input.text()
            
            (seed_phrase, address) = create_seed()

            send(f"REG>{s.user}>{s.pas}>{address}", s._skt)

            result = receive_buffer(s._skt)
            if result==REG_MSG:
                # show the seed phrase
                

                with open(s.user, "wb") as file: # save the phrase
                    file.write(encrypt_data(seed_phrase, s.pas))
                












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
        app = QApplication([])
        s._window.show()
        app.exec_()
    
    
    def __connect_event(s, user,  p_key: VerifyingKey, skt):


        try:
            # Handle failure on casting from string to int

            s._client: ClientBL= ClientBL(DEFAULT_IP ,DEFAULT_PORT, user, p_key, skt)

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
    

        