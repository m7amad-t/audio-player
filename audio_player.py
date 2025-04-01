import sys
from PyQt5 import QtWidgets, QtCore
from audio.engine import AudioEngine

class SimpleAudioPlayer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio_engine = AudioEngine()
        self.init_ui()
        
    def init_ui(self):
        # Set window properties
        self.setWindowTitle('Simple Audio Player')
        self.setGeometry(300, 300, 400, 150)
        
        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Create control panel
        control_panel = QtWidgets.QHBoxLayout()
        
        # Play/Pause button
        self.play_button = QtWidgets.QPushButton('Play')
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.toggle_playback)
        control_panel.addWidget(self.play_button)
        
        # Stop button
        self.stop_button = QtWidgets.QPushButton('Stop')
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_playback)
        control_panel.addWidget(self.stop_button)
        
        # Speed control
        speed_layout = QtWidgets.QHBoxLayout()
        speed_label = QtWidgets.QLabel('Speed:')
        self.speed_combo = QtWidgets.QComboBox()
        self.speed_combo.addItems(['0.5x', '1.0x', '1.5x', '2.0x', '5.0x', '10.0x', '15.0x'])
        self.speed_combo.setCurrentText('1.0x')
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_combo)
        
        # File info label
        self.file_info = QtWidgets.QLabel('No file loaded')
        
        # Load button
        load_button = QtWidgets.QPushButton('Load Audio File')
        load_button.clicked.connect(self.load_audio_file)
        
        # Add all components to main layout
        layout.addLayout(control_panel)
        layout.addLayout(speed_layout)
        layout.addWidget(self.file_info)
        layout.addWidget(load_button)
        
        # Show the window
        self.show()
        
    def load_audio_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Open Audio File',
            '',
            'Audio Files (*.wav *.mp3 *.flac *.ogg);;All Files (*)'
        )
        
        if file_path:
            self.statusBar().showMessage(f'Loading {file_path}...')
            if self.audio_engine.load_file(file_path):
                # Update file info
                channels_text = "mono" if self.audio_engine.channels == 1 else f"{self.audio_engine.channels} channels"
                duration = int(self.audio_engine.duration)
                minutes = duration // 60
                seconds = duration % 60
                duration_text = f"{minutes}:{seconds:02d}" if minutes else f"{seconds}s"
                
                self.file_info.setText(
                    f'File: {file_path.split("/")[-1]}\n'
                    f'Format: {channels_text}, {self.audio_engine.sample_rate}Hz\n'
                    f'Duration: {duration_text}'
                )
                
                # Enable playback controls
                self.play_button.setEnabled(True)
                self.stop_button.setEnabled(True)
                self.statusBar().showMessage(f'Loaded {file_path}')
            else:
                self.statusBar().showMessage(f'Failed to load {file_path}')
                QtWidgets.QMessageBox.critical(self, 'Error', 'Failed to load the audio file.')
    
    def toggle_playback(self):
        if not self.audio_engine.playing:
            # Get playback speed from combo box
            speed = float(self.speed_combo.currentText().replace('x', ''))
            self.audio_engine.play(speed=speed)
            self.play_button.setText('Pause')
            self.statusBar().showMessage(f'Playing ({speed}x speed)')
        elif self.audio_engine.paused:
            self.audio_engine.play()
            self.play_button.setText('Pause')
            self.statusBar().showMessage('Playing')
        else:
            self.audio_engine.pause()
            self.play_button.setText('Play')
            self.statusBar().showMessage('Paused')
    
    def stop_playback(self):
        self.audio_engine.stop()
        self.play_button.setText('Play')
        self.statusBar().showMessage('Stopped')
    
    def closeEvent(self, event):
        self.audio_engine.stop()
        event.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    player = SimpleAudioPlayer()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()