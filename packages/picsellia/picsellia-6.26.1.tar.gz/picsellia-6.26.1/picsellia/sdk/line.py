import logging
from typing import Optional
from uuid import UUID

import orjson
from beartype import beartype

from picsellia.colors import Colors
from picsellia.decorators import exception_handler
from picsellia.sdk.connexion import Connexion
from picsellia.sdk.dao import Dao
from picsellia.sdk.label import Label
from picsellia.types.schemas import LineSchema

logger = logging.getLogger("picsellia")


class Line(Dao):
    def __init__(
        self,
        connexion: Connexion,
        dataset_version_id: UUID,
        annotation_id: UUID,
        data: dict,
    ) -> None:
        self._dataset_version_id = dataset_version_id
        self._annotation_id = annotation_id
        Dao.__init__(self, connexion, data)

    @property
    def annotation_id(self) -> UUID:
        """UUID of (Annotation) holding this (Line)"""
        return self._annotation_id

    @property
    def coords(self) -> list[list[int]]:
        """Coords of this (Line)"""
        return self._coords

    @property
    def label(self) -> Label:
        """(Label) of this (Line)"""
        return self._label

    @property
    def text(self) -> Optional[str]:
        """OCR text of this (Polygon)"""
        return self._text

    def __str__(self):
        return f"{Colors.BLUE}Line ({len(self.coords)} points) with label {self.label.name} on annotation {self.annotation_id} {Colors.ENDC} (id: {self.id})"

    @exception_handler
    @beartype
    def sync(self) -> dict:
        r = self.connexion.get(f"/api/line/{self.id}").json()
        self.refresh(r)
        return r

    @exception_handler
    @beartype
    def refresh(self, data: dict) -> LineSchema:
        schema = LineSchema(**data)
        self._coords = schema.coords
        self._text = schema.text
        self._label = Label(
            self.connexion, self._dataset_version_id, schema.label.model_dump()
        )
        return schema

    @exception_handler
    @beartype
    def update(
        self,
        coords: Optional[list] = None,
        label: Optional[Label] = None,
        text: Optional[str] = None,
    ) -> None:
        """Update this line with new coords or new label.

        Examples:
            ```python
            line.update(coords=[[0, 0], [0, 1], [1, 1]])
            ```

        Arguments:
            coords (List, optional): New coords of this (Line). Defaults to None.
            label (Label, optional): New label of this (Line). Defaults to None.
            text (str, optional): New ocr text of this (Line). Defaults to None.
        """
        payload = {}
        if coords is not None:
            payload["line"] = coords
        if label is not None:
            payload["label_id"] = label.id
        if text is not None:
            payload["text"] = text
        assert payload != {}, "You can't update this line with no data to update"
        r = self.connexion.patch(
            f"/api/line/{self.id}", data=orjson.dumps(payload)
        ).json()
        self.refresh(r)
        logger.info(f"{self} updated")

    @exception_handler
    @beartype
    def delete(self) -> None:
        """Delete this line from the platform.

        :warning: **DANGER ZONE**: Be very careful here!

        Examples:
            ```python
            line.delete()
            ```
        """
        self.connexion.delete(f"/api/line/{self.id}")
        logger.info(f"{self} deleted.")
