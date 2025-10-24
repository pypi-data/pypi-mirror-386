#
# Copyright (c) 2012-2025 Snowflake Computing Inc. All rights reserved.
#
import functools
import json
import os
import queue
import threading
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum, unique

import google.protobuf.message
import pyspark.sql.connect.proto.base_pb2 as proto_base

from snowflake.connector.cursor import SnowflakeCursor
from snowflake.connector.telemetry import (
    TelemetryClient as PCTelemetryClient,
    TelemetryData as PCTelemetryData,
    TelemetryField as PCTelemetryField,
)
from snowflake.connector.time_util import get_time_millis
from snowflake.snowpark import Session
from snowflake.snowpark._internal.utils import get_os_name, get_python_version
from snowflake.snowpark.version import VERSION as snowpark_version
from snowflake.snowpark_connect.error.error_codes import ErrorCodes
from snowflake.snowpark_connect.utils.snowpark_connect_logging import logger
from snowflake.snowpark_connect.version import VERSION as sas_version


@unique
class TelemetryField(Enum):
    # inherited from snowflake.connector.telemetry.TelemetryField
    KEY_TYPE = PCTelemetryField.KEY_TYPE.value
    KEY_SOURCE = PCTelemetryField.KEY_SOURCE.value

    # constants
    KEY_ERROR_MSG = "error_msg"
    # Message keys for telemetry
    KEY_VERSION = "version"
    KEY_PYTHON_VERSION = "python_version"
    KEY_SNOWPARK_VERSION = "snowpark_version"
    KEY_OS = "operating_system"
    KEY_DATA = "data"
    KEY_START_TIME = "start_time"
    KEY_EVENT_ID = "event_id"


class TelemetryType(Enum):
    TYPE_REQUEST_SUMMARY = "scos_request_summary"
    TYPE_EVENT = "scos_event"
    EVENT_TYPE = "scos_event_type"


class EventType(Enum):
    SERVER_STARTED = "scos_server_started"
    WARNING = "scos_warning"


# global labels
SOURCE = "SparkConnectForSnowpark"
SCOS_VERSION = ".".join([str(d) for d in sas_version if d is not None])
SNOWPARK_VERSION = ".".join([str(d) for d in snowpark_version if d is not None])
PYTHON_VERSION = get_python_version()
OS = get_os_name()

STATIC_TELEMETRY_DATA = {
    TelemetryField.KEY_SOURCE.value: SOURCE,
    TelemetryField.KEY_VERSION.value: SCOS_VERSION,
    TelemetryField.KEY_SNOWPARK_VERSION.value: SNOWPARK_VERSION,
    TelemetryField.KEY_PYTHON_VERSION.value: PYTHON_VERSION,
    TelemetryField.KEY_OS.value: OS,
}

# list of config keys for which we record values, other config values are not recorded
RECORDED_CONFIG_KEYS = {
    "spark.sql.pyspark.inferNestedDictAsStruct.enabled",
    "spark.sql.pyspark.legacy.inferArrayTypeFromFirstElement.enabled",
    "spark.sql.repl.eagerEval.enabled",
    "spark.sql.crossJoin.enabled",
    "spark.sql.caseSensitive",
    "spark.sql.ansi.enabled",
    "spark.Catalog.databaseFilterInformationSchema",
    "spark.sql.tvf.allowMultipleTableArguments.enabled",
    "spark.sql.repl.eagerEval.maxNumRows",
    "spark.sql.repl.eagerEval.truncate",
    "spark.sql.session.localRelationCacheThreshold",
    "spark.sql.mapKeyDedupPolicy",
    "snowpark.connect.sql.passthrough",
    "snowpark.connect.cte.optimization_enabled",
    "snowpark.connect.iceberg.external_volume",
    "snowpark.connect.sql.identifiers.auto-uppercase",
    "snowpark.connect.udtf.compatibility_mode",
    "snowpark.connect.views.duplicate_column_names_handling_mode",
}

# these fields will be redacted when reporting the spark query plan
REDACTED_PLAN_SUFFIXES = [
    # config values can be set using SQL, so we have to redact it
    "sql",
    "pairs.value",
    "local_relation",
    "options",
]


@dataclass
class TelemetryMessage:
    """Container for telemetry messages in the processing queue."""

    message: dict
    timestamp: int
    is_warning: bool


def _basic_telemetry_data() -> dict:
    return {
        **STATIC_TELEMETRY_DATA,
        TelemetryField.KEY_EVENT_ID.value: str(uuid.uuid4()),
    }


def safe(func):
    """
    Decorator to safely execute telemetry functions, catching and logging exceptions
    without affecting the main application flow.
    """

    @functools.wraps(func)
    def wrap(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            # report failed operation to telemetry
            telemetry.send_warning_msg(
                f"Telemetry operation {func} failed due to exception", e
            )

    return wrap


class TelemetrySink(ABC):
    MAX_BUFFER_ELEMENTS = 20
    MAX_WAIT_MS = 10000  # 10 seconds

    @abstractmethod
    def add_telemetry_data(self, message: dict, timestamp: int) -> None:
        pass

    @abstractmethod
    def flush(self) -> None:
        pass


class NoOpTelemetrySink(TelemetrySink):
    def add_telemetry_data(self, message: dict, timestamp: int) -> None:
        pass

    def flush(self) -> None:
        pass


class ClientTelemetrySink(TelemetrySink):
    def __init__(self, telemetry_client: PCTelemetryClient) -> None:
        self._telemetry_client = telemetry_client
        self._lock = threading.Lock()
        self._reset()

    def add_telemetry_data(self, message: dict, timestamp: int) -> None:
        telemetry_data = PCTelemetryData(message=message, timestamp=timestamp)
        self._telemetry_client.try_add_log_to_batch(telemetry_data)
        with self._lock:
            self._events_since_last_flush += 1
        # flush more often than the underlying telemetry client
        if self._should_flush():
            self.flush()

    def flush(self) -> None:
        with self._lock:
            self._reset()
        self._telemetry_client.send_batch()

    def _should_flush(self) -> bool:
        current_time = get_time_millis()

        return (
            self._events_since_last_flush >= TelemetrySink.MAX_BUFFER_ELEMENTS
            or (current_time - self._last_flush_time) >= TelemetrySink.MAX_WAIT_MS
        )

    def _reset(self):
        self._events_since_last_flush = 0
        self._last_flush_time = get_time_millis()


class QueryTelemetrySink(TelemetrySink):

    MAX_BUFFER_SIZE = 20 * 1024  # 20KB
    TELEMETRY_JOB_ID = "43e72d9b-56d0-4cdb-a615-6b5b5059d6df"

    def __init__(self, session: Session) -> None:
        self._session = session
        self._lock = threading.Lock()
        self._reset()

    def add_telemetry_data(self, message: dict, timestamp: int) -> None:
        telemetry_entry = {"message": message, "timestamp": timestamp}

        # stringify entry, and escape single quotes
        entry_str = json.dumps(telemetry_entry).replace("'", "''")

        with self._lock:
            self._buffer.append(entry_str)
            self._buffer_size += len(entry_str)

        if self._should_flush():
            self.flush()

    def flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            # prefix query with a unique identifier for easier tracking
            query = f"select '{self.TELEMETRY_JOB_ID}' as scos_telemetry_export, '[{','.join(self._buffer)}]'"
            self._reset()

        self._session.sql(query).collect_nowait()

    def _reset(self) -> None:
        self._buffer = []
        self._buffer_size = 0
        self._last_export_time = get_time_millis()

    def _should_flush(self):
        current_time = get_time_millis()
        return (
            self._buffer_size >= QueryTelemetrySink.MAX_BUFFER_SIZE
            or len(self._buffer) >= TelemetrySink.MAX_BUFFER_ELEMENTS
            or (current_time - self._last_export_time) >= TelemetrySink.MAX_WAIT_MS
        )


class Telemetry:
    def __init__(self, is_enabled=True) -> None:
        self._sink = NoOpTelemetrySink()  # use no-op sink until initialized
        self._request_summary: ContextVar[dict] = ContextVar(
            "request_summary", default={}
        )
        self._is_enabled = is_enabled
        self._is_initialized = False
        self._lock = threading.Lock()

        # Async processing setup
        self._message_queue = queue.Queue(maxsize=10000)
        self._worker_thread = None

    def __del__(self):
        self.shutdown()

    def initialize(self, session: Session):
        """
        Must be called after the session is created to initialize telemetry.
        Gets the telemetry client from the session's connection and uses it
        to report telemetry data.
        """
        if not self._is_enabled:
            return

        with self._lock:
            if self._is_initialized:
                logger.warning("Telemetry is already initialized")
                return
            self._is_initialized = True

        telemetry = getattr(session._conn._conn, "_telemetry", None)
        if telemetry is None:
            # no telemetry client available, so we export with queries
            self._sink = QueryTelemetrySink(session)
        else:
            self._sink = ClientTelemetrySink(telemetry)

        self._start_worker_thread()
        logger.info(f"Telemetry initialized with {type(self._sink)}")

    @safe
    def initialize_request_summary(
        self, request: google.protobuf.message.Message
    ) -> None:
        summary = {
            "client_type": request.client_type,
            "spark_session_id": request.session_id,
            "request_type": request.__class__.__name__,
            "was_successful": True,
            "internal_queries": 0,
            "created_on": get_time_millis(),
        }

        if hasattr(request, "operation_id"):
            summary["spark_operation_id"] = request.operation_id

        self._request_summary.set(summary)

        _set_query_plan(request, summary)

    def _not_in_request(self):
        # we don't want to add things to the summary if it's not initialized
        return "created_on" not in self._request_summary.get()

    @safe
    def report_parsed_sql_plan(self, plan: google.protobuf.message.Message) -> None:
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        if "parsed_sql_plans" not in summary:
            summary["parsed_sql_plans"] = []

        summary["parsed_sql_plans"].append(
            _protobuf_to_json_with_redaction(plan, REDACTED_PLAN_SUFFIXES)
        )

    @safe
    def report_function_usage(self, function_name: str) -> None:
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        if "used_functions" not in summary:
            summary["used_functions"] = defaultdict(int)

        summary["used_functions"][function_name] += 1

    @safe
    def report_request_failure(self, e: Exception) -> None:
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        summary["was_successful"] = False
        summary["error_message"] = str(e)
        summary["error_type"] = type(e).__name__

        if not hasattr(e, "custom_error_code") or (e.custom_error_code is None):
            summary["error_code"] = ErrorCodes.INTERNAL_ERROR
        else:
            summary["error_code"] = e.custom_error_code

        error_location = _error_location(e)
        if error_location:
            summary["error_location"] = error_location

    @safe
    def report_config_set(self, pairs: Iterable) -> None:
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        if "config_set" not in summary:
            summary["config_set"] = []

        for p in pairs:
            summary["config_set"].append(
                {
                    "key": p.key,
                    "value": p.value if p.key in RECORDED_CONFIG_KEYS else "<redacted>",
                }
            )

    @safe
    def report_config_unset(self, keys: Iterable[str]) -> None:
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        if "config_unset" not in summary:
            summary["config_unset"] = []

        summary["config_unset"].extend(keys)

    @safe
    def report_config_get(self, keys: Iterable[str]) -> None:
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        if "config_get" not in summary:
            summary["config_get"] = []

        summary["config_get"].extend(keys)

    @safe
    def report_config_op_type(self, op_type: str):
        if self._not_in_request():
            return

        summary = self._request_summary.get()
        summary["config_op_type"] = op_type

    @safe
    def report_query(
        self, result: SnowflakeCursor | dict | Exception, **kwargs
    ) -> None:
        if result is None or isinstance(result, dict) or self._not_in_request():
            return

        # SnowflakeCursor and SQL errors will have sfqid
        # other exceptions will not have it
        # TODO: handle async queries, but filter out telemetry export queries
        qid = getattr(result, "sfqid", None)

        if qid is None:
            logger.warning("Missing query id in result: %s", result)

        is_internal = kwargs.get("_is_internal", False)
        if is_internal:
            self._report_internal_query()
        elif qid:
            self._report_query_id(qid)

    def _report_query_id(self, query_id: str):
        summary = self._request_summary.get()

        if "queries" not in summary:
            summary["queries"] = []

        summary["queries"].append(query_id)

    def _report_internal_query(self):
        summary = self._request_summary.get()

        if "internal_queries" not in summary:
            summary["internal_queries"] = 0

        summary["internal_queries"] += 1

    @safe
    def report_describe_query_cache_lookup(self):
        """Report a describe query cache lookup."""
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        if "describe_cache_lookups" not in summary:
            summary["describe_cache_lookups"] = 0

        summary["describe_cache_lookups"] += 1

    @safe
    def report_describe_query_cache_hit(self):
        """Report a describe query cache hit."""
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        if "describe_cache_hits" not in summary:
            summary["describe_cache_hits"] = 0

        summary["describe_cache_hits"] += 1

    @safe
    def report_describe_query_cache_expired(self, expired_by: float):
        """Report a describe query cache hit."""
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        if "describe_cache_expired" not in summary:
            summary["describe_cache_expired"] = 0

        summary["describe_cache_expired"] += 1

        if "describe_cache_expired_by" not in summary:
            summary["describe_cache_expired_by"] = []

        summary["describe_cache_expired_by"].append(expired_by)

    @safe
    def report_describe_query_cache_clear(self, query_prefix: str):
        """Report a describe query cache clear."""
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        if "describe_cache_clears" not in summary:
            summary["describe_cache_clears"] = []

        summary["describe_cache_clears"].append(query_prefix)

    @safe
    def report_udf_usage(self, udf_name: str):
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        if "udf_usage" not in summary:
            summary["udf_usage"] = defaultdict(int)

        summary["udf_usage"][udf_name] += 1

    def _report_io(self, op: str, type: str):
        if self._not_in_request():
            return

        summary = self._request_summary.get()

        if "io" not in summary:
            summary["io"] = []

        summary["io"].append({"op": op, "type": type})

    @safe
    def report_io_read(self, type: str):
        self._report_io("read", type)

    @safe
    def report_io_write(self, type: str):
        self._report_io("write", type)

    @safe
    def send_server_started_telemetry(self):
        message = {
            **_basic_telemetry_data(),
            TelemetryField.KEY_TYPE.value: TelemetryType.TYPE_EVENT.value,
            TelemetryType.EVENT_TYPE.value: EventType.SERVER_STARTED.value,
            TelemetryField.KEY_DATA.value: {
                TelemetryField.KEY_START_TIME.value: get_time_millis(),
            },
        }
        self._send(message)

    @safe
    def send_request_summary_telemetry(self):
        if self._not_in_request():
            self.send_warning_msg(
                "Trying to send request summary telemetry without initializing it"
            )
            return

        summary = self._request_summary.get()
        message = {
            **_basic_telemetry_data(),
            TelemetryField.KEY_TYPE.value: TelemetryType.TYPE_REQUEST_SUMMARY.value,
            TelemetryField.KEY_DATA.value: summary,
        }
        self._send(message)

    def send_warning_msg(self, msg: str, e: Exception = None) -> None:
        # using this within @safe decorator may result in recursive loop
        try:
            message = self._build_warning_message(msg, e)
            if not message:
                return

            self._send(message, is_warning=True)
        except Exception:
            # if there's an exception here, there's nothing we can really do about it
            pass

    def _build_warning_message(self, warning_msg: str, e: Exception = None) -> dict:
        try:
            data = {"warning_message": warning_msg}
            if e is not None:
                data["exception"] = repr(e)

            # add session and operation id if available
            spark_session_id = self._request_summary.get().get("spark_session_id", None)
            if spark_session_id is not None:
                data["spark_session_id"] = spark_session_id

            spark_operation_id = self._request_summary.get().get(
                "spark_operation_id", None
            )
            if spark_operation_id is not None:
                data["spark_operation_id"] = spark_operation_id

            message = {
                **_basic_telemetry_data(),
                TelemetryField.KEY_TYPE.value: TelemetryType.TYPE_EVENT.value,
                TelemetryType.EVENT_TYPE.value: EventType.WARNING.value,
                TelemetryField.KEY_DATA.value: data,
            }
            return message
        except Exception:
            return {}

    def _send(self, msg: dict, is_warning: bool = False) -> None:
        """Queue a telemetry message for asynchronous processing."""
        if not self._is_enabled:
            return

        timestamp = get_time_millis()
        try:
            telemetry_msg = TelemetryMessage(
                message=msg, timestamp=timestamp, is_warning=is_warning
            )
            self._message_queue.put_nowait(telemetry_msg)
        except queue.Full:
            # If queue is full, drop the message to avoid blocking
            logger.warning("Telemetry queue is full, dropping message")

    def _start_worker_thread(self) -> None:
        """Start the background worker thread for processing telemetry messages."""
        if self._worker_thread is None:
            self._worker_thread = threading.Thread(
                target=self._worker_loop, daemon=True, name="TelemetryWorker"
            )
            self._worker_thread.start()

    def _worker_loop(self) -> None:
        """Worker thread loop that processes messages from the queue."""
        while True:
            try:
                # block to allow the GIL to switch threads
                telemetry_msg = self._message_queue.get()
                if telemetry_msg is None:
                    # shutdown signal
                    break
                self._sink.add_telemetry_data(
                    telemetry_msg.message, telemetry_msg.timestamp
                )
            except Exception as e:
                if not telemetry_msg.is_warning:
                    self.send_warning_msg("Failed to add telemetry message to sink", e)
            finally:
                self._message_queue.task_done()

        # Flush the sink
        self._sink.flush()

    def shutdown(self) -> None:
        """Shutdown the telemetry worker thread and flush any remaining messages."""
        if not self._worker_thread or self._worker_thread.is_alive():
            return

        try:
            self._message_queue.put_nowait(None)
            # Wait for worker thread to finish
            self._worker_thread.join(timeout=3.0)
        except Exception:
            logger.warning(
                "Could not put shutdown message on telemetry queue", exc_info=True
            )


def _error_location(e: Exception) -> dict | None:
    """
    Inspect the exception traceback and extract the file name, line number, and function name
    from the last frame (the one that raised the exception).
    """
    tb = e.__traceback__
    if tb is None:
        return None

    while tb.tb_next is not None:
        tb = tb.tb_next

    # Get just the file name without the path
    full_path = tb.tb_frame.f_code.co_filename
    file_name = full_path.split("/")[-1]

    return {
        "file": file_name,
        "line": tb.tb_lineno,
        "fn": tb.tb_frame.f_code.co_name,
    }


def _is_map_field(field_descriptor) -> bool:
    """
    Check if a protobuf field is a map.
    """
    return (
        field_descriptor.label == field_descriptor.LABEL_REPEATED
        and field_descriptor.message_type is not None
        and field_descriptor.message_type.has_options
        and field_descriptor.message_type.GetOptions().map_entry
    )


def _protobuf_to_json_with_redaction(
    message: google.protobuf.message.Message, redacted_suffixes: list[str]
) -> dict:
    """
    Convert a protobuf Message to JSON dict with selective field redaction.

    Args:
        message: The protobuf Message to convert
        redacted_suffixes: List of field path suffixes to redact (e.g. ["jdbc.options"])

    Returns:
        Dictionary representation with specified fields redacted
    """

    MAX_MESSAGE_SIZE = 200 * 1024  # 200KB

    def _convert_field_value(value, field_descriptor, field_path: str):
        """Convert a protobuf field value to its JSON representation"""
        # Check if this field should be redacted
        should_redact = any(field_path.endswith(suffix) for suffix in redacted_suffixes)
        if should_redact:
            return "<redacted>"

        # Handle different field types
        if _is_map_field(field_descriptor):
            return dict(value)
        elif field_descriptor.type == field_descriptor.TYPE_MESSAGE:
            if field_descriptor.label == field_descriptor.LABEL_REPEATED:
                # Repeated message field
                return [_protobuf_to_json_recursive(item, field_path) for item in value]
            else:
                # Singular message field
                return _protobuf_to_json_recursive(value, field_path)
        elif field_descriptor.label == field_descriptor.LABEL_REPEATED:
            # Repeated scalar field
            return list(value)
        else:
            # Singular scalar field
            return value

    def _protobuf_to_json_recursive(
        msg: google.protobuf.message.Message, current_path: str = ""
    ) -> dict:
        """Recursively convert protobuf message to dict"""

        if not isinstance(msg, google.protobuf.message.Message):
            telemetry.send_warning_msg(f"Expected a protobuf message, got: {type(msg)}")
            return {}

        result = {}

        # Use ListFields() to get all set fields
        for field_descriptor, field_value in msg.ListFields():
            field_name = field_descriptor.name
            field_path = f"{current_path}.{field_name}" if current_path else field_name

            # Convert the field value
            result[field_name] = _convert_field_value(
                field_value, field_descriptor, field_path
            )

        return result

    return (
        _protobuf_to_json_recursive(message)
        if message.ByteSize() <= MAX_MESSAGE_SIZE
        # do not report huge query plans to avoid failures when sending telemetry
        else "<too_big>"
    )


def _set_query_plan(request: google.protobuf.message.Message, summary: dict) -> None:
    if isinstance(request, proto_base.ExecutePlanRequest):
        # ExecutePlanRequest has plan at top level
        if hasattr(request, "plan"):
            summary["query_plan"] = (
                _protobuf_to_json_with_redaction(request.plan, REDACTED_PLAN_SUFFIXES),
            )

    elif isinstance(request, proto_base.AnalyzePlanRequest):
        # AnalyzePlanRequest has plan under oneof analyze
        analyze_type = request.WhichOneof("analyze")
        if not analyze_type:
            return

        summary["analyze_type"] = analyze_type
        analyze_field = getattr(request, analyze_type)
        if hasattr(analyze_field, "plan"):
            summary["query_plan"] = _protobuf_to_json_with_redaction(
                analyze_field.plan, REDACTED_PLAN_SUFFIXES
            )


# global telemetry client
telemetry = Telemetry(is_enabled="SNOWPARK_CONNECT_DISABLE_TELEMETRY" not in os.environ)


class SnowparkConnectNotImplementedError(NotImplementedError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
