import abc
import logging
from datetime import date
from typing import ClassVar, Generic, Optional, TypeVar, Union
from uuid import UUID

from beartype import beartype
from orjson import orjson

from picsellia.decorators import exception_handler
from picsellia.sdk.campaign.abstract_step import AbstractCampaignStep
from picsellia.sdk.dao import Dao
from picsellia.sdk.job import Job
from picsellia.sdk.user import User
from picsellia.sdk.worker import Worker
from picsellia.services.campaign import parse_user_weights_to_assignees
from picsellia.types.enums import CampaignStepType, WorkerType
from picsellia.utils import filter_payload

logger = logging.getLogger("picsellia")

TCampaignStep = TypeVar("TCampaignStep", bound=AbstractCampaignStep)


class AbstractCampaign(Dao, abc.ABC, Generic[TCampaignStep]):
    _base_path: ClassVar[str]
    _allowed_step_types: ClassVar[list[CampaignStepType]]
    _worker_type: ClassVar[WorkerType]

    @exception_handler
    @beartype
    def sync(self) -> dict:
        r = self.connexion.get(f"{self._base_path}/{self.id}").json()
        self.refresh(r)
        return r

    @exception_handler
    @beartype
    def delete(self) -> None:
        """Delete a campaign.

        :warning: **DANGER ZONE**: Be very careful here!

        It will remove this campaign from our database, all tasks and assignments will be removed.
        This will not delete annotations, reviews and assets.

        Examples:
            ```python
            foo_campaign.delete()
            ```
        """
        self.connexion.delete(f"{self._base_path}/{self.id}")
        logger.info(f"{self} deleted")

    def _update(
        self,
        description: Optional[str] = None,
        instructions_object_name: Optional[str] = None,
        instructions_text: Optional[str] = None,
        end_date: Optional[date] = None,
        auto_add_new_assets: Optional[bool] = None,
        auto_close_on_completion: Optional[bool] = None,
        default_entry_step: Optional[TCampaignStep] = None,
        annotated_entry_step: Optional[TCampaignStep] = None,
    ):
        if default_entry_step and default_entry_step.campaign_id != self.id:
            raise ValueError("Given default entry step must be in this campaign")

        if annotated_entry_step and annotated_entry_step.campaign_id != self.id:
            raise ValueError("Given annotated entry step must be in this campaign")

        payload = {
            "description": description,
            "instructions_object_name": instructions_object_name,
            "instructions_text": instructions_text,
            "end_date": end_date,
            "auto_add_new_assets": auto_add_new_assets,
            "auto_close_on_completion": auto_close_on_completion,
        }

        if default_entry_step:
            payload["default_entry_step_id"] = default_entry_step.id

        if annotated_entry_step:
            payload["annotated_entry_step_id"] = annotated_entry_step.id

        filtered_payload = filter_payload(payload)
        r = self.connexion.patch(
            f"{self._base_path}/{self.id}", data=orjson.dumps(filtered_payload)
        ).json()
        self.refresh(r)
        logger.info(f"{self} updated")

    @exception_handler
    @beartype
    def add_step(
        self,
        name: str,
        type: Union[CampaignStepType, str],
        description: Optional[str] = None,
        assignees: Optional[
            list[tuple[Union[User, UUID, Worker], Union[float, int]]]
        ] = None,
        order: Optional[int] = None,
        sample_rate: Optional[float] = None,
    ) -> TCampaignStep:
        """Add a step on this campaign.

        `assignees` changed signature in 6.24, we now except a User or a user UUID.
        Worker will still be accepted until 6.26

        Examples:
            ```python
            users = foo_dataset.list_users()
            # In first step, 2 over 3 annotation task will be assigned to user 1, third one is going to user 0
            foo_campaign.add_step(
                name="annotation-step",
                type="ANNOTATION",
                description="annotation step",
                assignees=[(users[0], 1.0), (users[1], 2.0)]
            )
            # In second step, all review task will be assigned to user 2
            foo_campaign.add_step(
                name="review-step",
                type="REVIEW",
                description="review step",
                assignees=[(users[2], 1)]
            )
            ```
        Arguments:
            name (str): name of the step
            type (str or CampaignStepType): Type of the step: can be ANNOTATION or REVIEW
            description (str, optional): Description of the step. Defaults to None.
            assignees (list of tuple of (user or UUID), float, optional): Can be used to assign users to this step.
                Defaults to None.
            order (int, optional): Index where to insert the step in the workflow, the step will be appended at the end
                if nothing is specified. Defaults to None.
            sample_rate (float, optional): sample rate of this step. Defaults to None.
        Returns:
            dict, data of this step
        """
        campaign_step_type = CampaignStepType.validate(type)
        if campaign_step_type not in self._allowed_step_types:
            raise ValueError(
                f"Campaign step type must be in {self._allowed_step_types}"
            )

        payload = {
            "name": name,
            "type": campaign_step_type,
            "description": description,
            "order": order,
            "sample_rate": sample_rate,
        }
        if assignees:
            payload["assignees"] = parse_user_weights_to_assignees(assignees)

        r = self.connexion.post(
            f"{self._base_path}/{self.id}/steps",
            data=orjson.dumps(payload),
        ).json()
        logger.info(f"Step {name} has been added to this campaign")
        return self._build_step(r)

    @abc.abstractmethod
    def _build_step(self, data: dict):
        pass

    @exception_handler
    @beartype
    def list_steps(self) -> list[TCampaignStep]:
        """List all the steps of this campaign.

        Returns:
            a list of steps of this campaign as python dict
        """
        r = self.connexion.get(f"{self._base_path}/{self.id}/steps").json()
        return [self._build_step(item) for item in r["items"]]

    @exception_handler
    @beartype
    def _sync_assets(
        self, existing_annotations_step_id: Union[str, UUID, None] = None
    ) -> Job:
        r = self.connexion.get(
            f"{self._base_path}/{self.id}/assignments/sync/available"
        ).json()
        if "is_sync_available" in r and r["is_sync_available"] is False:
            reason = r["reason"]
            raise ValueError(f"Sync not available because {reason}")

        item_count = r["unsynced_item_count"]

        payload = {}
        if existing_annotations_step_id:
            payload["existing_annotations_step_id"] = existing_annotations_step_id

        r = self.connexion.post(
            f"{self._base_path}/{self.id}/assignments/sync",
            data=orjson.dumps(payload),
        ).json()
        self.refresh(r["campaign"])

        logger.info(
            f"Sync job is starting, {item_count} assets will be added to the campaign."
        )
        return Job(self.connexion, r["job"], version=2)
