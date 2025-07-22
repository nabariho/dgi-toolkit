import logging
from typing import Any, Protocol
from pydantic import ValidationError
from dgi.models import CompanyData
from dgi.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class RowValidationStrategy(Protocol):
    """
    Interface for row validation strategies.
    """

    def validate(self, row: dict[str, Any]) -> CompanyData: ...


class PydanticRowValidation:
    def __init__(self, model: type[CompanyData]):
        self.model = model

    def validate(self, row: dict[str, Any]) -> CompanyData:
        return self.model(**row)


class DgiRowValidator:
    """
    Validates rows of data using a pluggable validation strategy and required columns check.
    """

    def __init__(
        self,
        validation_strategy: RowValidationStrategy | None = None,
        required_columns: list[str] | None = None,
    ) -> None:
        if validation_strategy is None:
            self.validation_strategy = PydanticRowValidation(CompanyData)
        else:
            self.validation_strategy = validation_strategy
        self.required_columns = required_columns

    def validate_rows(self, rows: list[dict[str, Any]]) -> list[CompanyData]:
        valid_rows: list[CompanyData] = []
        errors: list[str] = []
        for i, row in enumerate(rows):
            row_str_keys = {str(k): v for k, v in row.items()}
            if self.required_columns:
                missing = [
                    col for col in self.required_columns if col not in row_str_keys
                ]
                if missing:
                    error_msg = f"Row {i+2}: Missing: {', '.join(missing)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            try:
                validated = self.validation_strategy.validate(row_str_keys)
                valid_rows.append(validated)
            except ValidationError as e:
                error_msg = f"Row {i+2}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Row {i+2}: Unexpected error: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        if not valid_rows:
            logger.error("Validation errors:\n%s", "\n".join(errors))
            raise DataValidationError("Validation errors:\n" + "\n".join(errors))
        if errors:
            logger.warning("Some rows were invalid and skipped:\n%s", "\n".join(errors))
        return valid_rows
