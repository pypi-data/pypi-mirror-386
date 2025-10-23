"""Contains enumerations used in this package."""

from enum import StrEnum


class MappingType(StrEnum):
    """The discriminator used between mappings.

    Each of these types should have their own mapping class derived of some sort of
    mapping.
    """

    fault = "fault"
    stratigraphy = "stratigraphy"
    well = "well"


class RelationType(StrEnum):
    """The kind of relation this mapping represents."""

    alias = "alias"
    child_to_parent = "child_to_parent"
    equivalent = "equivalent"
    fmu_to_target = "fmu_to_target"
    predecessor_to_successor = "predecessor_to_successor"


class DataEntrySource(StrEnum):
    user = "user"
    automated = "automated"


class TargetSystem(StrEnum):
    smda = "smda"
