import configparser
import shutil
import io
import os

from .helper import get_files_rec
from .generator import get_template_path, get_demo_path, generate
from .arduinocli import sketch_compile, sketch_upload, get_board, get_board_connected
from .userio import get_ssid_pass


def project_get_configfile(project_path):
    return os.path.join(project_path, "project.wgen")


def project_check(target):
    project_file = project_get_configfile(target)
    return os.path.exists(project_file) and os.path.isfile(project_file)


def project_config_make(input_path, template_path, output_path,
                        mode, ssid, port) -> str:
    # Make new config file with default content
    config = configparser.ConfigParser()
    config["PROJECT"] = \
        {
            "input_path": input_path,
            "template_path": template_path,
            "output_path": output_path,
        }
    config["METADATA"] = \
        {
            "mode": mode,
            "ssid": ssid,
            "port": port,
        }

    # Write to buffer and return content
    with io.StringIO() as buffer:
        config.write(buffer)
        buffer.seek(0)
        return buffer.read()


def project_config_readproject(userio, config_path):
    config = configparser.ConfigParser()
    config.read(project_get_configfile(config_path))

    if "PROJECT" not in config.sections() or \
       "input_path" not in config["PROJECT"] or \
       "output_path" not in config["PROJECT"] or \
       "template_path" not in config["PROJECT"]:
        userio.error("Invalid project file!")

    input_path = os.path.join(config_path, config["PROJECT"]["input_path"])
    output_path = os.path.join(config_path, config["PROJECT"]["output_path"])
    template_path = os.path.join(config_path, config["PROJECT"]["template_path"])

    return input_path, output_path, template_path


def project_config_readmeta(userio, config_path):
    config = configparser.ConfigParser()
    config.read(project_get_configfile(config_path))

    if "METADATA" not in config.sections():
        userio.error("Invalid project file!")

    return config["METADATA"]


def project_config_readfqbn(userio, config_path):
    config = configparser.ConfigParser()
    config.read(project_get_configfile(config_path))

    if "TARGET" not in config.sections():
        return None

    if "FQBN" not in config["TARGET"]:
        return None

    return config["TARGET"]["FQBN"]


def project_get_sketch(userio, project_path):
    '''Returns location of arduino output sketch. (main.ino)
       Returns None if project was not build yet.'''

    # Check project
    if not project_check(project_path):
        userio.error("Target project not found!")

    # Read project data
    input_path, output_path, template_path = project_config_readproject(userio, project_path)

    # Check if project has been build yet
    sketch_path = os.path.join(output_path, "main", "main.ino")
    if not os.path.exists(sketch_path) or not os.path.isfile(sketch_path):
        return None

    return sketch_path


def project_make_new(userio, project_path, delete_block, mode, ssid, port):
    # Check port
    if port < 0 or port > 65535:
        userio.error("Invalid port!")

    # Check mode
    if mode.lower() != "wifinina":
        userio.error("Target mode not supported!\nSupported modes: wifinina")

    # Check ssid
    if ssid == "":
        ssid = userio.get_user("Please enter network credentials:", "SSID: ")

    # Check if target exists
    if not os.path.exists(project_path):
        userio.error("Path " + project_path + " is invalid or does not exist!")

    userio.section("Generating 'hello world' project")

    # Check if target is empty
    if len(get_files_rec(project_path)) > 0:
        userio.warn("Target folder (%s) is not empty!"
                    % os.path.abspath(project_path))

        userio.warn("Data will %sbe deleted by this action!"
                    % ("" if delete_block else "not "))

        userio.print("Press Enter to continue anyway. Ctrl+C to cancel!")
        try:
            input()
        except KeyboardInterrupt:
            return

    # Get paths to target files/folders beforehand
    path_input = os.path.join(project_path, "input")
    path_output = os.path.join(project_path, "output")
    path_template = os.path.join(project_path, "template")

    path_input_src = get_demo_path()
    path_template_src = get_template_path()

    path_config = os.path.join(project_path, ".wgen")
    path_config_file = project_get_configfile(project_path)

    # Helper function to delete file or folder
    def delete_file_or_folder(target):
        if os.path.isfile(target):
            os.remove(target)
        else:
            shutil.rmtree(target)

    def error_or_delete(target, name):
        if os.path.exists(target):
            if delete_block:
                delete_file_or_folder(target)
            else:
                userio.error(name + " exists! (" + target + ")")

    # Check target files before we start
    # as not to leave a half initialized project
    error_or_delete(path_config, "Config folder")
    error_or_delete(path_config_file, "Config file")
    error_or_delete(path_input, "Input folder")
    error_or_delete(path_template, "Template folder")
    error_or_delete(path_output, "Output folder")

    # Eventually, create project files
    userio.print("Creating project files")

    # Project config folder
    os.mkdir(path_config)

    # Project config file
    with open(path_config_file, "w") as config_file:
        config_file.write(project_config_make(path_input, path_template,
                                              path_output, mode, ssid, port))

    # Project output folder
    userio.print("Creating output folder", verbose=True)
    os.mkdir(path_output)

    # Project output folder
    userio.print("Creating input files", verbose=True)
    shutil.copytree(path_input_src, path_input)

    userio.print("Creating template files", verbose=True)
    shutil.copytree(path_template_src, path_template)

    userio.section("Project created successfully.")
    userio.print("Use 'webduino-generator build' to build your project.")


def project_generate(userio, target, quiet):
    # Check project
    if not project_check(target):
        userio.error("Target project not found!")

    # Read project data
    input_path, output_path, template_path = project_config_readproject(userio, target)
    meta_data = project_config_readmeta(userio, target)

    # Enter ssid is none is in config
    if "ssid" not in meta_data:
        meta_data["ssid"] = ""

    # Get password (and ssid if necessary)
    meta_data["ssid"], meta_data["pass"] = get_ssid_pass(userio, meta_data["ssid"], quiet)

    # Eventually create output
    generate(userio, input_path, output_path, template_path, meta_data)


def project_compile(userio, project_path, force_select=False):
    userio.section("Compiling project output")

    # Get project output location
    sketch_path = project_get_sketch(userio, project_path)
    userio.print("Sketch located: " + sketch_path, verbose=True)

    # Get target FQBN
    fqbn = project_config_readfqbn(userio, project_path)
    if force_select or fqbn is None:
        name, fqbn = get_board(userio)

    # Compile sketch using arduino-cli
    sketch_compile(userio, sketch_path, fqbn)


def project_upload(userio, project_path):
    userio.section("Compiling project output")

    # Get project output location
    sketch_path = project_get_sketch(userio, project_path)
    userio.print("Sketch located: " + sketch_path, verbose=True)

    # Get target FQBN
    name, fqbn, address = get_board_connected(userio)

    # Compile sketch using arduino-cli
    sketch_upload(userio, sketch_path, fqbn, address)
