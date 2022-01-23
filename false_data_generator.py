# Generates fake data to be processed

# Last Updated: 16/07/2020
# Last Updated by: Justin Lawrence
# Author(s): Justin Lawrence
# Function: Groups data from serial port into packages and passes it along
# for further processing

import serial
from random import random
from random import randint
from time import time
from time import sleep

PORT_NAME = "COM1"
BAUD_RATE = 9600 # Should match arduino code
OPEN_PACKAGE = '{' # these six should match the arduino code
CLOSE_PACKAGE = '}'
OPEN_READING = '<'
CLOSE_READING = '>'
OPEN_VALUE = '('
CLOSE_VALUE = ')'
GYRO_MAX = 10
GYRO_MIN = -10
MAX_READING = 1024 # maximum possible analogRead() value
MIN_READING = 0
MAX_TEMPERATURE = 50.0
MIN_TEMPERATURE = 10.0
RANGE = MAX_TEMPERATURE - MIN_TEMPERATURE
RATE = 1
NUM_PACKAGES = 100

# () -> ()
# main program loop

def main():
	try: 
		serial_port = serial.Serial(PORT_NAME, BAUD_RATE)
	except ValueError:
		print("Baud Rate was not valid")
		return
	except serial.SerialException as fail:
		print("Problem initializing: ", fail)
		return
	for i in range(0, NUM_PACKAGES):
		package = generate_package()
		serial_port.write(package)
		sleep(RATE)
	serial_port.write('d'.encode())

# () -> (listof byte)
# produces a fake data package

def generate_package():
	result = OPEN_PACKAGE + generate_common_reading()
	for i in range(0, 4):
		result += generate_cell_reading()
	result += CLOSE_PACKAGE
	return result.encode()

# () -> String
# produces a fake common data reading

def generate_common_reading():
	result = OPEN_READING
	result += generate_time()
	for i in range(0,6):
		result += generate_gyro()
	return result + CLOSE_READING

# () -> String
# produces a fake data reading for a cell

def generate_cell_reading():
	result = OPEN_READING
	result += generate_voltage("high")
	result += generate_voltage("low")
	result += generate_temperature()
	return result + CLOSE_READING

# () -> String
# produce current unix time as a string

def generate_time():
	return OPEN_VALUE + str(int(time())) + CLOSE_VALUE

# () -> String
# produce a random gyro data point as a string

def generate_gyro():
	gyro_reading = randint(GYRO_MIN, GYRO_MAX)
	return OPEN_VALUE + str(gyro_reading) + CLOSE_VALUE

# "high" or "low" -> String
# produce either high or low random voltage as a string

def generate_voltage(option):
	if option == "high":
		voltage = randint(MAX_READING / 2, (MAX_READING - 1))
	else:
		voltage = randint(MIN_READING, MAX_READING / 2)
	return OPEN_VALUE + str(voltage) + CLOSE_VALUE

# () -> String
# produce random temperature as string

def generate_temperature():
	return OPEN_VALUE + str((random() * RANGE) + MIN_TEMPERATURE) + CLOSE_VALUE

main()
