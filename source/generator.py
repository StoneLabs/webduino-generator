from output import Section, Text, Error
from rich.progress import Progress, BarColumn, TextColumn

import configparser
import argparse
import os

#
# Parser input
#

parser = argparse.ArgumentParser(description="Webduino source builder")

parser.add_argument("input", metavar="input", type=str, 
                    help="Input folder")
parser.add_argument("-c", "--config", metavar="file", type=str,
                    default="./config.cfg", dest='config_file',
                    help="location of the config file (default: ./config.cfg)")
parser.add_argument("-t", "--template", metavar="folder", type=str,
                    default="./templates/", dest='template_folder',
                    help="location of the template folder (default: ./templates/)")

args = parser.parse_args()
print(args)

#
# Check arguments
#

# Check input
if not os.path.isdir(args.input):
    Error("Invalid input path!")

# Check config file
if not os.path.exists(args.config_file):
    Error("Config file not found!")

# Check templates folder
if not os.path.isdir(args.template_folder):
    Error("Invalid template path!")

#
# Read config file
#

Section("Reading config files...")
Text(" Network configuration...")

NetworkConfig = configparser.ConfigParser()
NetworkConfig.optionxform = str
NetworkConfig.read(args.config_file)

fileNameIn = ""
fileNameOut = ""
if NetworkConfig.get("GLOBAL", "CONNECTION") == "WIFI":
    fileNameIn = "main.wifi.txt"
    fileNameOut = "main.ino"
else:
    Error("reading config: Unknown connection type.")

Section("Writing program files...")
Text("( 1/ 1) main.ino")

with open(args.template_folder + fileNameIn, 'r') as file:
    data = file.read()
    for option in NetworkConfig.options("WIFI"):
        data = data.replace("__" + option + "__", NetworkConfig.get("WIFI", option))

    text_file = open("./output/" + fileNameOut, "w")
    text_file.write(data)
    text_file.close()