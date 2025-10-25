from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Tuple

JSONSerializable = Dict[str, Any] | List[Any] | str | int | float | bool


class AnnotatorKind(Enum):
    CODE = "CODE"
    LLM = "LLM"


EvaluatorKind = str
EvaluatorName = str

Score = bool | int | float | None
Label = str | None
Explanation = str | None


@dataclass(frozen=True)
class EvaluationResult:
    """
    Represents the result of an evaluation.
    Args:
        score: The score of the evaluation.
        label: The label of the evaluation.
        explanation: The explanation of the evaluation.
        metadata: Additional metadata for the evaluation.
    """

    score: float | None = None
    label: str | None = None
    explanation: str | None = None
    metadata: Mapping[str, JSONSerializable] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls, obj: Mapping[str, Any] | None
    ) -> EvaluationResult | None:
        if not obj:
            return None
        return cls(
            score=obj.get("score"),
            label=obj.get("label"),
            explanation=obj.get("explanation"),
            metadata=obj.get("metadata") or {},
        )

    def __post_init__(self) -> None:
        if self.score is None and not self.label:
            raise ValueError("Must specify score or label, or both")
        if self.score is None and not self.label:
            object.__setattr__(self, "score", 0)
        for k in ("label", "explanation"):
            v = getattr(self, k, None)
            if v is not None:
                object.__setattr__(self, k, str(v) or None)


EvaluatorOutput = (
    EvaluationResult
    | bool
    | int
    | float
    | str
    | Tuple[Score, Label, Explanation]
)


@dataclass
class EvaluationResultFieldNames:
    """Column names for mapping evaluation results in a DataFrame.

    Args:
        score: Optional name of column containing evaluation scores
        label: Optional name of column containing evaluation labels
        explanation: Optional name of column containing evaluation explanations
        metadata: Optional mapping of metadata keys to column names. If a column name
            is None or empty string, the metadata key will be used as the column name.

    Examples:
        >>> # Basic usage with score and label columns
        >>> EvaluationResultColumnNames(
        ...     score="quality.score", label="quality.label"
        ... )

        >>> # Using metadata with same key and column name
        >>> EvaluationResultColumnNames(
        ...     score="quality.score",
        ...     metadata={
        ...         "version": None
        ...     },  # Will look for column named "version"
        ... )

        >>> # Using metadata with different key and column name
        >>> EvaluationResultColumnNames(
        ...     score="quality.score",
        ...     metadata={
        ...         # Will look for "column_in_my_df.version" column and ingest as
        ...         # "eval.{EvaluatorName}.meatadata.model_version"
        ...         "model_version": "column_in_my_df.version",
        ...         # Will look for "column_in_my_df.ts" column and ingest as
        ...         # "eval.{EvaluatorName}.metadata.timestamp"
        ...         "timestamp": "column_in_my_df.ts",
        ...     },
        ... )

    Raises:
        ValueError: If neither score nor label column names are specified
    """

    score: str | None = None
    label: str | None = None
    explanation: str | None = None
    metadata: Dict[str, str | None] | None = None

    def __post_init__(self) -> None:
        if self.score is None and self.label is None:
            raise ValueError("Must specify score or label column name, or both")
