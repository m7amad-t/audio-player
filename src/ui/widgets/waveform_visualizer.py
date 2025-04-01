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
        self.chunk_size = 1024
        self.num_bars = 50
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
            
        chunk_start = max(0, current_frame - self.chunk_size // 2)
        chunk_end = min(len(self.audio_data), chunk_start + self.chunk_size)
        chunk = self.audio_data[chunk_start:chunk_end]
        
        if len(chunk) < self.chunk_size:
            return
            
        if len(chunk.shape) > 1:
            chunk = chunk.mean(axis=1)
        
        fft_data = np.abs(np.fft.fft(chunk)[:self.chunk_size//2])
        fft_data = fft_data / np.max(fft_data)
        bands = np.array_split(fft_data, self.num_bars)
        bar_values = [np.mean(band) for band in bands]
        
        bar_values = np.clip(bar_values, 0, 1)
        bar_values = np.power(bar_values, 0.5)
        
        for bar, val in zip(self.bars, bar_values):
            bar.set_height(val)
        
        self.draw()

    def reset_visualization(self):
        for bar in self.bars:
            bar.set_height(0)
        self.draw()
