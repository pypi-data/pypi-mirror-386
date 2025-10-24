from datetime import date
from pydantic import BaseModel, Field
from typing import Annotated
from uuid import UUID
from maleo.enums.identity import Gender
from maleo.enums.medical import MedicalService
from maleo.enums.status import DataStatus as DataStatusEnum, SimpleDataStatusMixin
from maleo.schemas.mixins.identity import DataIdentifier
from maleo.schemas.mixins.timestamp import DataTimestamp
from maleo.types.any import ListOfAny
from maleo.types.string import OptStr
from maleo.types.uuid import OptUUID
from .enums.inference import InferenceType


class RecordCoreDTO(
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    organization_id: Annotated[OptUUID, Field(None, description="Organization ID")] = (
        None
    )
    user_id: Annotated[UUID, Field(..., description="User ID")]
    medical_service: Annotated[
        MedicalService, Field(..., description="Medical service")
    ]
    name: Annotated[str, Field(..., description="Name", max_length=200)]
    date_of_birth: Annotated[date, Field(..., description="Date of Birth")]
    gender: Annotated[Gender, Field(..., description="Gender")]
    finding: Annotated[str, Field(..., description="Finding")]
    impression: Annotated[str, Field(..., description="Impression")]
    recommendation: Annotated[OptStr, Field(None, description="Recommendation")] = None
    filename: Annotated[str, Field(..., description="File's name")]


class RecordCoreDTOMixin(BaseModel):
    record: Annotated[RecordCoreDTO, Field(..., description="Record")]


class InferenceCoreDTO(
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    organization_id: Annotated[OptUUID, Field(None, description="Organization ID")] = (
        None
    )
    user_id: Annotated[UUID, Field(..., description="User ID")]
    medical_service: Annotated[
        MedicalService, Field(..., description="Medical service")
    ]
    name: Annotated[str, Field(..., description="Name", max_length=200)]
    date_of_birth: Annotated[date, Field(..., description="Date of Birth")]
    gender: Annotated[Gender, Field(..., description="Gender")]
    type: Annotated[InferenceType, Field(..., description="Inference's type")]
    duration: Annotated[float, Field(0.0, description="Inference's duration")] = 0.0
    output: Annotated[ListOfAny, Field(..., description="Inference's output")]


class InferenceCoreDTOMixin(BaseModel):
    inference: Annotated[InferenceCoreDTO, Field(..., description="Inference")]


class RecordInferenceDTO(
    InferenceCoreDTOMixin,
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class RecordInferencesDTOMixin(BaseModel):
    inferences: Annotated[
        list[RecordInferenceDTO],
        Field(list[RecordInferenceDTO](), description="Inferences"),
    ] = list[RecordInferenceDTO]()


class RecordCompleteDTO(RecordInferencesDTOMixin, RecordCoreDTO):
    pass


class InferenceRecordDTO(
    RecordCoreDTOMixin,
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


class InferenceRecordsDTOMixin(BaseModel):
    records: Annotated[
        list[InferenceRecordDTO],
        Field(list[InferenceRecordDTO](), description="Records"),
    ] = list[InferenceRecordDTO]()


class InferenceCompleteDTO(InferenceRecordsDTOMixin, InferenceCoreDTO):
    pass


class RecordAndInferenceDTO(
    InferenceCoreDTOMixin,
    RecordCoreDTOMixin,
    SimpleDataStatusMixin[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass
