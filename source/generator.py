from userio import Section, Text, Error, GetUserPass, console
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
parser.add_argument("-p", "--port", metavar="port", type=int,
                    default=80, dest='port',
                    help="Port of webserver")
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

# Check port
if args.port < 0 or args.port > 65535:
    Error("Invalid port!")

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
# Process input
#
Section("Processing input files...")

# Template strings for replacement
# The following patterns should be available (file_name, mime and content encoded as needed)
# {file_name} {file_hash} {file_content} {mime_hash} {mime}

template_str_add_index   = "\twebserver.setDefaultCommand(&f_{file_hash});\n\n"
template_str_add_static  = "\twebserver.addCommand(\"{file_name}\", &f_{file_hash});\n"
template_str_add_dynamic = "\twebserver.addCommand(\"{file_name}\", &f_{file_hash}::respond);\n"
template_str_def_mime    = "static const char m_{mime_hash}[] = \"{mime}\";\n"
template_str_def_dynamic = "namespace f_{file_hash} {{\n\t{file_content}\n}}\n\n"
template_str_def_static  = "static const unsigned char f_{file_hash}_s[] PROGMEM = {file_content};\n" + \
                           "inline void f_{file_hash} (WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete)" + \
                           "{{ staticResponder(server, type, url_tail, tail_complete, f_{file_hash}_s, m_{mime_hash}); }}\n"

# Get list of all files
files = set()
for dir_, _, files_ in os.walk(args.input):
    for file_name in files_:
        rel_dir = os.path.relpath(dir_, args.input)
        rel_file = os.path.join(rel_dir, file_name)

        rel_file = rel_file.replace("\\","/")
        if rel_file.startswith("./"):
            rel_file = rel_file[2:]

        files.add(rel_file)

# Strings to build
mimes = {}
commands_add = ""
commands_def_static  = ""
commands_def_dynamic = ""
commands_def_mimes   = ""

print(files)
for file_name in files:
    with open(os.path.join(args.input, file_name), 'r', encoding="UTF-8") as file:
        # Save mime hash and type
        mime, encoding = mimetypes.guess_type(file_name)
        mime_hash = hashlib.sha1(mime.encode("UTF-8")).hexdigest()
        mime_hash = mime_hash[:10]
        mimes[mime_hash] = mime

        # Get file hash
        file_hash = hashlib.sha1(file_name.encode("UTF-8")).hexdigest()
        file_hash = file_hash[:10]
        Text("-> " + file_hash + ": " + file_name + ", " + mime + " (" + mime_hash + ")")

        replacer = {"file_name": file_name, "file_hash": file_hash, "mime_hash": mime_hash}

        if (file_name.endswith(".cpp")):
            replacer["file_content"] = file.read().replace("\n", "\n\t")
            console.print(replacer)
            commands_add += template_str_add_dynamic.format(**replacer)
            commands_def_dynamic += template_str_def_dynamic.format(**replacer)
            continue

        replacer["file_content"] = cpp_str_esc(file.read())
        console.print(replacer)
        commands_add += template_str_add_static.format(**replacer)
        commands_def_static += template_str_def_static.format(**replacer)

        if (file_name == "index.html"):
                commands_add = template_str_add_index.format(**replacer) + commands_add

for m_hash in mimes:
    replacer = {"mime_hash" : m_hash, "mime": mimes[m_hash]}
    commands_def_mimes += template_str_def_mime.format(**replacer)

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
    data = data.replace("__PORT__", str(args.port))

    data = data.replace("__COMMANDS_ADD__", commands_add)

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

    data = data.replace("__COMMANDS_DEF_MIMES__", commands_def_mimes)
    data = data.replace("__COMMANDS_DEF_STATIC__", commands_def_static)
    data = data.replace("__COMMANDS_DEF_DYNAMIC__", commands_def_dynamic)
    
    text_file = open(os.path.join(args.output, "main/", "commands.h"), "w")
    text_file.write(data)
    text_file.close()