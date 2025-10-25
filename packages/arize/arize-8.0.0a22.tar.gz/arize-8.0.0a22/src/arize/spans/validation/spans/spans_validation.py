from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, List

from arize.spans.columns import SPAN_OPENINFERENCE_REQUIRED_COLUMNS
from arize.spans.validation.common import (
    argument_validation as common_arg_validation,
)
from arize.spans.validation.common import (
    dataframe_form_validation as common_df_validation,
)
from arize.spans.validation.common import (
    value_validation as common_value_validation,
)
from arize.spans.validation.spans import (
    dataframe_form_validation as df_validation,
)
from arize.spans.validation.spans import value_validation

if TYPE_CHECKING:
    import pandas as pd

    from arize.exceptions.base import ValidationError


def validate_argument_types(
    spans_dataframe: pd.DataFrame,
    project_name: str,
    dt_fmt: str,
    model_version: str | None = None,
) -> List[ValidationError]:
    checks = chain(
        common_arg_validation.check_field_convertible_to_str(
            project_name, model_version
        ),
        common_arg_validation.check_dataframe_type(spans_dataframe),
        common_arg_validation.check_datetime_format_type(dt_fmt),
    )
    return list(checks)


def validate_dataframe_form(
    spans_dataframe: pd.DataFrame,
) -> List[ValidationError]:
    df_validation.log_info_dataframe_extra_column_names(spans_dataframe)
    checks = chain(
        # Common
        common_df_validation.check_dataframe_index(spans_dataframe),
        common_df_validation.check_dataframe_required_column_set(
            spans_dataframe,
            required_columns=[
                col.name for col in SPAN_OPENINFERENCE_REQUIRED_COLUMNS
            ],
        ),
        common_df_validation.check_dataframe_for_duplicate_columns(
            spans_dataframe
        ),
        # Spans specific
        df_validation.check_dataframe_column_content_type(spans_dataframe),
    )
    return list(checks)


def validate_values(
    spans_dataframe: pd.DataFrame,
    project_name: str,
    model_version: str | None = None,
) -> List[ValidationError]:
    checks = chain(
        # Common
        common_value_validation.check_invalid_project_name(project_name),
        common_value_validation.check_invalid_model_version(model_version),
        # Spans specific
        value_validation.check_span_root_field_values(spans_dataframe),
        value_validation.check_span_attributes_values(spans_dataframe),
    )
    return list(checks)
