from rich.console import Console
console = Console()

def Section(text: str) -> None:
    console.print("[bold blue]::", "[bold white]" + text)

def Text(text: str) -> None:
    console.print(text)

def Error(text: str) -> None:
    console.print("[bold red]Error", text)
    exit(1)

if __name__ == "__main__":
    Section("Section demo")
    Text("Lorem ipsum")
    Text("Lorem ipsum")
    Text("Lorem ipsum")
    Section("Section demo")
    Text("Lorem ipsum")
    Text("Lorem ipsum")