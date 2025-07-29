"""API response mapping service with single responsibility for data transformation."""

import logging
from typing import Any

import pandas as pd
from pandas import DataFrame

from dgi.models import CompanyData

logger = logging.getLogger(__name__)


class ScreeningResponseMapper:
    """Service for mapping screening results to API response format."""

    @staticmethod
    def to_api_response(df: DataFrame) -> list[dict[str, Any]]:
        """Convert DataFrame to API response format.

        Args:
            df: DataFrame containing screening results

        Returns:
            List of dictionaries in API response format
        """
        if df.empty:
            logger.info("Empty DataFrame, returning empty response")
            return []

        try:
            # Convert DataFrame to list of dictionaries
            response_data = df.to_dict("records")

            # Ensure all values are serializable
            serializable_data: list[dict[str, Any]] = []
            for record in response_data:
                serializable_record: dict[str, Any] = {}
                for key, value in record.items():
                    # Handle NaN values and other non-serializable types
                    if pd.isna(value):
                        serializable_record[str(key)] = None
                    elif isinstance(value, int | float | str | bool):
                        serializable_record[str(key)] = value
                    else:
                        serializable_record[str(key)] = str(value)
                serializable_data.append(serializable_record)

            logger.info(
                f"Converted {len(serializable_data)} records to API response format"
            )
            return serializable_data

        except Exception as e:
            logger.error(f"Error converting DataFrame to API response: {e}")
            raise ValueError(
                f"Failed to convert data to API response format: {e}"
            ) from e

    @staticmethod
    def to_company_data_response(companies: list[CompanyData]) -> list[dict[str, Any]]:
        """Convert CompanyData objects to API response format.

        Args:
            companies: List of CompanyData objects

        Returns:
            List of dictionaries in API response format
        """
        if not companies:
            logger.info("Empty company list, returning empty response")
            return []

        try:
            response_data = []
            for company in companies:
                company_dict = company.model_dump()
                response_data.append(company_dict)

            logger.info(
                f"Converted {len(response_data)} company objects to API response format"
            )
            return response_data

        except Exception as e:
            logger.error(f"Error converting CompanyData to API response: {e}")
            raise ValueError(
                f"Failed to convert company data to API response format: {e}"
            ) from e

    @staticmethod
    def to_screening_summary_response(df: DataFrame, top_n: int) -> dict[str, Any]:
        """Convert screening results to summary response format.

        Args:
            df: DataFrame containing screening results
            top_n: Number of top results requested

        Returns:
            Dictionary containing screening summary
        """
        try:
            total_companies = len(df)
            returned_companies = min(top_n, total_companies)

            summary = {
                "total_companies_screened": total_companies,
                "companies_returned": returned_companies,
                "screening_criteria": {
                    "top_n": top_n,
                },
                "results": ScreeningResponseMapper.to_api_response(df.head(top_n)),
            }

            logger.info(
                f"Created screening summary: {total_companies} screened, {returned_companies} returned"
            )
            return summary

        except Exception as e:
            logger.error(f"Error creating screening summary: {e}")
            raise ValueError(f"Failed to create screening summary: {e}") from e

    @staticmethod
    def to_error_response(
        error_message: str, error_code: str | None = None
    ) -> dict[str, Any]:
        """Convert error to API response format.

        Args:
            error_message: Error message
            error_code: Optional error code

        Returns:
            Dictionary containing error response
        """
        error_response = {"error": True, "message": error_message, "data": None}

        if error_code:
            error_response["error_code"] = error_code

        logger.info(f"Created error response: {error_message}")
        return error_response

    @staticmethod
    def to_success_response(data: Any, message: str | None = None) -> dict[str, Any]:
        """Convert successful result to API response format.

        Args:
            data: Response data
            message: Optional success message

        Returns:
            Dictionary containing success response
        """
        response = {"error": False, "data": data}

        if message:
            response["message"] = message

        logger.debug("Created success response")
        return response


class PortfolioResponseMapper:
    """Service for mapping portfolio results to API response format."""

    @staticmethod
    def to_portfolio_response(portfolio_data: dict[str, Any]) -> dict[str, Any]:
        """Convert portfolio data to API response format.

        Args:
            portfolio_data: Portfolio data dictionary

        Returns:
            Dictionary containing portfolio response
        """
        try:
            # Ensure required fields are present
            required_fields = ["companies", "total_value", "total_yield"]
            for field in required_fields:
                if field not in portfolio_data:
                    raise ValueError(f"Missing required field: {field}")

            response = {
                "portfolio": {
                    "companies": portfolio_data["companies"],
                    "summary": {
                        "total_companies": len(portfolio_data["companies"]),
                        "total_value": portfolio_data["total_value"],
                        "total_yield": portfolio_data["total_yield"],
                        "average_yield": portfolio_data.get("average_yield", 0.0),
                        "diversification_score": portfolio_data.get(
                            "diversification_score", 0.0
                        ),
                    },
                }
            }

            logger.info(
                f"Converted portfolio data with {len(portfolio_data['companies'])} companies"
            )
            return response

        except Exception as e:
            logger.error(f"Error converting portfolio data to API response: {e}")
            raise ValueError(
                f"Failed to convert portfolio data to API response format: {e}"
            ) from e

    @staticmethod
    def to_portfolio_comparison_response(
        portfolios: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Convert portfolio comparison data to API response format.

        Args:
            portfolios: List of portfolio data dictionaries

        Returns:
            Dictionary containing portfolio comparison response
        """
        try:
            comparison_data = []
            for i, portfolio in enumerate(portfolios):
                portfolio_summary = {
                    "portfolio_id": i + 1,
                    "total_companies": len(portfolio.get("companies", [])),
                    "total_value": portfolio.get("total_value", 0.0),
                    "total_yield": portfolio.get("total_yield", 0.0),
                    "average_yield": portfolio.get("average_yield", 0.0),
                    "diversification_score": portfolio.get(
                        "diversification_score", 0.0
                    ),
                }
                comparison_data.append(portfolio_summary)

            response = {
                "comparison": {
                    "portfolios": comparison_data,
                    "total_portfolios": len(portfolios),
                }
            }

            logger.info(f"Converted {len(portfolios)} portfolios for comparison")
            return response

        except Exception as e:
            logger.error(f"Error converting portfolio comparison to API response: {e}")
            raise ValueError(
                f"Failed to convert portfolio comparison to API response format: {e}"
            ) from e


class MetricsResponseMapper:
    """Service for mapping metrics data to API response format."""

    @staticmethod
    def to_performance_metrics_response(metrics: dict[str, Any]) -> dict[str, Any]:
        """Convert performance metrics to API response format.

        Args:
            metrics: Performance metrics dictionary

        Returns:
            Dictionary containing performance metrics response
        """
        try:
            response = {
                "metrics": {
                    "performance": {
                        "execution_time_ms": metrics.get("execution_time_ms", 0),
                        "memory_usage_mb": metrics.get("memory_usage_mb", 0.0),
                        "cpu_usage_percent": metrics.get("cpu_usage_percent", 0.0),
                        "data_processed_rows": metrics.get("data_processed_rows", 0),
                    },
                    "business": {
                        "companies_screened": metrics.get("companies_screened", 0),
                        "companies_passed": metrics.get("companies_passed", 0),
                        "average_score": metrics.get("average_score", 0.0),
                        "score_distribution": metrics.get("score_distribution", {}),
                    },
                }
            }

            logger.info("Converted performance metrics to API response format")
            return response

        except Exception as e:
            logger.error(f"Error converting performance metrics to API response: {e}")
            raise ValueError(
                f"Failed to convert performance metrics to API response format: {e}"
            ) from e

    @staticmethod
    def to_health_metrics_response(health_data: dict[str, Any]) -> dict[str, Any]:
        """Convert health metrics to API response format.

        Args:
            health_data: Health metrics dictionary

        Returns:
            Dictionary containing health metrics response
        """
        try:
            response = {
                "health": {
                    "status": health_data.get("status", "unknown"),
                    "timestamp": health_data.get("timestamp", ""),
                    "uptime_seconds": health_data.get("uptime_seconds", 0),
                    "memory_usage_mb": health_data.get("memory_usage_mb", 0.0),
                    "active_connections": health_data.get("active_connections", 0),
                    "errors_count": health_data.get("errors_count", 0),
                    "warnings_count": health_data.get("warnings_count", 0),
                }
            }

            logger.info("Converted health metrics to API response format")
            return response

        except Exception as e:
            logger.error(f"Error converting health metrics to API response: {e}")
            raise ValueError(
                f"Failed to convert health metrics to API response format: {e}"
            ) from e
