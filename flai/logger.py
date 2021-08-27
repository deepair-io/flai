from rich.traceback import install
from rich.console import Console

# Creating a console for flai
console = Console()

# Error handeling by rich module
install(console=console, show_locals=False)
