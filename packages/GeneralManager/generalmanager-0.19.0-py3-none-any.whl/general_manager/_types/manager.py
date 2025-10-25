from __future__ import annotations

"""Type-only imports for public API re-exports."""

__all__ = [
    "GeneralManager",
    "GeneralManagerMeta",
    "GroupManager",
    "Input",
    "graphQlProperty",
]

from general_manager.manager.generalManager import GeneralManager
from general_manager.manager.meta import GeneralManagerMeta
from general_manager.manager.groupManager import GroupManager
from general_manager.manager.input import Input
from general_manager.api.property import graphQlProperty
