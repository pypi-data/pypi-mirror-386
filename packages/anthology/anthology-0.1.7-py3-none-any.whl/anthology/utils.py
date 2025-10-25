import os
from pathlib import Path
from typing import Any, Generator, List, Set, Tuple

import click
from cleo.io.null_io import NullIO
from poetry.factory import Factory
from poetry.installation.installer import Installer
from poetry.pyproject.toml import PyProjectTOML
from poetry.utils.env import EnvManager
from tomlkit.container import Container
from tomlkit.items import Table, Trivia

from anthology.definitions.config import AnthologyConfig
from anthology.definitions.version_constraint_collection import (
    VersionConstraintCollection,
)


def get_targets(dir: Path) -> Generator[PyProjectTOML, None, None]:
    """
    Iterates over the children of the specified directory and
    yields PyProjectTOML objects for each pyproject.toml file
    encountered.

    If a child directory is missing `pyproject.toml`, it is skipped with
    a warning. If a `pyproject.toml` cannot be parsed, a descriptive error
    is raised.

    :param dir: The directory to iterate through
    """
    for path in dir.iterdir():
        # Only consider subdirectories
        if not path.is_dir():
            continue

        pyproject_path = path / 'pyproject.toml'
        if not pyproject_path.exists():
            click.secho(f'⚠️  Missing pyproject.toml in {path}', fg='yellow')
            continue

        try:
            yield PyProjectTOML(pyproject_path)
        except Exception as e:
            # Surface a helpful message about the invalid file
            raise ValueError(f'Invalid pyproject.toml at {pyproject_path}: {e}')


def update_package_sources(config: AnthologyConfig, dir: Path = Path.cwd()):
    """
    Iterate over the sub-packages and set the sources for each to match
    the sources specified in the anthology config.

    :param config: The anthology config
    :param dir: The project directory
    """
    package_dir = dir / config.package_path
    sources = [source.to_dict() for source in config.source]
    for target in get_targets(package_dir):
        click.secho(f'⬆️  Updating package sources for {target.path}', fg='green')
        try:
            _ = target.data  # trigger parsing to catch errors
        except Exception as e:
            raise ValueError(f'Invalid pyproject.toml at {target.path}: {e}')
        if target.data is None:
            # Provide a clear error for invalid/missing files
            raise ValueError(f'Invalid pyproject.toml at {target.path}: document is empty or could not be parsed.')
        target.data.setdefault('tool', {'poetry': {'source': []}})
        target.data['tool']['poetry'].setdefault('source', [])
        target.data['tool']['poetry']['source'] = sources
        target.save()


def collect_subpackage_versions(config: AnthologyConfig, dir: Path = Path.cwd()) -> Set[str]:
    """
    Iterate over the sub-packages and collect the version specified for each.

    :param config: The anthology config
    :param dir: The project directory
    """
    versions: Set[str] = set()

    package_dir = dir / config.package_path
    for target in get_targets(package_dir):
        if 'version' in target.poetry_config:
            versions.add(target.poetry_config['version'])

    return versions


def collect_dependency_constraints(
    config: AnthologyConfig, dir: Path
) -> Tuple[VersionConstraintCollection, VersionConstraintCollection]:
    """
    Iterate over the sub-packages, collect dev-dependencies and dependencies for each sub-package. Combine all
    dependency and dev-dependency constraints together.

    :param config: The anthology config
    :param dir: The project directory
    """
    dependency_constraint_collections: List[VersionConstraintCollection] = []
    dev_dependency_constraint_collections: List[VersionConstraintCollection] = []

    # Get an iterator over all targets
    pyproject_toml_objects = get_targets(dir=dir / config.package_path)

    # Retrieve and merge all deps from pyproject files
    for pyproject_toml_object in pyproject_toml_objects:
        try:
            pyproject_document = pyproject_toml_object.data
        except Exception as e:
            raise ValueError(f'Invalid pyproject.toml at {pyproject_toml_object.path}: {e}')
        if pyproject_document is None:
            raise ValueError(
                f'Invalid pyproject.toml at {pyproject_toml_object.path}: document is empty or could not be parsed.'
            )

        # Retrieve the dependencies and add to our collection of constraints
        dependencies = pyproject_document.get('tool', {}).get('poetry', {}).get('dependencies', {})
        dependency_constraints = VersionConstraintCollection.construct_from_dependency_dict(dependencies=dependencies)
        dependency_constraint_collections.append(dependency_constraints)

        # Retrieve the dev dependencies and add to our collection of constraints
        dev_dependencies = pyproject_document.get('tool', {}).get('poetry', {}).get('dev-dependencies', {})
        dev_dependency_constraints = VersionConstraintCollection.construct_from_dependency_dict(
            dependencies=dev_dependencies
        )
        dev_dependency_constraint_collections.append(dev_dependency_constraints)

    overall_dependency_constraints = VersionConstraintCollection.combine(dependency_constraint_collections)
    overall_dev_dependency_constraints = VersionConstraintCollection.combine(dev_dependency_constraint_collections)

    return overall_dependency_constraints, overall_dev_dependency_constraints


def lock_meta_package(project_dir: Path, config: AnthologyConfig):
    """
    Produce an updated lockfile for the meta package.

    :param project_dir: The project directory
    :param config: The anthology config
    """
    target = PyProjectTOML(project_dir / 'pyproject.toml')
    # Instantiate poetry
    poetry = Factory().create_poetry(target.path)
    io = NullIO()

    master_venv = EnvManager(poetry).in_project_venv

    # Make sure we're using the project's master venv when installing
    previous_venv_path = os.getenv('VIRTUAL_ENV', '')
    try:
        os.environ['VIRTUAL_ENV'] = str(master_venv)
        venv = EnvManager(poetry).create_venv()
    except:
        click.secho(f'Failed to instantiate virtual environment in {dir}')
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
    click.secho(f'🪄 🔒 Generating lockfile for {target.path}', fg='green')
    # Configure poetry to update deps
    installer.lock()
    installer.run()


def extract_sub_package_version(project_dir: Path, config: AnthologyConfig):
    """
    Extract the version of the first sub-package we come across. Used to inform
    the meta-package version.

    :param project_dir: The project directory
    :param config: The anthology config
    """
    package_dir = project_dir / config.package_path
    first_target = next(get_targets(package_dir))
    try:
        _ = first_target.data
    except Exception as e:
        raise ValueError(f'Invalid pyproject.toml at {first_target.path}: {e}')
    if first_target.data is None:
        raise ValueError(f'Invalid pyproject.toml at {first_target.path}: document is empty or could not be parsed.')
    sub_package_version = first_target.data.get('tool', {}).get('poetry', {}).get('version')
    return sub_package_version


def extract_sub_package_names_and_paths(
    project_dir: Path, config: AnthologyConfig
) -> Generator[Tuple[str, Path], Any, Any]:
    """
    Extract the package name and path for each sub-package.

    :param project_dir: The project directory
    :param config: The anthology config
    """
    package_dir = project_dir / config.package_path
    for target in get_targets(dir=package_dir):
        try:
            data = target.data
        except Exception as e:
            raise ValueError(f'Invalid pyproject.toml at {target.path}: {e}')
        if data is None:
            raise ValueError(f'Invalid pyproject.toml at {target.path}: document is empty or could not be parsed.')
        name = data.get('tool', {}).get('poetry', {}).get('name')
        if not name:
            raise ValueError(
                f"Invalid pyproject.toml at {target.path}: missing 'tool.poetry.name'. "
                "Add a [tool.poetry] section with a 'name'."
            )
        path = target.path.parent
        yield name, path


def symlink_venv_into_subpackages(project_dir: Path, config: AnthologyConfig, master_venv: Path):
    """
    For each sub-package, creates a symlink back to the master venv.

    :param project_dir: The project directory
    :param config: The anthology config
    :param master_venv: The path to the master venv
    """
    package_dir = project_dir / config.package_path
    for target in get_targets(dir=package_dir):
        sub_package_dir = target.path.parent
        sub_package_venv = sub_package_dir / '.venv'
        sub_package_venv.unlink(missing_ok=True)
        click.secho(f'🔗 Creating symbolic link from {sub_package_venv} to {master_venv}', fg='green')
        sub_package_venv.symlink_to(target=master_venv, target_is_directory=True)


def update_interlinked_subpackage_dependencies(
    project_dir: Path, config: AnthologyConfig, sub_package_names: Set[str], version: str
):
    """
    For each sub-package, checks for any interlinked dependencies on other sub-packages and
    updates the dependency constraint.

    :param project_dir: The project directory
    :param config: The anthology config
    """
    package_dir = project_dir / config.package_path
    for target in get_targets(dir=package_dir):
        try:
            data = target.data
        except Exception as e:
            raise ValueError(f'Invalid pyproject.toml at {target.path}: {e}')
        if data is None:
            raise ValueError(f'Invalid pyproject.toml at {target.path}: document is empty or could not be parsed.')
        dependencies = data.get('tool', {}).get('poetry', {}).get('dependencies', {})
        for sub_package_name in sub_package_names:
            if sub_package_name in dependencies:
                # If the interlink has a table format, preserve it and update the version
                if isinstance(dependencies[sub_package_name], dict):
                    dependencies[sub_package_name]['version'] = version
                else:
                    dependencies[sub_package_name] = version

        target.save()


def generate_meta_pyproject_toml(project_dir: Path, config: AnthologyConfig, version: str = '1.0.0'):
    """
    Regenerate the meta-package pyproject.toml by merging together the version constraints for all
    sub-packages.

    :param project_dir: The project directory
    :param config: The anthology config
    :param version: The version to set for the meta-package
    """
    click.secho('🪄 📝 Generating meta pyproject.toml', fg='green')
    meta_pyproject = PyProjectTOML(path=project_dir / 'pyproject.toml')
    dependencies_table = Table(value=Container(), trivia=Trivia(), is_aot_element=False)
    dev_dependencies_table = Table(value=Container(), trivia=Trivia(), is_aot_element=False)

    pyproject_deps = {
        'tool': {
            'poetry': {
                'name': 'anthology-meta-package',
                'version': version,
                'description': 'Anthology Meta Package',
                'authors': ['anthology'],
                'source': [source.to_dict() for source in config.source],
                'package-mode': False,
            }
        }
    }

    dependency_constraints, dev_dependency_constraints = collect_dependency_constraints(config=config, dir=project_dir)

    # populate dependencies table, alphabetically sorted
    for dependency, constraint in sorted(dependency_constraints.constraints.items()):
        dependencies_table.append(dependency, constraint.output())

    # populate dev dependencies table, alphabetically sorted
    for dependency, constraint in sorted(dev_dependency_constraints.constraints.items()):
        dev_dependencies_table.append(dependency, constraint.output())

    # Add the sub-packages as development dependencies
    for name, path in extract_sub_package_names_and_paths(project_dir=project_dir, config=config):
        dev_dependencies_table.append(name, {'path': str(path.relative_to(project_dir)), 'develop': True})

    # Add the dependency and dev dependency tables to the document
    pyproject_deps['tool']['poetry']['dependencies'] = dependencies_table
    pyproject_deps['tool']['poetry']['dev-dependencies'] = dev_dependencies_table
    meta_pyproject.data['tool'] = pyproject_deps['tool']
    meta_pyproject.data['build-system'] = {'requires': ['poetry']}

    meta_pyproject.save()
