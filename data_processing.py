# Takes data written to .csv file and translates it to units deg/s, g,
# C, mV

# Last Updated: 27/06/2021
# Last Updated by: Justin Lawrence
# Author(s): Justin Lawrence
# Function: converts data to more natural units

import csv

VSIZE = 1023 # maximum voltage reading
SHORT = 32768 # maximum value that can be stored in a short

input_filename = input("Please input the current file name: ") # get filenames
output_filename = input("Please input the output file name: ")
gyro_range = int(input("Please input the gyroscope range (deg/s): ")) # get sensor ranges
accel_range = int(input("Please input the accelerometer range (g): "))
volt_range = int(input("Please input the AREF voltage (mV): "))
zero = input("Do you want to zero time (y/n): ")

with open(input_filename, 'r', newline='') as input_file:
    with open(output_filename, 'a', newline='') as output_file:
        reader = csv.reader(input_file) # setup reader/writer
        writer = csv.writer(output_file)
        first = True # first row
        for row in reader: # iterate through rows

            if first: # get initial time
                start = int(row[0])
                first = False

            out_row = [] # make output row
            for i in range(len(row)): # go through items in row
                if i == 0: # deal with time
                    if zero == 'y':
                        reading = int(row[i]) - start
                    else:
                        reading = int(row[i])
                elif i >= 1 and i <= 3: # deal with accelerometer
                    reading = int(row[i])/SHORT*accel_range
                elif i >= 4 and i <= 6: # deal with gyroscope
                    reading = int(row[i])/SHORT*gyro_range
                elif i == 7 or i == 9 or i == 11 or i == 13: # deal with voltages
                    reading = int(row[i])/VSIZE*volt_range
                elif i == 8 or i == 10 or i == 12 or i == 14: # deal with temperatures
                    reading = float(row[i])
                out_row.append(reading)
            writer.writerow(out_row) # write output row
