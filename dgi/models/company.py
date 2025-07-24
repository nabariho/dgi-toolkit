from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator  # type: ignore


class CompanyData(BaseModel):
    """Model for company financial data."""

    symbol: Annotated[str, Field(min_length=1, max_length=10)]
    name: Annotated[str, Field(min_length=1)]
    sector: Annotated[str, Field(min_length=1)]
    industry: Annotated[str, Field(min_length=1)]
    dividend_yield: Annotated[float, Field(ge=0.0, le=100.0)]  # Allow up to 100% yield
    payout_ratio: Annotated[
        float, Field(ge=0.0, le=200.0, alias="payout")
    ]  # Allow up to 200% payout
    dividend_growth_5y: Annotated[
        float, Field(ge=-100.0, le=100.0, alias="dividend_cagr")
    ]  # Allow negative growth
    fcf_yield: Annotated[float, Field(ge=-100.0, le=100.0)]  # Allow negative FCF yield

    # Aliased properties for backwards compatibility
    @property
    def company_name(self) -> str:
        """Alias for 'name' field."""
        return self.name

    @property
    def payout(self) -> float:
        """Alias for 'payout_ratio' field."""
        return self.payout_ratio

    @property
    def dividend_cagr(self) -> float:
        """Alias for 'dividend_growth_5y' field."""
        return self.dividend_growth_5y

    @classmethod
    @field_validator(
        "dividend_yield",
        "payout_ratio",
        "dividend_growth_5y",
        "fcf_yield",
        mode="before",
    )
    def must_be_number(cls, v: Any) -> float:
        if isinstance(v, int | float):
            return float(v)
        try:
            return float(v)
        except Exception as e:
            raise ValueError(f"Value '{v}' is not a valid number") from e
