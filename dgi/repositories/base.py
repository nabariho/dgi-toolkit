from abc import ABC, abstractmethod

from dgi.models import CompanyData


class CompanyDataRepository(ABC):
    @abstractmethod
    def get_rows(self) -> list[CompanyData]:
        """Return a list of validated CompanyData objects from the data source."""
