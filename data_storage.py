# Takes reading and stores it in an excel file
# Has not been tested with real circuit/readings as of yet

# Last Updated: 03/08/2020
# Last Updated by: Justin Lawrence
# Author(s): Justin Lawrence
# Function: stores given readings in excel

import csv
from time import time

FILE_NAME = "data-test.csv"
start = 0 # start time of clock

# () -> ()
# creates csv file and writer
# can throw an OSError

def initialize_csv():
	global file
	try:
		file = open(FILE_NAME, 'a', newline='')
	except OSError:
		raise OSError
	global csv_writer
	csv_writer = csv.writer(file)

# Reading, (listof Reading) -> ()
# main function for data storage

def main(common_data, cells_data):
	global start
	if time() - start >= 15: # autosave every 15 seconds
		cleanup_csv()
		initialize_csv()
		start = time()
	try:
		store_reading(common_data, cells_data)
	except ValueError:
		print("Failed to store data at: ", int(time()))

# Reading, (listof Reading) -> ()
# Stores a reading in the writer
# Can throw ValueError exception

def store_reading(common_reading, cell_readings):
	reading = common_reading 
	for cell_reading in cell_readings:
		for item in cell_reading:
			reading.append(item)
	try:
		csv_writer.writerow(reading)
	except ValueError:
		raise ValueError

# () -> ()
# closes/saves csv files

def cleanup_csv():
	file.close()