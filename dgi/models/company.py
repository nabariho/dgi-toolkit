from typing import Any
from pydantic import BaseModel, validator, Field
from pydantic.types import constr, confloat


class CompanyData(BaseModel):
    """Model for company financial data."""

    symbol: constr(min_length=1, max_length=10)  # type: ignore
    name: constr(min_length=1)  # type: ignore
    sector: constr(min_length=1)  # type: ignore
    industry: constr(min_length=1)  # type: ignore
    dividend_yield: confloat(ge=0.0, le=100.0)  # type: ignore  # Allow up to 100% yield
    payout_ratio: confloat(ge=0.0, le=200.0) = Field(alias="payout")  # type: ignore  # Allow up to 200% payout
    dividend_growth_5y: confloat(ge=-50.0, le=100.0) = Field(alias="dividend_cagr")  # type: ignore  # Allow negative growth
    fcf_yield: confloat(ge=-50.0, le=100.0)  # type: ignore  # Allow negative FCF yield

    class Config:
        allow_population_by_field_name = True

    # Support old field names as aliases
    @property
    def payout(self) -> float:
        return float(self.payout_ratio)

    @property
    def dividend_cagr(self) -> float:
        return float(self.dividend_growth_5y)

    @validator(
        "dividend_yield", "payout_ratio", "dividend_growth_5y", "fcf_yield", pre=True
    )
    def must_be_number(cls, v: Any) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(v)
        except Exception:
            raise ValueError(f"Value '{v}' is not a valid number")
