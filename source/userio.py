import getpass
from typing import Tuple

from rich.console import Console
console = Console()


def Section(text: str) -> None:
    console.print("[bold blue]::", "[bold white]" + text)


def Text(text: str) -> None:
    console.print(text)


def Error(text: str) -> None:
    console.print("[bold red]Error", text)
    exit(1)


def GetUserPass(userText: str, passText: str) -> Tuple[str, str]:
    console.print(userText, end="")
    userValue = input()
    passValue = getpass.getpass(passText)
    return userValue, passValue
