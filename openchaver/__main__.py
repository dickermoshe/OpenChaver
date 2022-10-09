import click

@click.command()
def monitor():
    """Monitor the client computer and upload screenshots to the server - This is the main service"""
    from .monitor import monitor_service
    monitor_service()

@click.command()
@click.argument("userid")
@click.argument("uninstall_code")
def setup(userid, uninstall_code):
    """Add the user to the client computer"""
    from .setup import setup
    setup(userid, uninstall_code)

@click.command()
@click.argument("uninstall_code")
def uninstall(uninstall_code):
    """Uninstall the program from the client computer"""
    from .setup import uninstall
    uninstall(uninstall_code)

@click.group()
def cli():
    pass

cli.add_command(monitor)
cli.add_command(setup)
cli.add_command(uninstall)

if __name__ == "__main__":
    cli()