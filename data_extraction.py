# Takes data package, breaks it up into its component parts,
# and sends it off as a dictionary
# Has not been tested with real circuit/readings as of yet

# Last Updated: 24/07/2021
# Last Updated by: Justin Lawrence
# Author(s): Justin Lawrence
# Function: turns data package into dictionary and sends it
# along to rtg and excel storage

import multiprocessing as mtp
import data_storage as ds
import real_time_plot as rtp

OPEN_PACKAGE = '{' # these six should match the arduino code
CLOSE_PACKAGE = '}'
OPEN_READING = '<'
CLOSE_READING = '>'
OPEN_VALUE = '('
CLOSE_VALUE = ')'
AREF = 1.75 # voltage at the aref pin
TO_VOLT = AREF / 1023 
RESISTANCE = 560 # resistance of measuring resistors in ohms
# These two should also match the Arduino code
ACCEL_RANGE = 4 # range of the accelerometer readings, in g
GYRO_RANGE = 250 # range of gyroscope readings, in deg/s
SHORT = 32768 # range of a short

# Reading is one of 
#   - [Int, Float, Float, Float, Float, Float, Float}
#     A reading for gyroscope and time data
#   - [Float, Int, Float]
#     A reading for a cell

# (listof Char) Pipe Boolean -> ()
# main function for handling packages

def main(chars, graph, send_data):
	common_data, cells = package_extract(chars)
	ds.main(common_data, cells)
	if send_data:
		graph.send(cells)

# (listof Char) -> Reading, (listof Reading)
# produce a dictionary representation of the readings in the data package

def package_extract(chars):
	values = list()
	readings = list()
	value = ""
	first_time = True
	for char in chars:
		if char == OPEN_PACKAGE:
			pass
		elif char == OPEN_READING:
			values.clear()
		elif char == OPEN_VALUE:
			value = ""
		elif char == CLOSE_VALUE:
			try:
				value = int(value)
			except ValueError:
				value = float(value)
			values.append(value)
		elif char == CLOSE_READING:
			if first_time:
				readings.append(list_to_reading_general(values))
				first_time = False
			else:
				readings.append(list_to_reading_cell(values))
		elif char == CLOSE_PACKAGE:
			pass
		else:
			value += char
	return readings[0], readings[1:]

# (listof Number) -> Reading
# converst a list of values to a reading for gyroscope/time data

def list_to_reading_general(values):
	reading = []
	reading.append(values[0]) # time isn't changed
	for i in range(1,7):
		if i < 4:
			reading.append((values[i] / SHORT) * ACCEL_RANGE)
		else:
			reading.append((values[i] / SHORT) * GYRO_RANGE)
	return reading

# (listof Number) -> Reading
# converts a list of values to a reading for a cell

def list_to_reading_cell(values):
	reading = []
	reading.append(values[0] * TO_VOLT * 2) # times two because of voltage splitting
	reading.append(RESISTANCE) # !!! For potential later uses
	reading.append(values[1])
	return reading
