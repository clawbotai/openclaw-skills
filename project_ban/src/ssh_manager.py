"""SSH connection manager — all remote commands funnel through here."""

from __future__ import annotations

import socket
import time
from pathlib import Path
from typing import Optional

import paramiko

from src.exceptions import TransientError


class SSHManager:
    """Paramiko-based SSH session wrapper.

    Supports both key-based and password-based authentication.
    If both are provided, key_path takes precedence.
    """

    def __init__(
        self,
        host: str,
        user: str,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self._host = host
        self._user = user
        self._password = password
        self._timeout = timeout
        self._client: paramiko.SSHClient = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs: dict[str, object] = {
            "hostname": self._host,
            "username": self._user,
            "timeout": self._timeout,
        }

        if key_path:
            resolved = str(Path(key_path).expanduser())
            connect_kwargs["key_filename"] = resolved
        elif password:
            connect_kwargs["password"] = password
        else:
            raise ValueError(
                "SSHManager requires either key_path or password for authentication"
            )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._client.connect(**connect_kwargs)  # type: ignore[arg-type]
                break
            except (paramiko.SSHException, socket.timeout, OSError) as exc:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 5  # 5s, 10s backoff
                    time.sleep(wait)
                    self._client = paramiko.SSHClient()
                    self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    continue
                if isinstance(exc, paramiko.SSHException):
                    raise TransientError(
                        f"SSH connection failed to {self._host} after {max_retries} attempts: {exc}"
                    ) from exc
                elif isinstance(exc, socket.timeout):
                    raise TransientError(
                        f"SSH connection timed out to {self._host} after {max_retries} attempts"
                    ) from exc
                else:
                    raise TransientError(
                        f"Network error connecting to {self._host} after {max_retries} attempts: {exc}"
                    ) from exc

    def execute_command(
        self, cmd: str, sudo: bool = False, timeout: Optional[int] = None
    ) -> tuple[int, str, str]:
        """Execute a command on the remote host. Returns (exit_code, stdout, stderr).

        When sudo=True and password auth is used, the password is written
        to sudo's stdin via the Paramiko channel (not shell piping).
        This avoids breaking backgrounded/nohup commands.
        """
        cmd_timeout = timeout or self._timeout
        full_cmd = f"sudo -S {cmd}" if sudo else cmd
        try:
            stdin, stdout, stderr = self._client.exec_command(
                full_cmd, timeout=cmd_timeout
            )
            # Feed password to sudo -S via stdin channel
            if sudo and self._password:
                stdin.write(self._password + "\n")
                stdin.flush()
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            # Strip sudo password prompt from stderr
            err = "\n".join(
                line for line in err.splitlines()
                if not line.startswith("Password:")
            )
            return (exit_code, out, err)
        except paramiko.SSHException as exc:
            raise TransientError(
                f"SSH command execution failed: {exc}"
            ) from exc
        except socket.timeout as exc:
            raise TransientError(
                f"SSH command timed out after {self._timeout}s: {cmd}"
            ) from exc

    def close(self) -> None:
        """Close the SSH connection."""
        self._client.close()

    def __enter__(self) -> "SSHManager":
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.close()
