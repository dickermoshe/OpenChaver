import click

@click.command()
def monitor():
    """Monitor the client computer and upload screenshots to the server - This is the main service"""
    from .monitor import monitor_service
    monitor_service()

@click.command()
def gui():
    """Run the GUI"""
    from .config import gui
    gui()


@click.group()
def cli():
    pass

cli.add_command(monitor)
cli.add_command(gui)

if __name__ == "__main__":
    cli()