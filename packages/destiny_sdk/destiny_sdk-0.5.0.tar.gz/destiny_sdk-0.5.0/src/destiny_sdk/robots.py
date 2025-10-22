"""Schemas that define inputs/outputs for robots."""

from enum import StrEnum, auto
from typing import Annotated, Any

from pydantic import UUID4, BaseModel, ConfigDict, Field, HttpUrl

from destiny_sdk.core import _JsonlFileInputMixIn
from destiny_sdk.enhancements import Enhancement


class RobotError(BaseModel):
    """A record of something going wrong with the robot."""

    message: Annotated[
        str,
        Field(
            description=(
                "Message which describes the error encountered during processing"
            )
        ),
    ]


class LinkedRobotError(_JsonlFileInputMixIn, RobotError):
    """
    A record of something going wrong when processing an individual reference.

    Used in results for batch requests - in single requests, the reference
    id is derived from the request id.
    """

    reference_id: UUID4 = Field(
        description="The ID of the reference which caused the error."
    )


class RobotResult(BaseModel):
    """Used to indicate to the repository that the robot has finished processing."""

    request_id: UUID4
    error: RobotError | None = Field(
        default=None,
        description="""
Error the robot encountered while creating enhancements. If this field is populated,
we assume the entire enhancement request or http request request failed,
rather than an individual reference.
If there was an error with processing an individual reference, it should be passed in
the result file and this field should be left as None. Vice-versa, if this field is
None, the repository will assume that the result file is ready for processing.
""",
    )


class RobotEnhancementBatchResult(BaseModel):
    """Used to indicate that the robot has finished processing a batch."""

    request_id: UUID4
    error: RobotError | None = Field(
        default=None,
        description="""
Error the robot encountered while creating enhancements. If this field is populated,
we assume the entire robot enhancement batch failed,
rather than an individual reference.
If there was an error with processing an individual reference, it should be passed in
the result file and this field should be left as None. Vice-versa, if this field is
None, the repository will assume that the result file is ready for processing.
""",
    )


class RobotResultValidationEntry(_JsonlFileInputMixIn, BaseModel):
    """A single entry in the validation result file for a batch enhancement request."""

    reference_id: UUID4 | None = Field(
        default=None,
        description=(
            "The ID of the reference which was enhanced. "
            "If this is empty, the EnhancementResultEntry could not be parsed."
        ),
    )
    error: str | None = Field(
        default=None,
        description=(
            "Error encountered during the enhancement process for this reference. "
            "If this is empty, the enhancement was successfully created."
        ),
    )


#: The result for a single reference when processed by an enhancement request.
#: This is a single entry in the result file.
EnhancementResultEntry = Annotated[
    Enhancement | LinkedRobotError,
    Field(),
]


class RobotRequest(BaseModel):
    """A batch enhancement request from the repo to a robot."""

    id: UUID4
    reference_storage_url: HttpUrl = Field(
        description="""
The URL at which the set of references are stored. The file is a jsonl
with each line formatted according to
:class:`Reference <libs.sdk.src.destiny_sdk.references.Reference>`, one
reference per line.
Each reference may have identifiers or enhancements attached, as
required by the robot.
If the URL expires, a new one can be generated using
``GET /enhancement-requests/{request_id}/``.
"""
    )
    result_storage_url: HttpUrl = Field(
        description="""
The URL at which the set of enhancements are to be stored. The file is to be a jsonl
with each line formatted according to
:class:`EnhancementResultEntry <libs.sdk.src.destiny_sdk.robots.EnhancementResultEntry>`.
If the URL expires, a new one can be generated using
``GET /enhancement-requests/{request_id}/``.
"""  # noqa: E501
    )
    extra_fields: dict | None = Field(
        default=None,
        description="Extra fields to pass to the robot. TBC.",
    )


class RobotEnhancementBatch(BaseModel):
    """A robot enhancement batch from the repo to a robot."""

    id: UUID4
    reference_storage_url: HttpUrl = Field(
        description="""
The URL at which the set of references are stored. The file is a jsonl
with each line formatted according to
:class:`Reference <libs.sdk.src.destiny_sdk.references.Reference>`, one
reference per line.
Each reference may have identifiers or enhancements attached, as
required by the robot.
If the URL expires, a new one can be generated using
``GET /robot-enhancement-batches/{batch_id}/``.
"""
    )
    result_storage_url: HttpUrl = Field(
        description="""
The URL at which the set of enhancements are to be stored. The file is to be a jsonl
with each line formatted according to
:class:`EnhancementResultEntry <libs.sdk.src.destiny_sdk.robots.EnhancementResultEntry>`.
If the URL expires, a new one can be generated using
``GET /robot-enhancement-batches/{batch_id}/``.
"""  # noqa: E501
    )
    extra_fields: dict | None = Field(
        default=None,
        description="Extra fields to pass to the robot. TBC.",
    )


class EnhancementRequestStatus(StrEnum):
    """The status of an enhancement request."""

    RECEIVED = auto()
    """Enhancement request has been received by the repo."""
    ACCEPTED = auto()
    """Enhancement request has been accepted by the robot."""
    PROCESSING = auto()
    """Enhancement request is being processed by the robot."""
    REJECTED = auto()
    """Enhancement request has been rejected by the robot."""
    PARTIAL_FAILED = auto()
    """Some enhancements failed to create."""
    FAILED = auto()
    """All enhancements failed to create."""
    IMPORTING = auto()
    """Enhancements have been received by the repo and are being imported."""
    INDEXING = auto()
    """Enhancements have been imported and are being indexed."""
    INDEXING_FAILED = auto()
    """Enhancements have been imported but indexing failed."""
    COMPLETED = auto()
    """All enhancements have been created."""


class _EnhancementRequestBase(BaseModel):
    """
    Base enhancement request class.

    A enhancement request is a request to create one or more enhancements.
    """

    robot_id: UUID4 = Field(
        description="The robot to be used to create the enhancements."
    )
    reference_ids: list[UUID4] = Field(
        description="The IDs of the references to be enhanced."
    )
    source: str | None = Field(
        default=None,
        description="The source of the batch enhancement request.",
    )


class EnhancementRequestIn(_EnhancementRequestBase):
    """The model for requesting multiple enhancements on specific references."""


class EnhancementRequestRead(_EnhancementRequestBase):
    """Core batch enhancement request class."""

    id: UUID4
    request_status: EnhancementRequestStatus = Field(
        description="The status of the request to create enhancements",
    )
    reference_data_url: HttpUrl | None = Field(
        default=None,
        description="""
The URL at which the set of references are stored. The file is a jsonl with each line
formatted according to
:class:`Reference <libs.sdk.src.destiny_sdk.references.Reference>`.
, one reference per line.
Each reference may have identifiers or enhancements attached, as
required by the robot.
If the URL expires, a new one can be generated using
``GET /enhancement-requests/{request_id}/``.
        """,
    )
    result_storage_url: HttpUrl | None = Field(
        default=None,
        description="""
The URL at which the set of enhancements are stored. The file is to be a jsonl
with each line formatted according to
:class:`EnhancementResultEntry <libs.sdk.src.destiny_sdk.robots.EnhancementResultEntry>`.
This field is only relevant to robots.
If the URL expires, a new one can be generated using
``GET /enhancement-requests/{request_id}/``.
        """,  # noqa: E501
    )
    validation_result_url: HttpUrl | None = Field(
        default=None,
        description="""
The URL at which the result of the enhancement request is stored.
This file is a txt file, one line per reference, with either an error
or a success message.
If the URL expires, a new one can be generated using
``GET /enhancement-requests/{request_id}/``.
        """,
    )
    error: str | None = Field(
        default=None,
        description="Error encountered during the enhancement process. This "
        "is only used if the entire enhancement request failed, rather than an "
        "individual reference. If there was an error with processing an individual "
        "reference, it is passed in the validation result file.",
    )


class _RobotEnhancementBatchBase(BaseModel):
    """
    Base robot enhancement batch class.

    A robot enhancement batch is a batch of pending enhancements the robot has picked up
    for processing.
    """

    robot_id: UUID4 = Field(
        description="The robot to be used to create the enhancements."
    )
    source: str | None = Field(
        default=None,
        description="The source of the batch enhancement request.",
    )


class RobotEnhancementBatchRead(_RobotEnhancementBatchBase):
    """Core robot enhancement batch class."""

    id: UUID4
    reference_data_url: HttpUrl | None = Field(
        default=None,
        description="""
The URL at which the set of references are stored. The file is a jsonl with each line
formatted according to
:class:`Reference <libs.sdk.src.destiny_sdk.references.Reference>`.
, one reference per line.
Each reference may have identifiers or enhancements attached, as
required by the robot.
If the URL expires, a new one can be generated using
``GET /enhancement-requests/{request_id}/``.
        """,
    )
    result_storage_url: HttpUrl | None = Field(
        default=None,
        description="""
The URL at which the set of enhancements are stored. The file is to be a jsonl
with each line formatted according to
:class:`EnhancementResultEntry <libs.sdk.src.destiny_sdk.robots.EnhancementResultEntry>`.
This field is only relevant to robots.
If the URL expires, a new one can be generated using
``GET /robot-enhancement-batches/{batch_id}/``.
        """,  # noqa: E501
    )
    validation_result_url: HttpUrl | None = Field(
        default=None,
        description="""
The URL at which the result of the enhancement request is stored.
This file is a txt file, one line per reference, with either an error
or a success message.
If the URL expires, a new one can be generated using
``GET /robot-enhancement-batches/{batch_id}/``.
        """,
    )
    error: str | None = Field(
        default=None,
        description="Error encountered during the enhancement process. This "
        "is only used if the entire enhancement batch failed, rather than an "
        "individual reference. If there was an error with processing an individual "
        "reference, it is passed in the validation result file.",
    )


class _RobotBase(BaseModel):
    """
    Base Robot class.

    A Robot is a provider of enhancements to destiny repository
    """

    model_config = ConfigDict(extra="forbid")  # Forbid extra fields on robot models

    name: str = Field(description="The name of the robot, must be unique.")
    description: str = Field(
        description="Description of the enhancement the robot provides."
    )
    owner: str = Field(description="The owner/publisher of the robot.")


class RobotIn(_RobotBase):
    """The model for registering a new robot."""


class Robot(_RobotBase):
    """Then model for a registered robot."""

    id: UUID4 = Field(
        description="The id of the robot provided by destiny repository. "
        "Used as the client_id when sending HMAC authenticated requests."
    )


class ProvisionedRobot(Robot):
    """
    The model for a provisioned robot.

    Used only when a robot is initially created,
    or when cycling a robot's client_secret.
    """

    client_secret: str = Field(
        description="The client secret of the robot, used as the secret key "
        "when sending HMAC authenticated requests."
    )


class _RobotAutomationBase(BaseModel):
    """Base Robot Automation class."""

    robot_id: UUID4 = Field(
        description="The ID of the robot that will be used to enhance the reference."
    )
    query: dict[str, Any] = Field(
        description="The percolator query that will be used to match references "
        " or enhancements against."
    )


class RobotAutomationIn(_RobotAutomationBase):
    """
    Automation model for a robot.

    This is used as a source of truth for an Elasticsearch index that percolates
    references or enhancements against the queries. If a query matches, a request
    is sent to the specified robot to perform the enhancement.
    """


class RobotAutomation(_RobotAutomationBase):
    """
    Core Robot Automation class.

    This is used as a source of truth for an Elasticsearch index that percolates
    references or enhancements against the queries. If a query matches, a request
    is sent to the specified robot to perform the enhancement.
    """

    id: UUID4 = Field(
        description="The ID of the robot automation.",
    )
