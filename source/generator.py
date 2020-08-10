import mimetypes 
import argparse
import hashlib
import shutil
import os

from userio import UserIO
from helper import cpp_str_esc, cpp_img_esc
from rich.table import Table
from rich.traceback import install
from rich.progress import Progress, BarColumn, TextColumn
install()

userio = UserIO()

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
parser.add_argument("-v", "--verbose", 
                    action="store_true", dest='verbose',
                    help="Enable verbose output")
parser.add_argument("-q", "--quiet", 
                    action="store_true", dest='quiet',
                    help="Hides password warning")
parser.add_argument("-o", "--output", metavar="folder", type=str,
                    default="./output/", dest='output',
                    help="location of the output folder (default: ./output/)")

#
# Check arguments
#
args = parser.parse_args()
userio.verbose = args.verbose

userio.print("[bold]Stone Labs. Webduino Gernerator\n")

userio.print("Dumping arguments", verbose=True)
userio.quickTable("", ["Argument", "Value"],
                  [[arg, getattr(args, arg)] for arg in vars(args)],
                  verbose=True)

# Check input
if not os.path.isdir(args.input):
    userio.error("Invalid input path!")

# Check output
if not os.path.isdir(args.output):
    userio.error("Invalid output path!")
if os.path.exists(os.path.join(args.output, "main/")):
    folder = os.path.abspath(os.path.join(args.output, "main/"))
    userio.warn("Output folder " + folder + " exists!")
    userio.print("Press Enter to delete. Ctrl+C to cancel!")
    try:
        input()
        shutil.rmtree(folder)
    except KeyboardInterrupt:
        exit(1)

# Check port
if args.port < 0 or args.port > 65535:
    userio.error("Invalid port!")

# Check output
if not os.path.isdir(args.output):
    userio.error("Invalid input path!")

# Check templates folder
if not os.path.isdir(args.template):
    userio.error("Invalid template path!")

if not args.quiet:
    userio.warn("SSID and Password will be saved as plaintext in the output!")
args.ssid, args.ssid_pass = userio.getUserPass("Please enter network credentials:", "SSID: ", "Password: ")


#
# Process input
#
userio.section("Processing input files...")

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
template_str_def_staticb = "static const unsigned char f_{file_hash}_s[] PROGMEM = {file_content};\n" + \
                           "inline void f_{file_hash} (WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete)" + \
                           "{{ staticResponder(server, type, url_tail, tail_complete, f_{file_hash}_s, sizeof(f_{file_hash}_s), m_{mime_hash}); }}\n"

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

userio.print("Processing " + str(len(files)) + " files...", verbose=True)

# Strings to build
mimes = {}
commands_add = ""
commands_def_static = ""
commands_def_dynamic = ""
commands_def_mimes = ""

files_verbose = []
progress_current = TextColumn("Test")
with Progress(BarColumn(),
              "[progress.percentage]{task.percentage:>3.1f}%",
              "[progress.description]{task.description}") as progress:
    task1 = progress.add_task("Converting", total=len(files), start=True)

    for file_name in files:
        # Update progress bar
        progress.tasks[task1].description = file_name

        # Save mime hash and type
        mime, encoding = mimetypes.guess_type(file_name)

        # https://stackoverflow.com/questions/1176022/unknown-file-type-mime
        # Not generating a Content-Type header entry would be the best solution
        # but is not feasible with the current system
        if mime == None:
            mime = "application/octet-stream"

        mime_hash = hashlib.sha1(mime.encode("UTF-8")).hexdigest()
        mime_hash = mime_hash[:10]
        mimes[mime_hash] = mime

        # Get file hash
        file_hash = hashlib.sha1(file_name.encode("UTF-8")).hexdigest()
        file_hash = file_hash[:10]

        # Save file for verbose table after processing all files
        files_verbose += [[file_name, file_hash, mime, mime_hash]]

        # Create string replace dict
        replacer = {"file_name": file_name, "file_hash": file_hash, "mime_hash": mime_hash}

        # Set default action for index.html
        if (file_name == "index.html"):
                commands_add = template_str_add_index.format(**replacer) + commands_add

        try:
            # Try to handle file non-binary UTF-8 file.
            with open(os.path.join(args.input, file_name), 'r', encoding="UTF-8") as file:
                if (file_name.endswith(".cpp")):
                    # Handle dynamic content (cpp files)
                    replacer["file_content"] = file.read().replace("\n", "\n\t")
                    commands_add += template_str_add_dynamic.format(**replacer)
                    commands_def_dynamic += template_str_def_dynamic.format(**replacer)
                else:
                    # Normal static page
                    replacer["file_content"] = cpp_str_esc(file.read())
                    commands_add += template_str_add_static.format(**replacer)
                    commands_def_static += template_str_def_static.format(**replacer)
        except UnicodeDecodeError:
            # Encode as binary if UTF-8 failes
            with open(os.path.join(args.input, file_name), 'rb') as file:
                replacer["file_content"] = cpp_img_esc(file)
                commands_add += template_str_add_static.format(**replacer)
                commands_def_static += template_str_def_staticb.format(**replacer)

        # Update progress bar
        progress.update(task1, advance=1)

    # All files processed
    progress.tasks[task1].description = "Done"

# Print table of all files processed
userio.print("Listing processed files:", verbose=True)
userio.quickTable("",
                  ["File name", "File hash", "File MIME", "MIME hash"],
                  files_verbose, verbose=True)

userio.print("Processing " + str(len(mimes)) + " mimes.", verbose=True)
for m_hash in mimes:
    replacer = {"mime_hash" : m_hash, "mime": mimes[m_hash]}
    commands_def_mimes += template_str_def_mime.format(**replacer)

userio.section("Writing program files...")
userio.print("( 0/ 3) main/")
try:
    os.mkdir(os.path.join(args.output, "main/"))
except OSError:
    userio.error("Could not create output directory!")

userio.print("( 1/ 3) main.ino")

with open(os.path.join(args.template, "main.wifi.ino"), 'r') as file:
    data = file.read()
    data = data.replace("__SSID__", cpp_str_esc(args.ssid))
    data = data.replace("__PASS__", cpp_str_esc(args.ssid_pass))
    data = data.replace("__PORT__", str(args.port))

    data = data.replace("__COMMANDS_ADD__", commands_add)

    text_file = open(os.path.join(args.output, "main/", "main.ino"), "w")
    text_file.write(data)
    text_file.close()

userio.print("( 2/ 3) WebServer.h")

with open(os.path.join(args.template, "WebServer.wifi.h"), 'r') as file:
    data = file.read()
    text_file = open(os.path.join(args.output, "main/", "WebServer.h"), "w")
    text_file.write(data)
    text_file.close()

userio.print("( 3/ 3) commands.h")

with open(os.path.join(args.template + "commands.h"), 'r') as file:
    data = file.read()

    data = data.replace("__COMMANDS_DEF_MIMES__", commands_def_mimes)
    data = data.replace("__COMMANDS_DEF_STATIC__", commands_def_static)
    data = data.replace("__COMMANDS_DEF_DYNAMIC__", commands_def_dynamic)
    
    text_file = open(os.path.join(args.output, "main/", "commands.h"), "w")
    text_file.write(data)
    text_file.close()