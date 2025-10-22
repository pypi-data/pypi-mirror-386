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
from picsellia.types.schemas import RectangleSchema
from picsellia.utils import filter_payload

logger = logging.getLogger("picsellia")


class Rectangle(Dao):
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
        """UUID of the (Annotation) holding this (Rectangle)"""
        return self._annotation_id

    @property
    def x(self) -> int:
        """Coordinates x of this (Rectangle)"""
        return self._x

    @property
    def y(self) -> int:
        """Coordinates y of this (Rectangle)"""
        return self._y

    @property
    def w(self) -> int:
        """Width of this (Rectangle)"""
        return self._w

    @property
    def h(self) -> int:
        """Height of this (Rectangle)"""
        return self._h

    @property
    def text(self) -> Optional[str]:
        """OCR text of this (Rectangle)"""
        return self._text

    @property
    def label(self) -> Label:
        """(Label) of this (Rectangle)"""
        return self._label

    def __str__(self):
        return f"{Colors.BLUE}Rectangle (x:{self.x},y:{self.y},w:{self.w},h:{self.h}) with label {self.label.name} on annotation {self.annotation_id} {Colors.ENDC} (id: {self.id})"

    @exception_handler
    @beartype
    def sync(self) -> dict:
        r = self.connexion.get(f"/api/rectangle/{self.id}").json()
        self.refresh(r)
        return r

    @exception_handler
    @beartype
    def refresh(self, data: dict) -> RectangleSchema:
        schema = RectangleSchema(**data)
        self._x = schema.x
        self._y = schema.y
        self._w = schema.w
        self._h = schema.h
        self._text = schema.text
        self._label = Label(
            self.connexion, self._dataset_version_id, schema.label.model_dump()
        )
        return schema

    @exception_handler
    @beartype
    def update(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        w: Optional[int] = None,
        h: Optional[int] = None,
        label: Optional[Label] = None,
        text: Optional[str] = None,
    ) -> None:
        """Update this rectangle with new coordinates or new label.

        Examples:
            ```python
            rect.update(x=10, label=label_car)
            ```

        Arguments:
            x (int, optional): New x coordinate of this (Rectangle). Defaults to None.
            y (int, optional): New y coordinate of this (Rectangle). Defaults to None.
            w (int, optional): New width of this (Rectangle). Defaults to None.
            h (int, optional): New height of this (Rectangle). Defaults to None.
            label (Label, optional): New label of this (Rectangle). Defaults to None.
            text (str, optional): New ocr text of this (Rectangle). Defaults to None.
        """
        payload = {"x": x, "y": y, "w": w, "h": h, "text": text}
        filtered_payload = filter_payload(payload)
        if label is not None:
            filtered_payload["label_id"] = label.id
        r = self.connexion.patch(
            f"/api/rectangle/{self.id}", data=orjson.dumps(filtered_payload)
        ).json()
        self.refresh(r)
        logger.info(f"{self} updated")

    @exception_handler
    @beartype
    def delete(self) -> None:
        """Delete this rectangle from the platform.

        :warning: **DANGER ZONE**: Be very careful here!

        Examples:
            ```python
            rect.delete()
            ```
        """
        self.connexion.delete(f"/api/rectangle/{self.id}")
        logger.info(f"{self} deleted.")
