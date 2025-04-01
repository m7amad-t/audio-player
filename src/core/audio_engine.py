import pygame
import soundfile as sf
from typing import Optional, Tuple

class AudioEngine:
    def __init__(self):
        self.playing: bool = False
        self.paused: bool = False
        self.current_position: float = 0
        self.duration: float = 0
        self.channels = None
        self.sample_rate = None
        self._init_pygame()
    
    def _init_pygame(self):
        pygame.mixer.init()
        pygame.mixer.music.set_volume(1.0)
    
    def load_file(self, file_path: str) -> bool:
        try:
            pygame.mixer.music.load(file_path)
            audio_data, sample_rate = sf.read(file_path)
            self.duration = len(audio_data) / sample_rate
            self.channels = audio_data.shape[1] if len(audio_data.shape) > 1 else 1
            self.sample_rate = sample_rate
            self.current_position = 0
            return True
        except Exception as e:
            return False
    
    def play(self, start_pos: float = 0):
        if start_pos > 0:
            pygame.mixer.music.play(start=start_pos)
        else:
            pygame.mixer.music.play()
        self.playing = True
        self.paused = False
        self.current_position = start_pos
    
    def pause(self):
        self.current_position = pygame.mixer.music.get_pos() / 1000.0  # Convert to seconds
        pygame.mixer.music.pause()
        self.paused = True
    
    def stop(self):
        pygame.mixer.music.stop()
        self.playing = False
        self.paused = False
        self.current_position = 0
    
    def cleanup(self):
        pygame.mixer.music.stop()
        pygame.mixer.quit()


