import os
import platform
import subprocess
import sys
import uuid
import threading
import time
from pathlib import Path
from typing import Optional

from vicoa.sdk.client import VicoaClient


def _platform_tag() -> tuple[str, str, str]:
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Darwin":
        arch = "arm64" if machine in ("arm64", "aarch64") else "x64"
        ext = ""
        tag = f"darwin-{arch}"
    elif system == "Linux":
        arch = "x64" if machine in ("x86_64", "amd64") else machine
        ext = ""
        tag = f"linux-{arch}"
    elif system == "Windows":
        arch = "x64" if machine in ("amd64", "x86_64") else machine
        ext = ".exe"
        tag = f"win-{arch}"
    else:
        # Fallback for unknown
        arch = machine or "unknown"
        ext = ""
        tag = f"{system.lower()}-{arch}"
    return tag, ext, system


def _packaged_binary_path() -> Path:
    """Return packaged binary path inside the wheel, if present."""
    tag, ext, _ = _platform_tag()
    base = Path(__file__).resolve().parent.parent / "_bin" / "codex" / tag
    return base / f"codex{ext}"


def _env_binary_path() -> Optional[Path]:
    """Return a path from VICOA_CODEX_PATH if set.

    Accepts either a direct file path to the binary or a directory, in which case
    we append the platform-specific binary name (codex[.exe]).
    """
    p = os.environ.get("VICOA_CODEX_PATH")
    if not p:
        return None
    p = os.path.expanduser(p)
    path = Path(p)
    if path.is_dir():
        tag, ext, _ = _platform_tag()
        return path / f"codex{ext}"
    return path


def _resolve_codex_binary() -> Path:
    # 1) explicit override via env var
    env_p = _env_binary_path()
    if env_p and env_p.exists():
        return env_p

    # 2) packaged in the wheel
    packaged = _packaged_binary_path()
    if packaged.exists():
        return packaged

    raise FileNotFoundError(
        "Codex binary not found.\n"
        "Set VICOA_CODEX_PATH to specify the binary path.\n"
        f"Otherwise, expected a packaged binary in the wheel at: {_packaged_binary_path()}\n\n"
        "To build in local vicoa repo:\n"
        "  cd integrations/cli_wrappers/codex/codex-rs && cargo build --release -p codex-cli\n"
        "The built binary will be at:\n"
        "  integrations/cli_wrappers/codex/codex-rs/target/release/codex\n"
        "Then set VICOA_CODEX_PATH to either the binary file or its directory."
    )


def run_codex(args, unknown_args, api_key: str):
    """Launch the Codex CLI binary and keep the agent session alive via heartbeat.

    Mirrors the Claude wrapper behavior by sending periodic heartbeats to the
    dashboard while the Codex subprocess is running.
    """
    try:
        bin_path = _resolve_codex_binary()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    env = os.environ.copy()

    # Wire Vicoa env for the Rust client
    env["VICOA_API_KEY"] = api_key
    if getattr(args, "base_url", None):
        env["VICOA_API_URL"] = args.base_url
    # Ensure there is a stable session ID shared with the Rust process
    session_id = env.setdefault("VICOA_SESSION_ID", str(uuid.uuid4()))

    # Ensure executable bit if running from packaged file on Unix
    try:
        if bin_path.is_file() and os.name != "nt":
            mode = os.stat(bin_path).st_mode
            # 0o111 owner/group/other execute bits
            if (mode & 0o111) == 0:
                os.chmod(bin_path, mode | 0o111)
    except Exception:
        pass

    cmd = [str(bin_path)]
    if unknown_args:
        cmd.extend(unknown_args)

    # Start a background heartbeat loop similar to the Claude wrapper.
    # This may 404 until the Codex process creates the instance; that's fine.
    stop_event = threading.Event()

    def _heartbeat_loop(
        api_key: str,
        base_url: Optional[str],
        agent_instance_id: str,
        interval: float = 30.0,
    ) -> None:
        try:
            client = VicoaClient(
                api_key=api_key,
                base_url=(base_url or "https://api.vibecodeanywhere.com:8443"),
            )
            session = client.session
            url = (base_url or "https://api.vibecodeanywhere.com:8443").rstrip(
                "/"
            ) + f"/api/v1/agents/instances/{agent_instance_id}/heartbeat"

            import random

            time.sleep(random.uniform(0, 2.0))
            while not stop_event.is_set():
                try:
                    resp = session.post(url, timeout=10)
                    _ = resp.status_code  # ignore; 404 expected until instance exists
                except Exception:
                    pass

                # Sleep with jitter; ensure a minimum reasonable delay
                delay = interval + random.uniform(-2.0, 2.0)
                if delay < 5:
                    delay = 5
                end_time = time.time() + delay
                while time.time() < end_time and not stop_event.is_set():
                    time.sleep(0.1)
        except Exception:
            # Never let heartbeat failures crash the launcher
            pass

    base_url = getattr(args, "base_url", None) or env.get("VICOA_API_URL")
    hb_thread = threading.Thread(
        target=_heartbeat_loop,
        args=(api_key, base_url, session_id),
        daemon=True,
    )
    hb_thread.start()

    try:
        subprocess.run(cmd, env=env, check=False)
    except KeyboardInterrupt:
        sys.exit(130)
    finally:
        # Signal heartbeat thread to exit and join briefly
        stop_event.set()
        try:
            hb_thread.join(timeout=2.0)
        except Exception:
            pass
