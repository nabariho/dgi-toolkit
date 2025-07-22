import logging
from typing import List, Dict, Any, Type, Optional
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class DgiRowValidator:
    def __init__(
        self, model: Type[BaseModel], required_columns: Optional[List[str]] = None
    ) -> None:
        self.model = model
        self.required_columns = required_columns

    def validate_rows(self, rows: List[Dict[Any, Any]]) -> List[Dict[str, Any]]:
        valid_rows: List[Dict[str, Any]] = []
        errors: List[str] = []
        for i, row in enumerate(rows):
            # Normalize keys to str
            row_str_keys = {str(k): v for k, v in row.items()}
            # Check required columns
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
                valid_rows.append(self.model(**row_str_keys).dict())
            except ValidationError as e:
                error_msg = f"Row {i+2}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        if errors:
            logger.error(
                "Validation errors:\n%s",
                "\n".join(errors),
            )
            raise ValueError("Validation errors:\n" + "\n".join(errors))
        return valid_rows
