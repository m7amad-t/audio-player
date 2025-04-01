from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush

class PlayerStateOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Initialize animation first
        self.opacity = 1.0
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        
        # State label
        self.state_label = QLabel()
        self.state_label.setStyleSheet("""
            QLabel {
                color: #00BFFF;
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        self.layout.addWidget(self.state_label, alignment=Qt.AlignCenter)
        
        # Message label
        self.message_label = QLabel()
        self.message_label.setStyleSheet("""
            QLabel {
                color: #6C7086;
                font-size: 14px;
                background-color: transparent;
            }
        """)
        self.layout.addWidget(self.message_label, alignment=Qt.AlignCenter)
        
        # Initial state
        self.set_state("no_file")

    def set_state(self, state):
        """Update the overlay state and message"""
        states = {
            "no_file": ("No File Selected", "Click 'Open' to select an audio file"),
            "stopped": ("Stopped", "Press 'Play' to start playback"),
            "loading": ("Loading...", "Please wait while the file loads"),
            "error": ("Error", "Failed to load audio file"),
        }
        
        if state in states:
            title, message = states[state]
            self.state_label.setText(title)
            self.message_label.setText(message)
            self.show()
            self.fade_in()
        else:
            self.hide()

    def fade_in(self):
        """Fade in the overlay"""
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()

    def fade_out(self):
        """Fade out the overlay"""
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.start()

    def paintEvent(self, event):
        """Custom paint event to create a semi-transparent background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create semi-transparent dark background
        painter.setBrush(QBrush(QColor(25, 24, 37, 200)))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        
        # Optional: Add subtle border
        painter.setPen(QPen(QColor("#00BFFF", 30), 1))
        painter.drawRect(self.rect())

    def resizeEvent(self, event):
        """Ensure the overlay covers the entire parent widget"""
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())
