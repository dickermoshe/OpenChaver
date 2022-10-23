import click
import logging

logger = logging.getLogger(__name__)


@click.group()
def cli():
    """OpenChaver - A simple, open source, WebChaver alternative"""
    pass


@cli.command()
def runservice():
    """Run the OpenChaver service"""
    from .service.__main__ import run_service
    logger.info("Running the OpenChaver Service")
    run_service()


@cli.command()
def runmonitor():
    """Run the OpenChaver Monitor"""
    from .monitor.__main__ import run_monitor
    logger.info("Running the OpenChaver Monitor")
    run_monitor()


@cli.command()
def setup():
    """Setup the OpenChaver Service & Auto Start the Monitor"""
    from .setup import run_setup
    logger.info("Setting up the OpenChaver Service & Auto Start the Monitor")
    run_setup()


if __name__ == '__main__':
    cli()
