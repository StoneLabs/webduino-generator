import configparser
import shutil
import io
import os

from .helper import get_files_rec
from .generator import get_template_path, get_demo_path


def project_make_config(input_path, template_path, output_path) -> str:
    # Make new config file with default content
    config = configparser.ConfigParser()
    config["PROJECT"] = \
        {
            "input_path": input_path,
            "template_path": template_path,
            "output_path": output_path,
        }

    # Write to buffer and return content
    with io.StringIO() as buffer:
        config.write(buffer)
        buffer.seek(0)
        return buffer.read()


def project_make_new(userio, project_path, delete_block):
    userio.section("Generating 'hello world' project")

    # Check if target exists
    if not os.path.exists(project_path):
        userio.error("Path " + project_path + " is invalid or does not exist!")

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
    path_config_file = os.path.join(project_path, "project.wgen")

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
        config_file.write(project_make_config(path_input,
                                              path_template,
                                              path_output))

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
