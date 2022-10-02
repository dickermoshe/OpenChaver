# To ensure that all the processes are running correctly
# and to restart them if they are not.
# This hello function creates a file in the current directory with the name of the service.

from pathlib import Path
def hello(base_dir: Path, service_name: str):
    """
    Hello
    """
    hello_file = base_dir / f"{service_name}.hello"
    hello_file.touch()
