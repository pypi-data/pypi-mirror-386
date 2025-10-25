from typing import Dict, List, Union

from poetry.core.constraints.version import VersionConstraint
from poetry.core.constraints.version.parser import parse_constraint
from tomlkit.items import AbstractTable

from anthology.definitions.version_constraint_container import (
    VersionConstraintContainer,
)


class VersionConstraintCollection:
    """
    Represents a collection of version constraints for dependencies.

    :attr constraints: A dictionary containing dependency names as keys and their
    respective VersionConstraint objects as values.
    """

    constraints: Dict[str, VersionConstraintContainer]

    def __init__(self):
        """
        Initialises an empty VersionConstraintCollection.
        """
        self.constraints = {}

    @classmethod
    def construct_from_dependency_dict(
        cls, dependencies: Dict[str, Union[str, AbstractTable]]
    ) -> 'VersionConstraintCollection':
        """
        Constructs a VersionConstraintCollection from a dictionary of dependencies.

        :param dependencies: A dictionary where keys are dependency names and values are version constraint strings or Table objects.
        """
        version_constraint_collection = cls()
        for dep_name, dep_constraint in dependencies.items():
            meta = None
            if isinstance(dep_constraint, AbstractTable):
                constraint = parse_constraint(dep_constraint.get('version'))
                meta = dep_constraint.remove('version')
            else:
                constraint = parse_constraint(dep_constraint)
            version_constraint_collection.insert(
                name=dep_name, constraint=VersionConstraintContainer(constraint=constraint, meta=meta)
            )
        return version_constraint_collection

    def insert(self, name: str, constraint: VersionConstraintContainer):
        """
        Inserts a version constraint for a dependency.

        :param name: The name of the dependency.
        :param constraint: The VersionConstraint object representing the constraint.
        """
        self.constraints[name] = constraint

    def merge(self, new_constraints: 'VersionConstraintCollection') -> 'VersionConstraintCollection':
        """
        Merges another VersionConstraintCollection into this collection.

        :param new_constraints: The VersionConstraintCollection to merge into this one.
        """
        merged_constraint_collection = VersionConstraintCollection()
        for constraint_name, constraint in new_constraints.constraints.items():
            existing_constraint = self.constraints.get(
                constraint_name, VersionConstraintContainer(constraint=parse_constraint('*'))
            )
            merged_constraint_collection.insert(constraint_name, existing_constraint.merge(constraint))

        for constraint_name, constraint in self.constraints.items():
            if constraint_name not in merged_constraint_collection.constraints:
                merged_constraint_collection.insert(constraint_name, constraint)

        return merged_constraint_collection

    @classmethod
    def combine(cls, constraint_collections: List['VersionConstraintCollection']) -> 'VersionConstraintCollection':
        """
        Combines multiple VersionConstraintCollections into one.

        :param constraint_collections: A list of VersionConstraintCollection objects to combine.
        """
        meta_constraint_collection = cls()
        for constraint_collection in constraint_collections:
            meta_constraint_collection = meta_constraint_collection.merge(new_constraints=constraint_collection)

        return meta_constraint_collection
