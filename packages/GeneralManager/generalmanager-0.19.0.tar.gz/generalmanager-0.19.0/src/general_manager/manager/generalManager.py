from __future__ import annotations
from typing import TYPE_CHECKING, Any, Iterator, Self, Type
from general_manager.manager.meta import GeneralManagerMeta

from general_manager.api.property import GraphQLProperty
from general_manager.cache.cacheTracker import DependencyTracker
from general_manager.cache.signals import dataChange
from general_manager.bucket.baseBucket import Bucket


class UnsupportedUnionOperandError(TypeError):
    """Raised when attempting to union a manager with an incompatible operand."""

    def __init__(self, operand_type: type) -> None:
        """
        Exception raised when attempting to perform a union with an unsupported operand type.

        Parameters:
            operand_type (type): The operand type that is not supported for the union; its representation is included in the exception message.
        """
        super().__init__(f"Unsupported type for union: {operand_type}.")


if TYPE_CHECKING:
    from general_manager.permission.basePermission import BasePermission
    from general_manager.interface.baseInterface import InterfaceBase


class GeneralManager(metaclass=GeneralManagerMeta):
    Permission: Type[BasePermission]
    _attributes: dict[str, Any]
    Interface: Type["InterfaceBase"]
    _old_values: dict[str, Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Create a manager by constructing its Interface and record the resulting identification.

        Parameters:
            *args: Positional arguments forwarded to the Interface constructor.
            **kwargs: Keyword arguments forwarded to the Interface constructor.
        """
        self._interface = self.Interface(*args, **kwargs)
        self.__id: dict[str, Any] = self._interface.identification
        DependencyTracker.track(
            self.__class__.__name__, "identification", f"{self.__id}"
        )

    def __str__(self) -> str:
        """Return a user-friendly representation showing the identification."""
        return f"{self.__class__.__name__}(**{self.__id})"

    def __repr__(self) -> str:
        """Return a detailed representation of the manager instance."""
        return f"{self.__class__.__name__}(**{self.__id})"

    def __reduce__(self) -> str | tuple[Any, ...]:
        """
        Provide pickling support for the manager instance.

        Returns:
            tuple[Any, ...]: Reconstruction data consisting of the class and identification tuple.
        """
        return (self.__class__, tuple(self.__id.values()))

    def __or__(
        self,
        other: Self | Bucket[Self],
    ) -> Bucket[Self]:
        """
        Combine this manager with another manager or a Bucket into a Bucket representing their union.

        Parameters:
            other (Self | Bucket[Self]): A manager of the same class or a Bucket to union with.

        Returns:
            Bucket[Self]: A Bucket containing the union of the managed objects represented by this manager and `other`.

        Raises:
            UnsupportedUnionOperandError: If `other` is not a Bucket and not a GeneralManager instance of the same class.
        """
        if isinstance(other, Bucket):
            return other | self
        elif isinstance(other, GeneralManager) and other.__class__ == self.__class__:
            return self.filter(id__in=[self.__id, other.__id])
        else:
            raise UnsupportedUnionOperandError(type(other))

    def __eq__(
        self,
        other: object,
    ) -> bool:
        """
        Determine whether another object represents the same managed entity.

        Returns:
            `true` if `other` is a `GeneralManager` whose identification equals this manager's, `false` otherwise.
        """
        if not isinstance(other, GeneralManager):
            return False
        return self.identification == other.identification

    @property
    def identification(self) -> dict[str, Any]:
        """Return the identification dictionary used to fetch the managed object."""
        return self.__id

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        """Iterate over attribute names and resolved values for the managed object."""
        for key, value in self._attributes.items():
            if callable(value):
                yield key, value(self._interface)
                continue
            yield key, value
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, (GraphQLProperty, property)):
                yield name, getattr(self, name)

    @classmethod
    @dataChange
    def create(
        cls,
        creator_id: int | None = None,
        history_comment: str | None = None,
        ignore_permission: bool = False,
        **kwargs: Any,
    ) -> Self:
        """
        Create a new managed object through the interface.

        Parameters:
            creator_id (int | None): Optional identifier of the creating user.
            history_comment (str | None): Audit comment stored with the change.
            ignore_permission (bool): When True, skip permission validation.
            **kwargs (Any): Additional fields forwarded to the interface `create` method.

        Returns:
            Self: Manager instance representing the created object.

        Raises:
            PermissionError: Propagated if the permission check fails.
        """
        if not ignore_permission:
            cls.Permission.checkCreatePermission(kwargs, cls, creator_id)
        identification = cls.Interface.create(
            creator_id=creator_id, history_comment=history_comment, **kwargs
        )
        return cls(identification)

    @dataChange
    def update(
        self,
        creator_id: int | None = None,
        history_comment: str | None = None,
        ignore_permission: bool = False,
        **kwargs: Any,
    ) -> Self:
        """
        Update the managed object and return a fresh manager representing the new state.

        Parameters:
            creator_id (int | None): Optional identifier of the user performing the update.
            history_comment (str | None): Audit comment recorded with the update.
            ignore_permission (bool): When True, skip permission validation.
            **kwargs (Any): Field updates forwarded to the interface.

        Returns:
            Self: Manager instance reflecting the updated object.

        Raises:
            PermissionError: Propagated if the permission check fails.
        """
        if not ignore_permission:
            self.Permission.checkUpdatePermission(kwargs, self, creator_id)
        self._interface.update(
            creator_id=creator_id,
            history_comment=history_comment,
            **kwargs,
        )
        return self.__class__(**self.identification)

    @dataChange
    def deactivate(
        self,
        creator_id: int | None = None,
        history_comment: str | None = None,
        ignore_permission: bool = False,
    ) -> Self:
        """
        Deactivate the managed object and return a manager for the resulting state.

        Parameters:
            creator_id (int | None): Optional identifier of the user performing the action.
            history_comment (str | None): Audit comment recorded with the deactivation.
            ignore_permission (bool): When True, skip permission validation.

        Returns:
            Self: Manager instance representing the deactivated object.

        Raises:
            PermissionError: Propagated if the permission check fails.
        """
        if not ignore_permission:
            self.Permission.checkDeletePermission(self, creator_id)
        self._interface.deactivate(
            creator_id=creator_id, history_comment=history_comment
        )
        return self.__class__(**self.identification)

    @classmethod
    def filter(cls, **kwargs: Any) -> Bucket[Self]:
        """
        Return a bucket containing managers that satisfy the provided lookups.

        Parameters:
            **kwargs (Any): Django-style filter expressions forwarded to the interface.

        Returns:
            Bucket[Self]: Bucket of matching manager instances.
        """
        DependencyTracker.track(
            cls.__name__, "filter", f"{cls.__parse_identification(kwargs)}"
        )
        return cls.Interface.filter(**kwargs)

    @classmethod
    def exclude(cls, **kwargs: Any) -> Bucket[Self]:
        """
        Return a bucket excluding managers that match the provided lookups.

        Parameters:
            **kwargs (Any): Django-style exclusion expressions forwarded to the interface.

        Returns:
            Bucket[Self]: Bucket of manager instances that do not satisfy the lookups.
        """
        DependencyTracker.track(
            cls.__name__, "exclude", f"{cls.__parse_identification(kwargs)}"
        )
        return cls.Interface.exclude(**kwargs)

    @classmethod
    def all(cls) -> Bucket[Self]:
        """Return a bucket containing every managed object of this class."""
        return cls.Interface.filter()

    @staticmethod
    def __parse_identification(kwargs: dict[str, Any]) -> dict[str, Any] | None:
        """
        Replace manager instances within a filter mapping by their identifications.

        Parameters:
            kwargs (dict[str, Any]): Mapping containing potential manager instances.

        Returns:
            dict[str, Any] | None: Mapping with managers substituted by identification dictionaries, or None if no substitutions occurred.
        """
        output: dict[str, Any] = {}
        for key, value in kwargs.items():
            if isinstance(value, GeneralManager):
                output[key] = value.identification
            elif isinstance(value, list):
                output[key] = [
                    v.identification if isinstance(v, GeneralManager) else v
                    for v in value
                ]
            elif isinstance(value, tuple):
                output[key] = tuple(
                    v.identification if isinstance(v, GeneralManager) else v
                    for v in value
                )
            else:
                output[key] = value
        return output if output else None
