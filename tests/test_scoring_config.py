"""Tests for scoring configuration module."""

import os

import pytest

from dgi.scoring_config import (
    ScoringConfig,
    ScoringThresholds,
    ScoringWeights,
    get_scoring_config,
    load_scoring_config_from_env,
    reset_scoring_config,
)


class TestScoringWeights:
    """Test scoring weights configuration."""

    def test_default_weights(self):
        """Test default weight values."""
        weights = ScoringWeights()
        assert weights.yield_weight == 1.0
        assert weights.growth_weight == 0.5
        assert weights.payout_penalty_weight == -0.1
        assert weights.payout_penalty_threshold == 60.0
        assert weights.fcf_yield_weight == 0.3
        assert weights.sector_bonus == 0.1
        assert weights.industry_bonus == 0.05

    def test_custom_weights(self):
        """Test custom weight values."""
        weights = ScoringWeights(
            yield_weight=2.0,
            growth_weight=1.0,
            payout_penalty_weight=-0.2,
            payout_penalty_threshold=70.0,
            fcf_yield_weight=0.5,
            sector_bonus=0.2,
            industry_bonus=0.1,
        )
        assert weights.yield_weight == 2.0
        assert weights.growth_weight == 1.0
        assert weights.payout_penalty_weight == -0.2
        assert weights.payout_penalty_threshold == 70.0
        assert weights.fcf_yield_weight == 0.5
        assert weights.sector_bonus == 0.2
        assert weights.industry_bonus == 0.1

    def test_weight_validation(self):
        """Test weight validation constraints."""
        # Test yield weight bounds
        with pytest.raises(ValueError):
            ScoringWeights(yield_weight=-1.0)

        with pytest.raises(ValueError):
            ScoringWeights(yield_weight=11.0)

        # Test growth weight bounds
        with pytest.raises(ValueError):
            ScoringWeights(growth_weight=-0.1)

        with pytest.raises(ValueError):
            ScoringWeights(growth_weight=15.0)

        # Test payout penalty weight bounds
        with pytest.raises(ValueError):
            ScoringWeights(payout_penalty_weight=0.1)  # Must be negative

        with pytest.raises(ValueError):
            ScoringWeights(payout_penalty_weight=-15.0)  # Too negative


class TestScoringThresholds:
    """Test scoring thresholds configuration."""

    def test_default_thresholds(self):
        """Test default threshold values."""
        thresholds = ScoringThresholds()
        assert thresholds.min_total_score == 0.0
        assert thresholds.max_total_score == 100.0
        assert thresholds.score_normalization_factor == 1.0

    def test_custom_thresholds(self):
        """Test custom threshold values."""
        thresholds = ScoringThresholds(
            min_total_score=-10.0, max_total_score=200.0, score_normalization_factor=2.0
        )
        assert thresholds.min_total_score == -10.0
        assert thresholds.max_total_score == 200.0
        assert thresholds.score_normalization_factor == 2.0

    def test_threshold_validation(self):
        """Test threshold validation constraints."""
        # Test min_total_score bounds
        with pytest.raises(ValueError):
            ScoringThresholds(min_total_score=-150.0)

        with pytest.raises(ValueError):
            ScoringThresholds(min_total_score=150.0)

        # Test max_total_score bounds
        with pytest.raises(ValueError):
            ScoringThresholds(max_total_score=-10.0)

        with pytest.raises(ValueError):
            ScoringThresholds(max_total_score=1500.0)

        # Test normalization factor bounds
        with pytest.raises(ValueError):
            ScoringThresholds(score_normalization_factor=0.0)

        with pytest.raises(ValueError):
            ScoringThresholds(score_normalization_factor=15.0)


class TestScoringConfig:
    """Test complete scoring configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ScoringConfig()

        # Test weights
        assert config.weights.yield_weight == 1.0
        assert config.weights.growth_weight == 0.5

        # Test thresholds
        assert config.thresholds.min_total_score == 0.0
        assert config.thresholds.max_total_score == 100.0

        # Test preferred sectors
        assert "Consumer Defensive" in config.preferred_sectors
        assert "Healthcare" in config.preferred_sectors
        assert "Utilities" in config.preferred_sectors

        # Test preferred industries
        assert "Drug Manufacturers" in config.preferred_industries
        assert "Utilities - Regulated Electric" in config.preferred_industries

        # Test penalty sectors
        assert "Energy" in config.penalty_sectors
        assert "Basic Materials" in config.penalty_sectors

        # Test penalty industries
        assert "Oil & Gas E&P" in config.penalty_industries
        assert "Oil & Gas Integrated" in config.penalty_industries

    def test_custom_config(self):
        """Test custom configuration values."""
        custom_weights = ScoringWeights(yield_weight=2.0, growth_weight=1.0)
        custom_thresholds = ScoringThresholds(max_total_score=200.0)

        config = ScoringConfig(
            weights=custom_weights,
            thresholds=custom_thresholds,
            preferred_sectors=["Tech", "Finance"],
            preferred_industries=["Software", "Banking"],
            penalty_sectors=["Energy"],
            penalty_industries=["Oil & Gas"],
        )

        assert config.weights.yield_weight == 2.0
        assert config.weights.growth_weight == 1.0
        assert config.thresholds.max_total_score == 200.0
        assert config.preferred_sectors == ["Tech", "Finance"]
        assert config.preferred_industries == ["Software", "Banking"]
        assert config.penalty_sectors == ["Energy"]
        assert config.penalty_industries == ["Oil & Gas"]


class TestEnvironmentConfigLoading:
    """Test configuration loading from environment variables."""

    def test_load_from_env_defaults(self):
        """Test loading configuration with default values."""
        # Clear any existing environment variables
        env_vars_to_clear = [
            "DGI_YIELD_WEIGHT",
            "DGI_GROWTH_WEIGHT",
            "DGI_PAYOUT_PENALTY_WEIGHT",
            "DGI_PAYOUT_PENALTY_THRESHOLD",
            "DGI_FCF_YIELD_WEIGHT",
            "DGI_SECTOR_BONUS",
            "DGI_INDUSTRY_BONUS",
            "DGI_MIN_TOTAL_SCORE",
            "DGI_MAX_TOTAL_SCORE",
            "DGI_SCORE_NORMALIZATION_FACTOR",
            "DGI_PREFERRED_SECTORS",
            "DGI_PREFERRED_INDUSTRIES",
            "DGI_PENALTY_SECTORS",
            "DGI_PENALTY_INDUSTRIES",
        ]

        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

        config = load_scoring_config_from_env()

        # Test default values
        assert config.weights.yield_weight == 1.0
        assert config.weights.growth_weight == 0.5
        assert config.weights.payout_penalty_weight == -0.1
        assert config.weights.payout_penalty_threshold == 60.0
        assert config.weights.fcf_yield_weight == 0.3
        assert config.weights.sector_bonus == 0.1
        assert config.weights.industry_bonus == 0.05

        assert config.thresholds.min_total_score == 0.0
        assert config.thresholds.max_total_score == 100.0
        assert config.thresholds.score_normalization_factor == 1.0

        # Test default lists
        assert "Consumer Defensive" in config.preferred_sectors
        assert "Healthcare" in config.preferred_sectors
        assert "Drug Manufacturers" in config.preferred_industries
        assert "Energy" in config.penalty_sectors
        assert "Oil & Gas E&P" in config.penalty_industries

    def test_load_from_env_custom_values(self):
        """Test loading configuration with custom environment values."""
        # Set custom environment variables
        os.environ["DGI_YIELD_WEIGHT"] = "2.0"
        os.environ["DGI_GROWTH_WEIGHT"] = "1.0"
        os.environ["DGI_PAYOUT_PENALTY_WEIGHT"] = "-0.2"
        os.environ["DGI_PAYOUT_PENALTY_THRESHOLD"] = "70.0"
        os.environ["DGI_FCF_YIELD_WEIGHT"] = "0.5"
        os.environ["DGI_SECTOR_BONUS"] = "0.2"
        os.environ["DGI_INDUSTRY_BONUS"] = "0.1"
        os.environ["DGI_MIN_TOTAL_SCORE"] = "-10.0"
        os.environ["DGI_MAX_TOTAL_SCORE"] = "200.0"
        os.environ["DGI_SCORE_NORMALIZATION_FACTOR"] = "2.0"
        os.environ["DGI_PREFERRED_SECTORS"] = "Tech,Finance"
        os.environ["DGI_PREFERRED_INDUSTRIES"] = "Software,Banking"
        os.environ["DGI_PENALTY_SECTORS"] = "Energy"
        os.environ["DGI_PENALTY_INDUSTRIES"] = "Oil & Gas"

        config = load_scoring_config_from_env()

        # Test custom values
        assert config.weights.yield_weight == 2.0
        assert config.weights.growth_weight == 1.0
        assert config.weights.payout_penalty_weight == -0.2
        assert config.weights.payout_penalty_threshold == 70.0
        assert config.weights.fcf_yield_weight == 0.5
        assert config.weights.sector_bonus == 0.2
        assert config.weights.industry_bonus == 0.1

        assert config.thresholds.min_total_score == -10.0
        assert config.thresholds.max_total_score == 200.0
        assert config.thresholds.score_normalization_factor == 2.0

        # Test custom lists
        assert config.preferred_sectors == ["Tech", "Finance"]
        assert config.preferred_industries == ["Software", "Banking"]
        assert config.penalty_sectors == ["Energy"]
        assert config.penalty_industries == ["Oil & Gas"]

        # Clean up environment variables
        for var in [
            "DGI_YIELD_WEIGHT",
            "DGI_GROWTH_WEIGHT",
            "DGI_PAYOUT_PENALTY_WEIGHT",
            "DGI_PAYOUT_PENALTY_THRESHOLD",
            "DGI_FCF_YIELD_WEIGHT",
            "DGI_SECTOR_BONUS",
            "DGI_INDUSTRY_BONUS",
            "DGI_MIN_TOTAL_SCORE",
            "DGI_MAX_TOTAL_SCORE",
            "DGI_SCORE_NORMALIZATION_FACTOR",
            "DGI_PREFERRED_SECTORS",
            "DGI_PREFERRED_INDUSTRIES",
            "DGI_PENALTY_SECTORS",
            "DGI_PENALTY_INDUSTRIES",
        ]:
            if var in os.environ:
                del os.environ[var]

    def test_load_from_env_empty_lists(self):
        """Test loading configuration with empty list environment variables."""
        # Set empty list environment variables
        os.environ["DGI_PREFERRED_SECTORS"] = ""
        os.environ["DGI_PREFERRED_INDUSTRIES"] = ""
        os.environ["DGI_PENALTY_SECTORS"] = ""
        os.environ["DGI_PENALTY_INDUSTRIES"] = ""

        config = load_scoring_config_from_env()

        # Should use defaults when empty
        assert len(config.preferred_sectors) > 0
        assert len(config.preferred_industries) > 0
        assert len(config.penalty_sectors) > 0
        assert len(config.penalty_industries) > 0

        # Clean up
        for var in [
            "DGI_PREFERRED_SECTORS",
            "DGI_PREFERRED_INDUSTRIES",
            "DGI_PENALTY_SECTORS",
            "DGI_PENALTY_INDUSTRIES",
        ]:
            if var in os.environ:
                del os.environ[var]


class TestGlobalConfig:
    """Test global configuration management."""

    def test_get_scoring_config_singleton(self):
        """Test that get_scoring_config returns the same instance."""
        reset_scoring_config()

        config1 = get_scoring_config()
        config2 = get_scoring_config()

        assert config1 is config2

    def test_reset_scoring_config(self):
        """Test that reset_scoring_config creates a new instance."""
        config1 = get_scoring_config()
        reset_scoring_config()
        config2 = get_scoring_config()

        assert config1 is not config2

    def test_config_immutability(self):
        """Test that configuration objects are immutable."""
        config = get_scoring_config()

        # Test that weights are frozen
        with pytest.raises(Exception):
            config.weights.yield_weight = 2.0

        # Test that thresholds are frozen
        with pytest.raises(Exception):
            config.thresholds.max_total_score = 200.0

        # Test that the main config is frozen
        with pytest.raises(Exception):
            config.preferred_sectors = ["New Sector"]
