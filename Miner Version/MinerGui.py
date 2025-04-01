from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from MinerBL import Miner
from protocol import *
from Miner_protocol import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QMessageBox, QGridLayout
from PyQt5.QtGui import QPixmap, QIcon, QImage, QPainter, QPen, QColor, QBrush
from PyQt5.QtCore import Qt, QSize, QPoint, QRect, QTimer
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

class DraggableTitleBar(QLabel):
    
    def __init__(s, app_name:str,on_close=None,parent=None):
        super().__init__(parent)
        s.setMouseTracking(True)
        s.dragging = False
        s.on_close = on_close
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
        if s.on_close!=None:
            s.on_close()

        s.parent().close()
    
    def set_on_close(s, on_click):
        s.on_close = on_click

class MinerGUI:

    def __init__(s):
        s._miner = None
        s._window = None
        s._err_label = None
        s._central_widget = None
        s.layout = None
    
        s.__setup_window()

    def __setup_window(s):
        s._app = QApplication([])

        s._window = QMainWindow()

        s._window.setAttribute(Qt.WA_TranslucentBackground)
        s._window.setWindowTitle("Input Window")
        s._window.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        s._window.setStyleSheet('''
            QLineEdit {
                background-color: white;
                border: 4px solid #000080;
                border-radius: 8px;
                font: 16px;
            }
        ''')
        
        # Window size and position (centered)
        s._window.setFixedSize(400, 240)
        
        # Central widget
        s._central_widget = QWidget(s._window)
        s._central_widget.setStyleSheet("""
            background-color: #ece9d8; 
            border: 4px solid #000080; 
            border-radius: 2px;
        """)
        s._central_widget.setGeometry(0, 30, s._window.width(), s._window.height()-30)
        s._window.setCentralWidget(s._central_widget)
        
        # Title bar (simplified)
        s.title_bar = DraggableTitleBar("XD Wallet Miner", None,s._window)
        s.title_bar.setStyleSheet("background-color: #000080; border-radius: 2 2 0 0")
        s.title_bar.setGeometry(0,0,s._window.width(),30)
        s.title_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Create the ui elements
        s.__create_elements()
    

    def __create_elements(s):
        """
        Create the ui elements in the window
        """
        s.layout = QVBoxLayout(s._central_widget)
        s.layout.setSpacing(0)

        
        # Input label
        input_label = QLabel("Username: ", s._central_widget)
        input_label.setStyleSheet("border: none; font: bold 20px;")
        input_label.setAlignment(Qt.AlignCenter)
        s.layout.addWidget(input_label)
        
        # Input field
        s.address_input = QLineEdit(s._central_widget)
        s.address_input.setFixedHeight(30)
        s.layout.addWidget(s.address_input)

        s._err_label = QLabel("", s._central_widget)
        s._err_label.setStyleSheet("color: red; font: bold 15px; border: none")
        s.layout.addWidget(s._err_label, alignment=Qt.AlignCenter)

        # Button
        s.start_button = QPushButton("Start Mining", s._central_widget)
        s.start_button.setFixedSize(100, 30)
        s.start_button.clicked.connect(s.__miner_start)
        s.start_button.setStyleSheet("""
            background-color: #000080; 
            color: white;
            border: none;
            font: bold 15px;
        """)
        #start_button.clicked.connect(s.on_submit)
        s.layout.addWidget(s.start_button, alignment=Qt.AlignCenter)
        
        # Add some spacing
        s.layout.insertSpacing(0, 40)
        s._central_widget.setLayout(s.layout)

    
    def draw(s):
        s._window.show()
        s._app.exec_()
    
    def __miner_start(s):
        address = s.address_input.text()
        
        try:
            s._skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s._skt.connect((DEFAULT_IP,DEFAULT_PORT))
        except Exception:
            if s._err_label==None:
                s._err_label = QLabel("Couldnt connect to node", s._central_widget)
                s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
                s.layout.insertWidget(4,s._err_label, alignment=Qt.AlignCenter)
            elif s._err_label.text()!="Couldnt connect to node":
                s._err_label.setText("Couldnt connect to node")
            return
        send("Miner user:>" + address, s._skt)

        result = receive_buffer(s._skt)

        if result[1].startswith("Valid"):
            s.__connect_event(result[1].split(">")[1])
        

    
    def __connect_event(s, address):


        try:
            # Handle failure on casting from string to int

            s._miner: Miner = Miner(s.address_input.text(), address, s._skt)
            s.title_bar.set_on_close(s._miner.disconnect)

            s.start_button.setDisabled(True)
                

        except Exception as e:
            # If our problem occurred before the client
            # mean that our client will be None
            error = s._window._miner and s._window._miner.get_last_error() or e

            write_to_log(f" 路 Client GUI 路 an error has occurred : {error}")
            messagebox.showerror("Error on Connect", error)
    

def main():
    n = MinerGUI()
    n.draw()

if __name__ == "__main__":
    main()