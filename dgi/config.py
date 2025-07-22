import os


class Config:
    DATA_PATH: str
    LOG_LEVEL: str
    DEFAULT_MIN_YIELD: float
    DEFAULT_MAX_PAYOUT: float
    DEFAULT_MIN_CAGR: float

    def __init__(self):
        self.DATA_PATH = os.getenv("DGI_DATA_PATH", "data/fundamentals_small.csv")
        self.LOG_LEVEL = os.getenv("DGI_LOG_LEVEL", "INFO")
        self.DEFAULT_MIN_YIELD = float(os.getenv("DGI_MIN_YIELD", "0.0"))
        self.DEFAULT_MAX_PAYOUT = float(os.getenv("DGI_MAX_PAYOUT", "100.0"))
        self.DEFAULT_MIN_CAGR = float(os.getenv("DGI_MIN_CAGR", "0.0"))


def get_config() -> Config:
    return Config()
