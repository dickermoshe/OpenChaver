import click

@click.group()
def cli():
    pass


@cli.command()
def services():
    from .services import run_services
    run_services()



if __name__ == '__main__':
    cli()