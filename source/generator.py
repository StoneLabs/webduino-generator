from output import Section, Text, Error
from helper import cpp_str_esc
from rich.progress import Progress, BarColumn, TextColumn

import configparser
import mimetypes 
import argparse
import hashlib
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
#print(args)

#
# Check arguments
#

# Check input
if not str(args.input).endswith("/"):
    args.input +=  "/"
if not os.path.isdir(args.input):
    Error("Invalid input path!")

# Check config file
if not os.path.exists(args.config_file):
    Error("Config file not found!")

# Check templates folder
if not str(args.template_folder).endswith("/"):
    args.template_folder +=  "/"
if not os.path.isdir(args.template_folder):
    Error("Invalid template path!")

#
# Read config file
#

Section("Reading config files...")

NetworkConfig = configparser.ConfigParser()
NetworkConfig.optionxform = str
NetworkConfig.read(args.config_file)

if NetworkConfig.get("GLOBAL", "CONNECTION") != "WIFI":
    Error("reading config: Unknown connection type.")


Section("Processing input files...")

files = set()
for dir_, _, files_ in os.walk(args.input):
    for file_name in files_:
        rel_dir = os.path.relpath(dir_, args.input)
        rel_file = os.path.join(rel_dir, file_name)

        rel_file = rel_file.replace("\\","/")
        if rel_file.startswith("./"):
            rel_file = rel_file[2:]

        files.add(rel_file)

mimes = {}
commands_add_str = ""
commands_def_str = "\n"
commands_api_str = ""

for filename in files:
    with open(args.input + filename, 'r', encoding="UTF-8") as file:
        mime, encoding = mimetypes.guess_type(filename)
        m_hash = hashlib.sha1(mime.encode("UTF-8")).hexdigest()
        m_hash_s = m_hash[:10]

        hash = hashlib.sha1(filename.encode("UTF-8")).hexdigest()
        hash_s = hash[:10]
        Text("-> " + hash_s + ": " + filename + ", " + mime + " (" + m_hash_s + ")")

        mimes[m_hash_s] = mime

        if (filename.endswith(".cpp")):
            commands_api_str += "namespace _"
            commands_api_str += hash_s
            commands_api_str += " {\n\t"
            commands_api_str += file.read().replace("\n","\n\t")
            commands_api_str += "\n}\n"

            commands_add_str += "webserver.addCommand(\""
            commands_add_str += filename
            commands_add_str += "\", &_"
            commands_add_str += hash_s
            commands_add_str += "::respond);\n\t"
            continue

        commands_add_str += "webserver.addCommand(\""
        commands_add_str += filename
        commands_add_str += "\", &_"
        commands_add_str += hash_s
        commands_add_str += ");\n\t"

        commands_def_str += "static const unsigned char _"
        commands_def_str += hash_s
        commands_def_str += "_s[] PROGMEM = "
        commands_def_str += cpp_str_esc(file.read())
        commands_def_str += ";\n"
        commands_def_str += "inline void _"
        commands_def_str += hash_s
        commands_def_str += " (WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete) { staticResponder(server, type, url_tail, tail_complete, _"
        commands_def_str += hash_s
        commands_def_str += "_s, _"
        commands_def_str += m_hash_s
        commands_def_str += "); }\n"

        if (filename == "index.html"):
                commands_add_str = "webserver.setDefaultCommand(&_" + hash_s + ");" + "\n\n\t" + commands_add_str

for m_hash in mimes:
    commands_def_str = "static const char _" + m_hash + "[] = " + cpp_str_esc(mimes[m_hash]) + ";\n" + commands_def_str

commands_def_str += "\n" + commands_api_str


Section("Writing program files...")
Text("( 0/ 3) main/")
try:
    os.mkdir("./output/main/")
except OSError:
    Error("Could not create output directory!")

Text("( 1/ 3) main.ino")

with open(args.template_folder + "main.wifi.ino", 'r') as file:
    data = file.read()
    for option in NetworkConfig.options("WIFI"):
        data = data.replace("__" + option + "__", NetworkConfig.get("WIFI", option))
    for option in NetworkConfig.options("SERVER"):
        data = data.replace("__" + option + "__", NetworkConfig.get("SERVER", option))

    data = data.replace("__COMMANDS_ADD__", commands_add_str)

    text_file = open("./output/main/" + "main.ino", "w")
    text_file.write(data)
    text_file.close()

Text("( 2/ 3) WebServer.h")

with open(args.template_folder + "WebServer.wifi.h", 'r') as file:
    data = file.read()
    text_file = open("./output/main/" + "WebServer.h", "w")
    text_file.write(data)
    text_file.close()

Text("( 3/ 3) commands.h")

with open(args.template_folder + "commands.h", 'r') as file:
    data = file.read()

    data = data.replace("__COMMANDS_DEF__", commands_def_str)
    
    text_file = open("./output/main/" + "commands.h", "w")
    text_file.write(data)
    text_file.close()