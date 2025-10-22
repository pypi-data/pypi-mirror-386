import logging
from typing import Optional
from uuid import UUID

from beartype import beartype

from picsellia.colors import Colors
from picsellia.decorators import exception_handler
from picsellia.sdk.connexion import Connexion
from picsellia.sdk.dao import Dao
from picsellia.sdk.downloadable import Downloadable
from picsellia.types.enums import DataProjectionType
from picsellia.types.schemas import (
    DataProjectionSchema,
)

logger = logging.getLogger("picsellia")


class DataProjection(Dao, Downloadable):
    def __init__(self, connexion: Connexion, data_id: UUID, data: dict):
        Dao.__init__(self, connexion, data)
        Downloadable.__init__(self)
        self._data_id = data_id

    def __str__(self):
        return f"{Colors.GREEN}Projection of data {self._data_id}{Colors.ENDC}"

    @property
    def data_id(self) -> UUID:
        """UUID of (Data) linked to this projection"""
        return self._data_id

    @property
    def name(self) -> Optional[str]:
        """Name of this (DataProjection). This can be None"""
        return self._name

    @property
    def object_name(self) -> Optional[str]:
        """Object name of this (DataProjection). If compute status is not DONE, this might be None."""
        return self._object_name

    @property
    def filename(self) -> Optional[str]:
        """Filename of this (DataProjection). If compute status is not DONE, this might be None."""
        return self._filename

    @property
    def type(self) -> DataProjectionType:
        """Type of this (DataProjection)"""
        return self._type

    @property
    def infos(self) -> Optional[dict]:
        """Infos of this (DataProjection). Can be None"""
        return self._infos

    @property
    def large(self) -> bool:
        return True

    @exception_handler
    @beartype
    def refresh(self, data: dict):
        schema = DataProjectionSchema(**data)
        self._url = schema.url
        self._name = schema.name
        self._object_name = schema.object_name
        self._filename = schema.filename
        self._infos = schema.infos
        self._type = schema.type
        return schema

    @exception_handler
    @beartype
    def sync(self) -> dict:
        r = self.connexion.get(f"/api/data/projection/{self.id}").json()
        self.refresh(r)
        return r

    @exception_handler
    @beartype
    def reset_url(self) -> str:
        """Reset url property of this (DataProjection) by calling platform.

        Returns:
            A url as a string of this Data.
        """
        self.sync()
        return self._url

    @exception_handler
    @beartype
    def delete(self) -> None:
        """Delete this projection from the platform.

        :warning: **DANGER ZONE**: Be very careful here!

        Examples:
            ```python
            projection.delete()
            ```
        """
        self.connexion.delete(f"/api/data/projection/{self.id}")
        logger.info(f"{self} deleted.")
