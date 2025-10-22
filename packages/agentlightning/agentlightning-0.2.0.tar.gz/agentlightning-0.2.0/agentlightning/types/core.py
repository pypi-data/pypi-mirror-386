# Copyright (c) Microsoft. All rights reserved.

"""Core data models shared across Agent Lightning components."""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Protocol,
    SupportsIndex,
    TypeVar,
    Union,
    cast,
)

from opentelemetry.sdk.trace import ReadableSpan
from pydantic import BaseModel, Field, model_validator

from .tracer import Span

if TYPE_CHECKING:
    from agentlightning.litagent import LitAgent
    from agentlightning.runner.base import Runner
    from agentlightning.tracer.base import Tracer

__all__ = [
    "Triplet",
    "RolloutLegacy",
    "Task",
    "TaskInput",
    "TaskIfAny",
    "RolloutRawResultLegacy",
    "RolloutRawResult",
    "RolloutMode",
    "GenericResponse",
    "ParallelWorkerBase",
    "Dataset",
    "AttemptStatus",
    "RolloutStatus",
    "RolloutConfig",
    "Rollout",
    "Attempt",
    "AttemptedRollout",
    "Hook",
]

T_co = TypeVar("T_co", covariant=True)


class Triplet(BaseModel):
    """Single interaction turn captured during reinforcement learning."""

    prompt: Any
    response: Any
    reward: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RolloutLegacy(BaseModel):
    """Legacy reporting payload exchanged with the deprecated HTTP server.

    !!! warning "Deprecated"
        Use [`Rollout`][agentlightning.Rollout] instead.
    """

    rollout_id: str

    # Echoing the input task
    task: Optional[Task] = None

    # Primary, high-level feedback
    final_reward: Optional[float] = None

    # Structured, sequential feedback for RL-style optimization
    triplets: Optional[List[Triplet]] = None

    # Optional, rich-context data for deep analysis
    trace: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="A list of spans that conform to the OpenTelemetry JSON format. "
        "Users of the opentelemetry-sdk can generate this by calling "
        "json.loads(readable_span.to_json()).",
    )
    logs: Optional[List[str]] = None

    # A bucket for any other relevant information
    metadata: Dict[str, Any] = Field(default_factory=dict)


RolloutStatus = Literal[
    "queuing",  # initial status
    "preparing",  # after the trace is claimed
    "running",  # after receiving the first trace
    "failed",  # crashed
    "succeeded",  # status OK
    "cancelled",  # cancelled by user (or watchdog)
    "requeuing",  # retrying
]
"""The status of a rollout."""

AttemptStatus = Literal[
    # A status is essentially a process.
    # It should not have scheduling/management statuses like "queuing" or "cancelled".
    "preparing",
    "running",
    "failed",
    "succeeded",
    "unresponsive",  # the worker has not reported results for a while
    "timeout",  # the worker has been emitting new logs, but have been working on the task for too long
]
"""The status of an attempt."""

RolloutMode = Literal["train", "val", "test"]
"""Possible rollout modes."""


class Attempt(BaseModel):
    """Execution attempt for a rollout, including metadata for retries."""

    rollout_id: str
    """The rollout which this attempt belongs to."""
    attempt_id: str
    """The universal id for current attempt."""
    sequence_id: int
    """The sequence number of the attempt, starting from 1."""
    start_time: float
    """The time when the attempt has started."""
    end_time: Optional[float] = None
    """The time when the attempt has ended."""
    status: AttemptStatus = "preparing"
    """The status of the attempt."""
    worker_id: Optional[str] = None
    """The rollout worker which is executing this attempt."""

    last_heartbeat_time: Optional[float] = None
    """The last time when the worker has reported progress (i.e., a span)."""

    metadata: Optional[Dict[str, Any]] = None
    """A bucket for any other relevant information."""


class RolloutConfig(BaseModel):
    """Configuration controlling rollout retries and timeouts."""

    timeout_seconds: Optional[float] = None
    """The timeout for the rollout, in seconds. None indicates no timeout."""
    unresponsive_seconds: Optional[float] = None
    """The unresponsive timeout for the rollout, in seconds. None indicates no unresponsive timeout."""
    max_attempts: int = Field(default=1, ge=1)
    """The maximum number of attempts for the rollout, including the first attempt."""
    retry_condition: List[AttemptStatus] = Field(default_factory=cast(Callable[[], List[AttemptStatus]], list))
    """The list of statuses that should trigger a retry."""


class Rollout(BaseModel):
    rollout_id: str
    """Unique identifier for the rollout."""

    input: TaskInput
    """Task input used to generate the rollout."""

    # Time to track the lifecycle of the rollout
    start_time: float
    """Timestamp when the rollout started."""
    end_time: Optional[float] = None
    """Timestamp when the rollout ended."""

    mode: Optional[RolloutMode] = None
    """Execution mode such as `"train"`, `"val"` or `"test"`. See [`RolloutMode`][agentlightning.RolloutMode]."""
    resources_id: Optional[str] = None
    """Identifier of the resources required to execute the rollout."""

    status: RolloutStatus = "queuing"
    """Latest status emitted by the controller."""

    config: RolloutConfig = Field(default_factory=RolloutConfig)
    """Retry and timeout configuration associated with the rollout."""

    metadata: Optional[Dict[str, Any]] = None
    """Additional metadata attached to the rollout."""


class AttemptedRollout(Rollout):
    """Rollout paired with the currently active attempt."""

    attempt: Attempt
    """The attempt that is currently processing the rollout."""

    @model_validator(mode="after")
    def check_consistency(self) -> AttemptedRollout:
        if self.attempt.rollout_id != self.rollout_id:
            raise ValueError("Inconsistent rollout_id between Rollout and Attempt")
        return self


TaskInput = Any
"""Task input type. Accepts arbitrary payloads."""


class Task(BaseModel):
    """Rollout request served to client agents.

    !!! warning "Deprecated"
        The legacy HTTP client/server stack still uses this model. Prefer
        [`LightningStore`][agentlightning.LightningStore] APIs for new workflows.
    """

    rollout_id: str
    input: TaskInput

    mode: Optional[RolloutMode] = None
    resources_id: Optional[str] = None

    # Optional fields for tracking task lifecycle
    create_time: Optional[float] = None
    last_claim_time: Optional[float] = None
    num_claims: Optional[int] = None

    # Allow additional metadata fields
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskIfAny(BaseModel):
    """A task or indication that no task is available.

    !!! warning "Deprecated"
        Use [`LightningStore`][agentlightning.LightningStore] APIs for new workflows.
    """

    is_available: bool
    """Indication that a task is available."""
    task: Optional[Task] = None


RolloutRawResultLegacy = Union[None, float, List[Triplet], List[Dict[str, Any]], List[ReadableSpan], RolloutLegacy]
"""Legacy rollout result type.

!!! warning "Deprecated"
    Use [`RolloutRawResult`][agentlightning.RolloutRawResult] instead.
"""

RolloutRawResult = Union[
    None,  # nothing (relies on tracer)
    float,  # only final reward
    List[ReadableSpan],  # constructed OTEL spans by user
    List[Span],  # constructed Span objects by user
]
"""Rollout result type.

Possible return values of [`rollout`][agentlightning.LitAgent.rollout].
"""


class GenericResponse(BaseModel):
    """Generic server response used by compatibility endpoints.

    !!! warning "Deprecated"
        This response is no longer used by the new
        [`LightningStore`][agentlightning.LightningStore] APIs.

    Attributes:
        status: Status string describing the result of the request.
        message: Optional human readable explanation.
        data: Arbitrary payload serialized as JSON.
    """

    status: str = "success"
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ParallelWorkerBase:
    """Base class for workloads executed across multiple worker processes.

    The lifecycle is orchestrated by the main process:

    * [`init()`][agentlightning.ParallelWorkerBase.init] prepares shared state.
    * Each worker calls [`init_worker()`][agentlightning.ParallelWorkerBase.init_worker] during start-up.
    * [`run()`][agentlightning.ParallelWorkerBase.run] performs the parallel workload.
    * Workers call [`teardown_worker()`][agentlightning.ParallelWorkerBase.teardown_worker] before exiting.
    * The main process finalizes through [`teardown()`][agentlightning.ParallelWorkerBase.teardown].

    Subclasses must implement [`run()`][agentlightning.ParallelWorkerBase.run]
    and can override other lifecycle hooks.
    """

    def __init__(self) -> None:
        """Initialize the base class. This method can be overridden by subclasses."""
        self.worker_id: Optional[int] = None

    def init(self, *args: Any, **kwargs: Any) -> None:
        """Initialize before spawning the workers. This method can be overridden by subclasses."""
        pass

    def init_worker(self, worker_id: int, *args: Any, **kwargs: Any) -> None:
        """Initialize the worker. This method can be overridden by subclasses."""
        self.worker_id = worker_id

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the workload. This method can be overridden by subclasses."""
        pass

    def teardown_worker(self, worker_id: int, *args: Any, **kwargs: Any) -> None:
        """Teardown the worker. This method can be overridden by subclasses."""
        pass

    def teardown(self, *args: Any, **kwargs: Any) -> None:
        """Teardown after the workers have exited. This method can be overridden by subclasses."""
        pass


class Dataset(Protocol, Generic[T_co]):
    """The general interface for a dataset.

    It's currently implemented as a protocol, having a similar interface to `torch.utils.data.Dataset`.
    You don't have to inherit from this class; you can use a simple list if you want to.
    """

    def __getitem__(self, index: SupportsIndex, /) -> T_co: ...

    def __len__(self) -> int: ...


class Hook(ParallelWorkerBase):
    """Base class for defining hooks in the agent runner's lifecycle."""

    async def on_trace_start(
        self, *, agent: LitAgent[Any], runner: Runner[Any], tracer: Tracer, rollout: Rollout
    ) -> None:
        """Hook called immediately after the tracer enters the trace context but before the rollout begins.

        Args:
            agent: The [`LitAgent`][agentlightning.LitAgent] instance associated with the runner.
            runner: The [`Runner`][agentlightning.Runner] managing the rollout.
            tracer: The [`Tracer`][agentlightning.Tracer] instance associated with the runner.
            rollout: The [`Rollout`][agentlightning.Rollout] object that will be processed.

        Subclasses can override this method to implement custom logic such as logging,
        metric collection, or resource setup. By default, this is a no-op.
        """

    async def on_trace_end(
        self, *, agent: LitAgent[Any], runner: Runner[Any], tracer: Tracer, rollout: Rollout
    ) -> None:
        """Hook called immediately after the rollout completes but before the tracer exits the trace context.

        Args:
            agent: The [`LitAgent`][agentlightning.LitAgent] instance associated with the runner.
            runner: The [`Runner`][agentlightning.Runner] managing the rollout.
            tracer: The [`Tracer`][agentlightning.Tracer] instance associated with the runner.
            rollout: The [`Rollout`][agentlightning.Rollout] object that has been processed.

        Subclasses can override this method to implement custom logic such as logging,
        metric collection, or resource cleanup. By default, this is a no-op.
        """

    async def on_rollout_start(self, *, agent: LitAgent[Any], runner: Runner[Any], rollout: Rollout) -> None:
        """Hook called immediately before a rollout *attempt* begins.

        Args:
            agent: The [`LitAgent`][agentlightning.LitAgent] instance associated with the runner.
            runner: The [`Runner`][agentlightning.Runner] managing the rollout.
            rollout: The [`Rollout`][agentlightning.Rollout] object that will be processed.

        Subclasses can override this method to implement custom logic such as
        logging, metric collection, or resource setup. By default, this is a
        no-op.
        """

    async def on_rollout_end(
        self,
        *,
        agent: LitAgent[Any],
        runner: Runner[Any],
        rollout: Rollout,
        spans: Union[List[ReadableSpan], List[Span]],
    ) -> None:
        """Hook called after a rollout *attempt* completes.

        Args:
            agent: The [`LitAgent`][agentlightning.LitAgent] instance associated with the runner.
            runner: The [`Runner`][agentlightning.Runner] managing the rollout.
            rollout: The [`Rollout`][agentlightning.Rollout] object that has been processed.
            spans: The spans that have been added to the store.

        Subclasses can override this method for cleanup or additional
        logging. By default, this is a no-op.
        """
