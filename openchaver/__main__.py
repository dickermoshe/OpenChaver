import click

@click.group()
def cli():
    pass


@cli.command()
def runservice():
    from .service.__main__ import run_service
    run_service()

@cli.command()
def runmonitor():
    from .monitor.__main__ import run_monitor
    run_monitor()

@cli.command()
def setup():
    from .setup import run_setup
    run_setup()

if __name__ == '__main__':
    cli()