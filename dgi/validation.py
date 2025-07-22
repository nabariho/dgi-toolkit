import logging
from typing import List, Dict, Any, Type
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class DgiRowValidator:
    def __init__(self, model: Type[BaseModel]) -> None:
        self.model = model

    def validate_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        valid_rows: List[Dict[str, Any]] = []
        errors: List[str] = []
        for i, row in enumerate(rows):
            try:
                valid_rows.append(self.model(**row).dict())
            except ValidationError as e:
                error_msg = f"Row {i+2}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        if errors:
            logger.error("Validation errors:\n%s", "\n".join(errors))
            raise ValueError("Validation errors:\n" + "\n".join(errors))
        return valid_rows
