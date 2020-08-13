import mimetypes
import hashlib
import shutil
import os

from .userio import UserIO
from .helper import cpp_str_esc, cpp_img_esc, get_files_rec, shorten
from jinja2 import Template
from rich.traceback import install as install_traceback
from rich.progress import Progress, BarColumn, TextColumn


def get_template_path():
    install_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(install_dir, "templates")


def get_demo_path():
    install_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(install_dir, "demo")


def delete_folder_safe(userio, output_path):
    # Deletes folder after user confirmation
    # returns False on failure
    if os.path.exists(output_path):
        folder = os.path.abspath(output_path)
        userio.warn("Folder " + folder + " exists!")
        userio.print("Press Enter to delete. Ctrl+C to cancel!")
        try:
            input()
            shutil.rmtree(folder)
            return True
        except KeyboardInterrupt:
            return False
    return True


def get_input_data(userio, input_path):
    # Get list of all files
    files = get_files_rec(input_path)
    userio.print("Processing " + str(len(files)) + " files...", verbose=True)
    userio.quick_table("", ["Input Files"],
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
            if mime is None:
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
                        file_type = 2  # Dynamic content
                    else:
                        # Normal static page
                        file_content = cpp_str_esc(file.read())
            except UnicodeDecodeError:
                # Encode as binary if UTF-8 fails
                with open(os.path.join(input_path, file_name), 'rb') as file:
                    file_content = cpp_img_esc(file)
                    file_type = 1  # Binary content

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

    userio.quick_table("",
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


def generate(userio, input_path, output_path, template_path,
             meta_data):

    # Verbose print generation
    userio.print("\nGenerating with following arguments:", verbose=True)
    userio.quick_table("", ["ARGUMENT", "VALUE"],
                       [["Input path", input_path],
                        ["Output path", output_path],
                        ["Template path", template_path]],
                       verbose=True)

    # Check input
    if not os.path.isdir(input_path):
        userio.error("Invalid input path!")

    # Check output
    if not os.path.isdir(output_path):
        userio.error("Invalid output path!")

    # Check output
    if not os.path.isdir(output_path):
        userio.error("Invalid input path!")

    # Check template
    if not os.path.isdir(template_path):
        userio.error("Invalid template path!")

    # Clear previous output
    if not delete_folder_safe(userio, os.path.join(output_path, "main/")):
        userio.error("Can't continue with existing output folder")

    # Process input
    userio.section("Processing input files...")
    file_data, mime_data = get_input_data(userio, input_path)

    # Pack meta data
    meta_data = {key: cpp_str_esc(value)
                 for key, value in meta_data.items()}

    # Print all data that can be used in jinja2 files processed
    userio.print("\nListing data available to the templates:", verbose=True)
    userio.quick_table("File Data",
                       ["File name", "File hash", "File MIME",
                        "MIME hash", "File type", "File content"],
                       [[file_name, *[shorten(value, 100)
                                      for value in file_data_struct.values()]]
                        for (file_name, file_data_struct) in file_data.items()],
                       verbose=True)

    userio.quick_table("MIME Data",
                       ["MIME", "MIME hash"],
                       mime_data.items(), verbose=True)

    userio.quick_table("Meta Data",
                       ["Key", "Value"],
                       meta_data.items(), verbose=True)

    # Now, find and process Template files
    userio.section("Writing program files...")
    generate_from_template(userio, template_path, output_path,
                           file_data, mime_data, meta_data)
