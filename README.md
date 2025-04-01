# 🎵 PyAudioViz Player

A modern audio player built with Python that brings your music to life with real-time waveform visualization and a sleek dark-themed interface.


## ✨ Key Features Showcase

### 🌊 Dynamic Waveform Visualization


### -bars visualization
<div align="center">
  <img src="docs/file_loading.gif" alt="-bars Visualization Demo" width="600"/>
  <p><i>Real-time -bars visualization</i></p>
</div>

### Circular Visualization
<div align="center">
  <img src="docs/viz_modes.gif" alt="Circular Visualization Demo" width="600"/>
  <p><i>Real-time Circular visualization</i></p>
</div>

### Wave Visualization
<div align="center">
  <img src="docs/file_loading.gif" alt="Wave Visualization Demo" width="600"/>
  <p><i>Real-time waveform visualization</i></p>
</div>

### Spectrum Visualization
<div align="center">
  <img src="docs/interface_demo.gif" alt="Spectrum Visualization Demo" width="600"/>
  <p><i>Real-time spectrum visualization</i></p>
</div>

## 🎮 Controls & Features

| Control | Action | Description |
|---------|--------|-------------|
| `Space` | Play/Pause | Toggle playback |
| `O` | Open file | Load new audio file |
| `→` | Forward 10s | Skip ahead |
| `←` | Backward 10s | Skip back |
| `Tab` | Change visualization | Cycle through display modes |
| `Click` | Seek | Click anywhere on the progress bar |

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Windows, macOS, or Linux

### Installation

```bash
# Clone the repository
git clone https://github.com/m7amad-t/audio-player.git
cd pyaudioviz-player

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## 📦 Core Dependencies

- **PyQt5**: Modern GUI framework
- **pygame**: Robust audio handling
- **numpy**: Audio processing
- **soundfile**: Audio file support

## 🛠️ Development Tools

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Quality checks
pytest                # Run tests
flake8               # Code linting
black .              # Code formatting
```

## 📁 Project Architecture

```
src/
├── core/
│   ├── audio_engine.py     # Audio playback & processing
│   └── config.py           # Application settings
└── ui/
    ├── main_window.py      # Main application window
    └── widgets/
        └── waveform_visualizer.py  # Visualization engine
```

## 🔧 Advanced Features

- 🎯 Precise seeking with progress bar
- 📊 Dynamic waveform rendering
- 🎨 Multiple visualization algorithms
- ⚡ Optimized performance
- 🎵 Support for various audio formats

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


<div align="center">
  <p>Made with ❤️ by [Mohammed]</p>
  
  <a href="https://github.com/m7amad-t/audio-player/issues">Report Bug</a>
  ·
  <a href="https://github.com/m7amad-t/audio-player/issues">Request Feature</a>
</div>
