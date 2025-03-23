import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import Qt

class DraggableTitleBar(QLabel):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.parent = parent
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(30)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.drag_start_position = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.parent.move(self.parent.pos() + event.globalPos() - self.parent.drag_start_position)
            self.parent.drag_start_position = event.globalPos()

class BalancesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set window properties
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Balances")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setGeometry(100, 100, 600, 400)
        self.setFixedSize(600, 400)

        # Create a central widget
        self.central_wid = QWidget(self)
        self.central_wid.setStyleSheet(
            "background-color: #ece9d8; border: 4px solid #000080; border-radius: 2px;"
        )
        self.central_wid.setGeometry(0, 30, self.width(), self.height() - 30)
        self.central_wid.setFixedSize(self.width(), self.height() - 30)
        self.setCentralWidget(self.central_wid)

        # Create a custom title bar
        self.title_bar = DraggableTitleBar("Balances", self)
        self.title_bar.setStyleSheet(
            "background-color: #000080; color: white; font: bold 16px; border-radius: 2px 2px 0 0;"
        )
        self.title_bar.setGeometry(0, 0, self.width(), 30)
        self.title_bar.setFixedSize(self.width(), 30)
        self.title_bar.raise_()

        # Create a layout for the tokens and buttons
        main_layout = QHBoxLayout(self.central_wid)

        # Create a grid layout for the tokens (2 columns)
        token_layout = QGridLayout()

        # List of token names
        self.token_name_list = [
            "Token1", "Token2", "Token3", "Token4", "Token5",
            "Token6", "Token7", "Token8", "Token9", "Token10", "Token11"
        ]

        # Add tokens to the grid layout
        for index, token_name in enumerate(self.token_name_list):
            row = index // 2  # Two tokens per row
            col = index % 2   # Two columns

            # Create a label with styled text
            token_label = QLabel()
            token_label.setText(
                f'<span style="background-color: #000080; color: white; font-weight: bold; padding: 2px;">${token_name}</span> '
                f'<span style="color: black;">{token_name}</span>'
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
        self.central_wid.setLayout(main_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = BalancesWindow()
    window.show()

    sys.exit(app.exec_())