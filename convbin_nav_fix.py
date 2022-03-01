"""
  @file convbin_nav_fix.py
  @brief Routines to fix ephemeris values of RINEX navigation file created by convbin
 
  @author Michal Zygmunt
 
  @copyright Copyright (c) 2021 ChipCraft Sp. z o.o. All rights reserved.
 
  @license See LICENSE file for license details.
 
  @todo none
  @bug none
 
  $Date: 2021-11-24 14:18:22 +0200 (sr., 14 lis 2021) $
  $Revision: 2058 $
  $LastChangedBy: mzygmunt $
"""

import argparse
import os.path
import sys
import time

start = time.time()

#%% Read input arguments

parser = argparse.ArgumentParser()
parser.add_argument("input_file", type=str,
                    help="input RINEX nav file to check for duplicated epochs. " \
                        "File path can be absolute or relative.")
parser.add_argument("-o", "--output_file", type=str,
                    help="output RINEX file to save. " \
                        "File path can be absolute or relative. " \
                        "If not specified, output file is written to input directory " \
                        "with name <input_file>_fix.<input_file_extension>")
args = parser.parse_args()

input_file_path_name = args.input_file
output_file_path_name = args.output_file

#%% Sanity check for input parameters    

# check validity of input file
in_file_path = ""
in_file_name = ""
in_file_ext = ""

if input_file_path_name != None:
    
    if os.path.exists(input_file_path_name) == True:
        
        # return filename.ext
        file_name_ext = os.path.basename(input_file_path_name)
        
        if file_name_ext == '':
            print("Directory specified instead of file!")
            print("Exiting!")
            sys.exit()
            
        if os.access(input_file_path_name, os.R_OK) == False:
            print("User don't have access rights to read specified file!")
            print("Exiting!")
            sys.exit()
            
        
        #split filename.ext into filename and ext
        in_file_name, in_file_ext = os.path.splitext(file_name_ext)
        
        # get input file directory path by cutting file name from path string 
        in_file_path = input_file_path_name[0:-len(file_name_ext)]
        # normalize path to remove slash from path
        in_file_path = os.path.normpath(in_file_path)
        
        
    elif input_file_path_name == "":
         print("Missing input file!")
         print("Exiting!")
         sys.exit()
    
    else:
        print("Can't locate file: " + input_file_path_name)
        print("Exiting!")
        sys.exit()

# check validity of output file
output_file_path = ""
out_file_name = ""

if output_file_path_name == None:
    output_file_path = in_file_path
    output_file_path_name = os.path.join(output_file_path, in_file_name + "_fix.nav")
else:
    file_name_ext = os.path.basename(output_file_path_name)
    
    #split filename.ext into filename and ext
    out_file_name, out_file_ext = os.path.splitext(file_name_ext)
    
    # get output file directory path by cutting file name from path string 
    output_file_path = output_file_path_name[0:-len(file_name_ext)]
    # normalize path to remove slash from path
    output_file_path = os.path.normpath(output_file_path)

if os.path.exists(output_file_path) == False:
    # try creating output directory
    try:
        os.makedirs(output_file_path)
    except IOError:
        print(sys.exc_type)
        sys.exit()
    
out_file = open(output_file_path_name, "w")
    
#%% Process RINEX nav file in scope of:
#   - change 'D' to 'E' exponential identifier
#   - add leading number (before delimiter) and update exponential power


# convert string representing exponential number to different format
def exp_as_string(text):
    text = text.strip().replace('D','e')
    num = float(text)
    line_out = "{:19.12E}".format(num)
    return line_out


# update content of one line, formatted with exp_as_string output
def update_line(line, val_start, val_start_idx, val_updated):
    
    line_out = ""
    
    # check line length to determine number of possible values
    line_length = len(line)
    
    # iterate over starting char of val_start list
    for item in range(val_start_idx, len(val_start)):
        
        if(line_length -1 > val_start[item]):
            
            # extract string containing just one value
            val_string = line[val_start[item]:val_start[item] + val_length]
                            
            # process string value and append to new output
            val_string_updated = exp_as_string(val_string)
            line_out += val_string_updated
                            
            if val_string.strip() != val_string_updated.strip():
                val_updated += 1    
            
    return line_out, val_updated


# start column of ephemeris data in row and its length
val_start = [4, 23, 42, 61]
val_length = 19

# header ending text
end_of_header = False
header_end = "END OF HEADER"

# counter of updated values
val_updated = 0

with open(input_file_path_name) as lines:
    for line in lines:
        
        # preserve original header from RINEX file        
        if end_of_header == False:
            out_file.write(line)
        
        if header_end in line:
            end_of_header = True
            continue        
        
        # process observables
        if end_of_header == True:
            
            # check if line contains GNSS nav data id
            if line[0] != ' ':
                
                # get content of sat id and date of ephemeris                
                line_new = line[0:23]
                
                # update satellite clock parameters (bias, drift, drift_rate)
                # 1 to skip initial value from this row at column 4, which
                # is already stored in line_new variable
                line_out, val_updated = update_line(line, val_start, 1, val_updated)
                line_new += line_out
                
                out_file.write(line_new)
                
            else:
                # gather ephemeris data for sat system and convert
                # to exponential notation all values in that line
                
                # set empty spaces on beginning of RINEX nav data row
                line_new = "    "
                
                # find how many values are in line, based on line length
                # 0 to scan for all possible values in this line
                line_out, val_updated = update_line(line, val_start, 0, val_updated)
                line_new += line_out
                
                out_file.write(line_new)
                
            # create new line symbol after each write
            out_file.write("\n")

out_file.close()

#%% statistics informations 

print("Number of updated values: " + str(val_updated))

stop = time.time()
delta = stop - start
print("Processing time: %.2f s\n" % delta)
