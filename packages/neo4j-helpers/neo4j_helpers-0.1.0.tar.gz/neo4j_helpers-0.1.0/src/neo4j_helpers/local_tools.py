from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Mapping, Sequence


class Neo4jLocalTools:
    """Helpers for interacting with a locally installed Neo4j distribution.

    This class encapsulates knowledge of the filesystem layout and bundled command
    line tools (`neo4j` and `neo4j-admin`). It does not talk to the database via
    Bolt; rather it assists with process orchestration and configuration files.
    """

    def __init__(
        self,
        neo4j_home: str | Path,
        *,
        java_home: str | Path | None = None,
        validate: bool = True,
        import_dir_override: str | Path | None = None,
    ) -> None:
        self.neo4j_home = Path(neo4j_home).expanduser().resolve()
        self._java_home = Path(java_home).expanduser().resolve() if java_home else None
        self._config_cache: dict[str, str] | None = None
        if import_dir_override is not None:
            self._import_dir_override = Path(import_dir_override).expanduser().resolve()
        else:
            override_env = os.environ.get("NEO4J_HELPERS_IMPORT_DIR")
            self._import_dir_override = Path(override_env).expanduser().resolve() if override_env else None
        if validate:
            self.ensure_installation()

    @property
    def bin_dir(self) -> Path:
        return self.neo4j_home / "bin"

    @property
    def conf_dir(self) -> Path:
        return self.neo4j_home / "conf"

    @property
    def data_dir(self) -> Path:
        default = (self.neo4j_home / "data").resolve()
        return self._directory_from_config(["server.directories.data"], default)

    @property
    def logs_dir(self) -> Path:
        default = (self.neo4j_home / "logs").resolve()
        return self._directory_from_config(["server.directories.logs"], default)

    @property
    def plugins_dir(self) -> Path:
        default = (self.neo4j_home / "plugins").resolve()
        return self._directory_from_config(
            ["server.directories.plugins", "server.directories.plugin"],
            default,
        )

    @property
    def run_dir(self) -> Path:
        default = (self.neo4j_home / "run").resolve()
        return self._directory_from_config(["server.directories.run"], default)

    @property
    def import_dir(self) -> Path:
        if self._import_dir_override is not None:
            return self._import_dir_override
        default = (self.neo4j_home / "import").resolve()
        return self._directory_from_config(["server.directories.import"], default)

    @property
    def transaction_logs_dir(self) -> Path:
        override = self._directory_from_config(
            [
                "server.directories.transaction_logs.root",
                "server.directories.transaction.logs.root",
            ],
            None,
        )
        if override is not None:
            return override
        return (self.data_dir / "transactions").resolve()

    @property
    def neo4j_bin(self) -> Path:
        return self.bin_dir / "neo4j"

    @property
    def neo4j_admin_bin(self) -> Path:
        return self.bin_dir / "neo4j-admin"

    def ensure_installation(self) -> None:
        """Ensure key executables exist, raising if they do not."""
        missing = [path for path in (self.neo4j_bin, self.neo4j_admin_bin) if not path.exists()]
        if missing:
            joined = ", ".join(str(path) for path in missing)
            raise FileNotFoundError(f"Missing Neo4j executable(s): {joined}")

    def is_installation_valid(self) -> bool:
        return self.neo4j_bin.exists() and self.neo4j_admin_bin.exists()

    def tool_environment(self, extra: Mapping[str, str] | None = None) -> dict[str, str]:
        env = os.environ.copy()
        env.setdefault("NEO4J_HOME", str(self.neo4j_home))
        if self._java_home:
            env.setdefault("JAVA_HOME", str(self._java_home))
        if extra:
            env.update(extra)
        return env

    def run_tool(
        self,
        executable: Path,
        args: Sequence[str] | None = None,
        *,
        env: Mapping[str, str] | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = True,
        timeout: float | None = None,
        logger: Any | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [str(executable)]
        if args:
            command.extend(str(part) for part in args)
        stream_to_logger = logger is not None
        capture = capture_output
        forward_to_console = not capture

        use_pipes = capture or stream_to_logger
        stdout_pipe = subprocess.PIPE if use_pipes else None
        stderr_pipe = subprocess.PIPE if use_pipes else None

        process = subprocess.Popen(
            command,
            env=self.tool_environment(env),
            stdout=stdout_pipe,
            stderr=stderr_pipe,
            text=text,
            close_fds=True,
            stdin=None,
        )

        stdout_data: str | bytes | None = None
        stderr_data: str | bytes | None = None

        def _ensure_text(raw: str | bytes | None) -> str:
            if raw is None:
                return ""
            if isinstance(raw, bytes):
                return raw.decode(errors="replace")
            return raw

        if use_pipes:
            try:
                stdout_raw, stderr_raw = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise
            except Exception:
                process.kill()
                raise

            if capture:
                stdout_data = stdout_raw
                stderr_data = stderr_raw

            stdout_text = _ensure_text(stdout_raw)
            stderr_text = _ensure_text(stderr_raw)

            if forward_to_console:
                if stdout_text:
                    sys.stdout.write(stdout_text)
                    sys.stdout.flush()
                if stderr_text:
                    sys.stderr.write(stderr_text)
                    sys.stderr.flush()

            if stream_to_logger:
                for line in stdout_text.splitlines():
                    self._emit_logger_line(logger, "stdout", line)
                for line in stderr_text.splitlines():
                    self._emit_logger_line(logger, "stderr", line)
        else:
            try:
                process.wait(timeout=timeout)
            except Exception:
                process.kill()
                raise

        if capture and text:
            stdout_data = stdout_data or ""
            stderr_data = stderr_data or ""
        elif capture and not text:
            stdout_data = stdout_data or b""
            stderr_data = stderr_data or b""

        result = subprocess.CompletedProcess(
            command,
            process.returncode,
            stdout=stdout_data,
            stderr=stderr_data,
        )
        if check and process.returncode != 0:
            result.check_returncode()
        return result

    def run_neo4j(self, args: Sequence[str] | None = None, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return self.run_tool(self.neo4j_bin, args or [], **kwargs)

    def run_admin(self, args: Sequence[str] | None = None, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return self.run_tool(self.neo4j_admin_bin, args or [], **kwargs)

    # --- Server lifecycle helpers -------------------------------------------------

    def is_running(self) -> bool:
        """Return ``True`` if ``neo4j status`` reports success."""
        try:
            result = self.run_neo4j(["status"], capture_output=True, check=False)
        except Exception:
            return False
        return result.returncode == 0

    def start_server(
        self,
        *,
        wait: bool = False,
        timeout: float = 60.0,
        poll_interval: float = 1.0,
        logger: Any | None = None,
    ) -> None:
        """Invoke ``neo4j start`` and optionally wait for the server to report ready."""
        self.run_neo4j(["start"], logger=logger)
        if wait:
            self._wait_for_status(True, timeout=timeout, poll_interval=poll_interval)

    def stop_server(
        self,
        *,
        wait: bool = False,
        timeout: float = 60.0,
        poll_interval: float = 1.0,
        logger: Any | None = None,
    ) -> None:
        """Invoke ``neo4j stop`` and optionally wait for the server to exit."""
        self.run_neo4j(["stop"], logger=logger)
        if wait:
            self._wait_for_status(False, timeout=timeout, poll_interval=poll_interval)

    def _wait_for_status(self, desired: bool, *, timeout: float, poll_interval: float) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() <= deadline:
            if self.is_running() == desired:
                return
            time.sleep(poll_interval)
        state = "running" if desired else "stopped"
        raise TimeoutError(f"Timed out waiting for Neo4j to be {state}")

    @staticmethod
    def _log_subprocess_stream(logger: Any, stream_name: str, stream: str | None) -> None:
        if not stream:
            return
        lines = stream.splitlines()
        if hasattr(logger, "log"):
            for line in lines:
                logger.log(f"[{stream_name}] {line}")
            return
        method_name = "info" if stream_name == "stdout" else "error"
        log_method = getattr(logger, method_name, None)
        if log_method is None:
            return
        for line in lines:
            log_method(line)

    @staticmethod
    def _emit_logger_line(logger: Any, stream_name: str, line: str) -> None:
        if not line:
            return
        if hasattr(logger, "log"):
            logger.log(f"[{stream_name}] {line}")
            return
        method_name = "info" if stream_name == "stdout" else "error"
        log_method = getattr(logger, method_name, None)
        if log_method is None:
            return
        log_method(line)

    def config_path(self, filename: str = "neo4j.conf") -> Path:
        return (self.conf_dir / filename).resolve()

    def read_config(self, filename: str = "neo4j.conf") -> str:
        return self.config_path(filename).read_text(encoding="utf-8")

    def write_config(self, filename: str, contents: str) -> None:
        path = self.config_path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        self._config_cache = None

    def list_databases(self) -> list[str]:
        databases_dir = self.data_dir / "databases"
        if not databases_dir.exists():
            return []
        return sorted(entry.name for entry in databases_dir.iterdir() if entry.is_dir())

    def list_transaction_logs(self) -> list[Path]:
        tx_dir = self.transaction_logs_dir
        if not tx_dir.exists():
            return []
        entries = [entry.resolve() for entry in tx_dir.iterdir() if entry.is_dir()]
        return sorted(entries, key=lambda path: path.name)

    def _directory_from_config(self, keys: Sequence[str], default: Path | None) -> Path | None:
        overrides = self._config_overrides()
        for key in keys:
            raw_value = overrides.get(key)
            if raw_value:
                return self._resolve_config_path(raw_value)
        return default

    def _config_overrides(self) -> dict[str, str]:
        if self._config_cache is not None:
            return self._config_cache
        config_file = self.config_path()
        if not config_file.exists():
            self._config_cache = {}
            return self._config_cache
        overrides: dict[str, str] = {}
        with config_file.open(encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not key or not value:
                    continue
                overrides[key] = value
        self._config_cache = overrides
        return overrides

    def _resolve_config_path(self, raw_value: str) -> Path:
        value = raw_value.strip()
        substitutions = {
            "${neo4j.home}": str(self.neo4j_home),
            "${neo4j_home}": str(self.neo4j_home),
        }
        for token, replacement in substitutions.items():
            value = value.replace(token, replacement)
        value = os.path.expandvars(value)
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = self.neo4j_home / path
        return path.resolve()


__all__ = ["Neo4jLocalTools"]
