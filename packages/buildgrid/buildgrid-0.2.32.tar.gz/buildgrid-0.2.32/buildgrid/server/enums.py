# Copyright (C) 2018 Bloomberg LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  <http://www.apache.org/licenses/LICENSE-2.0>
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from enum import Enum

from buildgrid._protos.build.bazel.remote.execution.v2 import remote_execution_pb2
from buildgrid._protos.build.buildgrid import introspection_pb2, monitoring_pb2
from buildgrid._protos.google.devtools.remoteworkers.v1test2 import bots_pb2

# RWAPI enumerations
# From google/devtools/remoteworkers/v1test2/bots.proto:


class BotStatus(Enum):
    # Initially unknown state.
    UNSPECIFIED = bots_pb2.BotStatus.Value("BOT_STATUS_UNSPECIFIED")
    # The bot is healthy, and will accept leases as normal.
    OK = bots_pb2.BotStatus.Value("OK")
    # The bot is unhealthy and will not accept new leases.
    UNHEALTHY = bots_pb2.BotStatus.Value("UNHEALTHY")
    # The bot has been asked to reboot the host.
    HOST_REBOOTING = bots_pb2.BotStatus.Value("HOST_REBOOTING")
    # The bot has been asked to shut down.
    BOT_TERMINATING = bots_pb2.BotStatus.Value("BOT_TERMINATING")


class LeaseState(Enum):
    # Initially unknown state.
    UNSPECIFIED = bots_pb2.LeaseState.Value("LEASE_STATE_UNSPECIFIED")
    # The server expects the bot to accept this lease.
    PENDING = bots_pb2.LeaseState.Value("PENDING")
    # The bot has accepted this lease.
    ACTIVE = bots_pb2.LeaseState.Value("ACTIVE")
    # The bot is no longer leased.
    COMPLETED = bots_pb2.LeaseState.Value("COMPLETED")
    # The bot should immediately release all resources associated with the lease.
    CANCELLED = bots_pb2.LeaseState.Value("CANCELLED")


# REAPI enumerations
# From build/bazel/remote/execution/v2/remote_execution.proto:


class OperationStage(Enum):
    # Initially unknown stage.
    UNKNOWN = remote_execution_pb2.ExecutionStage.Value.Value("UNKNOWN")
    # Checking the result against the cache.
    CACHE_CHECK = remote_execution_pb2.ExecutionStage.Value.Value("CACHE_CHECK")
    # Currently idle, awaiting a free machine to execute.
    QUEUED = remote_execution_pb2.ExecutionStage.Value.Value("QUEUED")
    # Currently being executed by a worker.
    EXECUTING = remote_execution_pb2.ExecutionStage.Value.Value("EXECUTING")
    # Finished execution.
    COMPLETED = remote_execution_pb2.ExecutionStage.Value.Value("COMPLETED")


# Internal enumerations
# From build.buildgrid/monitoring.proto:


class LogRecordLevel(Enum):
    # Initially unknown level.
    NOTSET = monitoring_pb2.LogRecord.Level.Value("NOTSET")
    # Debug message severity level.
    DEBUG = monitoring_pb2.LogRecord.Level.Value("DEBUG")
    # Information message severity level.
    INFO = monitoring_pb2.LogRecord.Level.Value("INFO")
    # Warning message severity level.
    WARNING = monitoring_pb2.LogRecord.Level.Value("WARNING")
    # Error message severity level.
    ERROR = monitoring_pb2.LogRecord.Level.Value("ERROR")
    # Critical message severity level.
    CRITICAL = monitoring_pb2.LogRecord.Level.Value("CRITICAL")


class MetricRecordType(Enum):
    # Initially unknown type.
    NONE = monitoring_pb2.MetricRecord.Type.Value("NONE")
    # A metric for counting.
    COUNTER = monitoring_pb2.MetricRecord.Type.Value("COUNTER")
    # A metric for mesuring a duration.
    TIMER = monitoring_pb2.MetricRecord.Type.Value("TIMER")
    # A metric in arbitrary value.
    GAUGE = monitoring_pb2.MetricRecord.Type.Value("GAUGE")
    # A metric with distribution semantics
    DISTRIBUTION = monitoring_pb2.MetricRecord.Type.Value("DISTRIBUTION")


class JobEventType(Enum):
    STOP = "stop"
    CHANGE = "change"


class MetricCategories(Enum):
    JOBS = "jobs"


class ServiceName(Enum):
    EXECUTION = "execution"
    OPERATIONS = "operations"
    BOTS = "bots"

    @classmethod
    def default_services(cls) -> tuple[str, str, str]:
        return (cls.EXECUTION.value, cls.OPERATIONS.value, cls.BOTS.value)


class ByteStreamResourceType(Enum):
    CAS = "cas"


class ActionCacheEntryType(Enum):
    """Type of the value stored in an Action Cache entry."""

    ACTION_RESULT_DIGEST = 0
    ACTION_RESULT = 1


class MeteringThrottleAction(Enum):
    DEPRIORITIZE = "deprioritize"
    REJECT = "reject"


class JobHistoryEvent(Enum):
    # Unspecified, should never be used (and is the default type for an empty `JobEvent` proto)
    UNSPECIFIED = introspection_pb2.JobEventType.Value("UNSPECIFIED")

    # Record of the creation of a new `JobEntry`
    CREATION = introspection_pb2.JobEventType.Value("CREATION")

    # Record of the creation of a new `OperationEntry` for a job
    # (i.e. at creation time, or when deduplicating a request into the job)
    NEW_OPERATION = introspection_pb2.JobEventType.Value("NEW_OPERATION")

    # Record of a job being assigned to a bot for execution.
    ASSIGNMENT = introspection_pb2.JobEventType.Value("ASSIGNMENT")

    # Record of a job being reported as completed by a bot
    COMPLETION = introspection_pb2.JobEventType.Value("COMPLETION")

    # Record of cancellation being requested and applied for an operation related to the job
    OPERATION_CANCELLATION = introspection_pb2.JobEventType.Value("OPERATION_CANCELLATION")

    # Record of a job being successfully cancelled
    CANCELLATION = introspection_pb2.JobEventType.Value("CANCELLATION")

    # Record of a job being requeued after a transient execution failure
    RETRY = introspection_pb2.JobEventType.Value("RETRY")

    # Record of a timestamp for some section of the execution
    # (see `ExecutedActionMetadata` proto for possible timestamps)
    PROGRESS_UPDATE = introspection_pb2.JobEventType.Value("PROGRESS_UPDATE")


class JobAssignmentStrategy(Enum):
    LOCALITY = "locality"
    CAPACITY = "capacity"
    PROACTIVE = "proactive"
