import click

@click.group()
def cli():
    pass

@cli.command()
def gui():
    from .gui import run_gui
    run_gui()


@cli.command()
def services():
    from .services import run_services
    run_services()



if __name__ == '__main__':
    cli()