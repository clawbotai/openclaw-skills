"""Boundary 2 — Target system anatomy verification."""

from __future__ import annotations

from src.exceptions import DeterministicError
from src.schemas import BanPayload
from src.ssh_manager import SSHManager


class SystemAnatomyMismatchError(DeterministicError):
    """Raised when the target system does not match expected anatomy."""

    def __init__(self, mismatches: list[str]) -> None:
        self.mismatches = mismatches
        detail = "; ".join(mismatches)
        super().__init__(f"System anatomy mismatch(es): {detail}")


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a dotted version string into a comparable tuple."""
    parts: list[int] = []
    for segment in version_str.strip().split("."):
        try:
            parts.append(int(segment))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def verify_target_anatomy(ssh: SSHManager, config: BanPayload) -> bool:
    """Verify the remote target matches expected OS, arch, version, and SIP state.

    Collects ALL mismatches before raising, never short-circuits.
    Returns True on success, raises SystemAnatomyMismatchError on failure.
    """
    mismatches: list[str] = []

    # Check OS kernel name
    exit_code, stdout, _ = ssh.execute_command("uname -s")
    kernel = stdout.strip()
    if exit_code != 0 or kernel != config.expected_os:
        mismatches.append(f"expected OS '{config.expected_os}', got '{kernel}'")

    # Check architecture
    exit_code, stdout, _ = ssh.execute_command("uname -m")
    arch = stdout.strip()
    if exit_code != 0 or arch != config.architecture:
        mismatches.append(f"expected architecture '{config.architecture}', got '{arch}'")

    # Check macOS version
    exit_code, stdout, _ = ssh.execute_command("sw_vers -productVersion")
    remote_version = stdout.strip()
    if exit_code != 0:
        mismatches.append(f"failed to retrieve macOS version (exit {exit_code})")
    else:
        if _parse_version(remote_version) < _parse_version(config.min_version):
            mismatches.append(
                f"macOS version {remote_version} is below minimum {config.min_version}"
            )

    # Check SIP status
    if config.require_sip_disabled:
        exit_code, stdout, _ = ssh.execute_command("csrutil status")
        sip_output = stdout.strip()
        if "disabled" not in sip_output.lower():
            mismatches.append(f"SIP is not disabled: '{sip_output}'")

    if mismatches:
        raise SystemAnatomyMismatchError(mismatches)

    return True
