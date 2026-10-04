import sys
import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
from pylsl import StreamInlet, resolve_byprop

FS = 256              # Sampling rate in Hz
WINDOW_SEC = 5        # Visible window length in seconds
N_CHANS = 8
BUFFER_LEN = FS * WINDOW_SEC
CHANNEL_SPACING = 75.0  # Spacing in uV between stacked channels (clean scale for EEG)

class LSLVisualizer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("g.MOBIlab+ Real-Time EEG Monitor (uV Calibrated)")
        self.resize(1100, 750)

        print("Searching for LSL stream 'gMOBIlab'...")
        streams = resolve_byprop('name', 'gMOBIlab', timeout=5.0)
        if not streams:
            raise RuntimeError("Could not find 'gMOBIlab' stream. Make sure bridge.py is running!")
        
        self.inlet = StreamInlet(streams[0], max_buflen=360)
        print("Connected to stream.")

        # Rolling circular buffer: shape (8 channels, BUFFER_LEN)
        self.data_buffer = np.zeros((N_CHANS, BUFFER_LEN), dtype=np.float32)

        # Plot setup
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setYRange(-CHANNEL_SPACING, N_CHANS * CHANNEL_SPACING)
        self.plot_widget.setXRange(0, BUFFER_LEN)
        self.plot_widget.setLabel('bottom', 'Samples', units='')
        self.plot_widget.setLabel('left', 'Electrode Channels', units='')
        
        # Channel tick labels
        yticks = [(i * CHANNEL_SPACING, f"Ch {i+1}") for i in range(N_CHANS)]
        self.plot_widget.getAxis('left').setTicks([yticks])
        self.setCentralWidget(self.plot_widget)

        # Distinct trace colors
        colors = ['#00e5ff', '#76ff03', '#ffd600', '#ff3d00', '#d500f9', '#00e676', '#ff9100', '#2979ff']
        self.curves = [
            self.plot_widget.plot(pen=pg.mkPen(colors[i % len(colors)], width=1.3))
            for i in range(N_CHANS)
        ]

        # 30 FPS update timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(33)

    def update_plot(self):
        # Pull all newly arrived samples from LSL
        samples, _ = self.inlet.pull_chunk(max_samples=256)
        if samples:
            new_data = np.array(samples, dtype=np.float32).T
            n_new = new_data.shape[1]

            # Shift left and insert new points
            if n_new >= BUFFER_LEN:
                self.data_buffer = new_data[:, -BUFFER_LEN:]
            else:
                self.data_buffer = np.roll(self.data_buffer, -n_new, axis=1)
                self.data_buffer[:, -n_new:] = new_data

            # Update trace positions
            for i in range(N_CHANS):
                channel_signal = self.data_buffer[i].copy()
                
                # Remove slow DC drift (high contact impedance on dry electrodes causes baseline shift)
                channel_signal -= np.mean(channel_signal)
                
                # Offset channel vertically for stacked viewing
                offset = i * CHANNEL_SPACING
                self.curves[i].setData(channel_signal + offset)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    viewer = LSLVisualizer()
    viewer.show()
    sys.exit(app.exec())