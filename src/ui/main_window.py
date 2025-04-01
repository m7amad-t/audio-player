from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLabel, QFileDialog,
                           QStyle, QSlider)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPalette, QColor, QIcon
import pygame
import soundfile as sf
import time
from ..core.audio_engine import AudioEngine
from .widgets.waveform_visualizer import WaveformVisualizer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio_engine = AudioEngine()
        self.is_playing = False
        self.current_file = None
        self.seeking = False
        self.total_duration = 0
        self.start_time = 0
        self.pause_position = 0
        self.init_ui()
        self.apply_dark_theme()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #2d2d2d;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: #ffffff;
                min-width: 120px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #444444;
            }
            QPushButton:disabled {
                background-color: #252525;
                color: #666666;
            }
            QLabel {
                color: #ffffff;
                padding: 5px;
            }
            QStatusBar {
                background-color: #252525;
                color: #888888;
            }
            QStatusBar::item {
                border: none;
            }
        """)

    def format_time(self, seconds):
        """Convert seconds to mm:ss format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def init_ui(self):
        self.setWindowTitle('Audio Player')
        self.setGeometry(300, 300, 800, 500)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # File info section
        self.file_label = QLabel('No file selected')
        self.file_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #252525;
                border-radius: 8px;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.file_label)

        # Add waveform visualizer
        self.visualizer = WaveformVisualizer(central_widget, width=7, height=4)
        layout.addWidget(self.visualizer)

        # Add progress bar section
        progress_layout = QHBoxLayout()
        
        # Current time label
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("""
            QLabel {
                color: #888888;
                min-width: 50px;
            }
        """)
        progress_layout.addWidget(self.current_time_label)
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(1000)  # Using 1000 for smoother sliding
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #333333;
                margin: 2px 0;
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                background: #00BFFF;
                border: none;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }

            QSlider::handle:horizontal:hover {
                background: #33CCFF;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }

            QSlider::sub-page:horizontal {
                background: #00BFFF;
                border-radius: 2px;
            }
        """)
        self.progress_slider.sliderPressed.connect(self.start_seeking)
        self.progress_slider.sliderReleased.connect(self.stop_seeking)
        self.progress_slider.valueChanged.connect(self.seek_position)
        progress_layout.addWidget(self.progress_slider)
        
        # Total time label
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setStyleSheet("""
            QLabel {
                color: #888888;
                min-width: 50px;
            }
        """)
        progress_layout.addWidget(self.total_time_label)
        
        layout.addLayout(progress_layout)

        # Control panel
        control_panel = QHBoxLayout()
        control_panel.setSpacing(10)
        
        # Common button style with centered content and emoji support
        button_style = """
            QPushButton {
                font-weight: bold;
                padding: 8px 16px;
                min-width: 120px;
                text-align: center;
                font-size: 14px;
            }
            QPushButton QIcon {
                margin-right: 5px;
            }
        """
        
        # Play/Pause button with emoji
        self.play_button = QPushButton('▶️ Play')  # Unicode play symbol
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setStyleSheet(button_style)
        
        # Stop button with emoji
        self.stop_button = QPushButton('⏹️ Stop')  # Unicode stop symbol
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setStyleSheet(button_style)
        
        # Load button with emoji
        load_button = QPushButton('📂 Load Audio')  # Unicode folder symbol
        load_button.clicked.connect(self.load_file)
        load_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #0066cc;
            }
            QPushButton:hover {
                background-color: #0077ee;
            }
            QPushButton:pressed {
                background-color: #0055bb;
            }
        """)

        # Add spacers to center the control buttons
        control_panel.addStretch()
        control_panel.addWidget(self.play_button)
        control_panel.addWidget(self.stop_button)
        control_panel.addStretch()

        # Add all components to main layout
        layout.addLayout(control_panel)
        layout.addWidget(load_button)

        # Status bar
        self.statusBar().showMessage('Ready')

        # Initialize timer for updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_time_display)
        self.update_timer.start(16)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio Files (*.mp3 *.wav *.ogg);;All Files (*)"
        )

        if file_path:
            try:
                # Load audio data for visualization
                audio_data, sample_rate = sf.read(file_path)
                self.visualizer.set_audio_data(audio_data, sample_rate)
                
                # Load audio for playback
                if self.audio_engine.load_file(file_path):
                    self.current_file = file_path
                    self.total_duration = len(audio_data) / sample_rate
                    self.total_time_label.setText(self.format_time(self.total_duration))
                    self.play_button.setEnabled(True)
                    self.stop_button.setEnabled(True)
                    self.progress_slider.setEnabled(True)
                    self.file_label.setText(f'Loaded: {file_path.split("/")[-1]}')
                    self.is_playing = False
                    self.pause_position = 0
                    self.play_button.setText('Play')
                    self.statusBar().showMessage(f'Loaded {file_path}')
                else:
                    self.statusBar().showMessage(f'Failed to load {file_path}')
            except Exception as e:
                self.statusBar().showMessage(f'Error: {str(e)}')

    def toggle_playback(self):
        if not self.is_playing:
            self.audio_engine.play(start_pos=self.pause_position)
            self.is_playing = True
            self.play_button.setText('⏸️ Pause')  # Unicode pause symbol
            self.start_time = time.time() - self.pause_position
            self.visualizer.timer.start(self.visualizer.update_interval)
            self.statusBar().showMessage('Playing')
        else:
            self.audio_engine.pause()
            self.is_playing = False
            self.play_button.setText('▶️ Play')  # Unicode play symbol
            self.pause_position = time.time() - self.start_time
            self.visualizer.timer.stop()
            self.statusBar().showMessage('Paused')

    def start_seeking(self):
        """Called when user starts dragging the slider"""
        self.seeking = True
        if self.is_playing:
            self.audio_engine.pause()

    def stop_seeking(self):
        """Called when user releases the slider"""
        self.seeking = False
        if self.is_playing:
            seek_time = (self.progress_slider.value() / 1000.0) * self.total_duration
            self.pause_position = seek_time
            self.audio_engine.play(start_pos=seek_time)

    def seek_position(self, value):
        """Called when slider value changes"""
        if self.seeking:
            current_time = (value / 1000.0) * self.total_duration
            self.current_time_label.setText(self.format_time(current_time))

    def stop_playback(self):
        self.audio_engine.stop()
        self.play_button.setText('▶️ Play')  # Unicode play symbol
        self.is_playing = False
        self.pause_position = 0
        self.progress_slider.setValue(0)
        self.current_time_label.setText("00:00")
        self.visualizer.timer.stop()
        self.visualizer.reset_visualization()
        self.statusBar().showMessage('Stopped')

    def update_time_display(self):
        if self.is_playing and not self.seeking:
            current_pos = pygame.mixer.music.get_pos() / 1000.0
            if current_pos >= 0:
                current_pos += self.pause_position
                # Update time label
                self.current_time_label.setText(self.format_time(current_pos))
                # Update slider
                slider_value = int((current_pos / self.total_duration) * 1000) if self.total_duration > 0 else 0
                self.progress_slider.blockSignals(True)
                self.progress_slider.setValue(slider_value)
                self.progress_slider.blockSignals(False)
            
            self.visualizer.update_plot()

    def closeEvent(self, event):
        self.update_timer.stop()
        self.audio_engine.cleanup()
        event.accept()












