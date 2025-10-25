# type: ignore[pb2]
from __future__ import annotations

import math
from typing import TYPE_CHECKING, List, Tuple, Union

import numpy as np

from arize.logging import log_a_list
from arize.types import ArizeTypes, Schema, TypedColumns, TypedValue, is_list_of

if TYPE_CHECKING:
    import pandas as pd


class CastingError(Exception):
    def __str__(self) -> str:
        return self.error_message()

    def __init__(self, error_msg: str, typed_value: TypedValue) -> None:
        self.error_msg = error_msg
        self.typed_value = typed_value

    def error_message(self) -> str:
        return (
            f"Failed to cast value {self.typed_value.value} of type {type(self.typed_value.value)} "
            f"to type {self.typed_value.type}. "
            f"Error: {self.error_msg}."
        )


class ColumnCastingError(Exception):
    def __str__(self) -> str:
        return self.error_message()

    def __init__(
        self,
        error_msg: str,
        attempted_columns: str,
        attempted_type: TypedColumns,
    ) -> None:
        self.error_msg = error_msg
        self.attempted_casting_columns = attempted_columns
        self.attempted_casting_type = attempted_type

    def error_message(self) -> str:
        return (
            f"Failed to cast to type {self.attempted_casting_type} "
            f"for columns: {log_a_list(self.attempted_casting_columns, 'and')}. "
            f"Error: {self.error_msg}"
        )


class InvalidTypedColumnsError(Exception):
    def __str__(self) -> str:
        return self.error_message()

    def __init__(self, field_name: str, reason: str) -> None:
        self.field_name = field_name
        self.reason = reason

    def error_message(self) -> str:
        return f"The {self.field_name} TypedColumns object {self.reason}."


class InvalidSchemaFieldTypeError(Exception):
    def __str__(self) -> str:
        return self.error_message()

    def __init__(self, msg: str) -> None:
        self.msg = msg

    def error_message(self) -> str:
        return self.msg


def cast_typed_columns(
    dataframe: pd.DataFrame,
    schema: Schema,
) -> Tuple[pd.DataFrame, Schema]:
    """
    Cast feature and tag columns in the dataframe to the types specified in each TypedColumns config.
    This optional feature provides a simple way for users to prevent
    type drift within a column across many SDK uploads.

    Arguments:
    ---------
        dataframe: pd.DataFrame
            A deepcopy of the user's dataframe.
        schema: Schema
            The schema, which may include feature and tag column names
            in a TypedColumns object or a List[string].

    Returns:
    -------
        dataframe: pd.DataFrame
            The dataframe, with columns cast to the specified types.
        schema: Schema
            A new Schema object, with feature and tag column names converted to the List[string] format
            expected in downstream validation.

    Raises:
    ------
        ColumnCastingError
            If casting fails.
        InvalidTypedColumnsError
            If the TypedColumns object is invalid.

    """
    typed_column_fields = schema.typed_column_fields()
    feature_field = "feature_column_names"
    tag_field = "tag_column_names"
    allowed_fields = {feature_field, tag_field}

    # Make sure the schema has typed column fields.
    if not typed_column_fields:
        raise InvalidSchemaFieldTypeError(
            "The Schema object does not have any fields of type TypedColumns. "
            "Cannot cast dataframe columns."
        )

    # Make sure no other schema fields have this type.
    if any({f for f in typed_column_fields if f not in allowed_fields}):
        raise InvalidSchemaFieldTypeError(
            "Only the feature_column_names and tag_column_names Schema fields can be of type "
            "TypedColumns. Fields with type TypedColumns:"
            + str(typed_column_fields)
        )

    for field_name in typed_column_fields:
        f = getattr(schema, field_name)
        if f:
            try:
                _validate_typed_columns(field_name, f)
            except InvalidTypedColumnsError:
                raise
            dataframe = _cast_columns(dataframe, f)

    # Now that the dataframe values have been cast to the specified types:
    # for downstream validation to work as expected,
    # feature & tag schema field types should be List[string] of column names.
    # Since Schema is a frozen class, we must construct a new instance.
    return dataframe, _convert_schema_field_types(schema)


def cast_dictionary(d: dict) -> dict:
    cast_dict = {}
    for k, v in d.items():
        if isinstance(v, TypedValue):
            v = _cast_value(v)
        cast_dict[k] = v
    return cast_dict


def _cast_value(
    typed_value: TypedValue,
) -> Union[str, int, float, List[str], None]:
    """
    Casts a TypedValue to its provided type, preserving all null values as None or float('nan').

    Arguments:
    ---------
    typed_value: TypedValue
        The TypedValue to cast.

    Returns:
    -------
    Union[str, int, float, List[str], None]
        The cast value.

    Raises:
    ------
    CastingError
        If the value cannot be cast to the provided type.

    """
    if typed_value.value is None:
        return None

    if typed_value.type == ArizeTypes.FLOAT:
        return _cast_to_float(typed_value)
    elif typed_value.type == ArizeTypes.INT:
        return _cast_to_int(typed_value)
    elif typed_value.type == ArizeTypes.STR:
        return _cast_to_str(typed_value)
    else:
        raise CastingError("Unknown casting type", typed_value)


def _cast_to_float(typed_value: TypedValue) -> Union[float, None]:
    try:
        return float(typed_value.value)
    except Exception as e:
        raise CastingError(str(e), typed_value) from e


def _cast_to_int(typed_value: TypedValue) -> Union[int, None]:
    # a NaN float can't be cast to an int. Proactively return None instead.
    if isinstance(typed_value.value, float) and math.isnan(typed_value.value):
        return None
    # If the value is a float, to avoid losing data precision,
    # we can only cast to an int if it is equivalent to an integer (e.g. 7.0).
    if (
        isinstance(typed_value.value, float)
        and not typed_value.value.is_integer()
    ):
        raise CastingError(
            "Cannot convert float with non-zero fractional part to int",
            typed_value,
        )
    try:
        return int(typed_value.value)
    except Exception as e:
        raise CastingError(str(e), typed_value) from e


def _cast_to_str(typed_value: TypedValue) -> Union[str, None]:
    # a NaN float can't be cast to a string. Proactively return None instead.
    if isinstance(typed_value.value, float) and math.isnan(typed_value.value):
        return None
    try:
        return str(typed_value.value)
    except Exception as e:
        raise CastingError(str(e), typed_value) from e


def _validate_typed_columns(
    field_name: str, typed_columns: TypedColumns
) -> None:
    """
    Validate a TypedColumns object.

    Arguments:
    ---------
        field_name: str
            The name of the Schema field that the TypedColumns object is associated with.
        typed_columns: TypedColumns
            The TypedColumns object to validate.

    Raises:
    ------
        InvalidTypedColumnsError
            If the TypedColumns object is invalid.

    """
    if typed_columns.is_empty():
        raise InvalidTypedColumnsError(field_name=field_name, reason="is empty")
    has_duplicates, duplicates = typed_columns.has_duplicate_columns()
    if has_duplicates:
        raise InvalidTypedColumnsError(
            field_name=field_name,
            reason=f"has duplicate column names: {log_a_list(list(duplicates), 'and')}",
        )


def _cast_columns(
    dataframe: pd.DataFrame, columns: TypedColumns
) -> pd.DataFrame:
    """
    Cast columns corresponding to a single TypedColumns object and a single Arize Schema field.
    (feature_column_names or tag_column_names)

    Arguments:
    ---------
        dataframe: pd.DataFrame
            A deepcopy of the user's dataframe.
        columns: TypedColumns
            The TypedColumns object, which specifies the columns to cast
            (and/or to not cast) and their target types.

    Returns:
    -------
        dataframe: pd.DataFrame
            The dataframe with columns cast to the specified types.

    Raises:
    ------
        ColumnCastingError
            If casting fails.

    """
    if columns.to_str:
        try:
            # Nullable StringDtype is an experimental feature:
            # https://pandas.pydata.org/docs/reference/api/pandas.StringDtype.html
            # https://pandas.pydata.org/docs/user_guide/text.html#working-with-text-data
            # 'string' is an alias for StringDtype
            # uses pd.NA for missing values (when storage arg is not configured)
            # In the future, try out pd.convert_dtypes (new in pandas 2.0):
            # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.convert_dtypes.html
            dataframe = _cast_df(dataframe, columns.to_str, "string")
        except Exception as e:
            raise ColumnCastingError(
                error_msg=str(e),
                attempted_columns=columns.to_str,
                attempted_type="string",
            ) from e
    if columns.to_int:
        # pandas nullable type must be capitalized: 'Int64'
        # see https://pandas.pydata.org/docs/reference/api/pandas.Int64Dtype.html
        # uses pd.NA for missing values
        try:
            dataframe = _cast_df(dataframe, columns.to_int, "Int64")
        except Exception as e:
            raise ColumnCastingError(
                error_msg=str(e),
                attempted_columns=columns.to_int,
                attempted_type="Int64",
            ) from e
    if columns.to_float:
        # pandas nullable type must be capitalized: 'Float64'
        # see https://pandas.pydata.org/docs/reference/api/pandas.Float64Dtype.html
        # uses pd.NA for missing values
        try:
            dataframe = _cast_df(dataframe, columns.to_float, "Float64")
        except Exception as e:
            raise ColumnCastingError(
                error_msg=str(e),
                attempted_columns=columns.to_float,
                attempted_type="Float64",
            ) from e

    return dataframe


def _cast_df(
    df: pd.DataFrame, cols: List[str], target_type_str: str
) -> pd.DataFrame:
    """
    Arguments:
    ---------
        df: pd.DataFrame
            A deepcopy of the user's dataframe.
        cols: List[str]
            The list of column names to cast.
        target_type_str: str
            The target type to cast to.

    Returns:
    -------
        df: pd.DataFrame
            The dataframe with columns cast to the specified types.

    Raises:
    ------
        Exception
            If casting fails. Common exceptions raised by astype() are TypeError and ValueError.

    """
    nan_mapping = {"nan": np.nan, "NaN": np.nan}
    df = df.replace(nan_mapping)

    # None or NaN-based values (including np.nan) are automatically converted to pandas pd.NA type
    return df.astype({col: target_type_str for col in cols})


def _convert_schema_field_types(
    schema: Schema,
) -> Schema:
    """
    Arguments:
    ---------
        schema: Schema
            The schema, which may include feature and tag column names
            in a TypedColumns object or a List[string].

    Returns:
    -------
        schema: Schema
            A Schema, with feature and tag column names
            converted to the List[string] format expected in downstream validation.

    """
    feature_column_names_list = (
        schema.feature_column_names
        if is_list_of(schema.feature_column_names, str)
        else (
            schema.feature_column_names.get_all_column_names()
            if schema.feature_column_names
            else []
        )
    )

    tag_column_names_list = (
        schema.tag_column_names
        if is_list_of(schema.tag_column_names, str)
        else schema.tag_column_names.get_all_column_names()
        if schema.tag_column_names
        else []
    )

    schema_dict = {
        "feature_column_names": feature_column_names_list,
        "tag_column_names": tag_column_names_list,
    }
    return schema.replace(**schema_dict)
