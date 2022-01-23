 /*
  Data logging program for experiment
  Has not been tested with and gyroscope yet
  Currently analog pins 0-3 for are voltages, 4-5 for clock and gyroscope
  Digital pins 4-7 are for temperature, 10-13 are for SD

  Last Updated: 19/09/2021
  Last Updated by: Justin Lawrence
  Author(s): Justin Lawrence
  Function: Logs data for in-lab experiment on SD card, and sends to computer
*/

// TODO: Allow the program to panic if something gets disconnected.
// TODO: Have the Arduino check that the serial buffer isn't full before writing.

#include <SD.h> // SD card library
#include <Wire.h> // Data shield requires this
#include "RTClib.h" // Data shield clock library
#include <OneWire.h> // Temperature sensor libraries
#include <DallasTemperature.h>
#include "I2Cdev.h" // Communication libraries for gyroscope
#include "MPU6050.h"

/*
 * RTC uses A4 and A5 pins, as does the gyroscope
 * SD uses digital pins 10-13
 */

struct cell_info {
  // Structure representing the details of the cell (relavant pins, etc.)
  OneWire address;
  uint8_t address_value;
  int pin;
  DallasTemperature temperature_sensor;
};

struct cell_reading {
  // Structure for holding time, temperature, and voltage/current readings of a cell
  float temperature; // temperature of  at time of reading (C)
  int voltage; // Pin before resistor (also pin at start), pin after resistor
};

struct cell {
  // Puts together a cell with its most recent reading
  cell_info info;
  cell_reading reading;
};

struct short_vector {
  // Structure for holding the x, y, and z components of a vector value
  int16_t x;
  int16_t y;
  int16_t z;
};

struct gyro_reading {
  // Strucure for holding gyroscope readings
  short_vector linear_acceleration;
  short_vector angular_velocity;
};

struct reading {
    unsigned long timestamp; // time of reading
    gyro_reading gyroscope; // universal gyroscope readings
    cell_reading cell_read; // readings of the cell
};

/* Global constant setup
*  Might have to be changed between uses
*  ALWAYS CHECK THE CONSTANTS ARE SET CORRECTLY!
*/

const String filename = "data.csv"; // Name can only be 8 characters long, not including .csv
bool filePath; // Declaring file path variable !!!
RTC_DS1307 rtc; // Sets up clock object
MPU6050 gyroscope_sensor(0x69); // gyroscopic sensor (don't change the address)
uint8_t gyro_range = MPU6050_GYRO_FS_250; // check library for other options, 250deg/s
uint8_t accel_range = MPU6050_ACCEL_FS_4; // check library for other options, 2g
uint8_t Loops = 7; // Loops*100 measurements used to calibrate gyroscope
const int signal_pin = 8; // connect the progress/panic light to this pin
const int control_pin = 3; // connect to switch to control the arduino (manual or computer)
const int manual_pin = 9; // connect to switch for manual signal
byte serial_state = 0; // 1 means continue running, 0 means kill the program
byte switch_state = 0; // 1 means manual override, 0 means run based on computer
cell crs; // all cells
reading current_reading; // the current reading of the setup
unsigned long start = 0; // time of most recent file save in unixtime
unsigned long save_freq = 1000*60*15; // frequency of saving in milliseconds
unsigned long temp_start = 0; // time of the most recent temperature reading, in millisceconds
unsigned long temp_freq = 5000; // frequency of temperature readings, in milliseconds
const char OPEN_PACKAGE = '{';
const char CLOSE_PACKAGE = '}';
const char OPEN_READING = '<';
const char CLOSE_READING = '>';
const char OPEN_VALUE = '(';
const char CLOSE_VALUE = ')';
const char DELIMETER = ',';
const char NEWLINE[4] = "\r\n";

void setup() {
  
  pinMode(signal_pin, OUTPUT);
  if (setup_communication()) {
    gyroscope_sensor.setFullScaleGyroRange(gyro_range);
    gyroscope_sensor.setFullScaleAccelRange(accel_range);
    calibrate_sensors(Loops);
    filePath = SD.open(filename, FILE_WRITE);
    if (filePath) {
      if (setup_cell()) {
        analogReference(EXTERNAL); // set to compare to aref
        analogRead(A0); delay(100); analogRead(A0); // first couple analog readings are innacurate
        crs.info.temperature_sensor.setResolution(12); // set to highest possible resoultion
        crs.info.temperature_sensor.setWaitForConversion(false); // don't block on requestTemperatures
        for (int j = 0; j < 2; j++) {
          crs.info.temperature_sensor.requestTemperatures();
          start = millis();
          while ((!crs.info.temperature_sensor.isConversionComplete()) && (millis() - start <= 5000));
            // This is needed because the temperature sensors give a faulty first reading with the decreased wait time
        }
        temp_start = millis();
        //rtc.adjust(DateTime(F(__DATE__), F(__TIME__))); // Sets the date and time to compile time, only include if the clock needs to be reset
        pinMode(control_pin, INPUT);
        pinMode(manual_pin, INPUT);
        start = rtc.now().unixtime(); // set initial time
        indicate_ready();
        digitalWrite(signal_pin, HIGH); // indicate a successful setup
        return;
      }
    }
  }
  panic(); 
}

// () -> Boolean
// sets up communication channels for arduino, produce true if successful
// rtc.begin() calls Wire.being(), so that's handled

boolean setup_communication() {
  Serial.begin(9600);
  bool clock_setup = rtc.begin();
  // this is essentially a wrapper for Wire.begin(), which must be called
  // for the gyroscope to work
  gyroscope_sensor.initialize();
  return SD.begin() && clock_setup && gyroscope_sensor.testConnection();
}

// () -> Boolean
// sets up the cell, returns true if all sensors are contacted

boolean setup_cell() {
  uint8_t sensor_address = 4;
  crs.info.address = sensor_address;
  crs.info.address_value = sensor_address;
  crs.info.pin = 14;
  crs.info.temperature_sensor.setOneWire(&crs.info.address);
  crs.info.temperature_sensor.begin();
  return true;
}

// uint_8 -> ()
// Calibrates gyroscope and accelerometer sensors, looping test loops times

void calibrate_sensors(uint8_t loops) {
  gyroscope_sensor.CalibrateAccel(loops);
  gyroscope_sensor.CalibrateGyro(loops);
}

// () -> ()
// Blinks light quickly 5 times to indicate the cell is ready for data collection

void indicate_ready() {
  for (byte i = 0; i < 5; i++) {
    digitalWrite(signal_pin, HIGH);
    delay(100);
    digitalWrite(signal_pin, LOW);
    delay(100);
  }
}

// () -> ()
// Blinks the signal light forever

void panic() {
  do {
    digitalWrite(signal_pin, HIGH);
    delay(1000);
    digitalWrite(signal_pin, LOW);
    delay(1000);
  } while (true);
}

void loop() {
  if (!check_continue()) {
    holding_loop();
  }
  read_sensors();
  if (switch_state == 0) write_Serial();
  write_SD();
}

// () -> ()
// reads the data from temperature sensor, apin, gyro, and rtc, and writes it to crs

void read_sensors() {
  current_reading.timestamp = rtc.now().unixtime();
  if (current_reading.timestamp - start > save_freq) {
    filePath.close();
    filePath = SD.open(filename, FILE_WRITE);
    if (!filePath) {
      panic();
    }
  }
  gyroscope_sensor.getMotion6(&current_reading.gyroscope.linear_acceleration.x,
                              &current_reading.gyroscope.linear_acceleration.y,
                              &current_reading.gyroscope.linear_acceleration.z,
                              &current_reading.gyroscope.angular_velocity.x,
                              &current_reading.gyroscope.angular_velocity.y,
                              &current_reading.gyroscope.angular_velocity.z);
  bool read_temp = false;
  if (millis() - temp_start > temp_freq) { 
    read_temp = true;
    temp_start = millis();
  }
  current_reading.cell_read = read_cell(crs, read_temp);
}


// cell_and_reading, boolean -> reading
// reads data from cell

cell_reading read_cell(cell &c, bool read_temp) {
  c.reading.voltage = analogRead(c.info.pin);
  if (read_temp) { // read temperature once every five seconds
    //while (!c.info.temperature_sensor.isConversionComplete()); // block until temperature sensor is done
    c.reading.temperature = c.info.temperature_sensor.getTempCByIndex(0);
    c.info.temperature_sensor.requestTemperatures(); // restart temperature request
  }
  return c.reading;
}

// () -> ()
// writes current data in crs to SD

void write_SD() {
  write_Time_SD();
  write_Gyroscope_SD();
  //write_Cell_SD(current_reading.cell_read); // !!!
  // filePath.print(NEWLINE);
}

// type -> ()
// abstract function to print a value to SD

template<class T>
inline void write_Value_SD(T val) {
  filePath.print(DELIMETER);
  filePath.print(val);
}

// cell_reading -> ()
// writes given cell reading data to SD

void write_Cell_SD(cell_reading r) {
    write_Value_SD(r.voltage);
    write_Value_SD(r.temperature);
}

// () -> ()
// writes time data in current reading to SD


void write_Time_SD() {
  filePath.print(current_reading.timestamp);
}

// () -> ()
// writes gyroscope readings to SD

void write_Gyroscope_SD() {
    write_Vector_SD(current_reading.gyroscope.linear_acceleration);
    write_Vector_SD(current_reading.gyroscope.angular_velocity);
}

// Vector -> ()
// writes vector readings to SD

void write_Vector_SD(short_vector vector) {
    write_Value_SD(vector.x);
    write_Value_SD(vector.y);
    write_Value_SD(vector.z);
}

// () -> ()
// writes current data in crs to serial

void write_Serial() {
  Serial.print(OPEN_PACKAGE);
  Serial.print(OPEN_READING);
  write_Time();
  write_Gyroscope();
  Serial.print(CLOSE_READING);
  write_Cell(current_reading.cell_read);
  Serial.print(CLOSE_PACKAGE);
}

// type implementing print -> ()
// abstract function to print a value to Serial

template<class T>
inline void write_Value(T val) {
  Serial.print(OPEN_VALUE);
  Serial.print(val);
  Serial.print(CLOSE_VALUE);
}

// cell_reading -> ()
// writes given cell reading data to serial

void write_Cell(cell_reading r) {
    Serial.print(OPEN_READING);
    write_Value(r.voltage);
    write_Value(r.temperature);
    Serial.print(CLOSE_READING);
}

// () -> ()
// writes time data in current reading to serial

void write_Time() {
  write_Value(current_reading.timestamp);
}

// () -> ()
// writes gyroscope readings to serial

void write_Gyroscope() {
    write_Vector(current_reading.gyroscope.linear_acceleration);
    write_Vector(current_reading.gyroscope.angular_velocity);
}

// Vector -> ()
// writes vector readings to serial

void write_Vector(short_vector vector) {
    write_Value(vector.x);
    write_Value(vector.y);
    write_Value(vector.z);
}

// () -> Boolean
// returns true if data recording should begin/continue

boolean check_continue() {
  switch_state = (digitalRead(control_pin) == HIGH);
  update_serial_state();
  if (switch_state) {
    return (digitalRead(manual_pin) == HIGH);
  } else {
    return serial_state;
  }
}

// () -> ()
// updates the current serial state

void update_serial_state() {
  if (Serial.available() > 0) {
    serial_state = Serial.read();
  }
  return;
}

// () -> ()
// saves SD file and holds until check_continue() == true

void holding_loop() {
  // filePath.close(); // !!!
  digitalWrite(signal_pin, LOW);
  do {
    delay(1);
  } while (!check_continue());
  filePath = SD.open(filename, FILE_WRITE);
  if (!filePath) {
    panic();
  }
  start = rtc.now().unixtime();
  digitalWrite(signal_pin, HIGH);
  delay(50);
}
