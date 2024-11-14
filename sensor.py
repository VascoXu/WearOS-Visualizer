import socket
import time 
from collections import deque


class SensorStreamer: 
    def __init__(self, host='0.0.0.0', port=5555, buffer_size=1024, sensor_window=200):
        # socket information
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        # sensor data 
        self.sensor_window = sensor_window
        self.accelerometer = deque(maxlen=self.sensor_window)
        self.gyroscope = deque(maxlen=self.sensor_window)
        print(f"UDP receiver listening on {self.host}:{self.port}.")

    def process_data(self, data):
        parts = data.split(',')
        if len(parts) == 5:
            timestamp, sensor_type, x, y, z = parts
            x, y, z = float(x), float(y), float(z)
            if sensor_type == "ACCELEROMETER":
                self.accelerometer.append([timestamp, x, y, z])
            elif sensor_type == "GYROSCOPE":
                self.gyroscope.append([timestamp, x, y, z])
            return (timestamp, sensor_type, x, y, z)
        else:
            return None

    def get_accelerometer(self):
        return list(self.accelerometer)

    def get_gyroscope(self):
        return list(self.gyroscope)             

    def update(self):
        data, _ = self.socket.recvfrom(self.buffer_size)
        return self.process_data(data.decode())
    
    def close(self):
        self.socket.close()
        print("UDP receiver closed.")
