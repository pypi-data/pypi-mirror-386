from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import opentelemetry.sdk.trace as trace_sdk
import pyarrow as pa
from openinference.semconv.resource import ResourceAttributes
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter as GrpcSpanExporter,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.trace import Tracer

from arize._flight.client import ArizeFlightClient
from arize._flight.types import FlightRequestType
from arize.config import SDKConfiguration
from arize.exceptions.base import INVALID_ARROW_CONVERSION_MSG
from arize.experiments.evaluators.base import Evaluators
from arize.experiments.evaluators.types import EvaluationResultFieldNames
from arize.experiments.functions import (
    run_experiment,
    transform_to_experiment_format,
)
from arize.experiments.types import (
    ExperimentTask,
    ExperimentTaskResultFieldNames,
)
from arize.utils.openinference_conversion import (
    convert_boolean_columns_to_str,
    convert_default_columns_to_json_str,
)
from arize.utils.size import get_payload_size_mb

if TYPE_CHECKING:
    import pandas as pd

    from arize._generated.api_client.models.experiment import Experiment


logger = logging.getLogger(__name__)


class ExperimentsClient:
    def __init__(self, sdk_config: SDKConfiguration):
        self._sdk_config = sdk_config
        from arize._generated import api_client as gen

        self._api = gen.ExperimentsApi(self._sdk_config.get_generated_client())
        # TODO(Kiko): Space ID should not be needed,
        # should work on server tech debt to remove this
        self._datasets_api = gen.DatasetsApi(
            self._sdk_config.get_generated_client()
        )
        self.list = self._api.experiments_list
        self.get = self._api.experiments_get
        self.delete = self._api.experiments_delete
        self.list_runs = self._api.experiments_runs_list  # REST ?

        # Custom methods
        self.create = self._create_experiment
        self.run = self._run_experiment

    def _run_experiment(
        self,
        name: str,
        dataset_id: str,
        task: ExperimentTask,
        dataset_df: pd.DataFrame | None = None,
        evaluators: Evaluators | None = None,
        dry_run: bool = False,
        concurrency: int = 3,
        set_global_tracer_provider: bool = False,
        exit_on_error: bool = False,
    ) -> Tuple[str, pd.DataFrame] | None:
        """
        Run an experiment on a dataset and upload the results.

        This function initializes an experiment, retrieves or uses a provided dataset,
        runs the experiment with specified tasks and evaluators, and uploads the results.

        Args:
            experiment_name (str): The name of the experiment.
            task (ExperimentTask): The task to be performed in the experiment.
            dataset_df (Optional[pd.DataFrame], optional): The dataset as a pandas DataFrame.
                If not provided, the dataset will be downloaded using dataset_id or dataset_name.
                Defaults to None.
            dataset_id (Optional[str], optional): The ID of the dataset to use.
                Required if dataset_df and dataset_name are not provided. Defaults to None.
            dataset_name (Optional[str], optional): The name of the dataset to use.
                Used if dataset_df and dataset_id are not provided. Defaults to None.
            evaluators (Optional[Evaluators], optional): The evaluators to use in the experiment.
                Defaults to None.
            dry_run (bool): If True, the experiment result will not be uploaded to Arize.
                Defaults to False.
            concurrency (int): The number of concurrent tasks to run. Defaults to 3.
            set_global_tracer_provider (bool): If True, sets the global tracer provider for the experiment.
                Defaults to False.
            exit_on_error (bool): If True, the experiment will stop running on first occurrence of an error.

        Returns:
            Tuple[str, pd.DataFrame]:
                A tuple of experiment ID and experiment result DataFrame.
                If dry_run is True, the experiment ID will be an empty string.

        Raises:
            ValueError: If dataset_id and dataset_name are both not provided, or if the dataset is empty.
            RuntimeError: If experiment initialization, dataset download, or result upload fails.
        """
        # TODO(Kiko): Space ID should not be needed,
        # should work on server tech debt to remove this
        dataset = self._datasets_api.datasets_get(dataset_id=dataset_id)
        space_id = dataset.space_id

        with ArizeFlightClient(
            api_key=self._sdk_config.api_key,
            host=self._sdk_config.flight_server_host,
            port=self._sdk_config.flight_server_port,
            scheme=self._sdk_config.flight_scheme,
            request_verify=self._sdk_config.request_verify,
            max_chunksize=self._sdk_config.pyarrow_max_chunksize,
        ) as flight_client:
            # set up initial experiment and trace model
            if dry_run:
                trace_model_name = "traces_for_dry_run"
                experiment_id = "experiment_id_for_dry_run"
            else:
                response = None
                try:
                    response = flight_client.init_experiment(
                        space_id=space_id,
                        dataset_id=dataset_id,
                        experiment_name=name,
                    )
                except Exception as e:
                    msg = f"Error during request: {str(e)}"
                    logger.error(msg)
                    raise RuntimeError(msg) from e

                if response is None:
                    # This should not happen with proper Flight client implementation,
                    # but we handle it defensively
                    msg = (
                        "No response received from flight server during request"
                    )
                    logger.error(msg)
                    raise RuntimeError(msg)
                experiment_id, trace_model_name = response

            # download dataset if not provided
            if dataset_df is None:
                try:
                    response = flight_client.get_dataset_examples(
                        space_id=space_id,
                        dataset_id=dataset_id,
                    )
                except Exception as e:
                    msg = f"Error during request: {str(e)}"
                    logger.error(msg)
                    raise RuntimeError(msg) from e
                if response is None:
                    # This should not happen with proper Flight client implementation,
                    # but we handle it defensively
                    msg = (
                        "No response received from flight server during request"
                    )
                    logger.error(msg)
                    raise RuntimeError(msg)

            if dataset_df is None or dataset_df.empty:
                raise ValueError(f"Dataset {dataset_id} is empty")

            input_df = dataset_df.copy()
            if dry_run:
                # only dry_run experiment on a subset (first 10 rows) of the dataset
                input_df = input_df.head(10)

            # trace model and resource for the experiment
            tracer, resource = _get_tracer_resource(
                project_name=trace_model_name,
                space_id=space_id,
                api_key=self._sdk_config.api_key,
                endpoint=self._sdk_config.otlp_url,
                dry_run=dry_run,
                set_global_tracer_provider=set_global_tracer_provider,
            )

            output_df = run_experiment(
                experiment_name=name,
                experiment_id=experiment_id,
                dataset=input_df,
                task=task,
                tracer=tracer,
                resource=resource,
                evaluators=evaluators,
                concurrency=concurrency,
                exit_on_error=exit_on_error,
            )
            output_df = convert_default_columns_to_json_str(output_df)
            output_df = convert_boolean_columns_to_str(output_df)
            if dry_run:
                return "", output_df

            # Convert to Arrow table
            try:
                logger.debug("Converting data to Arrow format")
                pa_table = pa.Table.from_pandas(output_df, preserve_index=False)
            except pa.ArrowInvalid as e:
                logger.error(f"{INVALID_ARROW_CONVERSION_MSG}: {str(e)}")
                raise pa.ArrowInvalid(
                    f"Error converting to Arrow format: {str(e)}"
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error creating Arrow table: {str(e)}")
                raise

            request_type = FlightRequestType.LOG_EXPERIMENT_DATA
            post_resp = None
            try:
                post_resp = flight_client.log_arrow_table(
                    space_id=space_id,
                    pa_table=pa_table,
                    dataset_id=dataset_id,
                    experiment_name=experiment_id,
                    request_type=request_type,
                )
            except Exception as e:
                msg = f"Error during update request: {str(e)}"
                logger.error(msg)
                raise RuntimeError(msg) from e

            if post_resp is None:
                # This should not happen with proper Flight client implementation,
                # but we handle it defensively
                msg = "No response received from flight server during request"
                logger.error(msg)
                raise RuntimeError(msg)

            return str(post_resp.experiment_id), output_df  # type: ignore

    def _create_experiment(
        self,
        name: str,
        dataset_id: str,
        experiment_runs: List[Dict[str, Any]] | pd.DataFrame,
        task_fields: ExperimentTaskResultFieldNames,
        evaluator_columns: Dict[str, EvaluationResultFieldNames] | None = None,
        force_http: bool = False,
    ) -> Experiment:
        """
        Log an experiment to Arize.

        Args:
            space_id (str): The ID of the space where the experiment will be logged.
            experiment_name (str): The name of the experiment.
            experiment_df (pd.DataFrame): The data to be logged.
            task_columns (ExperimentTaskResultColumnNames): The column names for task results.
            evaluator_columns (Optional[Dict[str, EvaluationResultColumnNames]]):
                The column names for evaluator results.
            dataset_id (str, optional): The ID of the dataset associated with the experiment.
                Required if dataset_name is not provided. Defaults to "".
            dataset_name (str, optional): The name of the dataset associated with the experiment.
                Required if dataset_id is not provided. Defaults to "".

        Examples:
            >>> # Example DataFrame:
            >>> df = pd.DataFrame({
            ...     "example_id": ["1", "2"],
            ...     "result": ["success", "failure"],
            ...     "accuracy": [0.95, 0.85],
            ...     "ground_truth": ["A", "B"],
            ...     "explanation_text": ["Good match", "Poor match"],
            ...     "confidence": [0.9, 0.7],
            ...     "model_version": ["v1", "v2"],
            ...     "custom_metric": [0.8, 0.6],
            ...})
            ...
            >>> # Define column mappings for task
            >>> task_cols = ExperimentTaskResultColumnNames(
            ...    example_id="example_id", result="result"
            ...)
            >>> # Define column mappings for evaluator
            >>> evaluator_cols = EvaluationResultColumnNames(
            ...     score="accuracy",
            ...     label="ground_truth",
            ...     explanation="explanation_text",
            ...     metadata={
            ...         "confidence": None,  # Will use "confidence" column
            ...         "version": "model_version",  # Will use "model_version" column
            ...         "custom_metric": None,  # Will use "custom_metric" column
            ...     },
            ... )
            >>> # Use with ArizeDatasetsClient.log_experiment()
            >>> ArizeDatasetsClient.log_experiment(
            ...     space_id="my_space_id",
            ...     experiment_name="my_experiment",
            ...     experiment_df=df,
            ...     task_columns=task_cols,
            ...     evaluator_columns={"my_evaluator": evaluator_cols},
            ...     dataset_name="my_dataset_name",
            ... )

        Returns:
            Optional[str]: The ID of the logged experiment, or None if the logging failed.
        """
        if not isinstance(experiment_runs, (list, pd.DataFrame)):
            raise TypeError(
                "Examples must be a list of dicts or a pandas DataFrame"
            )
        # transform experiment data to experiment format
        experiment_df = transform_to_experiment_format(
            experiment_runs, task_fields, evaluator_columns
        )

        below_threshold = (
            get_payload_size_mb(experiment_runs)
            <= self._sdk_config.max_http_payload_size_mb
        )
        if below_threshold or force_http:
            from arize._generated import api_client as gen

            data = experiment_df.to_dict(orient="records")

            body = gen.ExperimentsCreateRequest(
                name=name,
                datasetId=dataset_id,
                experimentRuns=data,
            )
            return self._api.experiments_create(experiments_create_request=body)

        # If we have too many examples, try to convert to a dataframe
        # and log via gRPC + flight
        logger.info(
            f"Uploading {len(experiment_df)} experiment runs via REST may be slow. "
            "Trying for more efficient upload via gRPC + Flight."
        )

        # TODO(Kiko): Space ID should not be needed,
        # should work on server tech debt to remove this
        dataset = self._datasets_api.datasets_get(dataset_id=dataset_id)
        space_id = dataset.space_id

        return self._create_experiment_via_flight(
            name=name,
            dataset_id=dataset_id,
            space_id=space_id,
            experiment_df=experiment_df,
        )

    def _create_experiment_via_flight(
        self,
        name: str,
        dataset_id: str,
        space_id: str,
        experiment_df: pd.DataFrame,
    ) -> Experiment:
        with ArizeFlightClient(
            api_key=self._sdk_config.api_key,
            host=self._sdk_config.flight_server_host,
            port=self._sdk_config.flight_server_port,
            scheme=self._sdk_config.flight_scheme,
            request_verify=self._sdk_config.request_verify,
            max_chunksize=self._sdk_config.pyarrow_max_chunksize,
        ) as flight_client:
            # set up initial experiment and trace model
            response = None
            try:
                response = flight_client.init_experiment(
                    space_id=space_id,
                    dataset_id=dataset_id,
                    experiment_name=name,
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
            experiment_id, _ = response

        # Convert to Arrow table
        try:
            logger.debug("Converting data to Arrow format")
            pa_table = pa.Table.from_pandas(experiment_df, preserve_index=False)
        except pa.ArrowInvalid as e:
            logger.error(f"{INVALID_ARROW_CONVERSION_MSG}: {str(e)}")
            raise pa.ArrowInvalid(
                f"Error converting to Arrow format: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error creating Arrow table: {str(e)}")
            raise

        request_type = FlightRequestType.LOG_EXPERIMENT_DATA
        post_resp = None
        try:
            post_resp = flight_client.log_arrow_table(
                space_id=space_id,
                pa_table=pa_table,
                dataset_id=dataset_id,
                experiment_name=experiment_id,
                request_type=request_type,
            )
        except Exception as e:
            msg = f"Error during update request: {str(e)}"
            logger.error(msg)
            raise RuntimeError(msg) from e

        if post_resp is None:
            # This should not happen with proper Flight client implementation,
            # but we handle it defensively
            msg = "No response received from flight server during request"
            logger.error(msg)
            raise RuntimeError(msg)

        experiment = self.get(
            experiment_id=str(post_resp.experiment_id)  # type: ignore
        )

        return experiment


def _get_tracer_resource(
    project_name: str,
    space_id: str,
    api_key: str,
    endpoint: str,
    dry_run: bool = False,
    set_global_tracer_provider: bool = False,
) -> Tuple[Tracer, Resource]:
    resource = Resource(
        {
            ResourceAttributes.PROJECT_NAME: project_name,
        }
    )
    tracer_provider = trace_sdk.TracerProvider(resource=resource)
    headers = {
        "authorization": api_key,
        "arize-space-id": space_id,
        "arize-interface": "otel",
    }
    insecure = endpoint.startswith("http://")
    exporter = (
        ConsoleSpanExporter()
        if dry_run
        else GrpcSpanExporter(
            endpoint=endpoint, insecure=insecure, headers=headers
        )
    )
    tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))

    if set_global_tracer_provider:
        trace.set_tracer_provider(tracer_provider)

    return tracer_provider.get_tracer(__name__), resource
