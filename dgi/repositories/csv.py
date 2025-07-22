from typing import List
import pandas as pd
from dgi.models import CompanyData
from dgi.validation import DgiRowValidator
from dgi.repositories.base import CompanyDataRepository


class CsvCompanyDataRepository(CompanyDataRepository):
    def __init__(self, csv_path: str, validator: DgiRowValidator):
        self.csv_path = csv_path
        self.validator = validator

    def get_rows(self) -> List[CompanyData]:
        df_raw = pd.read_csv(self.csv_path, dtype=str)
        return self.validator.validate_rows(df_raw.to_dict(orient="records"))
