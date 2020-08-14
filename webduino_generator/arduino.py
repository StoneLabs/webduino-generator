import subprocess
import json

from simple_term_menu import TerminalMenu
from .helper import get_tool


def get_ide_path(userio):
    # Get arduino IDE location
    ide_path = get_tool("arduino")
    if ide_path is None:
        userio.error("Could not locate 'arduino' command. Is the arduino IDE istalled?")
    userio.print("IDE located: " + ide_path, verbose=True)

    return ide_path


def get_cli_path(userio):
    # Get arduino IDE location
    cli_path = get_tool("arduino-cli")
    if cli_path is None:
        userio.error("Could not locate 'arduino-cli' command. Is arduino-cli istalled?")
    userio.print("CLI located: " + cli_path, verbose=True)

    return cli_path


def get_boards_json(userio, list_all=False):
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

    return boards


def get_boards(userio):
    boards = get_boards_json(userio, True)

    # arduino-cli board listall packes the result in a dict
    if "boards" not in boards:
        userio.error("Could not parse arduino-cli output")
    boards = boards["boards"]

    # Filter out invalid entries (or unwanted)
    boards = [board for board in boards if "name" in board]
    boards = [board for board in boards if "FQBN" in board]

    userio.print("Dumping processed arduino-cli response:", verbose=True)
    userio.print(boards, verbose=True)

    return boards


def get_boards_connected(userio):
    boards = get_boards_json(userio, False)

    processed = []
    for board in boards:
        if "boards" not in board:
            continue
        if "address" not in board:
            continue
        if len(board["boards"]) != 1:
            continue
        if "FQBN" not in board["boards"][0]:
            continue
        if "name" not in board["boards"][0]:
            continue
        processed += [{
            "name": board["boards"][0]["name"],
            "FQBN": board["boards"][0]["FQBN"],
            "address": board["address"]
        }]

    userio.print("Dumping processed arduino-cli response:", verbose=True)
    userio.print(processed, verbose=True)

    return processed


def get_board(userio):
    boards = get_boards(userio)

    if len(boards) == 0:
        userio.error("No boards found!")

    # Query user to select a board
    userio.print("Please select target board:")
    terminal_menu = TerminalMenu([board["name"] for board in boards], menu_highlight_style=None)

    selection = terminal_menu.show()

    # Menu cancled by user
    if selection is None:
        exit(0)
    board = boards[selection]

    userio.print("Selected board: ", verbose=True)
    userio.print(board, verbose=True)

    return board["name"], board["FQBN"]


def get_board_connected(userio):
    boards = get_boards_connected(userio)

    if len(boards) == 0:
        userio.error("No boards found!")

    # Query user to select a board
    userio.print("Please select target board:")
    terminal_menu = TerminalMenu([board["address"] + ": " + board["name"]
                                 for board in boards], menu_highlight_style=None)

    selection = terminal_menu.show()

    # Menu cancled by user
    if selection is None:
        exit(0)
    board = boards[selection]

    userio.print("Selected board: ", verbose=True)
    userio.print(board, verbose=True)

    return board["name"], board["FQBN"], board["address"]


def sketch_compile(userio, sketch_path, fqbn):
    # Compile sketch
    cli_path = get_cli_path(userio)
    subprocess.run([cli_path, "compile", "--fqbn", fqbn, sketch_path])


def sketch_upload(userio, sketch_path, fqbn, address):
    # Upload sketch
    cli_path = get_cli_path(userio)
    subprocess.run([cli_path, "upload", "-p", address, "--fqbn", fqbn, sketch_path])
