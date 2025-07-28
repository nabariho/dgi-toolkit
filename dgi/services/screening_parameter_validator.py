"""Screening parameter validation service."""

from dgi.exceptions import DataValidationError


class ScreeningParameterValidator:
    """Validates screening parameters according to business rules."""

    @staticmethod
    def validate_screening_parameters(
        min_yield: float, max_payout: float, min_cagr: float, top_n: int
    ) -> None:
        """Validate screening parameters using business rules.

        Args:
            min_yield: Minimum dividend yield (decimal, e.g., 0.02 for 2%)
            max_payout: Maximum payout ratio (percentage, e.g., 80.0 for 80%)
            min_cagr: Minimum dividend CAGR (decimal, e.g., 0.05 for 5%)
            top_n: Number of top stocks to return

        Raises:
            DataValidationError: If any parameter is invalid
        """
        ScreeningParameterValidator._validate_yield(min_yield)
        ScreeningParameterValidator._validate_payout(max_payout)
        ScreeningParameterValidator._validate_cagr(min_cagr)
        ScreeningParameterValidator._validate_top_n(top_n)

    @staticmethod
    def _validate_yield(min_yield: float) -> None:
        """Validate minimum yield parameter."""
        if min_yield < 0:
            raise DataValidationError("Minimum yield must be non-negative")
        if min_yield > 1.0:
            raise DataValidationError(
                "Minimum yield should be a decimal (e.g., 0.02 for 2%)"
            )

    @staticmethod
    def _validate_payout(max_payout: float) -> None:
        """Validate maximum payout parameter."""
        if max_payout < 0:
            raise DataValidationError("Maximum payout ratio must be non-negative")
        if max_payout > 200:
            raise DataValidationError("Maximum payout ratio must be between 0 and 200")

    @staticmethod
    def _validate_cagr(min_cagr: float) -> None:
        """Validate minimum CAGR parameter."""
        if min_cagr < -1.0:
            raise DataValidationError("Minimum CAGR must be greater than -100%")
        if min_cagr > 1.0:
            raise DataValidationError("Minimum CAGR must be less than 100%")

    @staticmethod
    def _validate_top_n(top_n: int) -> None:
        """Validate top N parameter."""
        if top_n < 1:
            raise DataValidationError("Top N must be at least 1")
        if top_n > 1000:
            raise DataValidationError("Top N must be less than or equal to 1000")
