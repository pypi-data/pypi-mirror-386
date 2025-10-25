import subprocess
import sys
from pathlib import Path
from typing import List

import click

from anthology.definitions.config import AnthologyConfig
from anthology.utils import (
    extract_sub_package_names_and_paths,
    extract_sub_package_version,
    generate_meta_pyproject_toml,
    get_targets,
    lock_meta_package,
    update_interlinked_subpackage_dependencies,
    update_package_sources,
)


@click.command()
@click.argument('args', nargs=-1)
def version(args: List[str]):
    """
    Version command for Anthology project.

    This command manages versioning within the Anthology project. It reads the Anthology configuration
    from the current working directory, executes 'poetry version' command in each of the sub-packages,
    updates package sources, locks sub-packages, extracts the version of the sub-package, and generates
    the meta pyproject.toml document with the updated version.

    :param args: Additional arguments to be passed to the 'poetry version' command.

    Raises:
        FileNotFoundError: If the Anthology configuration file is not found in the current directory.

    Example:
        To update the version of sub-packages in the Anthology project:

        >>> anthology version

        To update the version with additional arguments:

        >>> anthology version patch
    """
    args = args[2:]   # Ignore anthology cmd and subcmd
    dir_ = Path.cwd()
    # Read the package's anthology configuration
    try:
        config = AnthologyConfig.read(dir=dir_)
    except FileNotFoundError as e:
        click.secho(e, fg='red')
        return

    # Run poetry version in each of the sub-packages
    package_dir = dir_ / config.package_path
    cmd = ['poetry', 'version'] + list(args)
    for target in get_targets(dir=package_dir):
        target_dir = target.path.parent
        try:
            result = subprocess.run(args=cmd, cwd=target_dir, text=True, check=True)
            click.secho(result.stdout, fg='green')
        except subprocess.CalledProcessError:
            click.secho(f'Encountered exception running {cmd}: {result.stderr}', fg='red')
            sys.exit(1)

    # Make sure any configured sources are represented in the sub-package pyproject.toml documents
    update_package_sources(config=config, dir=dir_)

    # Get sub-package version
    version_ = extract_sub_package_version(project_dir=dir_, config=config)

    # Get sub-package names
    sub_package_names = set(name for name, _ in extract_sub_package_names_and_paths(project_dir=dir_, config=config))

    # Iterate over sub-packages, update any dependencies on other sub-packages
    update_interlinked_subpackage_dependencies(
        project_dir=dir_, config=config, sub_package_names=sub_package_names, version=version_
    )

    # Generate the meta pyproject.toml document
    generate_meta_pyproject_toml(project_dir=dir_, config=config, version=version_)

    # Lock the meta-package
    lock_meta_package(project_dir=dir_, config=config)
