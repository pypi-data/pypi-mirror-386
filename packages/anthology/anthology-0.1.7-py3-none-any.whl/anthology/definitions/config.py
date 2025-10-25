import sys
from pathlib import Path
from typing import Any, Dict, List

from poetry.config.source import Source
from pydantic import BaseModel

if sys.version_info < (3, 11):
    # compatibility for python <3.11
    import tomli as tomllib
else:
    import tomllib


class AnthologyConfig(BaseModel):
    """
    Represents the configuration for Anthology.

    :attr source: A list of sources to insert into the sub-packages.
    :attr package_path: The path to the sub-packages.
    """

    source: List[Source] = []
    package_path: str = 'packages'

    @classmethod
    def read(cls, dir: Path) -> 'AnthologyConfig':
        """
        Reads a configuration object from the specified directory.

        :param dir: The directory to read the config object from.
        """
        config_path = dir / 'anthology.toml'
        if not config_path.exists():
            raise FileNotFoundError(f'Anthology config missing: {config_path}')
        config_document: Dict[str, Any] = {}
        with open(config_path, 'rb') as fp:
            config_document = tomllib.load(fp)
        if 'source' in config_document:
            sources = [Source(**source) for source in config_document['source']]
            config_document['source'] = sources
        return cls.parse_obj(config_document)
