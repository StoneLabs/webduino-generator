import mimetypes 
import argparse
import hashlib
import shutil
import os

from userio import UserIO
from helper import cpp_str_esc, cpp_img_esc, get_files_rec
from jinja2 import Template
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

# Get list of all files
files = get_files_rec(args.input)
userio.print("Processing " + str(len(files)) + " files...", verbose=True)

# Data input functions
def _addFile(container):
    def inner(file_name, file_hash, mime, mime_hash, file_content, file_type):
        entry = {
            "file_hash": file_hash,
            "mime": mime,
            "mime_hash": mime_hash,
            "file_content": file_content,
            "file_type": file_type
        }
        container[file_name] = entry
        return container

    return inner

def _addMime(container):
    def inner(mime, mime_hash):
        container[mime] = mime_hash
        return container

    return inner

# Structure to hold the read information
fileData = {}
addFile = _addFile(fileData)

mimeData = {}
addMime = _addMime(mimeData)

# Process files
progress_current = TextColumn("Initializing...")
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

        # Get file hash
        file_hash = hashlib.sha1(file_name.encode("UTF-8")).hexdigest()
        file_hash = file_hash[:10]

        # Variable to hold file content
        file_content = ""
        file_type = 0

        try:
            # Try to handle file non-binary UTF-8 file.
            with open(os.path.join(args.input, file_name), 'r', encoding="UTF-8") as file:
                if (file_name.endswith(".cpp")):
                    # Handle dynamic content (cpp files)
                    file_content = file.read().replace("\n", "\n\t")
                    file_type = 2 # Dynamic content
                else:
                    # Normal static page
                    file_content = cpp_str_esc(file.read())
        except UnicodeDecodeError:
            # Encode as binary if UTF-8 fails
            with open(os.path.join(args.input, file_name), 'rb') as file:
                file_content = cpp_img_esc(file)
                file_type = 1 # Binary content

        # Save file for processing after all files were read
        addFile(cpp_str_esc(file_name), 
                file_hash, 
                cpp_str_esc(mime), 
                mime_hash, 
                file_content, 
                file_type)

        addMime(cpp_str_esc(mime),
                mime_hash)

        # Update progress bar
        progress.update(task1, advance=1)

    # All files processed
    progress.tasks[task1].description = "Done"

# Print table of all files processed (TODO rewrite)
#userio.print("Listing processed files:", verbose=True)
#userio.quickTable("",
#                  ["File name", "File hash", "File MIME", "MIME hash"],
#                  files_verbose, verbose=True)

userio.print("Preparing misc. data")

metaData = {
    "ssid": cpp_str_esc(args.ssid),
    "pass": cpp_str_esc(args.ssid_pass),
    "port": str(args.port)
}

userio.print(fileData, verbose=True)
userio.print(mimeData, verbose=True)
userio.print(metaData, verbose=True)

userio.section("Writing program files...")
userio.print("Creating output folder")

outputFolder = os.path.join(args.output, "main/")
try:
    os.mkdir(outputFolder)
except OSError:
    userio.error("Could not create output directory!")

userio.print("Processing templates")

# Get list of all template files
files = get_files_rec(args.template)
userio.print("Processing " + str(len(files)) + " template files...", verbose=True)

# Process each file
progress_current = TextColumn("Initializing...")
with Progress(BarColumn(),
              "[progress.percentage]{task.percentage:>3.1f}%",
              "[progress.description]{task.description}") as progress:
    task1 = progress.add_task("Converting", total=len(files), start=True)

    for file_name in files:
        # Update progress bar
        progress.tasks[task1].description = file_name

        # Get input and output path
        file_name_input = os.path.join(args.template, file_name)
        file_name_output = os.path.join(outputFolder, file_name)

        # Open handles for input and output files
        with open(file_name_input, "r") as file_input, \
             open(file_name_output, "w") as file_output:
            # Apply jinja2 processing and write processed file to output          
            template = Template(file_input.read())
            file_output.write(template.render(fileData=fileData, 
                                              mimeData=mimeData, 
                                              metaData=metaData))

        # Update progress bar
        progress.update(task1, advance=1)

    # All files processed
    progress.tasks[task1].description = "Done"