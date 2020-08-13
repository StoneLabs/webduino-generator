import subprocess
import json

from simple_term_menu import TerminalMenu
from .helper import get_tool


def get_cli_path(userio):
    # Get arduino IDE location
    cli_path = get_tool("arduino-cli")
    if cli_path is None:
        userio.error("Could not locate 'arduino-cli' command. Is arduino-cli istalled?")
    userio.print("CLI located: " + cli_path, verbose=True)

    return cli_path


def get_boards(userio, list_all=False, require_name=True, require_fqbn=False, require_port=False):
    cli_path = get_cli_path(userio)

    if list_all:
        result = subprocess.run([cli_path, "board", "listall", "--format=json"], stdout=subprocess.PIPE)
    else:
        result = subprocess.run([cli_path, "board", "list", "--format=json"], stdout=subprocess.PIPE)

    userio.print("Called arduino-cli with:", verbose=True)
    userio.print(result.args, verbose=True)
    userio.print("Dumping arduino-cli response:", verbose=True)
    userio.print(result.stdout.decode('utf-8'), verbose=True)

    if not result.returncode == 0:
        userio.error("arduino-cli exited with code " + str(result.returncode))

    try:
        boards = json.loads(result.stdout.decode('utf-8'))
    except Exception:
        userio.error("arduino-cli returned invalid JSON")

    # arduino-cli board listall packes the result in a dict
    if list_all:
        if "boards" not in boards:
            userio.error("Could not parse arduino-cli output")
        boards = boards["boards"]

    # Filter out invalid entries (or unwanted)
    if require_name:
        boards = [board for board in boards if "name" in board]
    if require_fqbn:
        boards = [board for board in boards if "FQBN" in board]
    if require_port:
        boards = [board for board in boards if "port" in board]

    userio.print("Dumping processed arduino-cli response:", verbose=True)
    userio.print(boards, verbose=True)

    return boards


def sketch_compile(userio, sketch_path):
    boards = get_boards(userio, True, require_fqbn=True)

    # Query user to select a board
    userio.print("Please select target board:")
    terminal_menu = TerminalMenu([board["name"] for board in boards], menu_highlight_style=None)

    board = boards[terminal_menu.show()]

    userio.print("Selected board: ", verbose=True)
    userio.print(board, verbose=True)

    # Compile sketch
    cli_path = get_cli_path(userio)
    subprocess.run([cli_path, "compile", "--fqbn", board["FQBN"], sketch_path])
