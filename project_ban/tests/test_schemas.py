"""Tests for schema validation and logic."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.schemas import IMMUTABLE_CORE_DAEMONS, WIFI_SURVIVAL_DAEMONS, BanPayload


def test_ban_payload_valid_basic() -> None:
    """Test basic valid configuration."""
    conf = {
        "target_host": "localhost",
        "ssh_user": "test",
        "ssh_password": "secret",
        "permitted_garments": ["com.custom.daemon"],
    }
    payload = BanPayload(**conf)
    assert payload.target_host == "localhost"
    assert "com.custom.daemon" in payload.merged_allowlist
    # Verify core daemons are automatically merged
    assert set(IMMUTABLE_CORE_DAEMONS).issubset(set(payload.merged_allowlist))


def test_ban_payload_none_coercion() -> None:
    """Test that None in permitted_garments (YAML artifact) is coerced to empty list."""
    conf = {
        "target_host": "localhost",
        "ssh_user": "test",
        "ssh_password": "secret",
        "permitted_garments": None,  # Simulates YAML 'key: ' (null)
    }
    payload = BanPayload(**conf)
    assert payload.permitted_garments == []
    assert set(IMMUTABLE_CORE_DAEMONS).issubset(set(payload.merged_allowlist))


def test_ban_payload_wifi_logic() -> None:
    """Test that use_wifi=True merges Wi-Fi daemons."""
    conf = {
        "target_host": "localhost",
        "ssh_user": "test",
        "ssh_password": "secret",
        "use_wifi": True,
    }
    payload = BanPayload(**conf)
    assert set(WIFI_SURVIVAL_DAEMONS).issubset(set(payload.merged_allowlist))


def test_ban_payload_auth_validation() -> None:
    """Test that missing both password and key raises error."""
    conf = {
        "target_host": "localhost",
        "ssh_user": "test",
        # No ssh_password or ssh_key_path
    }
    with pytest.raises(ValidationError) as exc:
        BanPayload(**conf)
    assert "Either ssh_key_path or ssh_password must be provided" in str(exc.value)
