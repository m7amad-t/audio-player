from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer, Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib import transforms, patheffects  # Added patheffects import
import numpy as np
import pygame
from enum import Enum
import matplotlib.pyplot as plt
import random
import time

class VisualizationType(Enum):
    WAVEFORM = "Waveform"
    BARS = "Bars"
    SPECTRUM = "Spectrum"
    CIRCULAR = "Circular"

class WaveformVisualizer(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        
        # Define standard colors
        self.background_color = (0.12, 0.12, 0.12)  # Dark gray for background
        self.figure_color = (0.15, 0.15, 0.15)      # Slightly lighter gray for figure
        
        self.axes.set_facecolor(self.background_color)
        self.fig.patch.set_facecolor(self.figure_color)
        super(WaveformVisualizer, self).__init__(self.fig)
        self.setParent(parent)
        
        # Visualization settings
        self.visualization_type = VisualizationType.WAVEFORM
        self.num_bars = 50
        
        # Animation state
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.update_interval = 50
        
        # Audio buffer for visualization
        self.chunk_size = 2048
        self.audio_data = None
        self.sample_rate = None
        
        # Initialize visualizations
        self.line = None
        self.bars = None
        self.spectrum_line = None
        self.spectrum_particles = None
        self.particle_history = []
        self.max_history = 10  # Number of frames to keep in history
        self.circular_line = None
        self._setup_visualization(VisualizationType.WAVEFORM)
        
        # Add particle system properties
        self.particles = []
        self.num_particles = 30
        self.particle_speed = 0.1
        self.particle_velocities = []
        self.last_bar_values = None  # Store previous bar values to detect peaks

    def _setup_axes(self):
        # Store the current visualization type before clearing
        current_type = self.visualization_type
        
        # Clear the entire figure and create new axes
        self.fig.clear()
        self.axes = self.fig.add_subplot(111)
        
        # Reset all artists
        self.line = None
        self.bars = None
        self.spectrum_line = None
        self.spectrum_particles = None
        self.circular_line = None
        self.circular_bars = []
        self.center_circle = None
        
        # Set appropriate limits for each visualization type
        if current_type == VisualizationType.WAVEFORM:
            self.axes.set_ylim(-1, 1)
            self.axes.set_xlim(0, self.chunk_size)
        elif current_type == VisualizationType.SPECTRUM:
            self.axes.set_ylim(-0.2, 1.2)
            self.axes.set_xlim(0, self.sample_rate/2 if self.sample_rate else 22050)
        elif current_type == VisualizationType.CIRCULAR:
            self.axes.set_ylim(-3, 3)
            self.axes.set_xlim(-3, 3)
            self.axes.set_aspect('equal')
        else:  # BARS
            self.axes.set_ylim(0, 1)
            self.axes.set_xlim(-1, self.num_bars)
        
        # Common settings for all visualizations
        self.axes.set_facecolor(self.background_color)
        self.fig.patch.set_facecolor(self.figure_color)
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.axes.grid(False)

    def _setup_visualization(self, viz_type: VisualizationType):
        self.visualization_type = viz_type
        self._setup_axes()
        
        if viz_type == VisualizationType.WAVEFORM:
            # Initialize hidden line (we'll use it as a reference)
            self.line, = self.axes.plot([], [], color='#00BFFF', lw=2, alpha=0)
            self.gradient_fill = None
            self.glow_fill = None
            self.top_line = None
            
            # Set background darker for better gradient visibility
            self.axes.set_facecolor((0.1, 0.1, 0.1))
            
            # Add subtle grid
            self.axes.grid(True, color='#222222', linestyle='-', linewidth=0.5)
        elif viz_type == VisualizationType.BARS:
            self.line = None
            self.spectrum_line = None
            self.spectrum_particles = None
            self.circular_line = None
            
            # Initialize bars
            self.bars = self.axes.bar(
                range(self.num_bars),
                [0] * self.num_bars,
                color='#00BFFF',
                width=0.8
            )
            
            # Initialize particles
            self.particles = []
            self.last_bar_values = None
            
            # Initialize particle scatter plot
            self.particle_scatter = self.axes.scatter(
                [], [], 
                c='#00BFFF',
                alpha=0.6,
                s=30
            )
        elif viz_type == VisualizationType.SPECTRUM:
            self.line = None
            self.bars = None
            self.circular_line = None
            self.spectrum_particles = self.axes.scatter(
                [], [], 
                c='#00BFFF',
                alpha=0.8,
                s=50,
                edgecolor='white',
                linewidth=0.5
            )
            self.spectrum_line, = self.axes.plot(
                [], [], 
                color='#00BFFF',
                alpha=0.4,
                lw=2,
                path_effects=[
                    patheffects.withSimplePatchShadow(  # Changed from matplotlib.patheffects
                        offset=(0, 0),
                        shadow_rgbFace='#00BFFF',
                        alpha=0.3
                    )
                ]
            )
            self.particle_history = []
            self.max_history = 8  # Reduced for faster response
            self.freq_bands = None
            self.axes.set_ylim(-0.1, 1.2)
            self.axes.set_xlim(0, self.sample_rate/2 if self.sample_rate else 22050)
            freq_ticks = [0, 5000, 10000, 15000, 20000]
            self.axes.set_xticks(freq_ticks)
            self.axes.set_xticklabels([f'{int(f/1000)}kHz' for f in freq_ticks])
            self.axes.tick_params(colors='#666666')
            self.axes.grid(True, color='#222222', linestyle='-', linewidth=0.5, alpha=0.3)
        elif viz_type == VisualizationType.CIRCULAR:
            self.line = None
            self.bars = None
            self.spectrum_line = None
            self.spectrum_particles = None
            
            # Set up larger initial plot area
            self.axes.set_ylim(-8, 8)  # Increased range
            self.axes.set_xlim(-8, 8)  # Increased range
            self.axes.set_aspect('equal')
            
            self.num_circular_bars = 32
            theta = np.linspace(0, 2*np.pi, self.num_circular_bars, endpoint=False)
            
            # Initialize bars
            self.circular_bars = []
            base_radius = 2.5  # Increased initial radius
            for angle in theta:
                bar = plt.Rectangle(
                    (0, 0), 0.1, 0.1,
                    facecolor='#00BFFF',
                    alpha=0.6
                )
                self.axes.add_patch(bar)
                self.circular_bars.append(bar)
            
            # Add center circle with larger initial size
            self.center_circle = plt.Circle(
                (0, 0), 
                base_radius, 
                color='#00BFFF',
                alpha=0.2,
                fill=True
            )
            self.axes.add_artist(self.center_circle)
            
            # Initialize scaling variables
            self.last_intensity = 0

        self.draw()

    def set_visualization_type(self, viz_type: VisualizationType):
        """Change the visualization type and reset the visualization."""
        if viz_type != self.visualization_type:
            self.visualization_type = viz_type
            self._setup_visualization(viz_type)
            self.draw()

    def set_audio_data(self, audio_data, sample_rate):
        self.audio_data = audio_data
        self.sample_rate = sample_rate

    def update_plot(self):
        if not pygame.mixer.music.get_busy() or self.audio_data is None:
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
            
        if len(chunk.shape) > 1:  # If stereo, take mean of channels
            chunk = chunk.mean(axis=1)
            
        if self.visualization_type == VisualizationType.WAVEFORM:
            self._update_waveform(chunk)
        elif self.visualization_type == VisualizationType.BARS:
            self._update_bars(chunk)
        elif self.visualization_type == VisualizationType.SPECTRUM:
            self._update_spectrum(chunk)
        elif self.visualization_type == VisualizationType.CIRCULAR:
            self._update_circular(chunk)
        
        self.draw()

    def _update_waveform(self, chunk):
        # Downsample and smooth the data
        downsample_factor = 4
        smoothing_window = 15
        
        # Downsample the chunk
        chunk_downsampled = chunk[::downsample_factor]
        
        # Apply smoothing using convolution
        window = np.hanning(smoothing_window)
        window = window / window.sum()
        chunk_smooth = np.convolve(chunk_downsampled, window, mode='valid')
        
        # Create smooth x coordinates
        x = np.linspace(0, len(chunk), len(chunk_smooth))
        
        # Add interpolation for smoother curves
        x_interp = np.linspace(0, len(chunk), len(chunk) // 2)
        chunk_interp = np.interp(x_interp, x, chunk_smooth)
        
        # Apply additional smoothing to interpolated data
        chunk_interp = np.convolve(chunk_interp, window, mode='valid')
        x_final = np.linspace(0, len(chunk), len(chunk_interp))
        
        # Calculate gradient colors
        num_points = len(chunk_interp)
        color_array = np.zeros((num_points, 4))  # RGBA array
        
        # Create gradient colors with smoother transition
        for i in range(num_points):
            pos = i / num_points
            # Smoother gradient from blue to cyan
            color_array[i] = [
                0,  # R
                0.75 + 0.25 * (1 - np.cos(pos * np.pi)) / 2,  # G (smoother transition)
                1,  # B
                0.7 * (1 - 0.3 * pos)  # A (gentler fade out)
            ]
        
        # Handle gradient fill
        if hasattr(self, 'gradient_fill') and self.gradient_fill is not None:
            self.gradient_fill.remove()
        self.gradient_fill = self.axes.fill_between(
            x_final, chunk_interp, np.zeros_like(chunk_interp),
            color=color_array,
            alpha=0.7
        )
        
        # Handle glow effect with smoother transition
        if hasattr(self, 'glow_fill') and self.glow_fill is not None:
            self.glow_fill.remove()
        self.glow_fill = self.axes.fill_between(
            x_final, chunk_interp, np.zeros_like(chunk_interp),
            color='#00BFFF',
            alpha=0.15,  # Reduced alpha for softer glow
            linewidth=0
        )
        
        # Handle top line with smoothing
        if not hasattr(self, 'top_line') or self.top_line is None:
            self.top_line, = self.axes.plot(
                x_final, chunk_interp,
                color='#FFFFFF',
                alpha=0.3,  # Reduced alpha for softer line
                linewidth=1
            )
        else:
            self.top_line.set_data(x_final, chunk_interp)
        
        # Add smooth transition between frames
        if not hasattr(self, 'last_chunk'):
            self.last_chunk = chunk_interp
        else:
            # Interpolate between last frame and current frame
            transition_factor = 0.3  # Adjust this value to control smoothness (0-1)
            chunk_interp = (1 - transition_factor) * self.last_chunk + transition_factor * chunk_interp
            self.last_chunk = chunk_interp

    def _update_bars(self, chunk):
        if self.bars is None:
            return
        
        # Compute FFT
        if len(chunk.shape) > 1:
            chunk = chunk.mean(axis=1)
        
        window = np.hanning(len(chunk))
        fft_data = np.abs(np.fft.fft(chunk * window))[:len(chunk)//2]
        
        # Scale the FFT data
        fft_data = fft_data / np.max(fft_data) if np.max(fft_data) > 0 else fft_data
        
        # Split frequency data into bands
        bands = np.array_split(fft_data, self.num_bars)
        bar_values = [np.mean(band) for band in bands]
        
        # Apply smoothing and scaling
        bar_values = np.clip(bar_values, 0, 1)
        bar_values = np.power(bar_values, 0.7)
        
        # Initialize last_bar_values if needed
        if self.last_bar_values is None:
            self.last_bar_values = np.zeros_like(bar_values)
        
        # Update bars and spawn particles
        for idx, (bar, value) in enumerate(zip(self.bars, bar_values)):
            spawn_particles = False
            num_particles = 0
            
            # Peak detection for main particle spawning
            is_peak = (value > 0.15 and value > self.last_bar_values[idx] * 1.1)
            
            if is_peak:
                spawn_particles = True
                num_particles = max(1, int(value * 3))
            else:
                # Random spawning for lower amplitude bars
                # Higher chance of spawning for higher values
                spawn_chance = value * 0.3  # 30% max chance for full-height bars
                if random.random() < spawn_chance and value > 0.05:  # Minimum threshold
                    spawn_particles = True
                    num_particles = 1  # Spawn single particle for random events
            
            if spawn_particles:
                # Adjust particle properties based on spawn type
                for _ in range(num_particles):
                    # Randomize initial velocity more for non-peak particles
                    velocity_multiplier = 1.0 if is_peak else 0.7
                    particle = BarParticle(
                        idx,
                        value * (1.0 if is_peak else 0.8),  # Slightly reduced intensity for random particles
                        value
                    )
                    # Adjust particle properties based on spawn type
                    if not is_peak:
                        particle.decay *= 1.2  # Faster decay for random particles
                        particle.velocity *= velocity_multiplier
                    self.particles.append(particle)
        
            # Update bar height and color
            bar.set_height(value)
            color = plt.cm.cool(value)
            bar.set_color(color)
            bar.set_alpha(0.6 + 0.4 * value)
        
        # Limit total number of particles
        max_particles = 200
        if len(self.particles) > max_particles:
            self.particles = self.particles[-max_particles:]
        
        # Update particles
        self.particles = [p for p in self.particles if p.update()]
        
        if self.particles:
            positions = np.array([[p.x, p.y] for p in self.particles])
            # Adjusted size calculation for more consistent appearance
            sizes = [30 * p.value * (p.life ** 0.3) for p in self.particles]
            # Smoother color transition
            colors = np.array([[0, 0.75, 1, max(0.2, p.life * 0.8)] for p in self.particles])
            
            self.particle_scatter.set_offsets(positions)
            self.particle_scatter.set_sizes(sizes)
            self.particle_scatter.set_color(colors)
        else:
            self.particle_scatter.set_offsets(np.empty((0, 2)))
            self.particle_scatter.set_sizes([])
            self.particle_scatter.set_color([])
        
        # Store current values for next frame
        self.last_bar_values = bar_values.copy()

    def _update_spectrum(self, chunk):
        if self.sample_rate is None:
            return

        # Compute FFT with overlapping windows for smoother animation
        window = np.hanning(len(chunk))
        fft_data = np.fft.rfft(chunk * window)
        fft_freq = np.fft.rfftfreq(len(chunk), 1/self.sample_rate)
        
        # Convert to dB scale and normalize
        magnitude_db = 20 * np.log10(np.abs(fft_data) + 1e-10)
        magnitude_db = np.clip(magnitude_db, -60, 0)  # Clip to reasonable range
        magnitude_normalized = (magnitude_db + 60) / 60  # Normalize to 0-1
        
        # Create particle effect
        # Downsample for better performance
        downsample_factor = 4
        freq_downsampled = fft_freq[::downsample_factor]
        mag_downsampled = magnitude_normalized[::downsample_factor]
        
        # Add some randomness to particle positions
        particle_x = freq_downsampled
        particle_y = mag_downsampled + np.random.normal(0, 0.02, len(mag_downsampled))
        
        # Update particle positions
        self.spectrum_particles.set_offsets(np.column_stack((particle_x, particle_y)))
        
        # Update particle sizes based on magnitude
        sizes = 50 + 100 * mag_downsampled**2
        self.spectrum_particles.set_sizes(sizes)
        
        # Update colors with gradient based on frequency
        colors = plt.cm.viridis(mag_downsampled)
        self.spectrum_particles.set_color(colors)
        
        # Update trail effect
        self.particle_history.append((particle_x, particle_y))
        if len(self.particle_history) > self.max_history:
            self.particle_history.pop(0)
        
        # Draw trails with fade effect
        if len(self.particle_history) > 1:
            trail_x = np.mean([x for x, _ in self.particle_history], axis=0)
            trail_y = np.mean([y for _, y in self.particle_history], axis=0)
            self.spectrum_line.set_data(trail_x, trail_y)

        # Add frequency bands highlights
        if not hasattr(self, 'freq_bands') or self.freq_bands is None:
            self.freq_bands = []
            band_colors = plt.cm.cool(np.linspace(0, 1, 4))
            for i, color in enumerate(band_colors):
                band = self.axes.axvspan(
                    fft_freq[0] + i * fft_freq[-1]/4,
                    fft_freq[0] + (i+1) * fft_freq[-1]/4,
                    color=color,
                    alpha=0.1
                )
                self.freq_bands.append(band)

        # Update frequency band intensities
        for i, band in enumerate(self.freq_bands):
            start_idx = int(len(magnitude_normalized) * i / 4)
            end_idx = int(len(magnitude_normalized) * (i + 1) / 4)
            intensity = np.mean(magnitude_normalized[start_idx:end_idx])
            band.set_alpha(0.1 + 0.2 * intensity)

    def _update_circular(self, chunk):
        if not hasattr(self, 'circular_bars'):
            return
        
        # Compute FFT with overlapping windows for better reactivity
        if len(chunk.shape) > 1:
            chunk = chunk.mean(axis=1)
        
        window = np.hanning(len(chunk))
        fft_data = np.abs(np.fft.rfft(chunk * window))
        
        # Scale the FFT data
        fft_data = fft_data / np.max(fft_data) if np.max(fft_data) > 0 else fft_data
        
        # Split frequency data into bands
        bands = np.array_split(fft_data, self.num_circular_bars)
        bar_values = [np.mean(band) for band in bands]
        
        # Apply more aggressive smoothing and scaling
        bar_values = np.clip(bar_values, 0, 1)
        bar_values = np.power(bar_values, 0.5)  # Less aggressive power for more reactivity
        
        # Calculate overall audio intensity with peak detection
        avg_intensity = np.mean(bar_values)
        peak_intensity = np.max(bar_values)
        intensity = (avg_intensity * 0.3 + peak_intensity * 0.7)  # Weight peaks more
        
        # Enhance peaks for more reactive scaling
        intensity = np.power(intensity, 0.7)  # Make scaling more sensitive to changes
        
        # Smooth intensity changes with faster response
        if not hasattr(self, 'last_intensity'):
            self.last_intensity = intensity
        
        smooth_factor = 0.5  # Reduced for faster response
        intensity = (smooth_factor * self.last_intensity + 
                    (1 - smooth_factor) * intensity)
        self.last_intensity = intensity
        
        # Calculate the base radius with more dramatic scaling
        min_radius = 2.5  # Increased base size
        max_radius = 6.0  # Increased maximum size
        base_radius = min_radius + (max_radius - min_radius) * intensity
        
        # Add subtle pulse effect
        pulse = 0.1 * np.sin(time.time() * 8)  # Faster, subtle pulse
        base_radius *= (1 + pulse * intensity)
        
        # Update center circle with enhanced effects
        self.center_circle.set_radius(base_radius)
        center_color = plt.cm.cool(intensity)
        self.center_circle.set_color(center_color)
        self.center_circle.set_alpha(0.2 + 0.1 * intensity)  # Dynamic opacity
        
        # Update bars around the circle with enhanced reactivity
        for idx, (bar, value) in enumerate(zip(self.circular_bars, bar_values)):
            angle = 2 * np.pi * idx / self.num_circular_bars
            
            # Enhanced bar dimensions
            bar_height = value * base_radius * 1.2  # Longer bars
            bar_width = (2 * np.pi * base_radius / self.num_circular_bars) * 0.85
            
            # Add slight outward push based on intensity
            radius_offset = base_radius * (1 + 0.1 * value * intensity)
            
            # Position bar with dynamic offset
            transform = transforms.Affine2D()\
                .translate(-bar_width/2, radius_offset)\
                .rotate(angle)\
                .translate(0, 0)
            
            bar.set_width(bar_width)
            bar.set_height(bar_height)
            bar.set_xy((0, 0))
            bar.set_transform(transform + self.axes.transData)
            
            # Enhanced color effects
            color_intensity = (value + intensity) / 2
            color = plt.cm.cool(color_intensity)
            bar.set_color(color)
            bar.set_alpha(0.4 + 0.6 * value)  # More dynamic opacity
        
        # Update plot limits with extra space for movement
        max_limit = (max_radius + 4) * 1.2  # Increased viewing area
        self.axes.set_xlim(-max_limit, max_limit)
        self.axes.set_ylim(-max_limit, max_limit)
        
        self.last_bar_values = bar_values.copy()

    def reset_visualization(self):
        """Reset the current visualization to its initial state."""
        self._setup_visualization(self.visualization_type)
        self.draw()

class Particle:
    def __init__(self, bar_idx, value, total_bars):
        self.bar_idx = bar_idx
        self.angle = 2 * np.pi * bar_idx / total_bars
        self.value = value
        self.base_radius = 1.2  # This will be updated dynamically
        self.height = 0
        self.velocity = 0.1 * (0.5 + random.random()) * value
        self.life = 1.0
        self.decay = 0.02 + 0.01 * random.random()
        self.max_height = 0.5 + 0.5 * value
        self.x = 0
        self.y = 0
        self.update_position()
    
    def update_position(self):
        # Calculate position relative to the bar's end
        bar_end = self.base_radius + (self.value * 1.2)
        total_radius = bar_end + self.height
        self.x = total_radius * np.cos(self.angle)
        self.y = total_radius * np.sin(self.angle)
    
    def update(self):
        self.height += self.velocity
        self.angle += np.random.normal(0, 0.02 * self.value)
        
        self.update_position()
        
        if self.height < self.max_height:
            self.velocity *= 0.98
        else:
            self.velocity *= 0.85
        
        self.life -= self.decay * (1 + self.height/2)
        
        return self.life > 0

class BarParticle:
    def __init__(self, bar_idx, value, y_pos):
        self.bar_idx = bar_idx
        self.x = bar_idx
        self.y = y_pos
        self.value = value
        self.life = 1.0
        self.decay = 0.015  # Reduced decay rate for longer life
        # Randomize initial velocity for more natural movement
        self.velocity = (0.1 + random.random() * 0.1) * value
        # Reduced max height for more consistent behavior
        self.max_height = y_pos + (1.5 * value)
        # Add horizontal velocity
        self.x_velocity = random.uniform(-0.02, 0.02) * value
        
    def update(self):
        # Update position with smoother movement
        self.y += self.velocity
        self.x += self.x_velocity
        
        # Gentler velocity changes
        if self.y < self.max_height:
            self.velocity *= 0.99  # Slower deceleration
        else:
            self.velocity *= 0.95  # Gentler fall
            
        # Gradual life decay
        self.life -= self.decay
        
        return self.life > 0

















