from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QApplication)
from PyQt5.QtCore import Qt

class StylishWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Input Window")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setStyleSheet('''
            QLineEdit {
                background-color: white;
                border: 4px solid #000080;
                border-radius: 8px;
                font: 16px;
            }
        ''')
        
        # Window size and position (centered)
        self.setFixedSize(400, 200)
        
        # Central widget
        central_widget = QWidget(self)
        central_widget.setStyleSheet("""
            background-color: #ece9d8; 
            border: 4px solid #000080; 
            border-radius: 2px;
        """)
        central_widget.setGeometry(0, 30, self.width(), self.height()-30)
        self.setCentralWidget(central_widget)
        
        # Title bar (simplified)
        title_bar = QLabel("Input Window", self)
        title_bar.setStyleSheet("""
            background-color: #000080; 
            color: white;
            font: bold 16px;
            padding-left: 10px;
            border-radius: 0;
        """)
        title_bar.setGeometry(0, 0, self.width(), 30)
        title_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Layout and widgets
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Input label
        input_label = QLabel("Enter your value:")
        input_label.setStyleSheet("border: none; font: bold 20px;")
        input_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(input_label)
        
        # Input field
        self.input_field = QLineEdit()
        self.input_field.setFixedHeight(30)
        layout.addWidget(self.input_field)
        
        # Button
        submit_button = QPushButton("Submit")
        submit_button.setFixedSize(100, 30)
        submit_button.setStyleSheet("""
            background-color: #000080; 
            color: white;
            border: none;
            font: bold 14px;
        """)
        submit_button.clicked.connect(self.on_submit)
        layout.addWidget(submit_button, alignment=Qt.AlignCenter)
        
        # Add some spacing
        layout.insertSpacing(2, 10)
        
    def on_submit(self):
        print("Submitted value:", self.input_field.text())

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = StylishWindow()
    window.show()
    sys.exit(app.exec_())