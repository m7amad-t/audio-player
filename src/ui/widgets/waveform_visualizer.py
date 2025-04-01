from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import numpy as np
import pygame

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
        self.update_interval = 50
        
        # Audio buffer for visualization
        self.chunk_size = 2048  # Increased for smoother waveform
        self.audio_data = None
        self.sample_rate = None
        
        # Initialize empty line
        self.line, = self.axes.plot([], [], color='#00BFFF', lw=2)
        
        # Set up the axes
        self.axes.set_ylim(-1, 1)  # Changed to show negative values
        self.axes.set_xlim(0, self.chunk_size)
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.axes.grid(True, alpha=0.1)  # Add subtle grid
        self.draw()

    def set_audio_data(self, audio_data, sample_rate):
        self.audio_data = audio_data
        self.sample_rate = sample_rate

    def update_plot(self):
        if not pygame.mixer.music.get_busy():
            return
            
        pos = pygame.mixer.music.get_pos() / 1000.0
        if pos < 0:
            return
            
        current_frame = int(pos * self.sample_rate)
        if current_frame >= len(self.audio_data):
            return
            
        # Get chunk of audio centered around current position
        chunk_start = max(0, current_frame - self.chunk_size // 2)
        chunk_end = min(len(self.audio_data), chunk_start + self.chunk_size)
        chunk = self.audio_data[chunk_start:chunk_end]
        
        if len(chunk) < self.chunk_size:
            return
            
        # Handle stereo audio
        if len(chunk.shape) > 1:
            chunk = chunk.mean(axis=1)
        
        # Create x-axis points
        x = np.linspace(0, len(chunk), len(chunk))
        
        # Update the line data
        self.line.set_data(x, chunk)
        
        # Add subtle fade effect
        alpha = 0.7
        self.line.set_alpha(alpha)
        
        self.draw()

    def reset_visualization(self):
        self.line.set_data([], [])
        self.draw()

