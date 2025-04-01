import sys
import os
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, QStyle,
                            QSlider, QMessageBox)
from PyQt5.QtCore import QTimer, Qt
import pygame
import soundfile as sf
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import numpy as np

class WaveformVisualizer(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor((0.12, 0.12, 0.12))
        self.fig.patch.set_facecolor((0.15, 0.15, 0.15))
        super(WaveformVisualizer, self).__init__(self.fig)
        self.setParent(parent)
        
        # Animation state
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.update_interval = 50  # 50ms default update interval
        
        # Audio buffer for visualization
        self.chunk_size = 1024  # Size of audio chunks to analyze
        self.num_bars = 50      # Number of frequency bars to display
        self.audio_data = None
        self.sample_rate = None
        
        # Initialize empty bars
        self.bars = self.axes.bar(
            range(self.num_bars),
            [0] * self.num_bars,
            color='#00BFFF',
            width=0.8
        )
        
        # Set up the axes
        self.axes.set_ylim(0, 1)
        self.axes.set_xlim(-1, self.num_bars)
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.draw()

    def set_audio_data(self, audio_data, sample_rate):
        """Set the audio data to be visualized."""
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        
    def update_plot(self):
        """Update the visualization in real-time."""
        if not pygame.mixer.music.get_busy():
            return
            
        # Get the current position in the audio
        pos = pygame.mixer.music.get_pos() / 1000.0  # Current position in seconds
        if pos < 0:
            return
            
        # Calculate the current frame in the audio data
        current_frame = int(pos * self.sample_rate)
        if current_frame >= len(self.audio_data):
            return
            
        # Get a chunk of audio data around the current position
        chunk_start = max(0, current_frame - self.chunk_size // 2)
        chunk_end = min(len(self.audio_data), chunk_start + self.chunk_size)
        chunk = self.audio_data[chunk_start:chunk_end]
        
        if len(chunk) < self.chunk_size:
            return
            
        # Compute FFT of the chunk
        if len(chunk.shape) > 1:  # If stereo, take mean of channels
            chunk = chunk.mean(axis=1)
        
        fft_data = np.abs(np.fft.fft(chunk)[:self.chunk_size//2])
        
        # Scale the FFT data and split into bands
        fft_data = fft_data / np.max(fft_data)
        bands = np.array_split(fft_data, self.num_bars)
        bar_values = [np.mean(band) for band in bands]
        
        # Apply some smoothing and scaling
        bar_values = np.clip(bar_values, 0, 1)
        bar_values = np.power(bar_values, 0.5)  # Adjust power for better visualization
        
        # Update the bar heights
        for bar, val in zip(self.bars, bar_values):
            bar.set_height(val)
        
        self.draw()

    def reset_visualization(self):
        """Reset all bars to zero."""
        for bar in self.bars:
            bar.set_height(0)
        self.draw()

class AudioPlayerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_pygame()
        self.init_ui()
        self.current_file = None
        self.is_playing = False
        self.current_position = 0
        self.total_duration = 0
        self.start_time = 0
        self.seeking = False
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                background-color: #121212;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #282828;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #383838;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
            QPushButton:disabled {
                background-color: #1F1F1F;
                color: #666666;
            }
            QLabel {
                color: #FFFFFF;
            }
            QStatusBar {
                background-color: #181818;
                color: #888888;
            }
        """)
        
        # Increase update frequency for smoother display
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_time_display)
        self.update_timer.start(16)  # Update every 16ms (approximately 60fps)

    def init_pygame(self):
        pygame.mixer.init()
        pygame.mixer.music.set_volume(1.0)

    def init_ui(self):
        self.setWindowTitle('Audio Player with Visualization')
        self.setGeometry(300, 300, 800, 500)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # File info section
        self.file_label = QLabel('No file selected')
        self.file_label.setStyleSheet("""
            padding: 10px;
            background-color: #282828;
            border-radius: 5px;
            color: #FFFFFF;
        """)
        layout.addWidget(self.file_label)

        # Add waveform visualizer
        self.visualizer = WaveformVisualizer(central_widget, width=7, height=4)
        self.visualizer.axes.set_facecolor('#121212')
        self.visualizer.fig.patch.set_facecolor('#121212')
        self.visualizer.bars = self.visualizer.axes.bar(
            range(self.visualizer.num_bars),
            [0] * self.visualizer.num_bars,
            color='#00BFFF',
            width=0.8
        )
        layout.addWidget(self.visualizer)

        # Time display and progress layout
        time_layout = QHBoxLayout()
        
        # Current time label
        self.current_time_label = QLabel('0:00')
        self.current_time_label.setStyleSheet("color: #888888;")
        time_layout.addWidget(self.current_time_label)
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(1000)
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(False)  # Disable initially
        self.progress_slider.sliderPressed.connect(self.start_seeking)
        self.progress_slider.sliderReleased.connect(self.stop_seeking)
        self.progress_slider.valueChanged.connect(self.seek_position)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #282828;
                margin: 2px 0;
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                background: #FFFFFF;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }

            QSlider::handle:horizontal:hover {
                background: #FFFFFF;
                box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
            }

            QSlider::sub-page:horizontal {
                background: #00BFFF;
                border-radius: 2px;
            }
        """)
        time_layout.addWidget(self.progress_slider, stretch=1)
        
        # Total time label
        self.total_time_label = QLabel('0:00')
        self.total_time_label.setStyleSheet("color: #888888;")
        time_layout.addWidget(self.total_time_label)
        
        layout.addLayout(time_layout)

        # Control buttons layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        # Load button
        self.load_button = QPushButton('Load File')
        self.load_button.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.load_button.clicked.connect(self.load_file)  # Connect the button click
        controls_layout.addWidget(self.load_button)

        # Play/Pause button
        self.play_button = QPushButton('Play')
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_button)

        # Stop button
        self.stop_button = QPushButton('Stop')
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_playback)
        controls_layout.addWidget(self.stop_button)

        layout.addLayout(controls_layout)

        # Status bar
        self.statusBar().showMessage('Ready')  # Removed volume label

    def format_time(self, seconds):
        """Convert seconds to mm:ss format with milliseconds"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def start_seeking(self):
        """Called when user starts dragging the slider"""
        self.seeking = True
        if self.is_playing:
            pygame.mixer.music.pause()

    def stop_seeking(self):
        """Called when user releases the slider"""
        self.seeking = False
        if self.is_playing:
            pygame.mixer.music.unpause()
            # Update start_time to maintain correct position tracking
            self.start_time = time.time() - (self.current_position / 1000.0)

    def seek_position(self, value):
        """Called when slider value changes"""
        if not hasattr(self, 'total_duration') or self.total_duration <= 0:
            return
            
        # Convert slider value (0-1000) to seconds
        position = (value / 1000.0) * self.total_duration
        self.current_position = position * 1000  # Convert to milliseconds for pygame
        
        # Update time display
        self.current_time_label.setText(self.format_time(position))
        
        if self.seeking:
            # Set new playback position
            pygame.mixer.music.play(start=position)
            if not self.is_playing:
                pygame.mixer.music.pause()
            else:
                self.start_time = time.time() - position
            
            # Update visualization
            self.visualizer.reset_visualization()

    def update_time_display(self):
        if self.is_playing and not self.seeking:
            # Calculate current position using system time
            elapsed = time.time() - self.start_time
            if elapsed >= 0:
                # Ensure we don't exceed the total duration
                current_pos = min(elapsed, self.total_duration)
                
                # Update time label
                self.current_time_label.setText(self.format_time(current_pos))
                
                # Update slider position (without triggering valueChanged)
                slider_value = int((current_pos / self.total_duration) * 1000) if self.total_duration > 0 else 0
                self.progress_slider.blockSignals(True)
                self.progress_slider.setValue(slider_value)
                self.progress_slider.blockSignals(False)
                
                # Check if playback has finished
                if current_pos >= self.total_duration:
                    self.stop_playback()

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
                
                # Calculate total duration
                self.total_duration = len(audio_data) / sample_rate
                self.total_time_label.setText(self.format_time(self.total_duration))
                self.progress_slider.setValue(0)
                self.current_time_label.setText('0:00')
                
                # Load audio for playback
                pygame.mixer.music.load(file_path)
                self.current_file = file_path
                self.current_position = 0
                self.start_time = 0
                self.seeking = False
                
                # Update UI
                self.file_label.setText(f'File: {os.path.basename(file_path)}')
                self.play_button.setEnabled(True)
                self.stop_button.setEnabled(True)
                self.progress_slider.setEnabled(True)
                self.statusBar().showMessage('File loaded successfully')
                
            except Exception as e:
                self.statusBar().showMessage(f'Error loading file: {str(e)}')
                QMessageBox.critical(self, 'Error', f'Failed to load the audio file:\n{str(e)}')

    def toggle_playback(self):
        if not self.is_playing:
            if pygame.mixer.music.get_pos() == -1:  # If starting fresh or was stopped
                pygame.mixer.music.play()
                self.start_time = time.time()
                self.current_position = 0
            else:  # If resuming from pause
                pygame.mixer.music.unpause()
                self.start_time = time.time() - (self.current_position / 1000.0)
            self.play_button.setText('Pause')
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.is_playing = True
            self.visualizer.timer.start(16)  # Increase visualization update rate
            self.statusBar().showMessage('Playing')
        else:
            pygame.mixer.music.pause()
            self.current_position = pygame.mixer.music.get_pos()
            self.play_button.setText('Play')
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.is_playing = False
            self.visualizer.timer.stop()
            self.statusBar().showMessage('Paused')

    def stop_playback(self):
        pygame.mixer.music.stop()
        self.play_button.setText('Play')
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.is_playing = False
        self.seeking = False
        self.visualizer.timer.stop()
        self.visualizer.reset_visualization()
        self.current_position = 0
        self.current_time_label.setText('0:00')
        self.progress_slider.setValue(0)
        self.start_time = 0
        self.statusBar().showMessage('Stopped')

    def closeEvent(self, event):
        self.update_timer.stop()
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    player = AudioPlayerGUI()
    player.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
















