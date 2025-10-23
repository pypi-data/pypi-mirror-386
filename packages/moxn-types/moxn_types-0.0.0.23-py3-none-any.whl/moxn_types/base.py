from datetime import datetime
from typing import (
    Any,
    ClassVar,
    Generic,
    Literal,
    Protocol,
    Sequence,
    TypeVar,
    runtime_checkable,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from moxn_types.content import Author, MessageRole

T = TypeVar("T")
U = TypeVar("U")


class VersionRef(BaseModel):
    """Explicitly specify either branch or commit for version reference."""

    branch_name: str | None = None
    commit_id: str | None = None

    @model_validator(mode="after")
    def validate_xor(self):
        """Ensure exactly one of branch_name or commit_id is provided."""
        if bool(self.branch_name) == bool(self.commit_id):
            raise ValueError("Exactly one of branch_name or commit_id must be provided")
        return self


class GitTrackedEntity(BaseModel):
    """Base class for entities tracked in git-like system."""

    branch_id: UUID | None = Field(
        None, alias="branchId", description="Current branch name/ID"
    )
    commit_id: UUID | None = Field(
        None, alias="commitId", description="Current commit SHA (null = working state)"
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_version_xor(self):
        """Ensure exactly one of branch_id or commit_id is provided."""
        # Temporarily disabled for backend compatibility
        # TODO: Re-enable once backend is fixed to send proper data
        # if bool(self.branch_id) == bool(self.commit_id):
        #     raise ValueError("Exactly one of branch_id or commit_id must be provided")
        return self


class Branch(BaseModel):
    """Named pointer to a commit."""

    id: UUID
    name: str
    head_commit_id: UUID | None = Field(None, alias="headCommitId")  # Commit SHA

    model_config = ConfigDict(populate_by_name=True)


class Commit(BaseModel):
    """Represents a snapshot of all entities at a point in time."""

    id: str  # Commit SHA hash
    message: str
    created_at: datetime | None = Field(None, alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class MoxnSchemaMetadata(BaseModel):
    """Metadata embedded in JSON Schema x-moxn-metadata field."""

    schema_id: UUID
    schema_version_id: UUID | None = None
    prompt_id: UUID
    prompt_version_id: UUID | None = None
    task_id: UUID
    branch_id: UUID | None = None  # Can be None in API responses
    commit_id: str | None = None

    model_config = {"populate_by_name": True}


@runtime_checkable
class RenderableModel(Protocol):
    moxn_schema_metadata: ClassVar[MoxnSchemaMetadata]

    def model_dump(
        self,
        *,
        mode: Literal["json", "python"] | str = "python",
        include: Any = None,
        exclude: Any = None,
        context: dict[str, Any] | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        serialize_as_any: bool = False,
    ) -> Any: ...

    def render(self, **kwargs: Any) -> Any: ...


# BaseHeaders removed - legacy authentication pattern


class MessageBase(GitTrackedEntity, Generic[T]):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    author: Author = Field(default=Author.HUMAN)  # Default to HUMAN
    role: MessageRole
    blocks: Sequence[Sequence[T]]
    task_id: UUID | None = Field(None, alias="taskId")


class BaseSchema(GitTrackedEntity):
    id: UUID
    name: str
    description: str | None = None
    exportedJSON: str


class BasePrompt(GitTrackedEntity, Generic[T, U]):
    id: UUID
    name: str
    description: str | None = None
    task_id: UUID = Field(..., alias="taskId")
    messages: Sequence[T]
    input_schema: U = Field(..., alias="inputSchema")
    message_order: list[UUID] | None = Field(None, alias="messageOrder")


class BaseTask(GitTrackedEntity, Generic[T]):
    id: UUID
    name: str
    description: str | None = None
    prompts: Sequence[T]
    definitions: dict[str, Any] = Field(default_factory=dict)
    branches: list[Branch] = Field(default_factory=list)
    last_commit: Commit | None = Field(None, alias="lastCommit")


# Response types for API operations
class BranchHeadResponse(BaseModel):
    """Response when resolving a branch to its head commit."""

    branch_id: str = Field(alias="branchId")  # Branch UUID
    branch_name: str = Field(alias="branchName")
    task_id: UUID = Field(alias="taskId")
    head_commit_id: str | None = Field(alias="headCommitId")  # Commit SHA
    parent_commit_id: str | None = Field(
        None, alias="parentCommitId"
    )  # Parent commit SHA
    effective_commit_id: str = Field(alias="effectiveCommitId")  # The commit ID to use
    has_uncommitted_changes: bool = Field(alias="hasUncommittedChanges")
    last_committed_at: datetime | None = Field(None, alias="lastCommittedAt")
    is_default: bool = Field(alias="isDefault")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class CommitInfoResponse(BaseModel):
    """Response with commit information."""

    commit: Commit
    branch_name: str | None = None

    model_config = ConfigDict(populate_by_name=True)
