from pydantic import BaseModel, validator, constr, confloat, Field
from typing import Any


class CompanyData(BaseModel):
    """
    Data model for a single company's fundamental data for DGI analysis.
    All fields are validated and type-checked for enterprise reliability.
    """

    symbol: constr(strip_whitespace=True, min_length=1) = Field(
        ..., description="Ticker symbol"
    )
    name: constr(strip_whitespace=True, min_length=1) = Field(
        ..., description="Company name"
    )
    sector: constr(strip_whitespace=True, min_length=1) = Field(
        ..., description="Sector"
    )
    industry: constr(strip_whitespace=True, min_length=1) = Field(
        ..., description="Industry"
    )
    dividend_yield: confloat(ge=0.0) = Field(..., description="Dividend yield (%)")
    payout: confloat(ge=0.0, le=100.0) = Field(..., description="Payout ratio (%)")
    dividend_cagr: confloat(ge=0.0) = Field(..., description="Dividend CAGR (%)")
    fcf_yield: confloat(ge=0.0) = Field(..., description="Free cash flow yield (%)")

    @validator("dividend_yield", "payout", "dividend_cagr", "fcf_yield", pre=True)
    def must_be_number(cls, v: Any) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(v)
        except Exception:
            raise ValueError(f"Value '{v}' is not a valid number")
