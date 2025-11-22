import sys
import time
from PyQt5 import QtWidgets

#
# Class object of the main window
#
class EMGMonitor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Setting the window title and size
        self.setWindowTitle("EMG Monitor")
        self.setGeometry(100, 100, 800, 600)

        # Data buffers
        self.raw_data = []
        self.filtered_data = []
        self.time_stamps = []
        self.start_time = time.time()

        # Initialize UI components
        self.initUI()

    def initUI(self):
        # Create a central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # Create a layout
        layout = QtWidgets.QVBoxLayout()

        # Add a label
        label = QtWidgets.QLabel("EMG Data Monitoring Interface")
        layout.addWidget(label)

        # Add a button
        button = QtWidgets.QPushButton("Start Monitoring")
        layout.addWidget(button)

        # Set the layout to the central widget
        central_widget.setLayout(layout)

#
# Run the application
#
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = EMGMonitor()
    window.show()
    sys.exit(app.exec_())