"""Boundary 1 — Payload schema and validation."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator


IMMUTABLE_CORE_DAEMONS: list[str] = [
    # Remote Access — without these, SSH dies
    "com.openssh.sshd",
    # Networking — without these, the machine goes dark
    "com.apple.networkd",
    "com.apple.configd",
    # Filesystem Integrity — without these, APFS snapshots break
    "com.apple.apfsd",
    # System Foundations — without these, launchd/logging break
    "com.apple.launchd",
    "com.apple.syslogd",
    "com.apple.CoreServices.coreservicesd",
    # Security/Crypto — without these, SSH key exchange fails
    # Discovered empirically 2026-02-14: sshd needs these for
    # key negotiation, certificate validation, PAM auth, and directory lookups
    "com.apple.securityd",
    "com.apple.trustd",
    "com.apple.opendirectoryd",
    "com.apple.authd",
]

# Prefixes that should be allowlisted by pattern match.
# macOS creates dynamic sshd instances with UUID suffixes
# (e.g. com.openssh.sshd.91207CD4-0808-423E-...) that must be preserved.
IMMUTABLE_PREFIXES: list[str] = [
    "com.openssh.sshd",
]

# Full Wi-Fi dependency chain — discovered empirically 2026-02-14.
# Stripping any of these kills Wi-Fi connectivity.
WIFI_SURVIVAL_DAEMONS: list[str] = [
    "com.apple.airportd",                  # Core 802.11 driver
    "com.apple.wifi.WiFiAgent",            # Wi-Fi agent (NOT com.apple.WiFiAgent)
    "com.apple.wifiFirmwareLoader",        # Loads radio firmware — without it, radio dies
    "com.apple.mDNSResponder.reloaded",    # DNS resolution
    "com.apple.mDNSResponderHelper.reloaded",  # DNS helper
    "com.apple.symptomsd",                 # Network quality / route decisions
    "com.apple.cfnetwork.cfnetworkagent",  # CFNetwork framework
]


class BanPayload(BaseModel):
    """Validated configuration for a B.A.N. run."""

    model_config = {"strict": True, "extra": "forbid"}

    # --- Connection ---
    target_host: str
    ssh_user: str
    ssh_key_path: Optional[str] = None
    ssh_password: Optional[str] = None

    # --- Pre-Flight Parameters ---
    expected_os: str = "Darwin"
    architecture: str = "arm64"
    min_version: str = "14.0.0"
    require_sip_disabled: bool = True

    # --- Safety ---
    dead_mans_switch_timeout: int = Field(default=300, ge=60, le=3600)
    skip_snapshot: bool = False  # Skip APFS snapshot (use when tmutil fails)

    # --- Daemon Allowlist ---
    permitted_garments: list[str] = Field(default_factory=list)

    # --- Network ---
    use_wifi: bool = False  # Auto-merges WIFI_SURVIVAL_DAEMONS into allowlist

    # --- QoS / Execution (optional — None = strip-only mode) ---
    target_binary: Optional[str] = None
    nice_value: int = Field(default=-20, ge=-20, le=19)

    # --- Computed ---
    merged_allowlist: list[str] = Field(default_factory=list, init=False)

    @model_validator(mode="before")
    @classmethod
    def _coerce_none_garments(cls, data: dict) -> dict:  # type: ignore[override]
        """YAML yields None for a key with only commented-out items."""
        if isinstance(data, dict) and data.get("permitted_garments") is None:
            data["permitted_garments"] = []
        return data

    @model_validator(mode="after")
    def _build_merged_allowlist(self) -> "BanPayload":
        combined: set[str] = set(IMMUTABLE_CORE_DAEMONS) | set(self.permitted_garments)
        if self.use_wifi:
            combined |= set(WIFI_SURVIVAL_DAEMONS)
        self.merged_allowlist = sorted(combined)
        return self

    @model_validator(mode="after")
    def _validate_auth(self) -> "BanPayload":
        if not self.ssh_key_path and not self.ssh_password:
            raise ValueError(
                "Either ssh_key_path or ssh_password must be provided"
            )
        return self
