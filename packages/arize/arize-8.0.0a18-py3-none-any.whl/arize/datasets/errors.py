from abc import ABC, abstractmethod


class DatasetError(Exception, ABC):
    def __str__(self) -> str:
        return self.error_message()

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def error_message(self) -> str:
        pass


class InvalidSessionError(DatasetError):
    def error_message(self) -> str:
        return (
            "Credentials not provided or invalid. Please pass in the correct api_key when "
            "initiating a new ArizeExportClient. Alternatively, you can set up credentials "
            "in a profile or as an environment variable"
        )

    def __repr__(self) -> str:
        return "InvalidSessionError()"


class InvalidConfigFileError(DatasetError):
    def error_message(self) -> str:
        return "Invalid/Misconfigured Configuration File"

    def __repr__(self) -> str:
        return "InvalidConfigFileError()"


class IDColumnUniqueConstraintError(DatasetError):
    def error_message(self) -> str:
        return "'id' column must contain unique values"

    def __repr__(self) -> str:
        return "IDColumnUniqueConstraintError()"


class RequiredColumnsError(DatasetError):
    def __init__(self, missing_columns: set) -> None:
        self.missing_columns = missing_columns

    def error_message(self) -> str:
        return f"Missing required columns: {self.missing_columns}"

    def __repr__(self) -> str:
        return f"RequiredColumnsError({self.missing_columns})"


class EmptyDatasetError(DatasetError):
    def error_message(self) -> str:
        return "DataFrame must have at least one row in it."

    def __repr__(self) -> str:
        return "EmptyDatasetError()"
