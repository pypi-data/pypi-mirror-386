from typing import Dict, Optional, Union

import tomlkit
from poetry.core.constraints.version import VersionConstraint
from pydantic import BaseModel, ConfigDict
from tomlkit.container import Container
from tomlkit.items import AbstractTable, Table, Trivia


class VersionConstraintContainer(BaseModel):
    """
    Represents a version constraint and its' associated metadata.
    """

    constraint: VersionConstraint
    meta: Optional[AbstractTable] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def merge(self, other: 'VersionConstraintContainer') -> 'VersionConstraintContainer':
        """
        Merge the version constraint and meta of VersionConstraintContainer objects.

        :param other: The VersionConstraintContainer to merge with self.
        """
        merged_constraint = self.constraint.intersect(other.constraint)
        merged_meta = None
        if other.meta:
            merged_meta = Table(value=Container(), trivia=Trivia(), is_aot_element=False)

            # If both containers have meta, only resolve source field
            if self.meta and self.meta.get('source'):
                merged_meta['source'] = self.meta.get('source')
            else:
                merged_meta = other.meta   # if no original meta, include all fields
        else:
            merged_meta = self.meta   # if no other meta, include all fields

        return VersionConstraintContainer(constraint=merged_constraint, meta=merged_meta)

    def output(self) -> Union[str, Dict[str, str]]:
        if self.meta:
            self.meta['version'] = str(self.constraint)
            return dict(self.meta.items())

        return str(self.constraint)
