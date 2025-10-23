from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List

import pandas as pd
import pyarrow as pa

from arize._flight.client import ArizeFlightClient
from arize._generated.api_client import models
from arize.config import SDKConfiguration
from arize.datasets.validation import validate_dataset_df
from arize.exceptions.base import INVALID_ARROW_CONVERSION_MSG
from arize.utils.openinference_conversion import (
    convert_boolean_columns_to_str,
    convert_datetime_columns_to_int,
    convert_default_columns_to_json_str,
)
from arize.utils.size import get_payload_size_mb

logger = logging.getLogger(__name__)

# TODO(Kiko): Decide based on size of payload instead
REST_LIMIT_DATASET_EXAMPLES = 0


class DatasetsClient:
    def __init__(self, sdk_config: SDKConfiguration):
        self._sdk_config = sdk_config

        # Import at runtime so it’s still lazy and extras-gated by the parent
        from arize._generated import api_client as gen

        # Use the shared generated client from the config
        self._api = gen.DatasetsApi(self._sdk_config.get_generated_client())

        # Forward methods to preserve exact runtime signatures/docs
        self.list = self._api.datasets_list
        self.get = self._api.datasets_get
        self.delete = self._api.datasets_delete

        # Custom methods
        self.list_examples = self._list_examples
        self.create = self._create_dataset

    def _list_examples(
        self,
        dataset_id: str,
        dataset_version_id: str = "",
        limit: int = 100,
        all: bool = False,
    ):
        if not all:
            return self._api.datasets_list_examples(
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                limit=limit,
            )

        # TODO(Kiko): Space ID should not be needed,
        # should work on server tech debt to remove this
        dataset = self.get(dataset_id=dataset_id)
        space_id = dataset.space_id

        with ArizeFlightClient(
            api_key=self._sdk_config.api_key,
            host=self._sdk_config.flight_server_host,
            port=self._sdk_config.flight_server_port,
            scheme=self._sdk_config.flight_scheme,
            request_verify=self._sdk_config.request_verify,
            max_chunksize=self._sdk_config.pyarrow_max_chunksize,
        ) as flight_client:
            try:
                response = flight_client.get_dataset_examples(
                    space_id=space_id,
                    dataset_id=dataset_id,
                    dataset_version_id=dataset_version_id,
                )
            except Exception as e:
                msg = f"Error during request: {str(e)}"
                logger.error(msg)
                raise RuntimeError(msg) from e
        if response is None:
            # This should not happen with proper Flight client implementation,
            # but we handle it defensively
            msg = "No response received from flight server during request"
            logger.error(msg)
            raise RuntimeError(msg)
        # The response from flightserver is the dataset ID. To return the dataset
        # object we make a GET query
        return models.DatasetsListExamples200Response(
            examples=response.to_dict(orient="records")
        )

    def _create_dataset(
        self,
        name: str,
        space_id: str,
        examples: List[Dict[str, Any]] | pd.DataFrame,
        force_http: bool = False,
    ):
        if not isinstance(examples, (list, pd.DataFrame)):
            raise TypeError(
                "Examples must be a list of dicts or a pandas DataFrame"
            )
        below_threshold = (
            get_payload_size_mb(examples)
            <= self._sdk_config.max_http_payload_size_mb
        )
        if below_threshold or force_http:
            from arize._generated import api_client as gen

            data = (
                examples.to_dict(orient="records")
                if isinstance(examples, pd.DataFrame)
                else examples
            )

            body = gen.DatasetsCreateRequest(
                name=name,
                spaceId=space_id,
                examples=data,
            )
            return self._api.datasets_create(datasets_create_request=body)

        # If we have too many examples, try to convert to a dataframe
        # and log via gRPC + flight
        logger.info(
            f"Uploading {len(examples)} examples via REST may be slow. "
            "Trying to convert to DataFrame for more efficient upload via "
            "gRPC + Flight."
        )
        data = (
            examples
            if isinstance(examples, pd.DataFrame)
            else pd.DataFrame(examples)
        )
        return self._create_dataset_via_flight(
            name=name,
            space_id=space_id,
            examples=data,
        )

    def _create_dataset_via_flight(
        self,
        name: str,
        space_id: str,
        examples: pd.DataFrame,
    ):
        data = examples.copy()
        # Convert datetime columns to int64 (ms since epoch)
        data = convert_datetime_columns_to_int(data)
        data = convert_boolean_columns_to_str(data)
        data = _set_default_columns_for_dataset(data)
        data = convert_default_columns_to_json_str(data)

        validation_errors = validate_dataset_df(data)
        if validation_errors:
            raise RuntimeError([e.error_message() for e in validation_errors])

        # Convert to Arrow table
        try:
            logger.debug("Converting data to Arrow format")
            pa_table = pa.Table.from_pandas(data, preserve_index=False)
        except pa.ArrowInvalid as e:
            logger.error(f"{INVALID_ARROW_CONVERSION_MSG}: {str(e)}")
            raise pa.ArrowInvalid(
                f"Error converting to Arrow format: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating Arrow table: {str(e)}")
            raise

        response = None
        with ArizeFlightClient(
            api_key=self._sdk_config.api_key,
            host=self._sdk_config.flight_server_host,
            port=self._sdk_config.flight_server_port,
            scheme=self._sdk_config.flight_scheme,
            request_verify=self._sdk_config.request_verify,
            max_chunksize=self._sdk_config.pyarrow_max_chunksize,
        ) as flight_client:
            try:
                response = flight_client.create_dataset(
                    space_id=space_id,
                    dataset_name=name,
                    pa_table=pa_table,
                )
            except Exception as e:
                msg = f"Error during update request: {str(e)}"
                logger.error(msg)
                raise RuntimeError(msg) from e
        if response is None:
            # This should not happen with proper Flight client implementation,
            # but we handle it defensively
            msg = "No response received from flight server during update"
            logger.error(msg)
            raise RuntimeError(msg)
        # The response from flightserver is the dataset ID. To return the dataset
        # object we make a GET query
        dataset = self.get(dataset_id=response)
        return dataset


def _set_default_columns_for_dataset(df: pd.DataFrame) -> pd.DataFrame:
    current_time = int(time.time() * 1000)
    if "created_at" in df.columns:
        if df["created_at"].isnull().values.any():
            df["created_at"].fillna(current_time, inplace=True)
    else:
        df["created_at"] = current_time

    if "updated_at" in df.columns:
        if df["updated_at"].isnull().values.any():
            df["updated_at"].fillna(current_time, inplace=True)
    else:
        df["updated_at"] = current_time

    if "id" in df.columns:
        if df["id"].isnull().values.any():
            df["id"] = df["id"].apply(
                lambda x: str(uuid.uuid4()) if pd.isnull(x) else x
            )
    else:
        df["id"] = [str(uuid.uuid4()) for _ in range(len(df))]

    return df
