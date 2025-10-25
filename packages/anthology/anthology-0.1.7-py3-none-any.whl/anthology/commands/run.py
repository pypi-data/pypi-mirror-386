import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import click

from anthology.definitions.config import AnthologyConfig
from anthology.utils import get_targets


@click.command()
@click.argument('cmd', nargs=-1)
def run(cmd: List[str]):
    """
    Run command for Anthology project.

    This command runs scripts defined in the Anthology project. It reads the Anthology configuration
    from the current working directory, locates the package directory, retrieves the scripts defined
    in the Anthology configuration for the target, and executes the specified script using subprocess.
    The command supports passing arguments to the script.

    :param cmd: The command and its arguments to be executed.

    Raises:
        FileNotFoundError: If the Anthology configuration file is not found in the current directory.

    Example:
        To run a script named 'build' in the Anthology project:

        >>> anthology run build

        To run a script named 'test' with arguments 'arg1' and 'arg2':

        >>> anthology run test arg1 arg2
    """
    cmd = cmd[2:]   # Ignore anthology cmd and subcmd
    click.secho(','.join(cmd), fg='green')
    dir_ = Path.cwd()
    # Read the package's anthology configuration
    try:
        config = AnthologyConfig.read(dir=dir_)
    except FileNotFoundError as e:
        click.secho(e, fg='red')
        return

    package_dir = dir_ / config.package_path
    for target in get_targets(dir=package_dir):
        scripts: Dict[str, str] = target.data.get('tool', {}).get('anthology', {}).get('scripts', {})
        script_name = cmd[0]
        if script_name not in scripts:
            click.secho(f'🙅 {script_name} not defined in {target.path}', fg='red')
            continue

        target_dir = target.path.parent
        try:
            script_args = [scripts[script_name]]
            result = subprocess.run(args=script_args, cwd=target_dir, text=True, shell=True, check=True)
            click.secho(result.stdout, fg='green')
        except subprocess.CalledProcessError:
            click.secho(f'Encountered exception running {cmd}: {result.stderr}', fg='red')
            sys.exit(1)
