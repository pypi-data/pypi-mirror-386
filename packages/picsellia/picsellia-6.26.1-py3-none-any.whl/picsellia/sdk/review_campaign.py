import logging
import os
from datetime import date
from typing import Optional
from uuid import UUID

from beartype import beartype

from picsellia.colors import Colors
from picsellia.decorators import exception_handler
from picsellia.sdk.campaign.abstract_campaign import AbstractCampaign
from picsellia.sdk.connexion import Connexion
from picsellia.sdk.dao import Dao
from picsellia.sdk.job import Job
from picsellia.sdk.review_campaign_step import ReviewCampaignStep
from picsellia.types.enums import CampaignStepType, ObjectDataType, WorkerType
from picsellia.types.schemas import ReviewCampaignSchema

logger = logging.getLogger("picsellia")


class ReviewCampaign(AbstractCampaign[ReviewCampaignStep]):
    _base_path = "/api/campaigns/review"
    _allowed_step_types = [CampaignStepType.REVIEW, CampaignStepType.QUALITY_CONTROL]
    _worker_type = WorkerType.DEPLOYMENT

    def __init__(self, connexion: Connexion, data: dict):
        Dao.__init__(self, connexion, data)

    def __str__(self):
        return f"{Colors.GREEN}Review Campaign {Colors.ENDC} for deployment {self.deployment_id} (id: {self.id})"

    @property
    def deployment_id(self) -> UUID:
        """UUID of the (Deployment) of this campaign"""
        return self._deployment_id

    @exception_handler
    @beartype
    def refresh(self, data: dict):
        schema = ReviewCampaignSchema(**data)
        self._deployment_id = schema.deployment_id
        return schema

    @exception_handler
    @beartype
    def update(
        self,
        description: Optional[str] = None,
        instructions_object_name: Optional[str] = None,
        instructions_text: Optional[str] = None,
        end_date: Optional[date] = None,
        auto_add_new_assets: Optional[bool] = None,
        auto_close_on_completion: Optional[bool] = None,
        default_entry_step: Optional[ReviewCampaignStep] = None,
    ) -> None:
        """Update this campaign parameters

        Examples:
            ```python
            foo_campaign.update(description="Yet another campaign")
            ```

        Arguments:
            description (str, optional): Description of the campaign. Defaults to None.
            instructions_object_name (str, optional): Instructions file object name stored on S3. Defaults to None.
            instructions_text (str, optional): Instructions text. Defaults to None.
            end_date (date, optional): End date of the campaign. Defaults to None.
            auto_add_new_assets (bool, optional):
                If true, new assets of this dataset will be added as a task in the campaign.  Defaults to None.
            auto_close_on_completion (bool, optional):
                If true, campaign will be close when all tasks will be done. Defaults to None.
            default_entry_step (Step, optional): Step where tasks will be created for new assets.
        """
        return self._update(
            description,
            instructions_object_name,
            instructions_text,
            end_date,
            auto_add_new_assets,
            auto_close_on_completion,
            default_entry_step,
            annotated_entry_step=None,
        )

    @exception_handler
    @beartype
    def upload_instructions_file(self, path: str) -> None:
        """Upload instructions for this campaign

        Examples:
            ```python
            foo_campaign.upload_instructions_file("/path/to/file.pdf")
            ```

        Arguments:
            path (str): Path of instructions file

        """
        instruction_file_name = os.path.basename(path)
        object_name = self.connexion.generate_deployment_object_name(
            instruction_file_name,
            ObjectDataType.REVIEW_CAMPAIGN_FILE,
            deployment_id=self.deployment_id,
        )
        self.connexion.upload_file(object_name, path)
        self.update(instructions_object_name=object_name)

    def _build_step(self, data: dict):
        return ReviewCampaignStep(self.connexion, data, self._id)

    @exception_handler
    @beartype
    def sync_assets(self) -> Job:
        """This will create tasks and assignments for assets that are not in the campaign yet.

        Your already reviewed assets will NOT be added to this campaign.

        Returns:
            a Job, that you can wait for.
        """
        return self._sync_assets(None)
