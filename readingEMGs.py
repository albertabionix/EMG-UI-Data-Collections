import sys
import serial
import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont, QPixmap
import pyqtgraph as pg
from datetime import datetime
import os
import mne
import csv
import pandas as pd
import matplotlib.pyplot as plt

# Configuration
SERIAL_PORT = "COM9"
BAUD_RATE = 115200
SAMPLING_RATE = 1000
WINDOW_SECONDS = 5
VERSION = "v2.1"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EDF_DIR = os.path.join(BASE_DIR, "recordings") # Directory for EDF files
RAW_DIR = os.path.join(BASE_DIR, "recordings", "raw")
FILTERED_DIR = os.path.join(BASE_DIR, "recordings", "filtered")

MAX_SAMPLES = SAMPLING_RATE * WINDOW_SECONDS

# Serial Thread
class SerialThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(float, float)

    def __init__(self, port, baud):
        super().__init__()
        self.port = port
        self.baud = baud
        self.running = True

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baud, timeout=0.01)
            while self.running:
                line = ser.readline().decode(errors="ignore").strip()
                parts = line.split(",")

                if len(parts) == 2:
                    try:
                        v1 = float(parts[0])
                        v2 = float(parts[1])
                        self.data_received.emit(v1, v2)
                    except ValueError:
                        pass
            ser.close()
        except Exception as e:
            print("Serial error:", e)


    def stop(self):
        self.running = False
        self.wait()

# Main Window 
class EMGMonitor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time EMG Monitor")
        self.setGeometry(100, 100, 900, 900)
        self.setStyleSheet("background-color: #540000; color: white;")

        self.data_ch1 = np.zeros(MAX_SAMPLES)
        self.data_ch2 = np.zeros(MAX_SAMPLES)
        self.ptr = 0

        self.init_ui()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)

        self.serial_thread = None

        self.elapsed_ms = 0

    # CSV 
    def init_csv(self):
        os.makedirs(RAW_DIR, exist_ok=True)
        os.makedirs(FILTERED_DIR, exist_ok=True)

        name = self.edit_name.text().strip() or "EMGTest"
        ts = datetime.now().strftime("%b-%d-%Y_%H-%M-%S-%f")[:-3]

        self.raw_csv_path = os.path.join(
            RAW_DIR, f"{name}_{ts}_raw.csv"
        )

        self.csv_file = open(self.raw_csv_path, "w", newline="")
        self.csv_writer = csv.writer(self.csv_file)

        self.csv_writer.writerow(["timestamp_ms", "emg_ch1", "emg_ch2"])

        self.start_time = datetime.now()


    # UI 
    def init_ui(self):
        # Logo
        logo_label = QtWidgets.QLabel()
        pixmap = QPixmap("transparent_logo.png")
        pixmap = pixmap.scaled(
            60, 60,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        logo_label.setPixmap(pixmap)
        title = QtWidgets.QLabel("Real-Time EMG Monitor")
        title.setFont(QFont("Arial", 22, QFont.Bold))

        self.timer_label = QtWidgets.QLabel("00:00.000")
        self.timer_label.setFont(QFont("Arial", 12))


        subtitle = QtWidgets.QLabel(f"Version {VERSION}")
        subtitle.setStyleSheet("color: #aaaaaa;")

        self.plot1 = pg.PlotWidget(title="EMG Channel 1")
        self.plot2 = pg.PlotWidget(title="EMG Channel 2")
        self.plotIMU = pg.PlotWidget(title="IMU Channel")

        for p in (self.plot1, self.plot2, self.plotIMU):
            p.setBackground("k")
            p.hideAxis("left")
            p.hideAxis("bottom")

        self.curve1 = self.plot1.plot(pen=pg.mkPen("#00ffff", width=2))
        self.curve2 = self.plot2.plot(pen=pg.mkPen("#ff4d6d", width=2))
        self.curveIMU = self.plotIMU.plot(pen=pg.mkPen("#21e30f", width=2))

        self.start_btn = QtWidgets.QPushButton("Start")
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.view_btn = QtWidgets.QPushButton("View CSV")
        self.edit_name = QtWidgets.QLineEdit()

        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.view_btn.clicked.connect(self.view_csv)

        self.start_btn.setStyleSheet("background:#1db954; font-size:16px; padding:8px;")
        self.stop_btn.setStyleSheet("background:#e63946; font-size:16px; padding:8px;")
        self.view_btn.setStyleSheet("background:#457b9d; font-size:16px; padding:8px;")

        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.start_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(self.view_btn)

        name = QtWidgets.QHBoxLayout()
        name.addWidget(QtWidgets.QLabel("ID:"))
        name.addWidget(self.edit_name)

        title_layout = QtWidgets.QHBoxLayout()
        title_layout.addWidget(logo_label)
        title_layout.addWidget(title)
        title_layout.addStretch()

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(title_layout)
        layout.addWidget(subtitle)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.plot1)
        layout.addWidget(self.plot2)
        layout.addWidget(self.plotIMU)
        layout.addLayout(btns)
        layout.addLayout(name)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # Controls 
    def start(self):
        self.data_ch1[:] = 0
        self.data_ch2[:] = 0
        self.ptr = 0
        self.elapsed_ms = 0
        self.timer_label.setText("00:00.000")

        self.init_csv()

        self.serial_thread = SerialThread(SERIAL_PORT, BAUD_RATE)
        self.serial_thread.data_received.connect(self.on_data)
        self.serial_thread.start()

        self.timer.start(30)

    def stop(self):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread = None

        self.timer.stop()

        if hasattr(self, "csv_file"):
            self.csv_file.close()
            del self.csv_file
            del self.csv_writer

        # Create filtered CSV
        self.filtered_csv_path = self.create_filtered_csv()

        if self.filtered_csv_path:
            QtWidgets.QMessageBox.information(
                self,
                "Recording Saved",
                f"RAW:\n{self.raw_csv_path}\n\nFILTERED:\n{self.filtered_csv_path}"
            )

    def create_filtered_csv(self):
        os.makedirs(FILTERED_DIR, exist_ok=True)
        if not os.path.exists(self.raw_csv_path):
            return None

        data = np.loadtxt(self.raw_csv_path, delimiter=",", skiprows=1)

        
        if data.ndim == 1:
            data = data.reshape(1, -1)

        t = data[:, 0]
        ch1 = data[:, 1]
        ch2 = data[:, 2]

        ch1_f = mne.filter.filter_data(
            ch1, SAMPLING_RATE, 20, 450, verbose=False
        )
        ch1_f = mne.filter.notch_filter(
            ch1_f, SAMPLING_RATE, [60], verbose=False
        )

        ch2_f = mne.filter.filter_data(
            ch2, SAMPLING_RATE, 20, 450, verbose=False
        )
        ch2_f = mne.filter.notch_filter(
            ch2_f, SAMPLING_RATE, [60], verbose=False
        )

        base = os.path.basename(self.raw_csv_path)
        filt_path = os.path.join(
            FILTERED_DIR, base.replace(".csv", "_filtered.csv")
        )

        with open(filt_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_ms", "emg_ch1_filt", "emg_ch2_filt"])
            for ti, v1, v2 in zip(t, ch1_f, ch2_f):
                writer.writerow([f"{ti:.3f}", v1, v2])

        return filt_path



    # Data Handling
    def on_data(self, ch1, ch2):
        if not hasattr(self, "csv_writer"):
            return

        i = self.ptr % MAX_SAMPLES

        self.data_ch1[i] = ch1
        self.data_ch2[i] = ch2
        self.ptr += 1

        elapsed = (datetime.now() - self.start_time).total_seconds() * 1000

        self.csv_writer.writerow([f"{elapsed:.3f}", ch1, ch2])

    def update_plot(self):
        idx = self.ptr % MAX_SAMPLES

        self.curve1.setData(np.roll(self.data_ch1, -idx))
        self.curve2.setData(np.roll(self.data_ch2, -idx))


        # Update timer label
        self.elapsed_ms += self.timer.interval()
        minutes = self.elapsed_ms // 60000
        seconds = (self.elapsed_ms % 60000) // 1000
        millis = self.elapsed_ms % 1000

        self.timer_label.setText(f"{minutes:02}:{seconds:02}.{millis:03}")

    # View csv
    def view_csv(self):
        # Raw
        if not hasattr(self, "raw_csv_path") or not os.path.exists(self.raw_csv_path):
            QtWidgets.QMessageBox.warning(self, "No Data", "No RAW CSV file found.")
            return

        df_raw = pd.read_csv(self.raw_csv_path)

        t_raw = df_raw["timestamp_ms"] / 1000.0
        ch1_raw = df_raw["emg_ch1"]
        ch2_raw = df_raw["emg_ch2"]

        plt.figure(figsize=(12, 8))

        plt.subplot(4, 1, 1)
        plt.plot(t_raw, ch1_raw)
        plt.title("RAW EMG – Channel 1")
        plt.ylabel("Amplitude")
        plt.grid(True)

        plt.subplot(4, 1, 2)
        plt.plot(t_raw, ch2_raw)
        plt.title("RAW EMG – Channel 2")
        plt.ylabel("Amplitude")
        plt.grid(True)

        # Filtered
        if not hasattr(self, "filtered_csv_path") or not os.path.exists(self.filtered_csv_path):
            plt.tight_layout()
            plt.show()
            return

        df_filt = pd.read_csv(self.filtered_csv_path)

        t_filt = df_filt["timestamp_ms"] / 1000.0
        ch1_filt = df_filt["emg_ch1_filt"]
        ch2_filt = df_filt["emg_ch2_filt"]

        plt.subplot(4, 1, 3)
        plt.plot(t_filt, ch1_filt)
        plt.title("FILTERED EMG – Channel 1 (20–450 Hz, Notch 60 Hz)")
        plt.ylabel("Amplitude")
        plt.grid(True)

        plt.subplot(4, 1, 4)
        plt.plot(t_filt, ch2_filt)
        plt.title("FILTERED EMG – Channel 2 (20–450 Hz, Notch 60 Hz)")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.grid(True)

        plt.tight_layout()
        plt.show()

        
        
# Run Application
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = EMGMonitor()
    win.show()
    sys.exit(app.exec_())
