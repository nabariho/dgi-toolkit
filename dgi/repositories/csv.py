import pandas as pd

from dgi.models import CompanyData
from dgi.repositories.base import CompanyDataRepository
from dgi.validation import DgiRowValidator


class CsvCompanyDataRepository(CompanyDataRepository):
    def __init__(self, csv_path: str, validator: DgiRowValidator):
        self.csv_path = csv_path
        self.validator = validator

    def get_rows(self) -> list[CompanyData]:
        df_raw = pd.read_csv(self.csv_path, dtype=str)
        # Convert to list of dicts with string keys to satisfy type checker
        records = df_raw.to_dict(orient="records")
        string_key_records = [
            {str(k): v for k, v in record.items()} for record in records
        ]
        return self.validator.validate_rows(string_key_records)
