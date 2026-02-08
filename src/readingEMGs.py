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
SERIAL_PORT = "COM4" # <------- CHANGE THIS PORT
BAUD_RATE = 115200 # The speed at which symbols or signal changes are transmitted per second in a communication channel.
SAMPLING_RATE = 1000 # How many times per second a digital audio system measures.
WINDOW_SECONDS = 5
VERSION = "v2.1"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EDF_DIR = os.path.join(BASE_DIR, "recordings") # Directory for EDF files
# Files are separated by raw and filtered data.
RAW_DIR = os.path.join(BASE_DIR, "recordings", "raw")
FILTERED_DIR = os.path.join(BASE_DIR, "recordings", "filtered")

MAX_SAMPLES = SAMPLING_RATE * WINDOW_SECONDS

# Serial Thread
class SerialThread(QtCore.QThread):
    # Initializes and reads the serial of the EMG sensor and puts it into a format the python file can read.
    data_received = QtCore.pyqtSignal(float, float)

    def __init__(self, port, baud):
        super().__init__()
        self.port = port 
        self.baud = baud
        self.running = True

    def run(self):
        # Starts the code and continuously reads the serial from the arduino by pressing the "Start" button.
        try:
            ser = serial.Serial(self.port, self.baud, timeout=0.01)
            while self.running:
                line = ser.readline().decode(errors="ignore").strip()
                parts = line.split(",") 
                # In arduino code it is in format of (Number, Number).

                if len(parts) == 2:
                    try:
                        v1 = float(parts[0]) # Read from EMG Sensor 1
                        v2 = float(parts[1]) # Read from EMG Sensor 2
                        self.data_received.emit(v1, v2)
                    except ValueError:
                        pass
            ser.close()
        except Exception as e:
            print("Serial error:", e)

    def stop(self):
        # Ends the code and stops reading the serial from the arduino by pressing the "Stop" button.
        self.running = False
        self.wait()

# Main Window 
class EMGMonitor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time EMG Monitor")
        self.setGeometry(100, 100, 900, 900) # Sets the window size
        self.setStyleSheet("background-color: #540000; color: white;")

        self.data_ch1 = np.zeros(MAX_SAMPLES)
        self.data_ch2 = np.zeros(MAX_SAMPLES)
        self.ptr = 0
        self.time_arr = np.zeros(MAX_SAMPLES)  # Store time in seconds for x-axis

        self.init_ui()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)

        self.serial_thread = None

        self.elapsed_ms = 0 # Tracks the time passed

    # CSV 
    def init_csv(self):
        # Initializes the saving of the .csv file by placing them in the correct folders and saving the data with the raw and filtered.
        os.makedirs(RAW_DIR, exist_ok=True)
        os.makedirs(FILTERED_DIR, exist_ok=True)

        name = self.edit_name.text().strip() or "EMGTest" # Checks if ID exists and if not then name the file "EMGTest"
        ts = datetime.now().strftime("%b-%d-%Y_%H-%M-%S-%f")[:-3] # Get the exact time and date to name the file

        self.raw_csv_path = os.path.join(
            RAW_DIR, f"{name}_{ts}_raw.csv" # Name the file and store in the folder
        )

        self.csv_file = open(self.raw_csv_path, "w", newline="") 
        self.csv_writer = csv.writer(self.csv_file)

        self.csv_writer.writerow(["timestamp_ms", "emg_ch1", "emg_ch2"]) # Store the different the data types

        self.start_time = datetime.now() # Get the correct date

    # UI 
    def init_ui(self):
        # Logo
        logo_label = QtWidgets.QLabel()
        pixmap = QPixmap("src/imgs/transparent_logo.png") # Get img from folder
        pixmap = pixmap.scaled(
            60, 60,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        logo_label.setPixmap(pixmap)

        # Title
        title = QtWidgets.QLabel("Real-Time EMG Monitor")
        title.setFont(QFont("Arial", 22, QFont.Bold))

        # Timer
        self.timer_label = QtWidgets.QLabel("00:00.000")
        self.timer_label.setFont(QFont("Arial", 12))

        # Subtitle (version)
        subtitle = QtWidgets.QLabel(f"Version {VERSION}")
        subtitle.setStyleSheet("color: #aaaaaa;")

        # All EMG/IMU graphs
        self.plot1 = pg.PlotWidget(title="EMG Channel 1")
        self.plot2 = pg.PlotWidget(title="EMG Channel 2")
        self.plotIMU = pg.PlotWidget(title="IMU Channel")
        for p in (self.plot1, self.plot2, self.plotIMU):
            p.setBackground("k")  # Black background
            p.setLabel('bottom', 'Time', units='s') 
            p.setLabel('left', 'Microvolts', units='μV')
            p.setYRange(-500, 500)
            p.showGrid(x=True, y=True, alpha=0.3)

        # Plots the EMG waves into the graphs per second.
        self.curve1 = self.plot1.plot(pen=pg.mkPen("#00ffff", width=2))
        self.curve2 = self.plot2.plot(pen=pg.mkPen("#ff4d6d", width=2))
        self.curveIMU = self.plotIMU.plot(pen=pg.mkPen("#21e30f", width=2))

        # All the buttons in the program.
        self.start_btn = QtWidgets.QPushButton("Start")
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.view_btn = QtWidgets.QPushButton("View CSV")
        self.edit_name = QtWidgets.QLineEdit()
        # Add functionality to the buttons.
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.view_btn.clicked.connect(self.view_csv)
        # Add designs to the buttons.
        self.start_btn.setStyleSheet("background:#1db954; font-size:16px; padding:8px;")
        self.stop_btn.setStyleSheet("background:#e63946; font-size:16px; padding:8px;")
        self.view_btn.setStyleSheet("background:#457b9d; font-size:16px; padding:8px;")

        # Layout the buttons on the UI in a horizontal format.
        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.start_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(self.view_btn)

        # Layout the textbox so that users can name the file with an specific ID.
        name = QtWidgets.QHBoxLayout()
        name.addWidget(QtWidgets.QLabel("ID:"))
        name.addWidget(self.edit_name)

        # Layout for the title and logo so that it appears horizontally on UI.
        title_layout = QtWidgets.QHBoxLayout()
        title_layout.addWidget(logo_label)
        title_layout.addWidget(title)
        title_layout.addStretch()

        # Now set up the main layout by adding all the widgets vertically onto the UI.
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
        # Initialize the data when the "Start" button is pressed.
        self.data_ch1[:] = 0
        self.data_ch2[:] = 0
        self.time_arr[:] = 0
        self.ptr = 0
        self.elapsed_ms = 0
        self.timer_label.setText("00:00.000")

        self.init_csv()

        # Start reading the serial when the "Start" button is pressed.
        self.serial_thread = SerialThread(SERIAL_PORT, BAUD_RATE)
        self.serial_thread.data_received.connect(self.on_data)
        self.serial_thread.start()

        self.timer.start(30)

    def stop(self):
        # Stop data collection when the "Stop" button has been pressed then save it into a .csv file.
        if self.serial_thread:
            self.serial_thread.stop() # Stop receiving the serial from Arduino
            self.serial_thread = None

        self.timer.stop()

        if hasattr(self, "csv_file"):
            self.csv_file.close()
            del self.csv_file
            del self.csv_writer

        # Create filtered CSV
        self.filtered_csv_path = self.create_filtered_csv()

        # Have a message box letting the user know where the .csv files are stored.
        if self.filtered_csv_path:
            QtWidgets.QMessageBox.information(
                self,
                "Recording Saved",
                f"RAW:\n{self.raw_csv_path}\n\nFILTERED:\n{self.filtered_csv_path}"
            )

    def create_filtered_csv(self):
        # Creates a filtered .csv file using a band pass filter [20, 450] and notch filter [60].
        os.makedirs(FILTERED_DIR, exist_ok=True)
        # Checks if the Recordings folder exists.
        if not os.path.exists(self.raw_csv_path):
            return None

        data = np.loadtxt(self.raw_csv_path, delimiter=",", skiprows=1)
        
        if data.ndim == 1:
            data = data.reshape(1, -1)

        t = data[:, 0]
        ch1 = data[:, 1]
        ch2 = data[:, 2]

        # EMG sensor 1
        ch1_f = mne.filter.filter_data(
            ch1, SAMPLING_RATE, 20, 450, verbose=False
        )
        ch1_f = mne.filter.notch_filter(
            ch1_f, SAMPLING_RATE, [60], verbose=False
        )
        # EMG sensor 2
        ch2_f = mne.filter.filter_data(
            ch2, SAMPLING_RATE, 20, 450, verbose=False
        )
        ch2_f = mne.filter.notch_filter(
            ch2_f, SAMPLING_RATE, [60], verbose=False
        )

        base = os.path.basename(self.raw_csv_path)
        filt_path = os.path.join(
            FILTERED_DIR, base.replace(".csv", "_filtered.csv") # Place the filtered .csv data into a separate folder.
        )

        # Open the .csv file and get label the data with the corresponding time.
        with open(filt_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_ms", "emg_ch1_filt", "emg_ch2_filt"])
            for ti, v1, v2 in zip(t, ch1_f, ch2_f):
                writer.writerow([f"{ti:.3f}", v1, v2]) 

        return filt_path

    # Data Handling
    def on_data(self, ch1, ch2):
        # A callback that gets called every time new data arrives by tracking how many samples has arrived and logs into the .csv file
        # with time stamps.
        if not hasattr(self, "csv_writer"):
            return

        i = self.ptr % MAX_SAMPLES

        # Stores the incoming samples into buffers.
        self.data_ch1[i] = ch1
        self.data_ch2[i] = ch2
        self.ptr += 1

        # Keeps track of the timer and the timespan.
        elapsed = (datetime.now() - self.start_time).total_seconds() * 1000
        self.time_arr[i] = (datetime.now() - self.start_time).total_seconds()

        self.csv_writer.writerow([f"{elapsed:.3f}", ch1, ch2])

    def update_plot(self):
        # Updates the two plot curves of the EMG signals and increments the time.
        idx = self.ptr % MAX_SAMPLES

        # Roll arrays so newest data is at the end
        rolled_ch1 = np.roll(self.data_ch1, -idx)
        rolled_ch2 = np.roll(self.data_ch2, -idx)
        rolled_time = np.roll(self.time_arr, -idx)

        # Only plot the valid time window
        valid = rolled_time > 0
        self.curve1.setData(rolled_time[valid], rolled_ch1[valid])
        self.curve2.setData(rolled_time[valid], rolled_ch2[valid])

        # Update timer label.
        self.elapsed_ms += self.timer.interval()
        minutes = self.elapsed_ms // 60000
        seconds = (self.elapsed_ms % 60000) // 1000
        millis = self.elapsed_ms % 1000


        # Set x-axis range to show latest 4 seconds
        if np.any(valid):
            x_max = rolled_time[valid][-1]
            x_min = max(0, x_max - 8)
            self.plot1.setXRange(x_min, x_max, padding=0)
            self.plot2.setXRange(x_min, x_max, padding=0)
            self.plotIMU.setXRange(x_min, x_max, padding=0)

        self.timer_label.setText(f"{minutes:02}:{seconds:02}.{millis:03}")

    # View csv

    def view_csv(self):
        # Robustly view and plot raw and filtered CSV data
        # RAW
        if not hasattr(self, "raw_csv_path") or not os.path.exists(self.raw_csv_path):
            QtWidgets.QMessageBox.warning(self, "No Data", "No RAW CSV file found.")
            return

        try:
            df_raw = pd.read_csv(self.raw_csv_path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to read RAW CSV: {e}")
            return

        # Check columns
        if not all(col in df_raw.columns for col in ["timestamp_ms", "emg_ch1", "emg_ch2"]):
            QtWidgets.QMessageBox.warning(self, "Error", "RAW CSV missing required columns.")
            return

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

        # FILTERED
        if not hasattr(self, "filtered_csv_path") or not os.path.exists(self.filtered_csv_path):
            plt.tight_layout()
            plt.show()
            return

        try:
            df_filt = pd.read_csv(self.filtered_csv_path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to read FILTERED CSV: {e}")
            plt.tight_layout()
            plt.show()
            return

        if not all(col in df_filt.columns for col in ["timestamp_ms", "emg_ch1_filt", "emg_ch2_filt"]):
            QtWidgets.QMessageBox.warning(self, "Error", "FILTERED CSV missing required columns.")
            plt.tight_layout()
            plt.show()
            return

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