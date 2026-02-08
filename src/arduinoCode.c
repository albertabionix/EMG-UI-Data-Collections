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
    // 1. Read raw ADC values (0 to 1023)
    int raw1 = analogRead(EMG_PIN_1); 
    int raw2 = analogRead(EMG_PIN_2); 

    // 2. Subtract the 1.5V reference offset (~307 for 5V Arduino)
    // Use 307 if powered by 5V, or ~465 if powered by 3.3V
    int emg1 = raw1 - 307;
    int emg2 = raw2 - 307;

    // 3. Send centered data (now includes negative numbers)
    Serial.print(emg1);
    Serial.print(",");
    Serial.println(emg2);

    nextSampleTime += 1000000 / SAMPLE_RATE;
  }
}

