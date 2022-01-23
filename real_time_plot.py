# Takes reading and plots it in real time
# Has not been tested with real circuit/readings as of yet

# Last Updated: 10/01/2021
# Last Updated by: Justin Lawrence
# Author(s): Justin Lawrence
# Function: plots reading's current over time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import multiprocessing as mtp

MAX_SIZE = 20 # maximum number of datapoints to display at once
INTERVAL = 10 # number of updates per second, should approximately match input
MAX_READING = 2 # the minimum and maximum projected readings
MIN_READING = 0
LEGEND_LOCATION = 'upper right' # location of legend on graph
COLOURS = ['blue', 'red', 'green', 'black'] # colour of line for each cell
LABELS = ["Cell One", "Cell Two", "Cell Three", "Cell Four"] # cell labels in legend
RATE = 10 # refresh rate in milliseconds (every n ms)
PREFIXES = ["C1: ", "C2: ", "C3: ", "C4: "]
PERCISION = 0 # number of decimal places to round temperature to
NUMBER_CELLS = 1 # the number of cells attached to the arduino
DROP_INDEX = 0 # index of the voltage drop in cell reading
TEMPERATURE_INDEX = 2 # index of the temperature in cell reading

# () -> ()
# creates lines and plots that will be updated over time

def initialize_plot():
	global fig
	global ax
	fig, ax = plt.subplots()
	ax.set_ylabel("Voltage Drop (V)")
	ax.set_ylim((MIN_READING, MAX_READING))
	ax.set_xticks([])
	ax.set_title("")
	global yvalues
	global lines
	yvalues = []
	lines = []
	for i in range(0, NUMBER_CELLS):
		yvalues.append(np.zeros(MAX_SIZE))
		line, = ax.plot(yvalues[i], color=COLOURS[i])
		lines.append(line)
	ax.legend(LABELS[0:NUMBER_CELLS], loc=LEGEND_LOCATION)

# Pipe -> ()
# main process loop for rtp

def main(terminal):
	global pipe_opening
	pipe_opening = terminal
	initialize_plot()
	global animation_object
	animation_object = FuncAnimation(fig, update, interval=RATE)
	plt.show()

# Number -> ()
# checks terminal pipe for data, updates if there is any

def update(_i):
	cells = pipe_opening.recv()
	for i in range(0, NUMBER_CELLS):
		update_values(cells[i][DROP_INDEX], i)
		lines[i].set_ydata(yvalues[i])
	title = update_temperatures(get_temperatures(cells))
	ax.set_title(title)

# (listof Reading) -> (listof Float)
# produces list of rounded cell temperatures

def get_temperatures(cells):
	temperatures = []
	for cell in cells:
		temperatures.append(round(cell[TEMPERATURE_INDEX], PERCISION))
	return temperatures

# Float (one of 0, 1, ..., NUMBER_CELLS) -> ()
# updates array of y-values by shifting everything right one

def update_values(current, cell):
	to_change = yvalues[cell]
	for i in range(19, 0, -1):
		to_change[i] = to_change[i-1]
	to_change[0] = current

# (listof Float) -> String
# produce heading with temperatures

def update_temperatures(temperatures):
	title = ""
	for i in range(0, NUMBER_CELLS):
		title += PREFIXES[i] + str(temperatures[i]) + " "
	return title