# EMG-UI-Data-Collections
An application to save EMG data into EDF format.

## Built with
* [![Python][Python.org]][Python-url]

[Python.org]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/

## Steps
1. Open arduino IDE and run
```
// Reads raw EMG signals from two Gravity Analog EMG modules
// Sends data to Python over Serial in format: ch1,ch2\n

#define EMG_PIN_1 A0
#define EMG_PIN_2 A1

const int SAMPLE_RATE = 1000;         
unsigned long nextSampleTime = 0;

void setup() {
  Serial.begin(115200);
  delay(2000);                        
  nextSampleTime = micros();
}

void loop() {
  unsigned long now = micros();

  if (now >= nextSampleTime) {
    int emg1 = analogRead(EMG_PIN_1); 
    int emg2 = analogRead(EMG_PIN_2); 

    
    Serial.print(emg1);
    Serial.print(",");
    Serial.println(emg2);

    nextSampleTime += 1000000 / SAMPLE_RATE;
  }
}

```
2. Check which port (Ex. COM1) the arduino is connected too and make sure that is the same in the program code. If not change it within the code.
3. Input the ID.
4. Press start.
5. Wait 


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
   ### [datetime](https://pypi.org/project/pyEDFlib/](https://docs.python.org/3/library/datetime.html)
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
