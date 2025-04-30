from ClientBL import ClientBL
from protocol import *
from Client_protocol import *

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
BAL_ICON = "Images/dolla.png"
HIS_ICON ="Images/history.png"
NOT_ICON = "Images/notif.png"
RED_NOT_ICON = "Images/rednotif.png"

class HoverLabel(QLabel):
    def __init__(self, text="", tooltip_text="", parent=None):
        super().__init__(text, parent)
        self.tooltip_text = tooltip_text
        self.tooltip_widget = None
        self.setCursor(Qt.ArrowCursor)
        
        # Configure tooltip appearance
        self.setStyleSheet("""
            QLabel {
                background-color: #000080;
                color: white;
                font: bold 12px;
                padding: 5px;
                border-radius: 4px;
            }
        """)

    def enterEvent(self, event):
        if self.tooltip_text:
            # Create a custom tooltip widget
            self.tooltip_widget = QLabel(self.tooltip_text, self.window())
            self.tooltip_widget.setStyleSheet("""
                QLabel {
                    background-color: #000080;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 4px;
                    border: 1px solid white;
                }
            """)
            self.tooltip_widget.setWindowFlags(Qt.ToolTip)
            
            # Position tooltip at bottom-right of label
            pos = self.mapToGlobal(self.rect().bottomRight())
            self.tooltip_widget.move(pos)
            self.tooltip_widget.show()
        
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.tooltip_widget:
            self.tooltip_widget.deleteLater()
            self.tooltip_widget = None
        super().leaveEvent(event)

class WindowsXPNotification(QLabel):
    clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._notification_type = ""
        
        # Windows XP style colors
        self._normal_style = """
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F0F0F0, stop:1 #D4D0C8);
                border: 2px solid #003C74;
                border-radius: 4px;
                padding: 6px;
                color: black;
                font: 14px "Tahoma";
            }
        """
        self._hover_style = """
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E2F0FD, stop:1 #B8DCFF);
                border: 2px solid #0058B3;
                border-radius: 4px;
                padding: 6px;
                color: black;
                font: 14px "Tahoma";
            }
        """
        self.setStyleSheet(self._normal_style)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(300, 80)
        
    def enterEvent(self, event):
        self.setStyleSheet(self._hover_style)
        
    def leaveEvent(self, event):
        self.setStyleSheet(self._normal_style)
        
    def mousePressEvent(self, event):
        self.clicked.emit(self._notification_type)
        super().mousePressEvent(event)
        self.close()

class SecWindow(QMainWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self._is_closed = False  # Track closed state
    
    def closeEvent(self, event):
        self._is_closed = True
        event.accept()  # Allow the window to close
    
    def isClosed(self):
        return self._is_closed

class NotificationBridge(QObject):
    # Define a signal to safely pass notifications to the main thread
    notification_requested = pyqtSignal(str, str)  # (type, message)

    def __init__(self, notif_manager, address):
        super().__init__()
        self.address = address
        self.notif_manager = notif_manager
        self.notification_requested.connect(self._show_notification)

    @pyqtSlot(str, str)
    def _show_notification(self, typpe, message):
        """Slot that runs in the main thread"""
        self.notif_manager.show_notification(typpe, message)

    def notif_add(self, typpe, tr):
        """Can be called from any thread"""
        try:
            if type(tr) == str:
                tr_tup = ast.literal_eval(tr)
            else:
                tr_tup = tr[0]

            if typpe == True:
                amount = tr_tup[5]
                token = tr_tup[6]
                if tr_tup[4] == self.address:
                    typpe = "received"
                else:
                    typpe = "included"
            elif typpe in ("verified", "failed"):
                amount = tr_tup[4]
                token = tr_tup[5]
            
            tokenvalue = f"{amount} {token}"
            # Emit signal instead of direct call
            self.notification_requested.emit(typpe, tokenvalue)
            
        except Exception:
            traceback.print_exc()

class XPNotificationManager:
    def __init__(self, parent_window, on_click):
        self.on_click = on_click
        self.parent = parent_window
        self.notifications = []
        self.spacing = 5
        self.max_notifications = 3
        
        # XP-style taskbar button (optional)
        self.taskbar_button = QPushButton("Notifications")
        self.taskbar_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F0F0F0, stop:1 #D4D0C8);
                border: 1px solid #7A96DF;
                border-radius: 3px;
                padding: 3px 8px;
                color: black;
                font: 11px "Tahoma";
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E2F0FD, stop:1 #B8DCFF);
            }
            QPushButton:pressed {
                background: #C2D8F5;
            }
        """)
        self.taskbar_button.setFixedHeight(24)
        
    def show_notification(self, notification_type, message):
        if len(self.notifications) >= self.max_notifications:
            oldest = self.notifications.pop(0)
            oldest.hide()
            oldest.deleteLater()
            
        notif = WindowsXPNotification(self.parent)
        notif._notification_type = notification_type
        
        # XP-style icons and colors
        if notification_type == "received":
            icon = "↓"
            color = "#006600"  # green
            title = f"Received {message}"
        elif notification_type=="included":
            icon = "✓"
            color = "#0033CC"  # blue
            title = f"Transaction of {message}\n is included in the block"
        elif notification_type=="failed":
            icon = "✕"
            color = "#e33434"  # red
            title = f"Transaction of {message}\n failed verification"
        else:
            icon = "✓"
            color = "#0033CC"
            title = f"Transaction of {message}\n is verified"
        notif.setText(f"""
            <div style='font-size: 14px; font-family: Tahoma;'>
                <span style='color: {color}; font-size: 16px;'>{icon}</span>
                <b>{title}</b><br>
            </div>
        """)
        
        # XP-style shadow (simpler than modern shadows)
        shadow = QGraphicsDropShadowEffect(notif)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(2, 2)
        notif.setGraphicsEffect(shadow)
        
        notif.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        notif.clicked.connect(self.on_notification_clicked)
        
        self.position_notification(notif)
        notif.show()
        
        # XP-style fade in animation
        animation = QPropertyAnimation(notif, b"windowOpacity")
        animation.setDuration(300)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()
        
        # Auto-close with XP-style slide animation
        QTimer.singleShot(5000, lambda: self.fade_out_notification(notif))
        
        self.notifications.append(notif)
        
    def position_notification(self, notification):
        screen_rect = self.parent.rect()
        x = screen_rect.right() - notification.width() - 10
        y = screen_rect.bottom() - notification.height() - 70
        
        # Stack upwards
        for notif in self.notifications:
            y -= notif.height() + self.spacing
        
        notification.move(x, max(y, 10))
        
    def fade_out_notification(self, notification):
        if notification in self.notifications:
            self.notifications.remove(notification)
            
            # XP-style slide out animation
            animation = QPropertyAnimation(notification, b"pos")
            animation.setDuration(300)
            animation.setStartValue(notification.pos())
            animation.setEndValue(QPoint(notification.x(), notification.y() + 50))
            animation.finished.connect(notification.deleteLater)
            animation.start()
            
    def on_notification_clicked(self):
        # XP-style feedback sound
        self.on_click()
        
class TaskbarButton(QPushButton):
    def __init__(s, window, icon, parent=None):
        super().__init__(parent)
        s.window = window  # The window this button controls
        s.setFixedSize(50, 50)  # Set a fixed size for the button

        # Set an icon for the button
        s.setIcon(QIcon(icon))  # Replace with your icon file path
        s.setIconSize(s.size())  # Set icon size to match button size
        s.parent = parent
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
        if s.window.isClosed()==True:
            s.close()
        
        if not s.window.isHidden() and s.window.isActiveWindow():
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

class DraggableTitleBar_withdisc(QLabel):
    
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
        s.parent().hide()
    
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
        s._history_window = None
        s._translist = []
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

        s._window.setWindowTitle("XP Wallet - Client")
        s._window.setAttribute(Qt.WA_TranslucentBackground)
        s._window.setWindowFlags(Qt.FramelessWindowHint)
        s._window.setWindowIcon(QIcon(WNW_ICON))
        
        s._central_widget = QWidget(s._window)
        s._window.setCentralWidget(s._central_widget)
        
        s.__setup_images()
        # Disable resize to fit with the background image
        s._window.setGeometry(300, 100, s._back_img_size[0], s._back_img_size[1]+s._start_img_size[1]+28)  # Set window size and position
        #s._window.setFixedSize(s._back_img_size[0], s._back_img_size[1]+s._start_img_size[1]+30)
        s.notif_manager = XPNotificationManager(s._window, s.notif_click)
        


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

        s.title_bar = DraggableTitleBar_withdisc("XP Wallet",None,s._window)
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

        s._login_window = SecWindow(s._window) 
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

        s._err_label = QLabel("", s._login_central_wid)
        s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
        s._login_layout.addWidget(s._err_label, alignment=Qt.AlignCenter)

        # Create and add the login button
        login_button = QPushButton("Login")
        login_button.setFixedSize(100,30)
        login_button.setStyleSheet("background-color: #000080; color: white; ")

        login_button.clicked.connect(s.__login_on_click)
        s._login_layout.addWidget(login_button, alignment=Qt.AlignCenter)


        s._login_central_wid.setLayout(s._login_layout)
        s._login_window.show()


    def __login_on_click(s):
        
            s.user = s._username_input.text()
            s.pas = s._password_input.text()
            if s.user=="" or s.pas=="": # first check if something is wrtiten
                s._err_label.setText("All fields should be filled")
                return
            
        
            try:
                s._skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s._skt.connect((DEFAULT_IP,DEFAULT_PORT))
            except Exception:
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
                seed_phrase = decrypt_data(enc_seed, s.pas)

                seed = bip39.phrase_to_seed(seed_phrase.decode())

                private_key_bytes = hashlib.sha256(seed).digest()
                private_key  = SigningKey.from_string(private_key_bytes, NIST256p)

                s._login_window.close() # close the login window

                s._logged_in = QWidget(s._window)
                s._logged_in.setGeometry(s._window.width()-120, s._window.height()-62, 120, 62)
                s._logged_in.setStyleSheet("""
                QWidget {
                    color: white; font: 15px; background-color: #000080; border:none            
                }

                """)
                logg_layout = QVBoxLayout(s._logged_in)
                logg_layout.setSpacing(3)
                l = QLabel("Logged in as:")
                us = QLabel(s.user)
                logg_layout.addWidget(l, alignment=Qt.AlignCenter)
                logg_layout.addWidget(us, alignment=Qt.AlignCenter)
                s._logged_in.setLayout(logg_layout)
                
                s._logged_in.show()
                s._logged_in.raise_()
                s.__connect_event(s.user, private_key, s._skt)

                return

            else:
                s._err_label = QLabel(result[1], s._login_central_wid)
                s._err_label.setStyleSheet("color: red; font-weight: bold;")
                s._login_layout.insertWidget(4,s._err_label, alignment=Qt.AlignCenter)

        
            
    def openreggui(s):
        s._reg_window = SecWindow(s._window) 
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

        s._err_label = QLabel("", s._reg_central_wid)
        s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
        s._reg_layout.addWidget(s._err_label, alignment=Qt.AlignCenter)

        # Create and add the login button
        reg_button = QPushButton("Register")
        reg_button.setFixedSize(100,30)
        reg_button.setStyleSheet("background-color: #000080; color: white; ")

        reg_button.clicked.connect(s.__reg_on_click)
        s._reg_layout.addWidget(reg_button, alignment=Qt.AlignCenter)

        s._reg_layout.insertSpacing(6, 8)
        s._reg_central_wid.setLayout(s._reg_layout)
        s._reg_window.show()
            
    def __reg_on_click(s):
        s.user = s._username_input.text()
        s.pas = s._password_input.text()

        if s.user=="" or s.pas=="": # first check if something is wrtiten
            s._err_label.setText("All fields should be filled")
            return
    
        try:    
            s._skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s._skt.connect((DEFAULT_IP,DEFAULT_PORT))     

        except Exception: # if no node
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
        else:
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
                logg_layout = QVBoxLayout(s._logged_in)
                logg_layout.setSpacing(3)
                l = QLabel("Logged in as:")
                us = QLabel(s.user)
                logg_layout.addWidget(l, alignment=Qt.AlignCenter)
                logg_layout.addWidget(us, alignment=Qt.AlignCenter)
                s._logged_in.setLayout(logg_layout)
                
                s._logged_in.show()
                s._logged_in.raise_()

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
    
    # Fix tooltips application-wide

        s._balance_window = SecWindow(s._window)
        s._balance_window.setAttribute(Qt.WA_TranslucentBackground)
        s._balance_window.setWindowTitle("Balances")
        s._balance_window.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        s._balance_window.setFixedSize(650, 450)

        balance_center = s._window.geometry().center()
        b_size = s._balance_window.size()
        s._balance_window.move(
            balance_center.x() - b_size.width() // 2,
            balance_center.y() - b_size.height() // 2
        )

        s._balance_icon = TaskbarButton(s._balance_window, BAL_ICON,s._taskbar)
        s._task_layout.addWidget(s._balance_icon)

        s._balance_window.setStyleSheet("""
        QToolTip {
            color: white;
            background-color: #000080;
            border: 1px solid white;
        }
        """)
        # Central widget
        s._balance_central_wid = QWidget(s._balance_window)
        s._balance_central_wid.setStyleSheet(
            "background-color: #ece9d8; border: 4px solid #000080; border-radius: 2px;"
        )
        s._balance_window.setCentralWidget(s._balance_central_wid)

        # Title bar
        s._balance_title_bar = DraggableTitleBar(f"Balances - {s.user}", s._balance_window)
        s._balance_title_bar.setStyleSheet(
            "background-color: #000080; color: white; border-radius: 2px 2px 0 0;"
        )
        s._balance_title_bar.setFixedHeight(30)
        s._balance_title_bar.setGeometry(0, 0, s._balance_window.width(), 30)

        #s._greet_label = QLabel(f"           Your balances are:",s._balance_central_wid)
       # s._greet_label.setStyleSheet("color:black; border: none; padding: 2px; font: bold 24px;")
        #s._greet_label.move(10,35)
        #s._greet_label.show()
        # Main layout
        main_layout = QHBoxLayout(s._balance_central_wid)
        main_layout.setContentsMargins(20, 50, 20, 20)
        main_layout.setSpacing(25)
        

        # Token grid
        token_grid = QGridLayout()
        
        token_grid.setHorizontalSpacing(25)
        token_grid.setVerticalSpacing(20)
        # Load balances

        conn = sqlite3.connect('databases/Client/blockchain.db')
        cursor = conn.cursor()
        address = s._client.get_address()
        cursor.execute('SELECT balance, token from balances WHERE address = ?', (address,))
        balances = cursor.fetchall()
        
        if not balances:
            balances = [(address, '0', ticker, '1') for ticker in s.tickerlist]
            cursor.executemany('INSERT INTO balances VALUES (?, ?, ?, ?)', balances) 
            conn.commit()
            cursor.execute('SELECT balance, token from balances WHERE address = ?', (address,))
            balances = cursor.fetchall()
        conn.close()

        balance_dict = {}
        for b in balances:
            balance_dict[b[1]] = b[0]

        # Add tokens to grid
        for index, (ticker, full_name) in enumerate(zip(s.tickerlist, s.token_name_list)):
            row = index // 2
            col = index % 2
            try:
                balance = balance_dict[ticker]
            except KeyError:
                balance = 0.0
            #balance = '0.0'

            # Create token widget
            token_widget = QWidget()
            token_widget.setFixedSize(200, 60)
            token_layout = QHBoxLayout(token_widget)
            token_layout.setContentsMargins(0, 0, 0, 0)
            token_layout.setSpacing(0)

            # Ticker label (left)
            ticker_label = HoverLabel(f"${ticker}", full_name, token_widget)
            ticker_label.setStyleSheet(
                "background-color: #000080;"
                "color: white;"
                "font: bold 15px;"
            )
            ticker_label.setFixedSize(100, 60)
            ticker_label.setAlignment(Qt.AlignCenter)

            # Balance label (right)
            balance_label = QLabel(str(balance), token_widget)
            balance_label.setStyleSheet(
                "color: black;"
                "font: bold 17px;"
                "border: 4px solid #000080;"
            )
            balance_label.setFixedSize(100, 60)
            balance_label.setAlignment(Qt.AlignCenter)

            token_layout.addWidget(ticker_label)
            token_layout.addWidget(balance_label)
            token_grid.addWidget(token_widget, row, col)

        # Button layout (center-right)
        button_layout = QVBoxLayout()
        button_layout.setSpacing(20)

        send_button = QPushButton("Send")
        send_button.clicked.connect(s.create_send_window)
        receive_button = QPushButton("Receive")
        receive_button.clicked.connect(s.__recv_window)

        for button in [send_button, receive_button]:
            button.setStyleSheet(
                "QPushButton {"
                "background-color: #000080;"
                "color: white;"
                "font: bold 16px;"
                "border-radius: 15px;"
                "padding: 10px;"
                "min-width: 120px;"
                "}"
                "QPushButton:hover {"
                "background-color: #1a1a8c;"
                "}"
            )
            button.setFixedSize(130, 50)
            button.setCursor(Qt.PointingHandCursor)
            button_layout.addWidget(button)

        # Add layouts to main layout
        main_layout.addLayout(token_grid)
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addLayout(button_layout)

        s._balance_window.show()

    def create_send_window(s):
        # Window configuration
        s._send_window = SecWindow(s._balance_window) 

        s._send_window.setAttribute(Qt.WA_TranslucentBackground)
        s._send_window.setWindowTitle("Send Tokens")
        s._send_window.setWindowFlags(Qt.FramelessWindowHint|Qt.Window|Qt.WindowStaysOnTopHint)
        s._send_window.setGeometry(
            int(s._balance_window.width()/2)-250, 
            int(s._balance_window.height()/2)-150, 
            500, 300
        )

        balance_center = s._balance_window.geometry().center()
        send_size = s._send_window.size()
        s._send_window.move(
            balance_center.x() - send_size.width() // 2,
            balance_center.y() - send_size.height() // 2
        )

        # Window styling
        s._send_window.setStyleSheet('''
            QLineEdit, QComboBox {
                background-color: white;
                border: 2px solid #000080;
                border-radius: 4px;
                font: 15px;
                padding: 2px;
            }
        ''')
        
        # Central widget setup
        s._send_central_wid = QWidget(s._send_window)
        s._send_central_wid.setStyleSheet("background-color: #ece9d8; border: 4px solid #000080; border-radius: 2px;")
        
        # Window geometry
        
        s._send_window.setFixedSize(500, 300)
        
        # Central widget geometry
        s._send_central_wid.setGeometry(0, 30, s._send_window.width(), s._send_window.height()-30)
        s._send_central_wid.setFixedSize(s._send_window.width(), s._send_window.height()-30)
        
        # Title bar
        title_bar = DraggableTitleBar("Send Tokens", s._send_window)
        title_bar.setStyleSheet("background-color: #000080; color: white; border-radius: 2px 2px 0 0;")
        title_bar.setGeometry(0, 0, s._send_window.width(), 30)
        title_bar.setFixedSize(s._send_window.width(), 30)
        title_bar.raise_()
        
        # Main layout
        send_layout = QVBoxLayout(s._send_central_wid)
        send_layout.setSpacing(5)
        
        # Recipient Address input
        address_label = QLabel("Recipient Address:", s._send_central_wid)
        address_label.setStyleSheet("font: bold 16px; border: none;")
        send_layout.addWidget(address_label, alignment=Qt.AlignCenter)
        
        s._address_input = QLineEdit(s._send_central_wid)
        s._address_input.setPlaceholderText("     Enter wallet address: (RRabc123...)")
        s._address_input.setFixedSize(300, 30)
        send_layout.addWidget(s._address_input, alignment=Qt.AlignCenter)
        
        # Token selection
        token_label = QLabel("Token:", s._send_central_wid)
        token_label.setStyleSheet("font: bold 16px; border: none;")
        send_layout.addWidget(token_label, alignment=Qt.AlignCenter)
        
        s._token_select = QComboBox(s._send_central_wid)
        s._token_select.addItems(s.tickerlist)  # Assuming s.tickerlist exists
        s._token_select.setFixedSize(100, 30)
        s._token_select.setStyleSheet("QComboBox { text-align: center; padding-left: 28px;} ")
        send_layout.addWidget(s._token_select, alignment=Qt.AlignCenter)
        
        # Amount input
        amount_label = QLabel("Amount:", s._send_central_wid)
        amount_label.setStyleSheet("font: bold 16px; border: none;")
        send_layout.addWidget(amount_label, alignment=Qt.AlignCenter)
        
        s._amount_input = QLineEdit(s._send_central_wid)
        s._amount_input.setPlaceholderText("0.00")
        s._amount_input.setFixedSize(100, 30)
        s._amount_input.setAlignment(Qt.AlignCenter)
        send_layout.addWidget(s._amount_input, alignment=Qt.AlignCenter)

        s._err_label = QLabel("", s._send_central_wid)
        s._err_label.setStyleSheet("color: red; font-weight: bold; border: none")
        send_layout.addWidget(s._err_label, alignment=Qt.AlignCenter)
        # Send button
        send_button = QPushButton("SEND", s._send_central_wid)
        send_button.setStyleSheet('''
            QPushButton {
                background-color: #000080;
                color: white;
                font: bold 16px;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #1a1a8c;
            }
        ''')
        send_button.setFixedSize(150, 40)
        

        send_button.clicked.connect(s.__send_transaction)  
        send_layout.addWidget(send_button, alignment=Qt.AlignCenter)
        
        s._send_central_wid.setLayout(send_layout)
        s._send_window.show()

    def __send_transaction(s):
        recv_address = s._address_input.text()
        amount = s._amount_input.text()
        token = s._token_select.currentText()

        if not recv_address or not amount or not token:
            s._err_label.setText("All fields should be filled")
            return
        a = is_valid_amount(amount)

        if a==False:
            s._err_label.setText("Invalid amount, must be a positive number")
            return
        
        if not check_address(recv_address):
            s._err_label.setText("Invaild address, wrong format")
            return
        
        address = s._client.get_address()
        if address == recv_address:
            s._err_label.setText("Invalid address, can`t send to yourself")
            return
        conn = sqlite3.connect('databases/Client/blockchain.db')
        cursor = conn.cursor()
        

        cursor.execute(f'''
        SELECT balance, nonce FROM balances WHERE address='{address}' AND token='{token}'
        ''')
        balance, nonce = cursor.fetchone()

        if float(amount)>float(balance):
            s._err_label.setText(f"Invalid amount, spending more then your balance ({balance})")
            return
        
        send(f"Is address valid?>{recv_address}", s._client.getsocket())
        time.sleep(0.02)
        result = s._client.get_message()
        if result!="Valid":
            s._err_label.setText(result)
            return

        if s._client.send_transaction(token, amount, recv_address):
            s._err_label.setStyleSheet("color: green")
            s._err_label.setText(f"Successfully sent transaction to {recv_address}, waiting for validation")
        else:
            s._err_label.setText(f"Failed to send transaction to {recv_address}")

    def __recv_window(s):
        s._recv_window = SecWindow(s._balance_window) 

        s._recv_window.setAttribute(Qt.WA_TranslucentBackground)
        s._recv_window.setWindowTitle("Recieve")
        s._recv_window.setWindowFlags(Qt.FramelessWindowHint|Qt.Window|Qt.WindowStaysOnTopHint)
        s._recv_window.setGeometry(
            int(s._balance_window.width()/2)-250, 
            int(s._balance_window.height()/2)-150, 
            370, 200
        )

        balance_center = s._balance_window.geometry().center()
        send_size = s._recv_window.size()
        s._recv_window.move(
            balance_center.x() - send_size.width() // 2,
            balance_center.y() - send_size.height() // 2
        )

        central_wid = QWidget(s._recv_window)
        central_wid.setStyleSheet("background-color: #ece9d8; border: 4px solid #000080; border-radius: 2px;")

        central_wid.setGeometry(0, 30, s._recv_window.width(), s._recv_window.height()-30)
        central_wid.setFixedSize(s._recv_window.width(), s._recv_window.height()-30)

        title_bar = DraggableTitleBar("Recieve", s._recv_window)
        title_bar.setStyleSheet("background-color: #000080; color: white; border-radius: 2px 2px 0 0;")
        title_bar.setGeometry(0, 0, s._recv_window.width(), 30)
        title_bar.setFixedSize(s._recv_window.width(), 30)
        title_bar.raise_()

        layout = QVBoxLayout(central_wid)
        layout.setSpacing(10)

        recv_label = QLabel("Your Address:",central_wid)
        recv_label.setStyleSheet("font: bold 16px; border: none; color:black")
        layout.addWidget(recv_label, alignment=Qt.AlignCenter)

        adr_label = QLabel(s._client.get_address(),central_wid)
        adr_label.setStyleSheet("font: bold 14px; color:black")
        adr_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        adr_label.setCursor(Qt.IBeamCursor)
        layout.addWidget(adr_label, alignment=Qt.AlignCenter)

        s.copied = QLabel("",central_wid)
        s.copied.setStyleSheet("font: bold 16px; color: #000080; border: none")
        layout.addWidget(s.copied, alignment=Qt.AlignCenter)

        s.copy_button = QPushButton("Copy",central_wid)
        s.copy_button.clicked.connect(s.__copy)
        s.copy_button.setStyleSheet('''
            QPushButton {
                background-color: #000080;
                color: white;
                font: bold 16px;
                border-radius: 8px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #1a1a8c;
            }
        ''')
        s.copy_button.setFixedSize(150, 40)
        layout.addWidget(s.copy_button, alignment=Qt.AlignCenter)

        central_wid.setLayout(layout)
        s._recv_window.show()

    def __copy(s):
        QApplication.clipboard().setText(s._client.get_address())
        s.copy_button.setStyleSheet('''
            QPushButton {
                background-color: white;
                color: #000080;
                font: bold 16px;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: grey;
            }
        ''')
        s.copied.setText("Copied!")

    def __open_history(s):
        s._history_window = SecWindow(s._window)
        s._history_window.setAttribute(Qt.WA_TranslucentBackground)
        s._history_window.setWindowTitle("History")
        s._history_window.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        s._history_window.setFixedSize(750, 450)  # Increased width

        # Center window
        balance_center = s._window.geometry().center()
        b_size = s._history_window.size()
        s._history_window.move(
            balance_center.x() - b_size.width() // 2,
            balance_center.y() - b_size.height() // 2
        )

        # Taskbar icon (if needed)
        s._history_icon = TaskbarButton(s._history_window, HIS_ICON, s._taskbar)
        s._task_layout.addWidget(s._history_icon)

        # Window styling
        s._history_window.setStyleSheet("""
        QToolTip {
            color: white;
            background-color: #000080;
            border: 1px solid white;
        }
        """)

        # Central widget
        s._history_central_wid = QWidget(s._history_window)
        s._history_central_wid.setStyleSheet(
            "background-color: #ece9d8; border: 4px solid #000080; border-radius: 2px;"
        )
        s._history_window.setCentralWidget(s._history_central_wid)

        title_bar = DraggableTitleBar(f"History - {s.user}", s._history_window)
        title_bar.setStyleSheet(
            "background-color: #000080; color: white; border-radius: 2px 2px 0 0;"
        )
        title_bar.setFixedHeight(30)
        title_bar.setGeometry(0, 0, s._history_window.width(), 30)
        # Main layout

        # Create table
        s.history_table = QTableWidget(s._history_central_wid)
        s.history_table.setGeometry(10,40, 730, 400)
        s.history_table.setColumnCount(5)
        s.history_table.setHorizontalHeaderLabels(["Time", "Sender", "Receiver", "Token", "Amount"])
        s.history_table.verticalHeader().setVisible(True)
        s.history_table.verticalHeader().setDefaultSectionSize(25)  # Row height
        s.history_table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #000080;
                color: white;
                padding: 4px;
                border: 1px solid white;
                font-weight: bold;
            }
        """)
        # Column width configuration
        s.history_table.setColumnWidth(0, 150)  # Time
        s.history_table.setColumnWidth(1, 200)  # Sender (wider)
        s.history_table.setColumnWidth(2, 200)  # Receiver (wider)
        s.history_table.setColumnWidth(3, 80)   # Token (narrower)
        s.history_table.setColumnWidth(4, 80)   # Amount (narrower)
        
        # Column resize behavior
        s.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        s.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        s.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        s.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        s.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        s.history_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)

        s.history_table.horizontalHeader().setMinimumSectionSize(50)  # Prevent cutting off

        # Update the QHeaderView::section style to include font-size
        s.history_table.horizontalHeader().setStyleSheet("""
        QHeaderView::section {
            background-color: #000080;
            color: white;
            padding: 6px;
            border: 1px solid white;
            font-weight: bold;
            font-size: 13px;
        }
        """)
        # Table styling
        s.history_table.setStyleSheet("QTableCornerButton::section {background-color: #000080;border: 1px solid white;}")
        s.history_table.setStyleSheet("""
            QTableWidget {
                background-color: #ece9d8;
                border: 1px solid #000080;
                font-size: 12px;
                gridline-color: #000080;
            }
            
            QTableWidget::item {
                padding: 3px;
            }
            QScrollBar:vertical {
                border: 1px solid #000080;
                background: #ece9d8;
                width: 14px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #000080;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
 

        # Add sample data (20 transactions to ensure scrolling)
        sample_transactions = s._translist
        if sample_transactions != []:

            s.history_table.setRowCount(len(sample_transactions))
            for row, transaction in enumerate(sample_transactions):
                for col, data in enumerate(transaction):
                    item = QTableWidgetItem(data)
                    item.setTextAlignment(Qt.AlignCenter)
                    s.history_table.setItem(row, col, item)
        # Scroll to bottom to show newest transactions
            s.history_table.scrollToBottom()
        # Add title bar (from original implementation)
        

        s._history_window.show()

    

    def add_to_history(s, translist):
        s._translist.extend(translist)
        #adr = s._client.get_address()
        #for t in translist:
        #    if t[1]==adr:
                
    def notif_click(s):
        if not s._history_window==None:
            if s._history_window.isVisible():
                s._history_window.activateWindow()  # Bring the window to the front
            else:
                s._history_window.show()  # Show the window if it's hidden
        
        else:
            s.__open_history()
            
    def notif_add(s,typpe,tr):
        s.notif_bridge.notif_add(typpe, tr)


    
    def draw(s):
        app = QApplication([])

        s._window.show()
        app.exec_()
    
    
    def __connect_event(s, user,  p_key: SigningKey, skt):


        try:
            # Handle failure on casting from string to int

            s._client: ClientBL= ClientBL(user, p_key, skt, s.show_error, s.add_to_history, s.notif_add)
            s.notif_bridge = NotificationBridge(s.notif_manager, s._client.get_address())
            # check if we successfully created socket
            # and ready to go
            if not s._client.get_success():
                raise Exception("failed to create and setup client bl")
            else:
                s.title_bar.set_on_close(s._client.disconnect)
                s._reg_cut.setParent(None)
                s._login_cut.setParent(None)

                s._balance_cut = DesktopShortcut(BAL_ICON, "Balance",s.openbalances ,s._central_widget)
                s._balance_cut.setFixedSize(86,80)

                s._history_cut = DesktopShortcut(HIS_ICON, "History", s.__open_history, s._central_widget)
                s._history_cut.setFixedSize(86,80)
                
                
                

                s._cut_login_layout.addWidget(s._balance_cut)
                s._cut_login_layout.addWidget(s._history_cut)    


                

        except Exception as e:
            # If our problem occurred before the client
            # mean that our client will be None
            error = s._client and s._client.get_last_error() or e
            traceback.print_exc()
            write_to_log(f" 路 Client GUI 路 an error has occurred : {error}")
    

    def __send_data_event(s):
        s._client.send_transaction()

    def show_error(s, title, error):
        QMessageBox.information(s._central_widget, title, error)

def main():
    n = ClientGUI()
    n.draw()



if __name__ == "__main__":
    main()
    

        