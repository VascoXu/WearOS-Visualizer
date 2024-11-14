import sys
import threading
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from sensor import SensorStreamer
from scipy.signal import stft


class SensorVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensor Data Visualizer")
        self.setGeometry(100, 100, 1000, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # create accelerometer visualization
        self.accelerometer_plot = pg.PlotWidget(title="Real-time Signal: Accelerometer")
        layout.addWidget(self.accelerometer_plot)
        self.acc_x_line = self.accelerometer_plot.plot(pen='r', name='X')
        self.acc_y_line = self.accelerometer_plot.plot(pen='g', name='Y')
        self.acc_z_line = self.accelerometer_plot.plot(pen='b', name='Z')
        
        # create spectrogram plot
        self.spectrogram_plot = pg.PlotWidget(title="Spectrogram")
        layout.addWidget(self.spectrogram_plot)
        
        # create ImageItem for spectrogram
        self.img = pg.ImageItem()
        self.spectrogram_plot.addItem(self.img)
        
        # setup spectrogram parameters
        self.spec_buffer_size = 128  # Number of time points in spectrogram
        self.spec_window_size = 128   # FFT window size
        self.spec_overlap = 32       # Overlap between windows
        
        # calculate number of frequency bins (n_fft // 2 + 1)
        self.n_freq_bins = self.spec_window_size // 2 + 1
        self.spec_buffer = np.zeros((self.spec_buffer_size, self.n_freq_bins))
        
        # create color map
        self.img.setLookupTable(pg.colormap.get('magma').getLookupTable())

        # set spectrogram axes
        self.spectrogram_plot.setLabel('left', 'Frequency', units='Hz')
        self.spectrogram_plot.setLabel('bottom', 'Time', units='s')
        
        # initialize sensor streaming
        self.buffer_size = 1000
        self.sensor_streamer = SensorStreamer(sensor_window=self.buffer_size)
        self.sensor_thread = threading.Thread(target=self.update_sensor)
        self.sensor_thread.daemon = True
        self.sensor_thread.start()
        
        # setup animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.animation_loop)
        self.timer.start(33)  # ~30Hz
        
    def update_sensor(self):
        while True:
            self.sensor_streamer.update()
            
    def compute_spectrogram(self, data):
        # compute FFT
        f, t, Zxx = stft(data, fs=200,  # Assuming 200Hz sampling rate
                        nperseg=self.spec_window_size,
                        noverlap=self.spec_overlap,
                        padded=False)
        
        # magnitude in dB
        mag = 20 * np.log10(np.abs(Zxx) + 1e-10)  # Add small constant to avoid log(0)
        
        # only update if we have enough data and dimensions match
        if mag.shape[0] == self.n_freq_bins:
            # roll the buffer and add new data
            self.spec_buffer = np.roll(self.spec_buffer, -1, axis=0)
            self.spec_buffer[-1, :] = mag[:, -1]
        
        return self.spec_buffer
            
    def animation_loop(self):
        acc_data = self.sensor_streamer.get_accelerometer()
        if acc_data and len(acc_data) >= self.spec_window_size:  # Check if we have enough data
            # update accelerometer data
            x = list(range(len(acc_data)))
            acc = np.array(acc_data, dtype=np.float32)
            self.acc_x_line.setData(x, acc[:, 1])
            self.acc_y_line.setData(x, acc[:, 2])
            self.acc_z_line.setData(x, acc[:, 3])
            
            # compute and update spectrogram
            acc_mag = np.sqrt(acc[:, 1]**2 + acc[:, 2]**2 + acc[:, 3]**2)
            spec_data = self.compute_spectrogram(acc_mag)
            
            # update spectrogram image
            self.img.setImage(spec_data.T,
                            autoLevels=False,
                            levels=[-50, 50]) 
            
    def closeEvent(self, event):
        self.sensor_streamer.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SensorVisualizer()
    window.show()
    sys.exit(app.exec_())