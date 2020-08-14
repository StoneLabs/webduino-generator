import configparser
import shutil
import io
import os

from .helper import get_files_rec
from .generator import get_template_path, get_demo_path, generate
from .arduino import sketch_compile, sketch_upload, get_board, get_board_connected
from .userio import get_ssid_pass


class Project():
    userio = None
    root_path = ""

    @staticmethod
    def make_config(input_path, template_path, output_path,
                    mode, ssid, port) -> str:
        '''Returns content of default config as string'''

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

    @staticmethod
    def create_project(userio, project_path, delete_block, mode, ssid, port):
        '''Creates new project in specified location'''

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

        # Open project and do not check if its a valid one
        project = Project(userio, project_path, check_valid=False)

        # Get paths to target files/folders beforehand
        path_input = os.path.join(project_path, "input")
        path_output = os.path.join(project_path, "output")
        path_template = os.path.join(project_path, "template")

        path_input_src = get_demo_path()
        path_template_src = get_template_path()

        path_config = project.get_config_folder_path()
        path_config_file = project.get_config_file_path()

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
            config_file.write(Project.make_config(path_input, path_template,
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

    def __init__(self, userio, root_path, check_valid=True):
        '''Open existing project. Will error if invalid project
           is passed and check_valid is True'''

        self.userio = userio
        self.root_path = root_path

        if check_valid and not self.check():
            self.userio.error("Invalid project passed.")

    def check(self):
        '''Checks whether current project is a valid project'''

        config_path = self.get_config_file_path()
        if not os.path.exists(config_path) or \
           not os.path.isfile(config_path):
            return False
        return True

    def get_config_file_path(self):
        '''Returns path to project.wgen of current project.'''

        config_path = os.path.join(self.root_path, "project.wgen")
        return config_path

    def get_config_folder_path(self):
        '''Returns path to .wgen config folder of current project.'''

        config_path = os.path.join(self.root_path, ".wgen")
        return config_path

    def get_sketch_path(self):
        '''Returns location of arduino output sketch. (main.ino)
        Returns None if project was not build yet.'''

        # Read project data
        input_path, output_path, template_path = self.read_config_project()

        # Check if project has been build yet
        sketch_path = os.path.join(output_path, "main", "main.ino")
        if not os.path.exists(sketch_path) or not os.path.isfile(sketch_path):
            return None

        return sketch_path

    def read_config_project(self):
        '''Returns input_path, output_path, template_path of current
           project.'''
        config = configparser.ConfigParser()
        config.read(self.get_config_file_path())

        if "PROJECT" not in config.sections() or \
           "input_path" not in config["PROJECT"] or \
           "output_path" not in config["PROJECT"] or \
           "template_path" not in config["PROJECT"]:
            self.userio.error("Invalid project file!")

        input_path = os.path.join(self.root_path, config["PROJECT"]["input_path"])
        output_path = os.path.join(self.root_path, config["PROJECT"]["output_path"])
        template_path = os.path.join(self.root_path, config["PROJECT"]["template_path"])

        return input_path, output_path, template_path

    def read_config_meta(self):
        config = configparser.ConfigParser()
        config.read(self.get_config_file_path())

        if "METADATA" not in config.sections():
            self.userio.error("Invalid project file!")

        return config["METADATA"]

    def read_config_fqbn(self):
        config = configparser.ConfigParser()
        config.read(self.get_config_file_path())

        if "TARGET" not in config.sections():
            return None

        if "FQBN" not in config["TARGET"]:
            return None

        return config["TARGET"]["FQBN"]

    def write_config_fqbn(self, fqbn):
        config = configparser.ConfigParser()
        config.read(self.get_config_file_path())

        if "TARGET" not in config.sections():
            config["TARGET"] = {}
        config["TARGET"]["FQBN"] = fqbn

        with open(self.get_config_file_path(), "w") as file:
            config.write(file)

    def generate(self, quiet):

        # Read project data
        input_path, output_path, template_path = self.read_config_project()
        meta_data = self.read_config_meta()

        # Enter ssid is none is in config
        if "ssid" not in meta_data:
            meta_data["ssid"] = ""

        # Get password (and ssid if necessary)
        meta_data["ssid"], meta_data["pass"] = get_ssid_pass(self.userio, meta_data["ssid"], quiet)

        # Eventually create output
        generate(self.userio, input_path, output_path, template_path, meta_data)

    def compile(self, force_select=False, save=False):
        self.userio.section("Compiling project output")

        # Get project output location
        sketch_path = self.get_sketch_path()
        self.userio.print("Sketch located: " + sketch_path, verbose=True)

        # Get target FQBN
        fqbn = self.read_config_fqbn()
        if force_select or fqbn is None:
            name, fqbn = get_board(self.userio)
        if save:
            self.write_config_fqbn(fqbn)

        # Compile sketch using arduino-cli
        sketch_compile(self.userio, sketch_path, fqbn)

    def upload(self):
        self.userio.section("Uploading project output")

        # Get project output location
        sketch_path = self.get_sketch_path()
        self.userio.print("Sketch located: " + sketch_path, verbose=True)

        # Get target FQBN
        name, fqbn, address = get_board_connected(self.userio)

        # Compile sketch using arduino-cli
        sketch_upload(self.userio, sketch_path, fqbn, address)
