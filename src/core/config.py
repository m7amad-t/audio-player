from dataclasses import dataclass
import json
from pathlib import Path

@dataclass
class AudioPlayerConfig:
    window_width: int = 1000
    window_height: int = 500
    update_interval: int = 16
    buffer_size: int = 8192
    supported_formats: tuple = ('.mp3', '.wav', '.ogg')

def load_config() -> AudioPlayerConfig:
    config_path = Path('config.json')
    if config_path.exists():
        with open(config_path) as f:
            config_dict = json.load(f)
            return AudioPlayerConfig(**config_dict)
    return AudioPlayerConfig()
