import argparse

from .userio import UserIO, get_ssid_pass
from .helper import cpp_str_esc, cpp_img_esc, get_files_rec, shorten
from .project import project_make_new, project_generate
from .generator import *


def command_version(userio, args):
    userio.print("Current version: " + __version__)


def command_generate(userio, args):
    # Check port
    if args.port < 0 or args.port > 65535:
        userio.error("Invalid port!")

    # Check mode
    if args.mode.lower() != "wifinina":
        userio.error("Target mode not supported!\nSupported modes: wifinina")

    # Check templates folder
    if args.template == "":
        args.template = get_template_path()
        userio.print("Using build in template files at " + args.template,
                     verbose=True)

    # Get SSID and password
    args.ssid, args.ssid_pass = get_ssid_pass(userio, args.ssid, args.quiet)

    # Pack meta data
    userio.section("Processing misc. data...")
    meta_data = {
        "mode": args.mode,
        "ssid": args.ssid,
        "pass": args.ssid_pass,
        "port": str(args.port)
    }

    # Eventually create output
    generate(userio, args.input, args.output, args.template, meta_data)


def command_init(userio, args):
    project_make_new(userio, args.target, args.force,
                     args.mode, args.ssid, args.port)


def command_build(userio, args):
    project_generate(userio, args.target, args.quiet)


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
    parser_init.add_argument("-s", "--ssid", metavar="ssid", type=str,
                             default="", dest='ssid',
                             help="SSID of network")
    parser_init.add_argument("-p", "--port", metavar="port", type=int,
                             default=80, dest='port',
                             help="Port of webserver")
    parser_init.add_argument("-m", "--mode", metavar="mode", type=str,
                             default="wifinina", dest='mode',
                             help="Connection mode/library to be used")
    parser_init.add_argument("-f", "--force",
                             action="store_true", dest='force',
                             help="Delete files that block project creation.")

    parser_build = subparsers.add_parser("build", help="Generate Arduino code from current project")
    parser_build.add_argument("target", metavar="target", type=str,
                              default=".", nargs="?",
                              help="Target folder where project will be created")
    parser_build.add_argument("-q", "--quiet",
                              action="store_true", dest='quiet',
                              help="Hides password warning")

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
    if hasattr(args, "verbose"):
        userio.verbose = args.verbose

    userio.print("[bold]Stone Labs. Webduino Gernerator\n")

    userio.print("Dumping arguments", verbose=True)
    userio.quick_table("", ["Argument", "Value"],
                       [[arg, getattr(args, arg)] for arg in vars(args)],
                       verbose=True)

    def handle():
        # Check command
        if args.command is None:
            userio.error("No command specified!")
        elif args.command == "version":
            command_version(userio, args)
        elif args.command == "init":
            command_init(userio, args)
        elif args.command == "build":
            command_build(userio, args)
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

    if userio.verbose:
        handle()
    else:
        try:
            handle()
        except NotImplementedError:
            userio.print("Sorry. This feature is not implemented yet. Use -v to trace.")


if __name__ == "__main__":
    main()
