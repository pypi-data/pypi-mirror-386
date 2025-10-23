# type: ignore[pb2]
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Tuple

from google.protobuf import json_format
from pyarrow import flight

from arize._flight.types import FlightRequestType
from arize._generated.protocol.flight import ingest_pb2 as flight_ing_pb2
from arize._generated.protocol.flight.ingest_pb2 import (
    PostExperimentDataResponse,
    WriteSpanAnnotationResponse,
    WriteSpanAttributesMetadataResponse,
    WriteSpanEvaluationResponse,
)
from arize.config import get_python_version
from arize.logging import log_a_list
from arize.utils.openinference_conversion import convert_json_str_to_dict
from arize.utils.proto import get_pb_schema_tracing
from arize.version import __version__

if TYPE_CHECKING:
    import pyarrow as pa


BytesPair = Tuple[bytes, bytes]
Headers = List[BytesPair]
FlightPostArrowFileResponse = (
    WriteSpanEvaluationResponse
    | WriteSpanAnnotationResponse
    | WriteSpanAttributesMetadataResponse
    | PostExperimentDataResponse
)

logger = logging.getLogger(__name__)


class FlightActionKey(Enum):
    CREATE_EXPERIMENT_DB_ENTRY = "create_experiment_db_entry"
    # GET_DATASET_VERSION = "get_dataset_version"
    # LIST_DATASETS = "list_datasets"
    # DELETE_DATASET = "delete_dataset"
    # DELETE_EXPERIMENT = "delete_experiment"


@dataclass(frozen=True)
class ArizeFlightClient:
    api_key: str = field(repr=False)
    host: str
    port: int
    scheme: str
    max_chunksize: int
    request_verify: bool

    # internal cache for the underlying FlightClient
    _client: flight.FlightClient | None = field(
        default=None, init=False, repr=False
    )

    # ---------- Properties ----------

    @property
    def headers(self) -> Headers:
        return [
            (b"origin", b"arize-logging-client"),
            (b"auth-token-bin", str(self.api_key).encode("utf-8")),
            (b"sdk-language", b"python"),
            (b"language-version", get_python_version().encode("utf-8")),
            (b"sdk-version", __version__.encode("utf-8")),
        ]

    @property
    def call_options(self) -> flight.FlightCallOptions:
        return flight.FlightCallOptions(headers=self.headers)

    # ---------- Connection management ----------

    def _ensure_client(self) -> flight.FlightClient:
        client = object.__getattribute__(self, "_client")
        if client is not None:
            return client

        # disable TLS verification for local dev on localhost, or if user opts out
        disable_cert = (
            self.request_verify is False or self.host.lower() == "localhost"
        )

        new_client = flight.FlightClient(
            location=f"{self.scheme}://{self.host}:{self.port}",
            disable_server_verification=disable_cert,
        )
        object.__setattr__(self, "_client", new_client)
        return new_client

    def close(self) -> None:
        client = object.__getattribute__(self, "_client")
        if client is not None:
            client.close()
            object.__setattr__(self, "_client", None)

    # ---------- Context manager ----------

    def __enter__(self) -> ArizeFlightClient:
        self._ensure_client()
        return self

    def __exit__(self, exc_type, exc_val, _) -> None:
        if exc_type:
            logger.error(f"An exception occurred: {exc_val}")
        self.close()

    # ---------- methods simple passthrough wrappers ----------

    def get_flight_info(self, *args: Any, **kwargs: Any):
        client = self._ensure_client()
        kwargs.setdefault("options", self.call_options)
        return client.get_flight_info(*args, **kwargs)

    def do_get(self, *args: Any, **kwargs: Any) -> flight.FlightStreamReader:
        client = self._ensure_client()
        kwargs.setdefault("options", self.call_options)
        return client.do_get(*args, **kwargs)

    def do_put(
        self, *args: Any, **kwargs: Any
    ) -> [flight.FlightStreamWriter, flight.FlightMetadataReader]:
        client = self._ensure_client()
        kwargs.setdefault("options", self.call_options)
        return client.do_put(*args, **kwargs)

    def do_action(self, *args: Any, **kwargs: Any) -> Iterable[flight.Result]:
        client = self._ensure_client()
        kwargs.setdefault("options", self.call_options)
        return client.do_action(*args, **kwargs)

    # ---------- logging methods ----------

    def log_arrow_table(
        self,
        space_id: str,
        request_type: FlightRequestType,
        pa_table: pa.Table,
        project_name: str | None = None,
        dataset_id: str | None = None,
        experiment_name: str | None = None,
    ) -> FlightPostArrowFileResponse:
        pa_schema = pa_table.schema
        if request_type in (
            FlightRequestType.EVALUATION,
            FlightRequestType.ANNOTATION,
            FlightRequestType.METADATA,
        ):
            proto_schema = get_pb_schema_tracing(project_name=project_name)
            base64_schema = base64.b64encode(proto_schema.SerializeToString())
            pa_schema = append_to_pyarrow_metadata(
                pa_table.schema, {"arize-schema": base64_schema}
            )

        doput_request = _get_pb_flight_doput_request(
            space_id=space_id,
            request_type=request_type,
            model_id=project_name,
            dataset_id=dataset_id,
            experiment_name=experiment_name,
        )

        descriptor = flight.FlightDescriptor.for_command(
            json_format.MessageToJson(doput_request).encode("utf-8")
        )
        try:
            flight_writer, flight_metadata_reader = self.do_put(
                descriptor, pa_schema, options=self.call_options
            )
            with flight_writer:
                # write table as stream to flight server
                flight_writer.write_table(pa_table, self.max_chunksize)
                # indicate that client has flushed all contents to stream
                flight_writer.done_writing()
                # read response from flight server
                flight_response = flight_metadata_reader.read()
                if flight_response is None:
                    return None

                res = None
                match request_type:
                    case FlightRequestType.EVALUATION:
                        res = WriteSpanEvaluationResponse()
                        res.ParseFromString(flight_response.to_pybytes())
                    case FlightRequestType.ANNOTATION:
                        res = WriteSpanAnnotationResponse()
                        res.ParseFromString(flight_response.to_pybytes())
                    case FlightRequestType.METADATA:
                        res = WriteSpanAttributesMetadataResponse()
                        res.ParseFromString(flight_response.to_pybytes())
                    case FlightRequestType.LOG_EXPERIMENT_DATA:
                        res = PostExperimentDataResponse()
                        res.ParseFromString(flight_response.to_pybytes())
                    case _:
                        raise ValueError(
                            f"Unsupported request_type: {request_type}"
                        )
                return res
        except Exception as e:
            logger.exception(f"Error logging arrow table to Arize: {e}")
            raise RuntimeError(
                f"Error logging arrow table to Arize: {e}"
            ) from e

    # ---------- dataset methods ----------

    def create_dataset(
        self,
        space_id: str,
        dataset_name: str,
        pa_table: pa.Table,
    ) -> str:
        doput_request = flight_ing_pb2.DoPutRequest(
            create_dataset=flight_ing_pb2.CreateDatasetRequest(
                space_id=space_id,
                dataset_name=dataset_name,
                dataset_type=flight_ing_pb2.GENERATIVE,
            )
        )
        descriptor = flight.FlightDescriptor.for_command(
            json_format.MessageToJson(doput_request).encode("utf-8")
        )
        try:
            flight_writer, flight_metadata_reader = self.do_put(
                descriptor, pa_table.schema, options=self.call_options
            )
            with flight_writer:
                # write table as stream to flight server
                flight_writer.write_table(pa_table, self.max_chunksize)
                # indicate that client has flushed all contents to stream
                flight_writer.done_writing()
                # read response from flight server
                flight_response = flight_metadata_reader.read()
                if flight_response is None:
                    return None

                res = None
                res = flight_ing_pb2.CreateDatasetResponse()
                res.ParseFromString(flight_response.to_pybytes())
                if res:
                    return str(res.dataset_id)
                return res
        except Exception as e:
            logger.exception(f"Error logging arrow table to Arize: {e}")
            raise RuntimeError(
                f"Error logging arrow table to Arize: {e}"
            ) from e

    def get_dataset_examples(
        self,
        space_id: str,
        dataset_id: str,
        dataset_version_id: str | None = None,
    ):
        # TODO(Kiko): Space ID should not be needed,
        # should work on server tech debt to remove this
        doget_request = flight_ing_pb2.DoGetRequest(
            get_dataset=flight_ing_pb2.GetDatasetRequest(
                space_id=space_id,
                dataset_id=dataset_id,
                dataset_version=dataset_version_id,
            )
        )
        descriptor = flight.Ticket(
            json_format.MessageToJson(doget_request).encode("utf-8")
        )
        try:
            reader = self.do_get(descriptor, options=self.call_options)
            # read all data into pandas dataframe
            df = reader.read_all().to_pandas()
            df = convert_json_str_to_dict(df)
            return df
        except Exception as e:
            logger.exception(f"Failed to get dataset id={dataset_id}")
            raise RuntimeError(f"Failed to get dataset id={dataset_id}") from e

    def init_experiment(
        self,
        space_id: str,
        dataset_id: str,
        experiment_name: str,
    ) -> Tuple[str, str] | None:
        request = flight_ing_pb2.DoActionRequest(
            create_experiment_db_entry=flight_ing_pb2.CreateExperimentDBEntryRequest(
                space_id=space_id,
                dataset_id=dataset_id,
                experiment_name=experiment_name,
            )
        )
        action = flight.Action(
            FlightActionKey.CREATE_EXPERIMENT_DB_ENTRY,
            json_format.MessageToJson(request).encode("utf-8"),
        )
        try:
            response = self.do_action(action, options=self.call_options)
        except Exception as e:
            logger.exception(f"Failed to init experiment {experiment_name}")
            raise RuntimeError(
                f"Failed to init experiment {experiment_name}"
            ) from e

        res = next(response, None)
        if res is None:
            return None
        resp_pb = flight_ing_pb2.CreateExperimentDBEntryResponse()
        resp_pb.ParseFromString(res.body.to_pybytes())
        return (
            resp_pb.experiment_id,
            resp_pb.trace_model_name,
        )


def append_to_pyarrow_metadata(
    pa_schema: pa.Schema, new_metadata: Dict[str, Any]
):
    # Ensure metadata is handled correctly, even if initially None.
    metadata = pa_schema.metadata
    if metadata is None:
        # Initialize an empty dict if schema metadata was None
        metadata = {}

    conflicting_keys = metadata.keys() & new_metadata.keys()
    if conflicting_keys:
        raise KeyError(
            "Cannot append metadata to pyarrow schema. "
            f"There are conflicting keys: {log_a_list(conflicting_keys, join_word='and')}"
        )

    updated_metadata = metadata.copy()
    updated_metadata.update(new_metadata)
    return pa_schema.with_metadata(updated_metadata)


def _get_pb_flight_doput_request(
    space_id: str,
    request_type: FlightRequestType,
    model_id: str | None = None,
    dataset_id: str | None = None,
    experiment_name: str | None = None,
) -> flight_ing_pb2.DoPutRequest:
    """Return a DoPutRequest for the given request_type."""

    common_args = {"space_id": space_id}

    if model_id:
        common_args["external_model_id"] = model_id
    if dataset_id:
        common_args["dataset_id"] = dataset_id
    if experiment_name:
        common_args["experiment_name"] = experiment_name

    if model_id:
        # model-based request types
        match request_type:
            case FlightRequestType.LOG_EXPERIMENT_DATA:
                return flight_ing_pb2.DoPutRequest(
                    write_span_evaluation_request=flight_ing_pb2.WriteSpanEvaluationRequest(
                        **common_args
                    )
                )
            case FlightRequestType.ANNOTATION:
                return flight_ing_pb2.DoPutRequest(
                    write_span_annotation_request=flight_ing_pb2.WriteSpanAnnotationRequest(
                        **common_args
                    )
                )
            case FlightRequestType.METADATA:
                return flight_ing_pb2.DoPutRequest(
                    write_span_attributes_metadata_request=flight_ing_pb2.WriteSpanAttributesMetadataRequest(
                        **common_args
                    )
                )
            case _:
                raise ValueError(f"Unsupported request_type: {request_type}")

    if dataset_id and experiment_name:
        # dataset-based request types
        match request_type:
            case FlightRequestType.LOG_EXPERIMENT_DATA:
                return flight_ing_pb2.DoPutRequest(
                    post_experiment_data=flight_ing_pb2.PostExperimentDataRequest(
                        **common_args
                    )
                )
            case _:
                raise ValueError(f"Unsupported request_type: {request_type}")

    raise ValueError(
        f"Unsupported combination: {request_type=} with provided arguments."
    )
