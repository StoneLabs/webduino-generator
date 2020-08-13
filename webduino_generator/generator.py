import mimetypes
import argparse
import hashlib
import configparser
import shutil
import os

from .__init__ import __version__
from .userio import UserIO
from .helper import cpp_str_esc, cpp_img_esc, get_files_rec, shorten
from jinja2 import Template
from rich.traceback import install as install_traceback
from rich.progress import Progress, BarColumn, TextColumn


def clearOutput(userio, output_path):
    # Deletes folder after user confirmation
    # returns False on failure
    if os.path.exists(output_path):
        folder = os.path.abspath(output_path)
        userio.warn("Output folder " + folder + " exists!")
        userio.print("Press Enter to delete. Ctrl+C to cancel!")
        try:
            input()
            shutil.rmtree(folder)
            return True
        except KeyboardInterrupt:
            return False
    return True

def get_ssid_pass(userio, no_warn):
    # Get SSID and password for wifi connection
    if not no_warn:
        userio.warn("SSID and Password will be saved as plaintext in the output!")
    return userio.getUserPass("Please enter network credentials:", "SSID: ", "Password: ")

def get_input_data(userio, input_path):
    # Get list of all files
    files = get_files_rec(input_path)
    userio.print("Processing " + str(len(files)) + " files...", verbose=True)
    userio.quickTable("",
                    ["Input Files"],
                    [[_file] for _file in files], verbose=True)

    # Data input functions
    def _addFile(container):
        def inner(file_name, file_hash, mime, mime_hash, file_content, file_type):
            entry = {
                "file_hash": file_hash,
                "mime": mime,
                "mime_hash": mime_hash,
                "file_type": file_type,
                "file_content": file_content
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
                with open(os.path.join(input_path, file_name), 'r', encoding="UTF-8") as file:
                    if (file_name.endswith(".cpp")):
                        # Handle dynamic content (cpp files)
                        file_content = file.read().replace("\n", "\n\t")
                        file_type = 2 # Dynamic content
                    else:
                        # Normal static page
                        file_content = cpp_str_esc(file.read())
            except UnicodeDecodeError:
                # Encode as binary if UTF-8 fails
                with open(os.path.join(input_path, file_name), 'rb') as file:
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

    return fileData, mimeData

def generate_from_template(userio, template_path, output_path, 
                           file_data, mime_data, meta_data):
    userio.print("Creating output folder", verbose=True)

    # Prepare output folder
    outputFolder = os.path.join(output_path, "main/")
    try:
        os.mkdir(outputFolder)
    except OSError:
        userio.error("Could not create output directory!")

    # Get list of all template files
    files = get_files_rec(template_path)
    userio.print("Processing " + str(len(files)) + " template files...", verbose=True)

    userio.quickTable("",
                    ["Template Files"],
                    [[_file] for _file in files], verbose=True)

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
            file_name_input = os.path.join(template_path, file_name)
            file_name_output = os.path.join(outputFolder, file_name)

            # Open handles for input and output files
            with open(file_name_input, "r") as file_input, \
                open(file_name_output, "w") as file_output:
                # Apply jinja2 processing and write processed file to output          
                template = Template(file_input.read())
                file_output.write(template.render(fileData=file_data, 
                                                  mimeData=mime_data, 
                                                  metaData=meta_data))

            # Update progress bar
            progress.update(task1, advance=1)

        # All files processed
        progress.tasks[task1].description = "Done"

def get_template_path():
    install_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(install_dir, "templates")

def get_demo_path():
    install_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(install_dir, "demo")

def command_generate(userio, args):

    # Check input
    if not os.path.isdir(args.input):
        userio.error("Invalid input path!")

    # Check output
    if not os.path.isdir(args.output):
        userio.error("Invalid output path!")

    # Check port
    if args.port < 0 or args.port > 65535:
        userio.error("Invalid port!")

    # Check mode
    if args.mode.lower() != "wifinina":
        userio.error("Target mode not supported!\nSupported modes: wifinina")

    # Check output
    if not os.path.isdir(args.output):
        userio.error("Invalid input path!")

    # Check templates folder
    if args.template == "":
        args.template = get_template_path()
        userio.print("Using build in template files at " + args.template, verbose=True)
    if not os.path.isdir(args.template):
        userio.error("Invalid template path!")

    # Clear previous output
    if not clearOutput(userio, os.path.join(args.output, "main/")):
        userio.error("Can't continue with existing output folder")
        exit(1)
    
    args.ssid, args.ssid_pass = get_ssid_pass(userio, args.quiet)

    #
    # Process input
    #
    userio.section("Processing input files...")
    file_data, mime_data = get_input_data(userio, args.input)

    #
    # Pack misc data
    #
    userio.section("Processing misc. data...")
    meta_data = {
        "mode": cpp_str_esc(args.mode),
        "ssid": cpp_str_esc(args.ssid),
        "pass": cpp_str_esc(args.ssid_pass),
        "port": str(args.port)
    }

    # Print all data that can be used in jinja2 files processed
    userio.print("\nListing data available to the templates:", verbose=True)
    userio.quickTable("File Data",
                    ["File name", "File hash", "File MIME", "MIME hash", "File type", "File content"],
                    [[file_name, *[shorten(value, 100) for value in file_data_struct.values()]] 
                        for (file_name,file_data_struct) in file_data.items()]
                    , verbose=True)

    userio.quickTable("MIME Data",
                    ["MIME", "MIME hash"],
                    mime_data.items(), verbose=True)

    userio.quickTable("Meta Data",
                    ["Key", "Value"],
                    meta_data.items(), verbose=True)

    # Now, find and process Template files
    userio.section("Writing program files...")
    generate_from_template(userio, args.template, args.output,
                           file_data, mime_data, meta_data)

def command_version(userio, args):
    userio.print("Current version: " + __version__)

def command_init(userio, project_path, delete_block):
    userio.section("Generating hello world project")

    if not os.path.exists(project_path):
        userio.error("Path " + project_path + " is invalid or does not exist!")

    if len(get_files_rec(project_path)) > 0:
        userio.warn("Target folder (" + os.path.abspath(project_path) + ") is not empty!")
        userio.warn("Data will %sbe deleted by this action!" % ("" if delete_block else "not "))
        userio.print("Press Enter to continue anyway. Ctrl+C to cancel!")
        try:
            input()
        except KeyboardInterrupt:
            return
    
    path_input = os.path.join(project_path, "input")
    path_template = os.path.join(project_path, "template")
    path_template_src = get_template_path()

    path_config = os.path.join(project_path, ".webduino-generator")
    path_config_file = os.path.join(project_path, "project.cfg")

    def delete_file_or_folder(target):
        if os.path.isfile(target):
            os.remove(target)
        else:
            shutil.rmtree(target)

    # Check before we start
    if os.path.exists(path_config):
        if delete_block:
            delete_file_or_folder(path_config)
        else:
            userio.error("Config folder " + path_config + " exists! Is there already a project here?")

    if os.path.exists(path_config_file):
        if delete_block:
            delete_file_or_folder(path_config_file)
        else:
            userio.error("Project file " + path_config_file + " exists! Is there already a project here?")

    userio.print("Creating project files")
    os.mkdir(path_config)
    with open(path_config_file, "w") as config_file:
        config_file.write("todo")

    def copy_tree_if_not_exists(src, target, name):
        if os.path.exists(target) and delete_block:
            delete_file_or_folder(target)
        if os.path.isfile(target):
            userio.error(name + " exists and is file!")
        if os.path.isdir(target):
            userio.warn(name + " exists! Do nothing!")
            return
        shutil.copytree(src, target)

    userio.print("Creating input files")
    copy_tree_if_not_exists(get_demo_path(), path_input, "Input folder")

    userio.print("Creating template files")
    copy_tree_if_not_exists(get_template_path(), path_template, "Template folder")

    userio.section("Project created successfully.")
    userio.print("Use 'webduino-generator build' to build your project.")


def main():
    install_traceback()
    userio = UserIO()

    #
    # Parser input
    #
    parser = argparse.ArgumentParser(prog="webduino-generator",
                                     description="Webduino source builder")


    subparsers = parser.add_subparsers(dest="command")

    parser_generate = subparsers.add_parser("generate", help="Generate Arduino code from input folder without a project")
    parser_generate.add_argument("input", metavar="input", type=str, 
                        help="Input folder")
    parser_generate.add_argument("-t", "--template", metavar="folder", type=str,
                        default="", dest='template',
                        help="location of the template folder (build in is used if no path is supplied)")
    parser_generate.add_argument("-s", "--ssid", metavar="ssid", type=str,
                        default="", dest='ssid',
                        help="SSID of network")
    parser_generate.add_argument("-p", "--port", metavar="port", type=int,
                        default=80, dest='port',
                        help="Port of webserver")
    parser_generate.add_argument("-m", "--mode", metavar="mode", type=str,
                        default="wifinina", dest='mode',
                        help="Connection mode/library to be used")
    parser_generate.add_argument("-q", "--quiet", 
                        action="store_true", dest='quiet',
                        help="Hides password warning")
    parser_generate.add_argument("-o", "--output", metavar="folder", type=str,
                        default=".", dest='output',
                        help="location of the output folder (default: ./output/)")
           
    
    parser_init = subparsers.add_parser("init", help="Create new project in current working directory")
    parser_init.add_argument("target", metavar="target", type=str,
                             default=".", nargs="?",
                             help="Target folder where project will be created")
    parser_init.add_argument("-f", "--force", 
                             action="store_true", dest='force',
                             help="Delete files that block project creation.")


    parser_build = subparsers.add_parser("build", help="Generate Arduino code from current project")
    parser_compile = subparsers.add_parser("compile", help="Compile Arduino code from current project")
    parser_upload = subparsers.add_parser("upload", help="Upload Arduino code from current project")
    parser_open = subparsers.add_parser("open", help="Open generated code in arduino ide")
    parser_version = subparsers.add_parser("version", help="Display current version")

    # Global arguments
    for subparser in subparsers.choices.values():
        group = subparser.add_argument_group("global arguments")
        group.add_argument("-v", "--verbose",
                           action="store_true", dest='verbose',
                           help="Enable verbose output")

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

    # Check command
    if args.command == None:
        userio.error("No command specified!")
    elif args.command == "version":
        command_version(userio, args)
    elif args.command == "init":
        command_init(userio, args.target, args.force)
    elif args.command == "build":
        raise NotImplementedError
    elif args.command == "compile":
        raise NotImplementedError
    elif args.command == "upload":
        raise NotImplementedError
    elif args.command == "open":
        raise NotImplementedError
    elif args.command == "generate":
        command_generate(userio, args)
    else:
        userio.error("Unknown command. This should never happen!")

if __name__ == "__main__":
    main()