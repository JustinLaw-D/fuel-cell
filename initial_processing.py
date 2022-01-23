# Reads data directly from Serial and sends it off to storage and processing
# Has not been tested with real circuit/readings as of yet

# Last Updated: 08/08/2021
# Last Updated by: Justin Lawrence
# Author(s): Justin Lawrence
# Function: Groups data from serial port into packages and passes it along
# for further processing

# TODO: this program randomly hung once
# I can't seem to replicate the problem.


import serial
import keyboard
import multiprocessing as mtp
import data_extraction as de
import data_storage as ds
import real_time_plot as rtp

PORT_NAME = "COM3" # be sure to check these on every new computer, especially not windows
BAUD_RATE = 9600 # Should match arduino code
OPEN_PACKAGE = '{' # these two should also match the arduino code
CLOSE_PACKAGE = '}'
RECORDING_MESSAGE = "Recording"
STOP_MESSAGE = "Not recording"

# () -> Boolean
# does initial setup of program, returns True if it works

def setup():
	try:
		ds.initialize_csv()
	except OSError:
		print("Failed to open csv file: ", OSError)
		return False
	try:
		global serial_port 
		serial_port = serial.Serial(PORT_NAME, BAUD_RATE)
		serial_port.reset_input_buffer() # clean buffers
		serial_port.reset_output_buffer()
	except ValueError:
		print("Baud Rate was not valid")
		return False
	except serial.SerialException as fail:
		print("Problem initializing: ", fail)
		return False
	return True

# () -> (Connection, Connection, Process)
def graph_setup():
	try:
		recieve, send = mtp.Pipe(False)
		graph_process = mtp.Process(target=rtp.main, args=(recieve,))
		graph_process.daemon = True
		graph_process.start()
		return recieve, send, graph_process
	except mtp.ProcessError as err:
		raise err

# () -> ()
# main program loop

def main():
	if not setup():
		return
	graph_set = False
	# this line is just here for scope, these values shouldn't be used
	recieve, send, graph_process = None, None, None
	keyboard.on_press_key('enter', handle_enter)
	keyboard.on_press_key('backspace', handle_backspace)
	global record
	record = False
	global run
	run = True
	while run:
		if not graph_set and record:
			graph_set = True
			try:
				recieve, send, graph_process = graph_setup()
			except mtp.ProcessError:
				print("Graph failed to initializing", mtp.ProcessError)
				break # !!! At some point this shouldn't exit under these conditions
		elif record:
			try:
				current_reading = collect_data()
				# the run condition needs to be here to prevent storing an incomplete package
				if record and run and graph_set:
					pass_to_processing(current_reading, send, graph_process.is_alive())
			except serial.SerialException as err:
				print("Serial communications break: ", err)
				break
	end_program()

# KeyEvent -> ()
# called whenever enter is pressed, and stops/starts data collection

def handle_enter(_kevent):
	global record
	record = not record
	serial_port.write(int(record).to_bytes(1, byteorder='little'))
	if record:
		print(RECORDING_MESSAGE)
	else:
		print(STOP_MESSAGE)
	return

# KeyEvent -> ()
# called whenever backspace is pressed, shuts down program after current
# reading is done

def handle_backspace(_kevent):
	global run
	run = False
	return

# () -> (listof Char)
# reads from serial port until package is complete, return package
# can raise serial.SerialException

def collect_data():
	current_reading = list()
	character = ' '
	while serial_port.is_open and run:
		if serial_port.in_waiting > 0:
			try:
				character = serial_port.read().decode()
			except serial.SerialException:
				raise serial.SerialException
			current_reading.append(character)
			if character == CLOSE_PACKAGE:
				break
	return current_reading

# (listof Char), Pipe, Boolean -> ()
# passes package along to processing program

def pass_to_processing(package, pipe_send, is_alive):
	de.main(package, pipe_send, is_alive)

# () -> ()
# cleans up and ends program

def end_program():
	ds.cleanup_csv()

if __name__ == '__main__':
	main()

