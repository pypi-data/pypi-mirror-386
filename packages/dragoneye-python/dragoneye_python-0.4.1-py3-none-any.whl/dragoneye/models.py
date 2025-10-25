from typing import Dict, Sequence

from pydantic import BaseModel

from dragoneye.types.common import (
    NormalizedBbox,
    PredictionTaskState,
    PredictionTaskUUID,
    PredictionType,
    TaxonID,
    TaxonPrediction,
)


class PredictionTaskStatusResponse(BaseModel):
    prediction_task_uuid: PredictionTaskUUID
    prediction_type: PredictionType
    status: PredictionTaskState


class ClassificationTraitRootPrediction(BaseModel):
    id: TaxonID
    name: str
    displayName: str
    taxons: Sequence[TaxonPrediction]


class ClassificationObjectPrediction(BaseModel):
    normalizedBbox: NormalizedBbox
    category: TaxonPrediction
    traits: Sequence[ClassificationTraitRootPrediction]


class ClassificationPredictImageResponse(BaseModel):
    predictions: Sequence[ClassificationObjectPrediction]
    prediction_task_uuid: PredictionTaskUUID


class ClassificationVideoObjectPrediction(ClassificationObjectPrediction):
    frame_id: str
    timestamp_microseconds: int


class ClassificationPredictVideoResponse(BaseModel):
    timestamp_us_to_predictions: Dict[
        int, Sequence[ClassificationVideoObjectPrediction]
    ]
    frames_per_second: int
    prediction_task_uuid: PredictionTaskUUID
