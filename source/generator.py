from userio import Section, Text, Error, GetUserPass
from helper import cpp_str_esc
from rich.progress import Progress, BarColumn, TextColumn

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
parser.add_argument("-t", "--template", metavar="folder", type=str,
                    default="./templates/", dest='template',
                    help="location of the template folder (default: ./templates/)")
parser.add_argument("-s", "--ssid", metavar="ssid", type=str,
                    default="", dest='ssid',
                    help="SSID of network")
parser.add_argument("-o", "--output", metavar="folder", type=str,
                    default="./output/", dest='output',
                    help="location of the output folder (default: ./output/)")

#
# Check arguments
#
args = parser.parse_args()

# Check input
if not os.path.isdir(args.input):
    Error("Invalid input path!")

# Check output
if not os.path.isdir(args.output):
    Error("Invalid input path!")

# Check templates folder
if not os.path.isdir(args.template):
    Error("Invalid template path!")

Text("Please enter network credentials:")
args.ssid, args.ssid_pass = GetUserPass("SSID: ", "Password: ")

print(args)

#
# Read config file
#
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

print(files)
for filename in files:
    with open(os.path.join(args.input, filename), 'r', encoding="UTF-8") as file:
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
    os.mkdir(os.path.join(args.output, "main/"))
except OSError:
    Error("Could not create output directory!")

Text("( 1/ 3) main.ino")

with open(os.path.join(args.template, "main.wifi.ino"), 'r') as file:
    data = file.read()
    data = data.replace("__SSID__", cpp_str_esc(args.ssid))
    data = data.replace("__PASS__", cpp_str_esc(args.ssid_pass))

    data = data.replace("__COMMANDS_ADD__", commands_add_str)

    text_file = open(os.path.join(args.output, "main/", "main.ino"), "w")
    text_file.write(data)
    text_file.close()

Text("( 2/ 3) WebServer.h")

with open(os.path.join(args.template, "WebServer.wifi.h"), 'r') as file:
    data = file.read()
    text_file = open(os.path.join(args.output, "main/", "WebServer.h"), "w")
    text_file.write(data)
    text_file.close()

Text("( 3/ 3) commands.h")

with open(os.path.join(args.template + "commands.h"), 'r') as file:
    data = file.read()

    data = data.replace("__COMMANDS_DEF__", commands_def_str)
    
    text_file = open(os.path.join(args.output, "main/", "commands.h"), "w")
    text_file.write(data)
    text_file.close()