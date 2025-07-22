from pydantic import BaseModel, validator
from typing import Any


class DgiRow(BaseModel):
    symbol: str
    name: str
    sector: str
    industry: str
    dividend_yield: float
    payout: float
    dividend_cagr: float
    fcf_yield: float

    @validator("dividend_yield", "payout", "dividend_cagr", "fcf_yield", pre=True)
    def must_be_number(cls, v: Any) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(v)
        except Exception:
            raise ValueError(f"Value '{v}' is not a valid number")
