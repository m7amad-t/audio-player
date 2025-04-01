from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLabel, QFileDialog, QComboBox,
                           QStyle, QSlider, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QPalette, QColor, QIcon
import pygame
import soundfile as sf
import time
from ..core.audio_engine import AudioEngine
from .widgets.waveform_visualizer import WaveformVisualizer, VisualizationType
from pathlib import Path

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
                background-color: #191825;
            }
            QWidget {
                background-color: #191825;
                color: #ffffff;
            }
            QPushButton {
                background-color: #865DFF;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: #ffffff;
                min-width: 120px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #2e0249;
            }
            QPushButton:pressed {
                background-color: #2e0279;
            }
            QPushButton:disabled {
                background-color: #19182f;
                color: #666666;
            }
            QLabel {
                color: #ffffff;
                padding: 5px;
            }
            QStatusBar {
                background-color: #19182f;
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
        self.setGeometry(100, 100, 1000, 700)
        icon_base_path = Path(__file__).parent / 'assets'
        # Set window icon
        icon_path = icon_base_path / 'icon.png'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            print(f"Warning: Icon not found at {icon_path}")

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # File info section - Fixed height
        self.file_label = QLabel('No file selected')
        self.file_label.setFixedHeight(50)
        self.file_label.setStyleSheet("""
            QLabel {
                padding: 0 15px;
                background-color: #19182f;
                border-radius: 8px;
                font-size: 13px;
                min-height: 50px;
                max-height: 50px;
                line-height: 50px;
                qproperty-alignment: AlignLeft | AlignVCenter;
            }
        """)
        layout.addWidget(self.file_label)

        # Visualization type selector
        viz_selector_container = QWidget()
        viz_selector_layout = QHBoxLayout(viz_selector_container)
        viz_selector_layout.setContentsMargins(0, 0, 0, 10)
        
        viz_label = QLabel("Visualization:")
        viz_label.setStyleSheet("color: #888888;")
        viz_selector_layout.addWidget(viz_label)
        
        self.viz_combo = QComboBox()
        self.viz_combo.addItems([viz_type.value for viz_type in VisualizationType])
        self.viz_combo.setFixedWidth(150)
        self.viz_combo.setStyleSheet("""
            QComboBox {
                background-color: #19182f;
                color: #888888;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:hover {
                border: 1px solid #4a4a4a;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(src/ui/assets/down-arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        self.viz_combo.currentTextChanged.connect(self._on_viz_type_changed)
        viz_selector_layout.addWidget(self.viz_combo)
        viz_selector_layout.addStretch()
        
        layout.addWidget(viz_selector_container)

        # Visualization section
        self.visualizer = WaveformVisualizer(central_widget, width=7, height=4)
        layout.addWidget(self.visualizer, 1) 
        
        # Progress section - Fixed height
        progress_widget = QWidget()
        progress_widget.setFixedHeight(50)
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        # Current time label
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("""
            QLabel {
                color: #888888;
                min-width: 50px;
                qproperty-alignment: AlignCenter;
            }
        """)
        progress_layout.addWidget(self.current_time_label)
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(1000)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #333333;
                margin: 2px 0;
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                background: #865dff;
                border: none;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }

            QSlider::handle:horizontal:hover {
                background: #ffffff;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }

            QSlider::sub-page:horizontal {
                background: #865daa;
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
                qproperty-alignment: AlignCenter;
            }
        """)
        progress_layout.addWidget(self.total_time_label)
        
        layout.addWidget(progress_widget)

        # Control panel - Fixed height
        control_widget = QWidget()
        control_widget.setFixedHeight(60)
        control_panel = QHBoxLayout(control_widget)
        control_panel.setContentsMargins(0, 0, 0, 0)
        control_panel.setSpacing(10)
        
        # Button style
        button_style = """
            QPushButton {
                font-weight: bold;
                padding: 8px 16px;
                min-width: 120px;
                min-height: 40px;
                max-height: 40px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }
        """
        
        # Add spacers and buttons to control panel
        control_panel.addStretch()
        
        # Backward 10s button
        self.backward_button = QPushButton()
        self.backward_button.setEnabled(False)
        if (icon_base_path / 'minus_10.png').exists():
            self.backward_button.setIcon(QIcon(str(icon_base_path / 'minus_10.png')))
        else:
            # Fallback to standard icon
            self.backward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.backward_button.setIconSize(QSize(25, 25))
        self.backward_button.clicked.connect(self.skip_backward)
        self.backward_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #211951;
                border: none;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #2e0249;
                color : #ffffff;                                          
            }
            QPushButton:pressed {
                background-color: #2e0249;
                color : #ffffff;
            }
            QPushButton:disabled {
                background-color: #19182f;
            }
        """)
        self.backward_button.setToolTip("Back 10 seconds")
        control_panel.addWidget(self.backward_button)

        # Play/Pause button
        self.play_button = QPushButton('Play')
        self.play_button.setEnabled(False)
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.toggle_playback)
        self.play_button.setIconSize(QSize(25, 25))
        self.play_button.setStyleSheet(button_style)
        control_panel.addWidget(self.play_button)

        # Stop button
        self.stop_button = QPushButton('Stop')
        self.stop_button.setEnabled(False)
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_button.setIconSize(QSize(25, 25))
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setStyleSheet(button_style)
        control_panel.addWidget(self.stop_button)

        # Forward 10s button
        self.forward_button = QPushButton()
        self.forward_button.setEnabled(False)
        if (icon_base_path / 'plus_10.png').exists():
            self.forward_button.setIcon(QIcon(str(icon_base_path / 'plus_10.png')))
        else:
            # Fallback to standard icon
            self.forward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.forward_button.setIconSize(QSize(25, 25))
        self.forward_button.clicked.connect(self.skip_forward)
        self.forward_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #211951;
                border: none;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #2e0249;
                color : #ffffff;                                          
            }
            QPushButton:pressed {
                background-color: #2e0249;
                color : #ffffff;
            }
            QPushButton:disabled {
                background-color: #19182f;
            }
        """)
        self.forward_button.setToolTip("Forward 10 seconds")
        control_panel.addWidget(self.forward_button)

        control_panel.addStretch()
        
        layout.addWidget(control_widget)


        load_button = QPushButton('                       Load Audio                      ')
        load_button.setFixedHeight(40)
        load_button.clicked.connect(self.load_file)
        load_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #865dff;
            }
            QPushButton:hover {
                background-color: #2e0249;
            }
            QPushButton:pressed {
                background-color: #2e0249;
            }
        """)
        load_button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        load_button.setIconSize(QSize(20, 20))
        load_button.setFixedHeight(40)
        load_button.setFixedWidth(350)
        load_button.setFlat(True)
        
        container = QWidget()


        container_layout = QHBoxLayout(container)
        container_layout.addWidget(load_button)
        container_layout.setSpacing(10)

        container_layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(container)

        # Status bar
        self.statusBar().setFixedHeight(30)
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
                    # Enable skip buttons
                    self.forward_button.setEnabled(True)
                    self.backward_button.setEnabled(True)
                else:
                    self.statusBar().showMessage(f'Failed to load {file_path}')
            except Exception as e:
                self.statusBar().showMessage(f'Error: {str(e)}')

    def toggle_playback(self):
        if not self.is_playing:
            self.audio_engine.play(start_pos=self.pause_position)
            self.is_playing = True
            self.play_button.setText('Pause')  # Unicode pause symbol
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.start_time = time.time() - self.pause_position
            self.visualizer.timer.start(self.visualizer.update_interval)
            self.statusBar().showMessage('Playing')
        else:
            self.audio_engine.pause()
            self.is_playing = False
            self.play_button.setText('Play')
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
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
        """Stop playback and reset position"""
        if hasattr(self, 'audio_engine') and self.audio_engine:
            self.audio_engine.stop()
            self.is_playing = False
            self.play_button.setText('Play')
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.pause_position = 0
            self.progress_slider.setValue(0)
            self.current_time_label.setText('00:00')
            self.visualizer.timer.stop()
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

    def _on_viz_type_changed(self, viz_type_str):
        viz_type = VisualizationType(viz_type_str)
        self.visualizer.set_visualization_type(viz_type)

    def skip_forward(self):
        """Skip forward 10 seconds"""
        if not self.current_file:
            return
        
        # Calculate new position
        current_pos = time.time() - self.start_time if self.is_playing else self.pause_position
        new_pos = min(current_pos + 10, self.total_duration)
        
        # Store the playing state
        was_playing = self.is_playing
        
        # Stop current playback
        if self.is_playing:
            self.audio_engine.pause()
        
        # Update position
        self.pause_position = new_pos
        
        # Resume playback if it was playing
        if was_playing:
            self.audio_engine.play(start_pos=new_pos)
            self.start_time = time.time() - new_pos
        
        # Update UI
        slider_value = int((new_pos / self.total_duration) * 1000) if self.total_duration > 0 else 0
        self.progress_slider.setValue(slider_value)
        self.current_time_label.setText(self.format_time(new_pos))
        self.statusBar().showMessage(f'Skipped to {self.format_time(new_pos)}')

    def skip_backward(self):
        """Skip backward 10 seconds"""
        if not self.current_file:
            return
        
        # Calculate new position
        current_pos = time.time() - self.start_time if self.is_playing else self.pause_position
        new_pos = max(0, current_pos - 10)
        
        # Store the playing state
        was_playing = self.is_playing
        
        # Stop current playback
        if self.is_playing:
            self.audio_engine.pause()
        
        # Update position
        self.pause_position = new_pos
        
        # Resume playback if it was playing
        if was_playing:
            self.audio_engine.play(start_pos=new_pos)
            self.start_time = time.time() - new_pos
        
        # Update UI
        slider_value = int((new_pos / self.total_duration) * 1000) if self.total_duration > 0 else 0
        self.progress_slider.setValue(slider_value)
        self.current_time_label.setText(self.format_time(new_pos))
        self.statusBar().showMessage(f'Skipped to {self.format_time(new_pos)}')

    def closeEvent(self, event):
        self.update_timer.stop()
        self.audio_engine.cleanup()
        event.accept()





















