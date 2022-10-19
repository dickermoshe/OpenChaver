import click

@click.group()
def cli():
    pass


@cli.command()
def monitor():
    from .monitor import run_monitor
    run_monitor()

@cli.command()
def services():
    from .services import run_services
    run_services()


if __name__ == '__main__':
    cli()