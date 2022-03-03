"""
  @file rtcm2rinex.py
  @brief Routines to automate converting RTCM messages to RINEX obs and nav files
 
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
import datetime
import os
import platform
import subprocess
import sys
import time

#%% get platform and python version

op_sys = platform.system()
if op_sys != "Windows" and op_sys != "Linux":
    print('CONVBIN was not compiled for ' + op_sys + ' platform!')
    print('Exiting!')
    sys.exit()

python_app = ""
if sys.version_info[0] == 2:
    if op_sys == "Windows":
        python_app = "python"
    if op_sys == "Linux":
        python_app = "python2"
        
elif sys.version_info[0] == 3:
        python_app = "python3"

else:
    print("Unrecognized version of Python detected!")
    print("Exiting!")
    sys.exit()

#%% Read input arguments

parser = argparse.ArgumentParser()
parser.add_argument("date", type=str,
                    help="calendar date of beginning of RTCM messages as <YYYY/MM/DD>. " \
                        "RTCM messages doesn't contain gnss week information. " \
                        "Almost any date can be used, but only correct date ensures " \
                        "real-life values in RINEX file.")
parser.add_argument("./input_file", type=str,
                    help="RTCM binary <input_file> to process. " \
                        "File path can be aboslute or relative.")
parser.add_argument("-d", "--dest", type=str,
                    help="destination <directory> to save RINEX files. " \
                        "Directory path can be absolute or relative.")
args = parser.parse_args()

in_time = args.date
in_file_path_name = args.input_file
out_dir_path = args.dest
    
#%% Sanity check for input parameters

# check if date string is valid date object
is_valid_date = True
try:
    year, month, day = in_time.split('/')
    datetime.datetime(int(year), int(month), int(day))
except ValueError:
    is_valid_date = False

if is_valid_date == False:
    print("Input date is invalid!")
    print("Exiting!")
    sys.exit()

# check validity of input file
in_file_path = ""
in_file_name = ""
in_file_ext = ""

if os.path.exists(in_file_path_name) == True:
    
    # return filename.ext
    file_name_ext = os.path.basename(in_file_path_name)
    
    if file_name_ext == '':
        print("Directory specified instead of file!")
        print("Exiting!")
        sys.exit()
    
    if os.access(in_file_path_name, os.R_OK) == False:
        print("User don't have access rights to read specified file!")
        print("Exiting!")
        sys.exit()
    
    #split filename.ext into filename and ext
    in_file_name, in_file_ext = os.path.splitext(file_name_ext)
    
    # get input file directory path by cutting file name from path string 
    in_file_path = in_file_path_name[0:-len(file_name_ext)]
    # normalize path to remove slash from path
    in_file_path = os.path.normpath(in_file_path)
    
elif in_file_name == "":
     print("Missing input file!")
     print("Exiting!")
     sys.exit()

else:
    print("Can't locate file: " + in_file_path_name)
    print("Exiting!")
    sys.exit()

# check output directory
if out_dir_path == None:
    out_dir_path = in_file_path

out_dir_path = os.path.normpath(out_dir_path)

if os.path.exists(out_dir_path) == False:
    # try creating output directory
    try:
        os.makedirs(out_dir_path)
    except IOError:
        print(sys.exc_type)
        sys.exit()

#%% Convert RTCM to RINEX by 'convbin'

start = time.time()

print("[1/4]: Converting RTCM to RINEX using 'convbin'...")

arg_time = '-tr ' + in_time + ' 00:00:00'
arg_format = '-r rtcm3'
arg_out_path = '-d ' + out_dir_path
arg_file = in_file_path_name

convbin_command = ''
output = 0

if op_sys == "Windows":
    arg_app = 'convbin.exe'
    
if op_sys == "Linux":
    arg_app = '#!./convbin'

convbin_command = ' '.join([arg_app, arg_time, arg_format, arg_out_path, arg_file])
output = subprocess.call(convbin_command, shell = True)

if output != 0:
    print("Convbin returned invalid output!")
    sys.exit()

stop = time.time()
delta = stop - start
print("Processing time: %.2f s\n" % delta)

#%% Fix content of RINEX nav file by re-formatting ephemeris data with 'convbin_nav_fix.py'

print("[2/4]: Fixing content of RINEX nav file by re-formatting ephemeris data...")

# create input and output files paths/names
in_rn_name = in_file_name + '.nav'
out_rn_name = in_file_name + '_fix.nav'

in_rn_path = os.path.join(out_dir_path, in_rn_name)
out_rn_path = os.path.join(out_dir_path, out_rn_name)

if not os.path.exists(in_rn_path):
    print("Can't locate file: " + in_rn_path)
    print("Exiting!")
    sys.exit()

arg_script = 'convbin_nav_fix.py ' + in_rn_path + ' -o ' + out_rn_path
fix_command = ' '.join([python_app, arg_script])
output = subprocess.call(fix_command, shell = True)
 
#%% Fix content of RINEX obs file by removing duplicated epochs by 'convbin_obs_fix.py'

print("[3/4]: Fixing content of RINEX obs file by removing duplicated entries...")

# create input and output files paths/names
in_ro_name = in_file_name + '.obs'
out_ro_name = in_file_name + '_fix.obs'

in_ro_path = os.path.join(out_dir_path, in_ro_name)
out_ro_path = os.path.join(out_dir_path, out_ro_name)

if not os.path.exists(in_ro_path):
    print("Can't locate file: " + in_ro_path)
    print("Exiting!")
    sys.exit()

arg_script = 'convbin_obs_fix.py ' + in_ro_path + ' -o ' + out_ro_path
fix_command = ' '.join([python_app, arg_script])
output = subprocess.call(fix_command, shell = True)

#%% Process temporary output files

print("[4/4] Finishing files operations...")

# replace original obs output from 'convbin' with fixed obs file
file_to_change = os.path.join(out_dir_path, in_file_name)

# nav files
if os.path.exists(file_to_change + '.nav') == True:
    os.remove(file_to_change + '.nav')
    #print("File deleted: " + file_to_change + '.nav')

if os.path.exists(file_to_change + '_fix.nav') == True:
    os.rename(file_to_change + '_fix.nav', file_to_change + '.nav')
    #print("File renamed: " + file_to_change + '_fix.nav ->', file_to_change + '.nav')

# obs files
if os.path.exists(file_to_change + '.obs') == True:
    os.remove(file_to_change + '.obs')
    #print("File deleted: " + file_to_change + '.obs')

if os.path.exists(file_to_change + '_fix.obs') == True:
    os.rename(file_to_change + '_fix.obs', file_to_change + '.obs')
    #print("File renamed: " + file_to_change + '_fix.obs ->', file_to_change + '.obs')

