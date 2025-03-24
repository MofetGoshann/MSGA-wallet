from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from ClientBL import ClientBL
from protocol import *
from Client_protocol import *
from PIL import Image, ImageTk
import PyQt5
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QMessageBox, QGridLayout
from PyQt5.QtGui import QPixmap, QIcon, QImage, QPainter, QPen, QColor, QBrush
from PyQt5.QtCore import Qt, QSize, QPoint, QRect, QTimer
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
WNW_ICON = "Images/wallet.ico"

class TaskbarButton(QPushButton):
    def __init__(s, window, icon, parent=None):
        super().__init__(parent)
        s.window = window  # The window this button controls
        s.setFixedSize(50, 50)  # Set a fixed size for the button

        # Set an icon for the button
        s.setIcon(QIcon(icon))  # Replace with your icon file path
        s.setIconSize(s.size())  # Set icon size to match button size

        # Set initial style
        s.update_style()

        # Connect the button click to show or bring the window to the front
        s.clicked.connect(s.show_or_focus_window)

        # Use a timer to check window focus
        s.timer = QTimer()
        s.timer.timeout.connect(s.check_window_focus)
        s.timer.start(300)  # Check every 500ms

    def show_or_focus_window(s):
        """Show the window or bring it to the front if it's already open."""
        if s.window.isVisible():
            s.window.activateWindow()  # Bring the window to the front
        else:
            s.window.show()  # Show the window if it's hidden

    def check_window_focus(s):
        """Check if the associated window is in focus and update the button style."""
        s.update_style()

    def update_style(s):
        """Update the button's style based on the window's focus state."""
        if not s.window.isVisible():
            s.close()
        
        if s.window.isActiveWindow():
            s.setStyleSheet("""
                QPushButton {
                    background-color: rgba(6, 0, 128, 0.5);
                    border: 2px solid blue;

                }
            """)
        else:
            s.setStyleSheet("""
                QPushButton {
                    background-color: rgba(211, 211, 211, 100);
                    border: 2px solid gray;
                }
            """)

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
    


    
    def __close_main(s):
        s.parent().close()


class DesktopShortcut(QWidget):
    def __init__(s, icon_path, app_name, on_clickback, parent=None):
        super().__init__(parent)
        s.icon_path = icon_path
        s.app_name = app_name
        s.callback = on_clickback
        s.selected = False
        s.initUI()

    def initUI(s):
        # Create a vertical layout
        s.setStyleSheet("""
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
        
        layout = QVBoxLayout(s)
        layout.setSpacing(2)
        layout.setContentsMargins(2,2,2,2)
        
        # Create a button with an icon
        s.button = QPushButton(s)
        s.button.clicked.connect(s.callback)
        s.button.setIcon(QIcon(s.icon_path))
        s.button.setIconSize(QSize(64, 64))  # Set icon size
        s.button.setFixedSize(64, 64)  # Set button size
        """
        s.button.setStyleSheet(
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
        s.label = QLabel(s.app_name, s)
        s.label.setAlignment(Qt.AlignCenter)
        s.label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-family: "Tahoma";
            }
        """)

        # Add the button and label to the layout
        layout.addWidget(s.button, 0, Qt.AlignCenter)
        layout.addWidget(s.label, 0, Qt.AlignCenter)

        # Set the layout to the widget
        s.setLayout(layout)

        # Set the widget background to transparent
        s.setAttribute(Qt.WA_TranslucentBackground)
        s.setWindowFlags(Qt.FramelessWindowHint)

    def enterEvent(s, event):
        # Change the background color when the mouse enters the widget
        s.setStyleSheet("""
            QWidget {
                border: 1px solid #0078d7;
                border-radius: 2px;
                padding: 2px;
                background-color: rgba(0, 120, 215, 0.2);
            }
        """)

    def mousePressEvent(s, event):
        # Change style on selection
        s.selected = not s.selected  # Toggle selection
        if s.selected:
            s.setStyleSheet("""
                QWidget {
                    border: 1px solid #0078d7;
                    border-radius: 2px;
                    padding: 2px;
                    background-color: rgba(0, 85, 153, 0.2);
            }
            """)
        else:
            s.setStyleSheet("""
                QWidget {
                    border: 1px solid transparent;
                    border-radius: 4px;
                    padding: 2px;
                    background-color: transparent;
            }
            """)
        super().mousePressEvent(event)
    
    def leaveEvent(s, event):
        # Reset the background color when the mouse leaves the widget
        if not s.selected:
            s.setStyleSheet("""
            QWidget {
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 2px;
                background-color: transparent;
            }
        """)
    

    def mouseDoubleClickEvent(s, event):
        # open th needed window when the shortcut is clicked
        s.callback()
    
class SelectableLabel(QLabel):
    def __init__(s, parent=None):
        super().__init__(parent)

        # Variables to store the selection rectangle
        s.start_point = None
        s.end_point = None
        s.drawing = False

    def mousePressEvent(s, event):
        # Start drawing the selection rectangle
        if event.button() == Qt.LeftButton:
            s.start_point = event.pos()
            s.end_point = event.pos()
            s.drawing = True

    def mouseMoveEvent(s, event):
        # Update the selection rectangle as the mouse moves
        if s.drawing:
            s.end_point = event.pos()
            s.update()  # Trigger a repaint

    def mouseReleaseEvent(s, event):
        # Finalize the selection rectangle
        if event.button() == Qt.LeftButton:
            s.end_point = event.pos()
            s.drawing = False
            s.update()  # Trigger a repaint

    def paintEvent(s, event):
        # Call the base class paintEvent to draw the QLabel content (e.g., text or image)
        super().paintEvent(event)

        # Draw the selection rectangle if drawing is in progress
        if s.drawing and s.start_point and s.end_point:
            painter = QPainter(s)

            # Draw the border of the rectangle
            painter.setPen(QPen(QColor(0, 0, 255)))  # Blue dashed line

            # Fill the rectangle with a semi-transparent color
            fill_color = QColor(0, 0, 255, 50)  # Blue with 20% opacity
            painter.setBrush(QBrush(fill_color))

            # Calculate the normalized rectangle
            rect = QRect(s.start_point, s.end_point).normalized()
            painter.drawRect(rect)

    def get_selection_rect(s):
        # Return the selected rectangle (in widget coordinates)
        if s.start_point and s.end_point:
            return QRect(s.start_point, s.end_point).normalized()
        return None

        

class ClientGUI:

    def __init__(s):
        s._client = None
        
        s._window = None
        s._login_window = None
        s._reg_window = None
        s.tickerlist = ["NTL", "TAL", "SAN", "PEPE", "MNSR", "MSGA", "52C", "GMBL", "MGR", "RR"]
        s.token_name_list = ["NataliCoin", "TalCoin", "SanyaCoin", "PepeCoin", "MonsterCoin", "MakeShevahGreatAgainCoin", "52Coin", "GambleCoin", "MegiraCoin", "VipeRRCoin"]
        s._login_layout = None
        s._reg_layout = None

        s._back_img = None
        s._start_img = None
        s._back_img_size = [0, 0]
        s._btn_img_size = [0, 0]


        # UI
        s._connect_button = None
        s._disconnect_button = None
        s._login_button = None
        s._err_label=None

        s._ip_entry = None
        s._port_entry = None
        s._cmd_entry = None
        s._args_entry = None

        s._receive_field = None

        s.__setup_window()

    def __setup_window(s):
        
        s._app = QApplication([])
        s._window = QMainWindow()

        s._window.setWindowTitle("XP Wallet")
        s._window.setAttribute(Qt.WA_TranslucentBackground)
        s._window.setWindowFlags(Qt.FramelessWindowHint)
        s._window.setWindowIcon(QIcon(WNW_ICON))

        s._central_widget = QWidget(s._window)
        s._window.setCentralWidget(s._central_widget)

        s.__setup_images()
        # Disable resize to fit with the background image
        s._window.setGeometry(300, 100, s._back_img_size[0], s._back_img_size[1]+s._start_img_size[1]+28)  # Set window size and position
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



        
        s._back_label = SelectableLabel(s._central_widget)
        
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
        s._task_layout.setAlignment(Qt.AlignLeft)
        s._task_layout.insertSpacing(0,s._start_img_size[0])
        s._task_layout.setContentsMargins(5, 0, 5, 0)
        s._taskbar.setLayout(s._task_layout)
        s.title_bar = DraggableTitleBar("XP Wallet", s._window)
        s.title_bar.setStyleSheet("background-color: #000080; border-radius: 2 2 0 0")
        
        s.title_bar.setGeometry(0,0,s._back_img_size[0],30)
        s.title_bar.raise_()
        s._taskbar.setGeometry(0,s._back_img_size[1]+28,s._back_img_size[0],s._start_img_size[1])

        s._start_button.raise_()
        
        s._cut_login_layout = QVBoxLayout(s._back_label)
        s._cut_login_layout.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        s._cut_login_layout.setSpacing(10)
        s._cut_login_layout.setContentsMargins(0,10,0,10)
        s._login_cut = DesktopShortcut(REG_ICON, "Login", s.openlogingui ,s._back_label)
        s._login_cut.setFixedSize(86,86)

        s._reg_cut = DesktopShortcut(LOGIN_ICON, "Register", s.openreggui, s._back_label)
        s._reg_cut.setFixedSize(86,86)

        s._balance_cut = DesktopShortcut(REG_ICON, "Balance",s.openbalances ,s._central_widget)
        s._balance_cut.setFixedSize(86,80)

        s._history_cut = DesktopShortcut(LOGIN_ICON, "History", s.openreggui, s._central_widget)
        s._history_cut.setFixedSize(86,80)

        s._cut_login_layout.addWidget(s._balance_cut)
        s._cut_login_layout.addWidget(s._history_cut)   
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

        s._login_button = TaskbarButton(s._login_window, REG_ICON,s._taskbar)
        s._task_layout.addWidget(s._login_button)

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
        s._login_window.setFixedSize(400,240)

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
        s._username_input.setStyleSheet("background-color: white; font: 16px")
        s._username_input.setFixedHeight(30)
        s._login_layout.addWidget(s._username_input)

        # Create and add the password label and input field
        password_label = QLabel("Password:", s._login_central_wid)
        password_label.setStyleSheet(" border: none; font: bold 20px;")
        password_label.setAlignment(Qt.AlignCenter)
        password_label.setFixedHeight(20)
        s._login_layout.addWidget(password_label)

        s._password_input = QLineEdit(s._login_central_wid)
        s._password_input.setStyleSheet("background-color: white; font: 16px")
        s._password_input.setEchoMode(QLineEdit.Password)  # Hide the password input
        s._password_input.setFixedHeight(30)  # Hide the password input
        s._login_layout.addWidget(s._password_input)

        # Create and add the login button
        login_button = QPushButton("Login")
        login_button.setFixedSize(100,30)
        login_button.setStyleSheet("background-color: #000080; color: white; ")

        login_button.clicked.connect(s.__login_on_click)
        s._login_layout.addWidget(login_button, alignment=Qt.AlignCenter)

        s._login_layout.insertSpacing(4, 8)
        s._login_layout.insertSpacing(6, 8)

        s._login_central_wid.setLayout(s._login_layout)
        s._login_window.show()


    def __login_on_click(s):
        
            s.user = s._username_input.text()
            s.pas = s._password_input.text()
            if s.user=="" or s.pas=="": # first check if something is wrtiten
                    if s._err_label==None: # if no error label
                    
                        s._err_label = QLabel("All fields should be filled", s._login_central_wid)
                        s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
                        s._login_layout.insertWidget(4,s._err_label, alignment=Qt.AlignCenter)
                
                    elif s._err_label.text()!="All fields should be filled": # if already is error label but different error
                        s._err_label.setText("All fields should be filled")
                    return
            
        
            try:
                s._skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s._skt.connect((DEFAULT_IP,DEFAULT_PORT))
            except Exception:
                if s._err_label==None:
                    s._err_label = QLabel("Couldnt connect to node", s._login_central_wid)
                    s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
                    s._login_layout.insertWidget(4,s._err_label, alignment=Qt.AlignCenter)
                elif s._err_label.text()!="Couldnt connect to node":
                    s._err_label.setText("Couldnt connect to node")
                return

            send(f"LOGIN>{s.user}>{s.pas}", s._skt)

            result = receive_buffer(s._skt)
            if result[1].startswith(LOG_MSG):
                with open("phrases/"+s.user+".bin", "rb") as file: # check if seed is on this computer
                    enc_seed = file.read()
                if not enc_seed:
                    # add input for seed
                    while s._login_layout.count():# remove all widgets from the current layout
                        item = s._login_layout.takeAt(0)
                        widget = item.widget()
                        if widget:
                            widget.setParent(None)  # Remove the widget from the current layout
                    s.adr = result[1].split(">")[1]
                    seed_label = QLabel("Seed(12 words: word1 word2 ...):", s._login_central_wid)
                    seed_label.setStyleSheet(" border: none; font: bold 20px;")
                    seed_label.setAlignment(Qt.AlignCenter)
                    seed_label.setFixedHeight(20)

                    s._login_layout.addWidget(seed_label)

                    s._seed_input = QLineEdit(s._login_central_wid) 
                    s._seed_input.setStyleSheet("background-color: white; font: 16px")
                    s._seed_input.setFixedHeight(30)  # Hide the password input
                    s._login_layout.addWidget(s._seed_input, alignment=Qt.AlignCenter)  

                    ok_button = QPushButton("Ok")
                    ok_button.clicked.connect(s.check_seed)
                    ok_button.setFixedSize(100,30)
                    ok_button.setStyleSheet("background-color: #000080; color: white; ")
                    s._login_layout.addWidget(ok_button, alignment=Qt.AlignCenter)

                    return      
                seed = decrypt_data(enc_seed, s.pas)

                private_key_bytes = hashlib.sha256(seed).digest()
                private_key  = SigningKey.from_string(private_key_bytes, NIST256p)

                s._login_window.close() # close the login window
                s.__connect_event(s.user, private_key, s._skt)

                return

            else:
                s._err_label = QLabel(result[1], s._login_central_wid)
                s._err_label.setStyleSheet("color: red; font-weight: bold;")
                s._login_layout.insertWidget(4,s._err_label, alignment=Qt.AlignCenter)

        
            
    def openreggui(s):
        s._reg_window = QMainWindow() 
        s._reg_window.setAttribute(Qt.WA_TranslucentBackground)
        s._reg_window.setWindowTitle("Register")
        s._reg_window.setWindowFlags(Qt.FramelessWindowHint|Qt.Window) # remove the title bar

        s._reg_button = TaskbarButton(s._reg_window, LOGIN_ICON,s._taskbar)
        s._task_layout.addWidget(s._reg_button)
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
        s._reg_window.setFixedSize(400,240)

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
        s._username_input.setStyleSheet("background-color: white; font: 16px")
        s._username_input.setFixedHeight(30)
        s._reg_layout.addWidget(s._username_input)

        # Create and add the password label and input field
        password_label = QLabel("Password:", s._reg_central_wid)
        password_label.setStyleSheet(" border: none; font: bold 20px;")
        password_label.setAlignment(Qt.AlignCenter)
        password_label.setFixedHeight(20)
        s._reg_layout.addWidget(password_label)

        s._password_input = QLineEdit(s._reg_central_wid)
        s._password_input.setStyleSheet("background-color: white; font: 16px")
        s._password_input.setEchoMode(QLineEdit.Password)  # Hide the password input
        s._password_input.setFixedHeight(30)
        s._reg_layout.addWidget(s._password_input)

        # Create and add the login button
        reg_button = QPushButton("Register")
        reg_button.setFixedSize(100,30)
        reg_button.setStyleSheet("background-color: #000080; color: white; ")

        reg_button.clicked.connect(s.__reg_on_click)
        s._reg_layout.addWidget(reg_button, alignment=Qt.AlignCenter)

        s._reg_layout.insertSpacing(4, 8)
        s._reg_layout.insertSpacing(6, 8)
        s._reg_central_wid.setLayout(s._reg_layout)
        s._reg_window.show()
            
    def __reg_on_click(s):
        s.user = s._username_input.text()
        s.pas = s._password_input.text()

        if s.user=="" or s.pas=="": # first check if something is wrtiten
            if s._err_label==None: # if no error label
            
                s._err_label = QLabel("All fields should be filled", s._reg_central_wid)
                s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
                s._reg_layout.insertWidget(4,s._err_label, alignment=Qt.AlignCenter)
        
            elif s._err_label.text()!="All fields should be filled": # if already is error label but different error
                s._err_label.setText("All fields should be filled")
            return
    
        try:    
            s._skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s._skt.connect((DEFAULT_IP,DEFAULT_PORT))     

        except Exception: # if no node
            if s._err_label==None:
                s._err_label = QLabel("Couldnt connect to node", s._reg_central_wid)
                s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
                s._reg_layout.insertWidget(4,s._err_label, alignment=Qt.AlignCenter)
                
            elif s._err_label!="Couldnt connect to node":
                s._err_label.setText("Couldnt connect to node")           
            return
        
        (seed_phrase, address) = create_seed()
        send(f"REG>{s.user}>{s.pas}>{address}", s._skt)
        write_to_log(f"REG>{s.user}>{s.pas}>{address}")

        result = receive_buffer(s._skt)
        print(result)
        if result[1]==REG_MSG:
            # show the seed phrase

            while s._reg_layout.count():# remove all widgets from the current layout
                item = s._reg_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)  # Remove the widget from the current layout


            seed_write_label = QLabel("Write this backup phrase down, never send\n it to anyone, it is needed in case of emergency", s._reg_central_wid)
            seed_write_label.setStyleSheet("font: bold 15px; border:none; ")
            seed_write_label.setAlignment(Qt.AlignCenter)

            with open("phrases/"+s.user+".bin", "wb") as file: # save the phrase encrypted
                file.write(encrypt_data(seed_phrase.encode(), s.pas))

            spl:list = seed_phrase.split(" ") # ,ake the seed phrase two lines
            spl.insert(6,"\n")
            seed_phrase = " ".join(spl)

            seed_label = QLabel(seed_phrase, s._reg_central_wid)
            seed_label.setStyleSheet("background-color: white; font: bold 16px")
            seed_label.setAlignment(Qt.AlignCenter)

            ok_button = QPushButton("Ok")
            ok_button.clicked.connect(s.end_reg)
            ok_button.setFixedSize(100,30)
            ok_button.setStyleSheet("background-color: #000080; color: white; ")
            

            s._reg_layout.addWidget(seed_write_label)
            s._reg_layout.addWidget(seed_label)
            s._reg_layout.addWidget(ok_button, alignment=Qt.AlignCenter)
            s._reg_layout.insertSpacing(1,5)
            s._reg_layout.insertSpacing(2,15)
            s._reg_layout.insertSpacing(4,15)
            s._reg_central_wid.setLayout(s._reg_layout)
            

            
            
            return
        elif s._err_label==None: # if no error label
            
            s._err_label = QLabel(result[1], s._reg_central_wid)
            s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
            s._reg_layout.insertWidget(4,s._err_label, alignment=Qt.AlignCenter)
        
        elif s._err_label.text()!=result[1]: # if already is error label but different error
            s._err_label.setText(result[1])
                
    def check_seed(s):

        mnemonic = s._seed_input.text() # get the phrase seed

        if len(mnemonic.split(" ")) !=12: # 12 words
            if s._err_label==None:

                s._err_label = QLabel("Wrong seed, 12 words needed", s._login_central_wid)
                s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
                s._login_layout.insertWidget(3,s._err_label, alignment=Qt.AlignCenter)
            
            elif s._err_label.text()!="Wrong seed, 12 words needed":
                s._err_label.setText("Wrong seed, 12 words needed")
        else: # mnemonic is valid
            try:
                seed = bip39.phrase_to_seed(mnemonic)

                private_key_bytes = hashlib.sha256(seed).digest()
                private_key  = SigningKey.from_string(private_key_bytes, NIST256p)
                public_key = private_key.get_verifying_key()
                adr = address_from_key(public_key)
                if adr!=s.adr: # check the address
                    if s._err_label==None:
                        s._err_label = QLabel("Wrong seed", s._login_central_wid)
                        s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
                        s._login_layout.insertWidget(6,s._err_label, alignment=Qt.AlignCenter)
                
                    elif s._err_label.text()!="Wrong seed":
                        s._err_label.setText("Wrong seed")
                    return
                
                with open("phrases/"+s.user+".bin", "wb") as file: # save the phrase encrypted
                    file.write(encrypt_data(mnemonic.encode(), s.pas))

                s._login_window.close() # close the login window

                s.__connect_event(s.user, public_key, s._skt)
                return 
            
            except Exception:
                if s._err_label==None:
                    s._err_label = QLabel("Wrong seed", s._login_central_wid)
                    s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
                    s._login_layout.insertWidget(6,s._err_label, alignment=Qt.AlignCenter)
                
                elif s._err_label.text()!="Wrong seed":
                    s._err_label.setText("Wrong seed")
                    
    def end_reg(s):
        with open("phrases/"+s.user+".bin", "rb") as file: # read the phrase encrypted
            enc = file.read()
        encoded_phrase = decrypt_data(enc, s.pas) # decrypt

        phrase = encoded_phrase.decode()
        seed = bip39.phrase_to_seed(phrase)

        private_key_bytes = hashlib.sha256(seed).digest()
        private_key  = SigningKey.from_string(private_key_bytes, NIST256p)
        print(type(private_key))
        s._reg_window.close()
        s.__connect_event(s.user, private_key, s._skt)    

    def openbalances(s):
        s._balance_window = QMainWindow()
        s._balance_window.setAttribute(Qt.WA_TranslucentBackground)
        s._balance_window.setWindowTitle("Balances")
        s._balance_window.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        s._balance_window.setGeometry(100, 100, 600, 400)
        s._balance_window.setFixedSize(600, 400)

        # Create a central widget
        s._balance_central_wid = QWidget(s._balance_window)
        s._balance_central_wid.setStyleSheet(
            "background-color: #ece9d8; border: 4px solid #000080; border-radius: 2px;"
        )
        s._balance_central_wid.setGeometry(0, 30, s._balance_window.width(), s._balance_window.height() - 30)
        s._balance_central_wid.setFixedSize(s._balance_window.width(), s._balance_window.height() - 30)
        s._balance_window.setCentralWidget(s._balance_central_wid)

        # Create a custom title bar
        s._balance_title_bar = DraggableTitleBar("Balances", s._balance_window)
        s._balance_title_bar.setStyleSheet(
            "background-color: #000080; color: white; font: bold 16px; border-radius: 2px 2px 0 0;"
        )
        s._balance_title_bar.setGeometry(0, 0, s._balance_window.width(), 30)
        s._balance_title_bar.setFixedSize(s._balance_window.width(), 30)
        s._balance_title_bar.raise_()

        # Create a layout for the tokens and buttons
        main_layout = QHBoxLayout(s._balance_central_wid)

        # Create a grid layout for the tokens (2 columns)
        token_layout = QGridLayout()
        
        conn = sqlite3.connect(f'databases/Client/blockchain.db')
        cursor = conn.cursor()

        address = s._client.get_address()
        cursor.execute('''
        SELECT balance from balances WHERE address = ?
        ''', (address, ))

        balances = cursor.fetchall()

        # Add tokens to the grid layout
        for index, token_name in enumerate(s.tickerlist):
            row = index // 2  # Two tokens per row
            col = index % 2   # Two columns

            full_name = s.token_name_list[index]
            balance = balances[index][0]
            # Create a label with styled text
            token_label = QLabel()
            token_label.setText(
                f'<span style="background-color: #000080; color: white; font-weight: bold; padding: 2px;">${token_name}</span> '
                f'<span style="color: black;">({full_name}): {balance}</span>'
            )
            token_label.setStyleSheet("font: bold 14px; border: none; padding: 5px;")
            token_layout.addWidget(token_label, row, col)

        # Add the token layout to the main layout
        main_layout.addLayout(token_layout)

        # Create a vertical layout for the buttons
        button_layout = QVBoxLayout()

        # Create Send and Receive buttons
        send_button = QPushButton("Send")
        receive_button = QPushButton("Receive")

        # Style the buttons
        send_button.setStyleSheet(
            "background-color: #000080; color: white; font: bold 16px; border-radius: 8px; padding: 10px;"
        )
        receive_button.setStyleSheet(
            "background-color: #000080; color: white; font: bold 16px; border-radius: 8px; padding: 10px;"
        )

        # Add buttons to the button layout
        button_layout.addWidget(send_button)
        button_layout.addWidget(receive_button)

        # Add the button layout to the main layout
        main_layout.addLayout(button_layout)

        # Set the main layout for the central widget
        s._balance_central_wid.setLayout(main_layout)

        s._balance_window.show()





    def __minimize(s):
        s._window.showMinimized()
    
    def __maximize(s):
        if s._window.isMaximized():
            s._window.showNormal()  # Restore to normal size

        else:
            s._window.showMaximized()  # Maximize the window

    
    def __close_main(s):

        s._window.close()
        if s._login_window!=None:
            s._login_window.close()
        
        if s._reg_window!=None:
            s._reg_window.close()
    
    def draw(s):
        app = QApplication([])
        s._window.show()
        app.exec_()
    
    
    def __connect_event(s, user,  p_key: SigningKey, skt):


        try:
            # Handle failure on casting from string to int

            s._client: ClientBL= ClientBL(user, p_key, skt, s.show_error)

            # check if we successfully created socket
            # and ready to go
            if not s._client.get_success():
                raise Exception("failed to create and setup client bl")
            else:
                s._reg_cut.setParent(None)
                s._login_cut.setParent(None)

                s._balance_cut = DesktopShortcut(REG_ICON, "Balance",s.openbalances ,s._central_widget)
                s._balance_cut.setFixedSize(86,80)

                s._history_cut = DesktopShortcut(LOGIN_ICON, "History", s.openreggui, s._central_widget)
                s._history_cut.setFixedSize(86,80)

                s._cut_login_layout.addWidget(s._balance_cut)
                s._cut_login_layout.addWidget(s._history_cut)    


                

        except Exception as e:
            # If our problem occurred before the client
            # mean that our client will be None
            error = s._client and s._client.get_last_error() or e
            traceback.print_exc()
            write_to_log(f" 路 Client GUI 路 an error has occurred : {error}")
            messagebox.showerror("Error on Connect", error)
    
    def __send_data_event(s):
        s._client.send_transaction("SNC", 14.88, "qwe")

    def show_error(s, title, error):
        QMessageBox.information(s._central_widget, title, error)

def main():
    n = ClientGUI()
    n.draw()



if __name__ == "__main__":
    main()
    

        