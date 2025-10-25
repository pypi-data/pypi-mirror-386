import os
import sys
from pathlib import Path
from typing import List

import click
from cleo.formatters.style import Style
from cleo.io.inputs.argv_input import ArgvInput
from cleo.io.io import IO
from cleo.io.outputs.output import Verbosity
from cleo.io.outputs.stream_output import StreamOutput
from poetry.factory import Factory
from poetry.installation.installer import Installer
from poetry.utils.env import EnvManager

from anthology.definitions.config import AnthologyConfig
from anthology.utils import (
    collect_subpackage_versions,
    generate_meta_pyproject_toml,
    symlink_venv_into_subpackages,
    update_package_sources,
)


@click.command()
@click.argument('cmd', nargs=-1)
def install(cmd: List[str]):
    """
    Install command for Anthology project.

    This command installs sub-packages defined in the Anthology project. It reads the Anthology configuration
    from the specified directory, ensures that any configured sources are represented in the sub-package
    pyproject.toml documents, locks the sub-packages, generates the meta pyproject.toml document, instantiates
    Poetry, and installs dependencies using Poetry's Installer. Additionally, it symlinks the master virtual
    environment into the sub-packages.

    :param dir: The directory where the Anthology project resides. Defaults to './'.

    Raises:
        FileNotFoundError: If the Anthology configuration file is not found in the specified directory.

    Example:
        To install sub-packages in the current directory:

        >>> anthology install

        To install sub-packages in a specific directory:

        >>> anthology install /path/to/anthology_project
    """
    if len(cmd) == 2:
        dir = Path.cwd()
    else:
        dir = Path(cmd[2])
    # Read the package's anthology configuration
    try:
        config = AnthologyConfig.read(dir=dir)
    except FileNotFoundError as e:
        click.secho(e, fg='red')
        exit(1)

    # Make sure any configured sources are represented in the sub-package pyproject.toml documents
    try:
        update_package_sources(config=config, dir=dir)
    except Exception as e:
        click.secho(e, fg='red')
        exit(1)

    # Retrieve the sub-package versions
    versions = collect_subpackage_versions(config=config, dir=dir)

    if len(versions) > 1:
        click.secho(f'Package versions are mis-matched: {versions}', fg='red')
        exit(1)

    if len(versions) == 0:
        click.secho('No package versions are configured, defaulting to 1.0.0', fg='green')
        versions.add('1.0.0')

    # Generate the meta pyproject.toml document
    try:
        generate_meta_pyproject_toml(project_dir=dir, config=config, version=versions.pop())
    except Exception as e:
        click.secho(e, fg='red')
        exit(1)

    # Instantiate poetry
    poetry = Factory().create_poetry(dir, with_groups=True)

    # Instantiate io
    input = ArgvInput()
    input.set_stream(sys.stdin)

    io = IO(
        input=input,
        output=StreamOutput(sys.stdout),
        error_output=StreamOutput(sys.stderr),
    )
    io.set_verbosity(verbosity=Verbosity(Verbosity.NORMAL))

    # Set our own CLI styles
    formatter = io.output.formatter
    formatter.set_style('c1', Style('cyan'))
    formatter.set_style('c2', Style('default', options=['bold']))
    formatter.set_style('info', Style('blue'))
    formatter.set_style('comment', Style('green'))
    formatter.set_style('warning', Style('yellow'))
    formatter.set_style('debug', Style('default', options=['dark']))
    formatter.set_style('success', Style('green'))
    # Dark variants
    formatter.set_style('c1_dark', Style('cyan', options=['dark']))
    formatter.set_style('c2_dark', Style('default', options=['bold', 'dark']))
    formatter.set_style('success_dark', Style('green', options=['dark']))
    io.output.set_formatter(formatter)
    io.error_output.set_formatter(formatter)

    master_venv = EnvManager(poetry).in_project_venv

    # Make sure we're using the project's master venv when installing
    previous_venv_path = os.getenv('VIRTUAL_ENV', '')
    try:
        os.environ['VIRTUAL_ENV'] = str(master_venv)
        venv = EnvManager(poetry).create_venv()
    except:
        click.secho(f'Failed to instantiate virtual environment in {dir}')
        exit(1)
    finally:
        # Reset the venv environment var to its' previous value
        os.environ['VIRTUAL_ENV'] = previous_venv_path

    # Instantiate poetry's Installer object
    installer = Installer(
        io,
        venv,
        poetry.package,
        poetry.locker,
        poetry.pool,
        poetry.config,
    )

    # Configure poetry to update deps
    installer.update()

    # Execute poetry install
    try:
        result = installer.run()
    except Exception as e:
        click.secho(e, fg='red')
        exit(1)

    if result != 0:
        exit(1)

    # Symlink the master venv into the sub-packages
    try:
        symlink_venv_into_subpackages(project_dir=dir, config=config, master_venv=master_venv)
    except Exception as e:
        click.secho(e, fg='red')
        exit(1)
