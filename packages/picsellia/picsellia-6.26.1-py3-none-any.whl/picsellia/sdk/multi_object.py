from typing import Generic, Optional, TypeVar, Union
from uuid import UUID

from beartype import beartype

from picsellia import exceptions as exceptions
from picsellia.colors import Colors
from picsellia.sdk.connexion import Connexion
from picsellia.sdk.dao import Dao

T = TypeVar("T", bound=Dao)


class MultiObject(Generic[T]):
    @beartype
    def __init__(self, connexion: Connexion, items: list[T]) -> None:
        self._connexion = connexion

        if not items:
            raise exceptions.NoDataError("A MultiObject can't be empty")

        self.items: list[T] = items

    @property
    def connexion(self) -> Connexion:
        return self._connexion

    @property
    def ids(self) -> list[UUID]:
        return [obj.id for obj in self.items]

    @beartype
    def __str__(self) -> str:
        return f"{Colors.GREEN}MultiObject{Colors.ENDC} object, size: {len(self.items)}"

    @beartype
    def __repr__(self) -> str:
        return self.__str__()

    @beartype
    def __eq__(self, other) -> bool:
        if isinstance(other, list):
            if len(other) != len(self.items):
                return False

            for item in self.items:
                if item not in other:
                    return False

            return True

        if isinstance(other, MultiObject):
            self.assert_same_connexion(other)
            if len(self.items) != len(other.items):
                return False

            for item in self.items:
                if item not in other.items:
                    return False

            return True

        return False

    @beartype
    def __len__(self) -> int:
        return len(self.items)

    @beartype
    def assert_enough_items(self) -> None:
        if len(self.items) < 2:
            raise exceptions.NoDataError(
                "You can't remove from this list the last item. A MultiObject can't be empty"
            )

    @beartype
    def assert_same_connexion(self, other: Union["MultiObject", Dao]) -> None:
        if self.connexion != other.connexion:
            raise exceptions.BadRequestError(
                "Objects that you manipulate does not come from the same client."
            )

    @beartype
    def __delitem__(self, i: int) -> None:
        self.assert_enough_items()
        del self.items[i]

    @beartype
    def __setitem__(self, i: int, v: T) -> None:
        self.assert_same_connexion(v)
        self.items[i] = v

    @beartype
    def append(self, x: T) -> None:
        self.assert_same_connexion(x)
        self.items.append(x)

    @beartype
    def extend(self, objects: Union[T, "MultiObject", list[T]]) -> None:
        # objects cannot be typed MultiObject[T] because:
        # beartype.roar.BeartypeDecorHintForwardRefException: Forward reference 'MultiObject[T]' not valid Python attribute name.
        if isinstance(objects, Dao):
            self.assert_same_connexion(objects)
        elif isinstance(objects, MultiObject) or isinstance(objects, list):
            for x in objects:
                self.assert_same_connexion(x)
        else:
            raise TypeError(objects)
        self.items.extend(objects)

    @beartype
    def insert(self, i: int, x: T) -> None:
        self.assert_same_connexion(x)
        self.items.insert(i, x)

    @beartype
    def remove(self, x: T) -> None:
        self.assert_enough_items()
        self.items.remove(x)

    @beartype
    def pop(self, i: Optional[int] = None) -> T:
        self.assert_enough_items()
        if i:
            return self.items.pop(i)
        else:
            return self.items.pop()

    @beartype
    def clear(self) -> None:
        raise exceptions.NoDataError("You can't clear a MultiObject.")

    @beartype
    def index(
        self, x: T, start: Optional[int] = None, end: Optional[int] = None
    ) -> int:
        if start:
            if end:
                return self.items.index(x, start, end)
            else:
                return self.items.index(x, start)
        else:
            return self.items.index(x)

    @beartype
    def count(self, x: T) -> int:
        return self.items.count(x)

    @beartype
    def sort(self, key=None, reverse=False) -> None:
        self.items.sort(key=key, reverse=reverse)

    @beartype
    def reverse(self) -> None:
        self.items.reverse()

    @beartype
    def copy(self) -> "MultiObject":
        raise NotImplementedError("Not implemented. Please contact support")
