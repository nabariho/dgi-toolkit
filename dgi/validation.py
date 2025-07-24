import logging
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import ValidationError

if TYPE_CHECKING:
    from dgi.models import CompanyData
else:
    try:
        from dgi.models import CompanyData
    except ImportError:
        CompanyData = Any  # type: ignore

from dgi.exceptions import DataValidationError

# Export for external use
__all__ = ["DataValidationError", "DgiRowValidator", "PydanticRowValidation"]

logger = logging.getLogger(__name__)


class RowValidationStrategy(Protocol):
    """Interface for row validation strategies."""

    def validate(self, row: dict[str, Any]) -> "CompanyData": ...


class PydanticRowValidation:
    def __init__(self, model: type["CompanyData"]) -> None:
        self.model = model

    def validate(self, row: dict[str, Any]) -> "CompanyData":
        return self.model.model_validate(row)


class DgiRowValidator:
    """Validates CSV rows for DGI analysis."""

    def __init__(self, strategy: RowValidationStrategy) -> None:
        self._strategy = (
            strategy  # Remove explicit type annotation that was causing issues
        )
        self.required_columns = (
            None  # This attribute is no longer used in the new_code, but kept for now
        )

    def validate_rows(
        self, rows: list[dict[str, Any]]
    ) -> list["CompanyData"]:  # Fix type
        valid_rows: list[CompanyData] = []
        errors: list[str] = []
        for i, row in enumerate(rows):
            row_str_keys = {str(k): v for k, v in row.items()}
            if self.required_columns:
                missing = [
                    col for col in self.required_columns if col not in row_str_keys
                ]
                if missing:
                    error_msg = f"Row {i + 2}: Missing: {', '.join(missing)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            try:
                validated = self._strategy.validate(row_str_keys)
                valid_rows.append(validated)
            except ValidationError as e:
                error_msg = f"Row {i + 2}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Row {i + 2}: Unexpected error: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        if not valid_rows:
            logger.error("Validation errors:\n%s", "\n".join(errors))
            raise DataValidationError("Validation errors:\n" + "\n".join(errors))
        if errors:
            logger.warning("Some rows were invalid and skipped:\n%s", "\n".join(errors))
        return valid_rows
