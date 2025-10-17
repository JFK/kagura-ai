"""Tests for CompressionPolicy"""

import pytest

from kagura.core.compression import CompressionPolicy


def test_policy_defaults():
    """Test default policy values"""
    policy = CompressionPolicy()

    assert policy.strategy == "smart"
    assert policy.max_tokens == 4000
    assert policy.trigger_threshold == 0.8
    assert policy.preserve_recent == 5
    assert policy.preserve_system is True
    assert policy.target_ratio == 0.5
    assert policy.enable_summarization is True
    assert policy.summarization_model == "gpt-5-mini"


def test_policy_custom_values():
    """Test policy with custom values"""
    policy = CompressionPolicy(
        strategy="trim",
        max_tokens=2000,
        trigger_threshold=0.7,
        preserve_recent=10,
        preserve_system=False,
        target_ratio=0.6,
        enable_summarization=False,
        summarization_model="gpt-4o",
    )

    assert policy.strategy == "trim"
    assert policy.max_tokens == 2000
    assert policy.trigger_threshold == 0.7
    assert policy.preserve_recent == 10
    assert policy.preserve_system is False
    assert policy.target_ratio == 0.6
    assert policy.enable_summarization is False
    assert policy.summarization_model == "gpt-4o"


def test_policy_validation_trigger_threshold_high():
    """Test trigger_threshold validation (too high)"""
    with pytest.raises(ValueError, match="trigger_threshold"):
        CompressionPolicy(trigger_threshold=1.5)


def test_policy_validation_trigger_threshold_low():
    """Test trigger_threshold validation (too low)"""
    with pytest.raises(ValueError, match="trigger_threshold"):
        CompressionPolicy(trigger_threshold=-0.1)


def test_policy_validation_target_ratio_high():
    """Test target_ratio validation (too high)"""
    with pytest.raises(ValueError, match="target_ratio"):
        CompressionPolicy(target_ratio=1.5)


def test_policy_validation_target_ratio_low():
    """Test target_ratio validation (too low)"""
    with pytest.raises(ValueError, match="target_ratio"):
        CompressionPolicy(target_ratio=-0.1)


def test_policy_validation_max_tokens_zero():
    """Test max_tokens validation (zero)"""
    with pytest.raises(ValueError, match="max_tokens"):
        CompressionPolicy(max_tokens=0)


def test_policy_validation_max_tokens_negative():
    """Test max_tokens validation (negative)"""
    with pytest.raises(ValueError, match="max_tokens"):
        CompressionPolicy(max_tokens=-100)


def test_policy_validation_preserve_recent_negative():
    """Test preserve_recent validation (negative)"""
    with pytest.raises(ValueError, match="preserve_recent"):
        CompressionPolicy(preserve_recent=-1)


def test_policy_summarization_requirement_smart():
    """Test summarization strategy requires enable_summarization"""
    with pytest.raises(ValueError, match="requires enable_summarization"):
        CompressionPolicy(strategy="smart", enable_summarization=False)


def test_policy_summarization_requirement_summarize():
    """Test summarize strategy requires enable_summarization"""
    with pytest.raises(ValueError, match="requires enable_summarization"):
        CompressionPolicy(strategy="summarize", enable_summarization=False)


def test_policy_trim_without_summarization():
    """Test trim strategy works without summarization"""
    # Should not raise
    policy = CompressionPolicy(strategy="trim", enable_summarization=False)
    assert policy.strategy == "trim"
    assert policy.enable_summarization is False


def test_policy_off_without_summarization():
    """Test off strategy works without summarization"""
    # Should not raise
    policy = CompressionPolicy(strategy="off", enable_summarization=False)
    assert policy.strategy == "off"
    assert policy.enable_summarization is False


def test_policy_auto_without_summarization():
    """Test auto strategy works without summarization (falls back to trim)"""
    # Should not raise - auto will fall back to trim if no summarization
    policy = CompressionPolicy(strategy="auto", enable_summarization=False)
    assert policy.strategy == "auto"
    assert policy.enable_summarization is False
