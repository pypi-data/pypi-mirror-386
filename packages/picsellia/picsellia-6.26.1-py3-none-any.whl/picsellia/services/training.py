from typing import Optional
from uuid import UUID

from picsellia.exceptions import NoDataError
from picsellia.sdk.artifact import Artifact
from picsellia.sdk.connexion import Connexion
from picsellia.sdk.evaluation import MultiEvaluation
from picsellia.sdk.log import Log
from picsellia.services.lister.evaluation_lister import (
    EvaluationFilter,
    EvaluationLister,
)


class TrainingService:
    """This service is used by Experiment and FastTraining dao to fetch evaluations, artifacts and logs."""

    def __init__(self, connexion: Connexion, experiment_id: UUID):
        self.connexion = connexion
        self.experiment_id = experiment_id

    def list_evaluations(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[list[str]] = None,
        q: Optional[str] = None,
    ) -> MultiEvaluation:
        filters = EvaluationFilter.model_validate(
            {"limit": limit, "offset": offset, "order_by": order_by, "query": q}
        )
        evaluations = EvaluationLister(self.connexion, self.experiment_id).list_items(
            filters
        )

        if len(evaluations) == 0:
            raise NoDataError(
                "No evaluation done by this training found with this query"
            )

        return MultiEvaluation(self.connexion, self.experiment_id, evaluations)

    def list_logs(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[list[str]] = None,
    ) -> list[Log]:
        params = {"limit": limit, "offset": offset, "order_by": order_by}
        r = self.connexion.get(
            f"/api/experiment/{self.experiment_id}/logs/extended", params=params
        ).json()
        return [Log(self.connexion, item) for item in r["items"]]

    def get_log(self, name: str) -> Log:
        params = {"name": name}
        r = self.connexion.get(
            f"/api/experiment/{self.experiment_id}/logs/find", params=params
        ).json()
        return Log(self.connexion, r)

    def list_artifacts(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[list[str]] = None,
    ) -> list[Artifact]:
        params = {"limit": limit, "offset": offset, "order_by": order_by}
        r = self.connexion.get(
            f"/api/experiment/{self.experiment_id}/artifacts", params=params
        ).json()
        return [Artifact(self.connexion, item) for item in r["items"]]

    def get_parameters(self) -> dict:
        return self.get_log("parameters").data
