# EMG-UI-Data-Collections
Using this program we will be collecting EMG data from able-bodied people and storing said data in a secure location.

## Built with
* [![Python][Python.org]][Python-url]

[Python.org]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/

## Steps
1. Change the SERIAL_PORT to the appropriate port that the Arduino is connected to on your laptop device (COMX for Windows devices or usbmodem for MacOS devices)
2. Run the Python file in the terminal using python “.\src\readingEMGs.py” in the extracted directory.
   ```
   python .\src\readingEMGs.py
   ```
3. Enter the assigned participant ID number into the “ID” input box with the format participantID_action.
4. When the test is ready to begin and the participant is in the proper position, press the “Start” button and you should be able to see the EMG wavelengths being read in real time.
5. When the participant has completed their tests then press the “Stop” button. Wait a couple of seconds to let the program automatically filter the EMG data.
6. Click “View CSV” to view the collected data.

## Python Packages
   ### [MNE](https://mne.tools/stable/index.html)
   ```py
   pip install mne
   ```
   > A powerful library for processing, analyzing, and visualizing EEG data. Used to filter raw brain signals, extract relevant epochs, and prepare data for machine learning classification.
   ### [PyQt5](https://www.pythonguis.com/pyqt5-tutorial/)
   ```py
   pip install PyQt5
   ```
   > A library used for GUI development.
   ### [PyQtgraph](https://www.pyqtgraph.org/)
   ```py
   pip install PyQtgraph
   ```
   > A library used for plotting the graphs in the GUI.
   ### [pyEDFlib](https://pypi.org/project/pyEDFlib/)
   ```py
   pip install pyEDFlib
   ```
   > A library used for coverting the obtained data into a readable .edf file.
   ### [datetime](https://docs.python.org/3/library/datetime.html)
   ```py
   pip install datetime
   ```
   > A library used for getting the date.
   ### [os](https://docs.python.org/3/library/os.html)
   ```py
   pip install os
   ```
   > A library used for accessing the operating system
   ### [numpy]([https://docs.python.org/3/library/os.html](https://numpy.org/))
   ```py
   pip install numpy
   ```
   > A library used for mathematical functions.
