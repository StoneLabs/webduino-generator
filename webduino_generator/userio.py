import getpass
from typing import Tuple, List

from rich.console import Console
from rich.table import Table
from rich import box


def get_ssid_pass(userio, ssid, no_warn):
    # Get SSID and password for wifi connection
    if not no_warn:
        userio.warn("SSID and Password will be saved as plaintext in the output!")
    if ssid == "":
        ssid = userio.get_user("Please enter network credentials:", "SSID: ")
        return ssid, userio.get_pass(None, "Password: ")
    else:
        return ssid, userio.get_pass("Please enter network credentials:\nSSID: " + ssid, "Password: ")


class UserIO:
    console = Console()
    console._log_render.show_time = False
    verbose = False

    def __out__(self, *args):
        if self.verbose:
            self.console.log(*args)
        else:
            self.console.print(*args)

    def section(self, text: str) -> None:
        self.__out__("\n[bold blue]::", "[bold white]" + text)

    def print(self, text: str, verbose: bool = False) -> None:
        if verbose and not self.verbose:
            return
        self.__out__(text)

    def warn(self, text: str) -> None:
        self.__out__("[bold yellow]Warning:", text)

    def error(self, text: str) -> None:
        self.__out__("[bold red]Error: ", text)
        exit(1)

    def quick_table(self, title: str, header: List[str], rows: List[List[str]],
                    verbose: bool = False) -> None:
        if verbose and not self.verbose:
            return

        table = Table(title=title)
        table.box = box.SIMPLE_HEAD

        for i in header:
            table.add_column(i)
        for row in rows:
            table.add_row(*[str(cell) for cell in row])

        self.__out__(table)

    def get_user(self, prompt: str, userText: str) -> Tuple[str, str]:
        if prompt is not None:
            self.console.print(prompt)
        self.console.print(userText, end="")
        try:
            userValue = input()
        except KeyboardInterrupt:
            exit(1)
        return userValue

    def get_pass(self, prompt: str, passText: str) -> Tuple[str, str]:
        if prompt is not None:
            self.console.print(prompt)
        try:
            passValue = getpass.getpass(passText)
        except KeyboardInterrupt:
            exit(1)
        return passValue
