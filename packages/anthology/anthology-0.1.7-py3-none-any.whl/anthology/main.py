import click

from anthology.commands import install, run, version


@click.group()
def anthology():
    pass


anthology.add_command(run)
anthology.add_command(install)
anthology.add_command(version)

if __name__ == '__main__':
    anthology()
