import logging
from typing import Optional
from uuid import UUID

import orjson
from beartype import beartype

from picsellia.colors import Colors
from picsellia.decorators import exception_handler
from picsellia.sdk.connexion import Connexion
from picsellia.sdk.dao import Dao
from picsellia.types.schemas import LabelGroupSchema

logger = logging.getLogger("picsellia")


class LabelGroup(Dao):
    def __init__(
        self, connexion: Connexion, dataset_version_id: UUID, data: dict
    ) -> None:
        Dao.__init__(self, connexion, data)
        self._dataset_version_id = dataset_version_id

    @property
    def name(self) -> str:
        """Name of this (LabelGroup)"""
        return self._name

    @property
    def parent_id(self) -> Optional[UUID]:
        """Id of the (LabelGroup) parent of this (LabelGroup)"""
        return self._parent_id

    @property
    def dataset_version_id(self) -> UUID:
        """Id of the (DatasetVersion) of this (LabelGroup)"""
        return self._dataset_version_id

    def __str__(self):
        return f"{Colors.YELLOW}LabelGroup '{self.name}'{Colors.ENDC} (id: {self.id})"

    @exception_handler
    @beartype
    def sync(self) -> dict:
        r = self.connexion.get(f"/api/label/group/{self.id}").json()
        self.refresh(r)
        return r

    @exception_handler
    @beartype
    def refresh(self, data: dict) -> LabelGroupSchema:
        schema = LabelGroupSchema(**data)
        self._name = schema.name
        self._parent_id = schema.parent_id
        return schema

    @exception_handler
    @beartype
    def update(self, name: str = None, parent_id: UUID = None) -> None:
        """Update this (LabelGroup) with a new name or a new parent_id.

        Examples:
            ```python
            group.update(name="new")
            ```

        Arguments:
            name: New name of this (LabelGroup)
            parent_id (uuid, optional): New name of this (LabelGroup)
        """
        payload = {}
        if name:
            payload["name"] = name

        if parent_id:
            payload["parent_id"] = parent_id

        r = self.connexion.patch(
            f"/api/label/group/{self.id}", data=orjson.dumps(payload)
        ).json()
        self.refresh(r)
        logger.info(f"{self} updated")

    @exception_handler
    @beartype
    def set_parent(self, parent: "LabelGroup") -> None:
        """Set a new parent for this (LabelGroup)

        Examples:
            ```python
            root = dataset_version.create_label_group("root")
            leaf = dataset_version.create_label_group("leaf")
            leaf.set_parent(root)
            ```

        Arguments:
            parent (LabelGroup): New parent of this (LabelGroup)
        """
        if parent.dataset_version_id != self.dataset_version_id:
            raise ValueError("LabelGroup must belong to the same DatasetVersion")
        return self.update(parent_id=parent.id)

    @exception_handler
    @beartype
    def get_parent(self) -> Optional["LabelGroup"]:
        """Get (LabelGroup) parent of this (LabelGroup). If no (LabelGroup) is set, return None.

        Examples:
            ```python
            root = dataset_version.create_label_group("root")
            leaf = dataset_version.create_label_group("leaf", root)
            group = leaf.get_parent()
            ```

        Returns:
            a (LabelGroup) if there is a parent, else None
        """
        if not self._parent_id:
            return None

        r = self.connexion.get(f"/api/label/group/{self._parent_id}").json()
        return LabelGroup(self.connexion, self._dataset_version_id, r)

    @exception_handler
    @beartype
    def delete(self) -> None:
        """Delete this (LabelGroup) from the platform.

        :warning: **DANGER ZONE**: Be very careful here!

        Examples:
            ```python
            group.delete()
            ```
        """
        self.connexion.delete(f"/api/label/group/{self.id}")
        logger.info(f"{self} deleted.")
