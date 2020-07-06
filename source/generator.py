from output import Section, Text, Error
from rich.progress import Progress, BarColumn, TextColumn

import configparser

Section("Reading config files...")
Text(" Network configuration...")

NetworkConfig = configparser.ConfigParser()
NetworkConfig.optionxform = str
NetworkConfig.read("./config/network.cfg")

fileNameIn = ""
fileNameOut = ""
if NetworkConfig.get("GLOBAL", "CONNECTION") == "WIFI":
    fileNameIn = "main.wifi.txt"
    fileNameOut = "main.ino"
else:
    Error("reading config: Unknown connection type.")

Section("Writing program files...")
Text("( 1/ 1) main.ino")

with open("./templates/" + fileNameIn, 'r') as file:
    data = file.read()
    for option in NetworkConfig.options("WIFI"):
        data = data.replace("__" + option + "__", NetworkConfig.get("WIFI", option))

    text_file = open("./output/" + fileNameOut, "w")
    text_file.write(data)
    text_file.close()