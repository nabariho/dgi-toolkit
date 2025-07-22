from abc import ABC, abstractmethod
from typing import List
from dgi.models import CompanyData


class CompanyDataRepository(ABC):
    @abstractmethod
    def get_rows(self) -> List[CompanyData]:
        """Return a list of validated CompanyData objects from the data source."""
        pass
