"""
  @file convbin_obs_fix.py
  @brief Routines to clean duplicate epochs in rinex observation file created by convbin
 
  @author Michal Zygmunt
 
  @copyright Copyright (c) 2021 ChipCraft Sp. z o.o. All rights reserved.
 
  @license See LICENSE file for license details.
 
  @todo none
  @bug none
 
  $Date: 2021-11-24 14:19:11 +0200 (sr., 24 lis 2021) $
  $Revision: 2059 $
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
                    help="input RINEX file to check for duplicated epochs. " \
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
    output_file_path_name = os.path.join(output_file_path, in_file_name + "_fix.obs")
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
    
#%% Process RINEX obs file in scope of:
#   - drop duplicated observations
#   - removing duplicated epoch identifier
#   - fixing satellite number stored in epoch row

end_of_header = False
epoch_is_set = False

output_lines = []
temp_lines = []
duplicated_lines = 0

epoch_current = ""
epoch_prev = ""

with open(input_file_path_name) as lines:
    for line in lines:
        
        # preserve original header from RINEX file
        if line[0] == '>':
            end_of_header = True
        
        if end_of_header == False:
            out_file.write(line)
        
        # process observables
        if end_of_header == True:
            
            if line[0] == '>':
                if epoch_is_set == False:
                    epoch_current = line
                    epoch_is_set = True
                else:
                    epoch_prev = epoch_current
                    epoch_current = line
            
                # check if consecutive epochs have different time
                # 2:29 means 'yyyy mm dd hh mm ss.sssssss' of epoch date/time id
                if epoch_prev[2:29] != epoch_current[2:29]:
                    
                    # fix satellite counter for this epoch
                    sats = len(temp_lines)
                    
                    if sats > 0:
                    
                        # extract date / time information from prev_epoch
                        tokens = epoch_prev.split()
                        line = ("> %s %s %s %s %s %s %2d %2d                     \n" %
                                (tokens[1], tokens[2], tokens[3], # yyyy mm dd
                                 tokens[4], tokens[5], tokens[6], # hh mm ss.sssssss
                                 int(tokens[7]), sats)) # epoch_flag sats
                        
                        out_file.write(line)
                        
                        for item in range(sats):
                            out_file.write(temp_lines[item])
                        temp_lines = []
                
                else: # epoch_prev[2:29] == epoch_current[2:29] / date and time is equal
                
                    # save row of duplicated epoch
                    duplicated_lines += 1
                    
                    # split epoch into values and get epochs flag
                    tokens_prev = line.split()
                    tokens_current = line.split()
                    epoch_flag_prev = tokens_prev[7]
                    epoch_flag_current = tokens_current[7]
                    
                    # check if flags match and generate warning if they don't
                    if epoch_flag_prev != epoch_flag_current:
                        print("WARNING: flags of duplicated epochs are different!")
                        print(epoch_prev)
                        print(epoch_current)
            
            else: # line[0] != '>'
                
                # check if read line is not already stored in temp_lines
                if line not in temp_lines:
                    # append observations registerred on this epoch
                    # to temporary list
                    temp_lines.append(line)
                else:
                    duplicated_lines += 1
                

# end of file reached; save content of last temp results
out_file.write(epoch_current)
                    
for item in range(0, len(temp_lines)):
    out_file.write(temp_lines[item])
del temp_lines

out_file.close()

#%% statistics informations 

print("Number of duplicated lines removed: " + str(duplicated_lines))

stop = time.time()
delta = stop - start
print("Processing time: %.2f s\n" % delta)
