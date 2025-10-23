"""Vicoa Main Entry Point

This is the main entry point for the vicoa command that supports:
- Default (no subcommand): Claude chat integration
- serve: Webhook server with tunnel options
- mcp: MCP stdio server
"""

import argparse
import sys
import subprocess
import json
import os
from pathlib import Path
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import secrets
import requests
import time
import threading
from typing import Optional

AGENT_CHOICES = ["claude", "amp", "codex"]


def get_current_version():
    """Get the current installed version of vicoa"""
    try:
        from vicoa import __version__

        return __version__
    except Exception:
        return "unknown"


def check_for_updates():
    """Check PyPI for a newer version of vicoa"""
    try:
        response = requests.get("https://pypi.org/pypi/vicoa/json", timeout=2)
        latest_version = response.json()["info"]["version"]
        current_version = get_current_version()

        if latest_version != current_version and current_version != "unknown":
            print(f"\n✨ Update available: {current_version} → {latest_version}")
            print("   Run: pip install --upgrade omnara")
            print("   Please keep omnara up-to-date for the best experience")
            print("   New versions often include important bug fixes\n")
    except Exception:
        pass


def get_credentials_path():
    """Get the path to the credentials file"""
    config_dir = Path.home() / ".vicoa"
    return config_dir / "credentials.json"


def get_user_config_path():
    """Get the path to the user config file (for non-secret settings)."""
    config_dir = Path.home() / ".omnara"
    return config_dir / "config.json"


def load_user_config() -> dict:
    """Load user config from ~/.omnara/config.json if present."""
    path = get_user_config_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception:
        return {}


def save_user_config(new_data: dict):
    """Persist user config to ~/.omnara/config.json, merging with existing."""
    path = get_user_config_path()
    path.parent.mkdir(mode=0o700, exist_ok=True)
    existing = load_user_config()
    existing.update(new_data)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def load_stored_api_key():
    """Load API key from credentials file if it exists"""
    credentials_path = get_credentials_path()

    if not credentials_path.exists():
        return None

    try:
        with open(credentials_path, "r") as f:
            data = json.load(f)
            api_key = data.get("write_key")
            if api_key and isinstance(api_key, str):
                return api_key
            else:
                print("Warning: Invalid API key format in credentials file.")
                return None
    except json.JSONDecodeError:
        print(
            "Warning: Corrupted credentials file. Please re-authenticate with --reauth."
        )
        return None
    except (KeyError, IOError) as e:
        print(f"Warning: Error reading credentials file: {str(e)}")
        return None


def save_api_key(api_key):
    """Save API key to credentials file"""
    credentials_path = get_credentials_path()

    # Create directory if it doesn't exist
    credentials_path.parent.mkdir(mode=0o700, exist_ok=True)

    # Save the API key
    data = {"write_key": api_key}
    with open(credentials_path, "w") as f:
        json.dump(data, f, indent=2)

    # Set file permissions to 600 (read/write for owner only)
    os.chmod(credentials_path, 0o600)


class AuthHTTPServer(HTTPServer):
    """Custom HTTP server with attributes for authentication"""

    api_key: Optional[str]
    state: Optional[str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = None
        self.state = None


class AuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for the OAuth callback"""

    def log_message(self, format, *args):
        # Suppress default logging
        pass

    def do_GET(self):
        # Parse query parameters
        if "?" in self.path:
            query_string = self.path.split("?", 1)[1]
            params = urllib.parse.parse_qs(query_string)

            # Verify state parameter
            server: AuthHTTPServer = self.server  # type: ignore
            if "state" in params and params["state"][0] == server.state:
                if "api_key" in params:
                    api_key = params["api_key"][0]
                    # Store the API key in the server instance
                    server.api_key = api_key
                    print("\n✓ Authentication successful!")

                    # Send success response with nice styling
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"""
                    <html>
                    <head>
                        <title>Vicoa CLI - Authentication Successful</title>
                        <meta http-equiv="refresh" content="1;url=https://vibecodeanywhere.com/dashboard">
                        <style>
                            body {
                                margin: 0;
                                padding: 0;
                                min-height: 100vh;
                                background: linear-gradient(135deg, #1a1618 0%, #2a1f3d 100%);
                                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                color: #fef3c7;
                            }
                            .card {
                                background: rgba(26, 22, 24, 0.8);
                                border: 1px solid rgba(245, 158, 11, 0.2);
                                border-radius: 12px;
                                padding: 48px;
                                text-align: center;
                                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3),
                                           0 0 60px rgba(245, 158, 11, 0.1);
                                max-width: 400px;
                                animation: fadeIn 0.5s ease-out;
                            }
                            @keyframes fadeIn {
                                from { opacity: 0; transform: translateY(20px); }
                                to { opacity: 1; transform: translateY(0); }
                            }
                            .icon {
                                width: 64px;
                                height: 64px;
                                margin: 0 auto 24px;
                                background: rgba(134, 239, 172, 0.2);
                                border-radius: 50%;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                animation: scaleIn 0.5s ease-out 0.2s both;
                            }
                            @keyframes scaleIn {
                                from { transform: scale(0); }
                                to { transform: scale(1); }
                            }
                            .checkmark {
                                width: 32px;
                                height: 32px;
                                stroke: #86efac;
                                stroke-width: 3;
                                fill: none;
                                stroke-dasharray: 100;
                                stroke-dashoffset: 100;
                                animation: draw 0.5s ease-out 0.5s forwards;
                            }
                            @keyframes draw {
                                to { stroke-dashoffset: 0; }
                            }
                            h1 {
                                margin: 0 0 16px;
                                font-size: 24px;
                                font-weight: 600;
                                color: #86efac;
                            }
                            p {
                                margin: 0;
                                opacity: 0.8;
                                line-height: 1.5;
                            }
                            .close-hint {
                                margin-top: 24px;
                                font-size: 14px;
                                opacity: 0.6;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="card">
                            <div class="icon">
                                <svg class="checkmark" viewBox="0 0 24 24">
                                    <path d="M20 6L9 17l-5-5" />
                                </svg>
                            </div>
                            <h1>Authentication Successful!</h1>
                            <p>Your CLI has been authorized to access Vicoa.</p>
                            <p class="close-hint">Redirecting to dashboard in a moment...</p>
                            <p style="margin-top: 20px; font-size: 12px;">
                                If you are not redirected automatically,
                                <a href="https://vibecodeanywhere.com/dashboard" style="color: #86efac;">click here</a>.
                            </p>
                        </div>
                        <script>
                            setTimeout(() => {
                                window.location.href = 'https://vibecodeanywhere.com/dashboard';
                            }, 500);
                        </script>
                    </body>
                    </html>
                    """)
                    # Give the browser time to receive the response
                    self.wfile.flush()
                    return
            else:
                # Invalid or missing state parameter
                self.send_response(403)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                <html>
                <head><title>Vicoa CLI - Authentication Failed</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>Authentication Failed</h1>
                    <p>Invalid authentication state. Please try again.</p>
                </body>
                </html>
                """)
                return

        # Send error response
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"""
        <html>
        <head><title>Vicoa CLI - Authentication Failed</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>Authentication Failed</h1>
            <p>No API key was received. Please try again.</p>
        </body>
        </html>
        """)


def authenticate_via_browser(auth_url="https://vibecodeanywhere.com"):
    """Authenticate via browser and return the API key"""

    # Generate a secure random state parameter
    state = secrets.token_urlsafe(32)

    # Start local server to receive the callback
    server = AuthHTTPServer(("127.0.0.1", 0), AuthCallbackHandler)
    server.state = state
    server.api_key = None
    port = server.server_port

    # Construct the auth URL
    auth_base = auth_url.rstrip("/")
    auth_url = f"{auth_base}/cli-auth?port={port}&state={urllib.parse.quote(state)}"

    print("\nOpening browser for authentication...")
    print("If your browser doesn't open automatically, visit this link:")
    print(f"\n  {auth_url}\n")

    # Run server in a thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Open browser
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    print("After signing in to Vicoa:")
    print("  • Local CLI: Click 'Authenticate Local CLI' button in your browser")
    print("  • Remote session: Copy the API key and paste below")

    # Simple blocking input with timeout check in background
    print(
        "\nPaste API key here (or wait for browser authentication): ",
        end="",
        flush=True,
    )

    import subprocess

    api_key = None
    start_time = time.time()
    timeout = 300

    # Create a subprocess to read input that we can ACTUALLY KILL
    proc = subprocess.Popen(
        [sys.executable, "-c", "import sys; print(sys.stdin.readline().strip())"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=sys.stdin,
        text=True,
    )

    while time.time() - start_time < timeout:
        # Check if browser authenticated
        if server.api_key:
            print("\n✓ Authentication successful!")
            api_key = server.api_key
            proc.kill()  # KILL the subprocess - this actually works!
            break

        # Check if user pasted token
        if proc.poll() is not None:  # Process finished
            if proc.stdout:
                output = proc.stdout.read().strip()
                if output:
                    print("✓ Token received!")
                    api_key = output
                    break

        time.sleep(0.1)

    # Make sure subprocess is dead
    try:
        proc.kill()
    except ProcessLookupError:
        pass  # Process already dead

    if not api_key:
        print("\n✗ Authentication timed out")

    # If we got the API key, wait a bit for the browser to process
    if api_key and server.api_key:
        time.sleep(1.5)  # Give browser time to receive response and start redirect

    # Shutdown server in a separate thread to avoid deadlock
    def shutdown_server():
        server.shutdown()

    shutdown_thread = threading.Thread(target=shutdown_server)
    shutdown_thread.start()
    shutdown_thread.join(timeout=1)  # Wait max 1 second for shutdown

    server.server_close()

    if api_key:
        return api_key
    else:
        raise Exception("Authentication failed - no API key received")


def ensure_api_key(args):
    """Ensure API key is available, authenticate if needed"""
    # Check if API key is provided via argument
    if hasattr(args, "api_key") and args.api_key:
        return args.api_key

    # Check if API key is in environment variable
    env_api_key = os.environ.get("VICOA_API_KEY")
    if env_api_key:
        return env_api_key

    # Try to load from storage
    api_key = load_stored_api_key()
    if api_key:
        return api_key

    # Authenticate via browser
    print("No API key found. Starting authentication...")
    auth_url = getattr(args, "auth_url", "https://vibecodeanywhere.com")
    try:
        api_key = authenticate_via_browser(auth_url)
        save_api_key(api_key)
        print("Authentication successful! API key saved.")
        return api_key
    except Exception as e:
        raise Exception(f"Authentication failed: {str(e)}")


def cmd_headless(args, unknown_args):
    """Handle the 'headless' subcommand"""
    api_key = ensure_api_key(args)

    # Import and run the headless Claude module
    import importlib

    module = importlib.import_module("integrations.headless.claude_code")
    headless_main = getattr(module, "main")

    # Prepare sys.argv for the headless runner
    original_argv = sys.argv
    new_argv = ["headless_claude", "--api-key", api_key]

    if hasattr(args, "base_url") and args.base_url:
        new_argv.extend(["--base-url", args.base_url])

    if hasattr(args, "name") and args.name:
        new_argv.extend(["--name", args.name])

    # Add headless-specific flags
    if hasattr(args, "prompt") and args.prompt:
        new_argv.extend(["--prompt", args.prompt])

    if hasattr(args, "permission_mode") and args.permission_mode:
        new_argv.extend(["--permission-mode", args.permission_mode])

    if hasattr(args, "allowed_tools") and args.allowed_tools:
        new_argv.extend(["--allowed-tools", args.allowed_tools])

    if hasattr(args, "disallowed_tools") and args.disallowed_tools:
        new_argv.extend(["--disallowed-tools", args.disallowed_tools])

    if hasattr(args, "cwd") and args.cwd:
        new_argv.extend(["--cwd", args.cwd])

    # Add any unrecognized arguments as extra args for Claude Code SDK
    if unknown_args:
        new_argv.extend(unknown_args)

    try:
        sys.argv = new_argv
        headless_main()
    finally:
        sys.argv = original_argv


def run_agent_chat(args, unknown_args):
    """Run the agent chat integration, streaming through the relay when possible."""
    from omnara.commands.run import run_agent_with_terminal_relay

    api_key = ensure_api_key(args)
    exit_code = run_agent_with_terminal_relay(args, unknown_args, api_key)
    if exit_code != 0:
        sys.exit(exit_code)
    return exit_code


def run_agent_default(args, unknown_args):
    """Run the agent locally without the relay (legacy behaviour)."""
    agent = getattr(args, "agent", "claude").lower()

    api_key = ensure_api_key(args)

    env = os.environ.copy()
    env["OMNARA_API_KEY"] = api_key

    base_url = getattr(args, "base_url", None)
    if base_url:
        env["OMNARA_API_URL"] = base_url
        env["OMNARA_BASE_URL"] = base_url

    agent_instance_id = getattr(args, "agent_instance_id", None)
    if agent_instance_id:
        env["OMNARA_AGENT_INSTANCE_ID"] = agent_instance_id

    if getattr(args, "name", None):
        env["OMNARA_AGENT_DISPLAY_NAME"] = args.name

    if agent == "codex":
        from omnara.agents.codex import run_codex

        exit_code = run_codex(args, unknown_args, api_key)
        if exit_code is None:
            exit_code = 0
        if exit_code != 0:
            sys.exit(exit_code)
        return

    module = None
    if agent == "claude":
        module = "integrations.cli_wrappers.claude_code.claude_wrapper_v3"
    elif agent == "amp":
        module = "integrations.cli_wrappers.amp.amp"
    else:
        print(f"Error: Unknown agent '{agent}'", file=sys.stderr)
        sys.exit(1)

    command = [sys.executable, "-m", module]
    if unknown_args:
        command.extend(list(unknown_args))

    try:
        result = subprocess.run(command, env=env)
    except FileNotFoundError as exc:
        print(f"Error launching agent: {exc}", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        sys.exit(result.returncode)


def cmd_serve(args, unknown_args=None):
    """Handle the 'serve' subcommand"""
    # Run the webhook server with appropriate tunnel configuration
    cmd = [
        sys.executable,
        "-m",
        "integrations.webhooks.claude_code.claude_code",
    ]

    # Handle tunnel configuration (webhook-specific)
    if not args.no_tunnel:
        # Default: use Cloudflare tunnel
        cmd.append("--cloudflare-tunnel")
        print("[INFO] Starting webhook server with Cloudflare tunnel...")
    else:
        # Local only, no tunnel
        print("[INFO] Starting local webhook server (no tunnel)...")

    if args.port is not None:
        cmd.extend(["--port", str(args.port)])

    # Pass through ALL unknown arguments (including permission flags)
    # These will flow through to HeadlessClaudeRunner and then to Claude CLI
    if unknown_args:
        cmd.extend(unknown_args)

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[INFO] Webhook server stopped by user")
        sys.exit(0)


def cmd_mcp(args):
    """Handle the 'mcp' subcommand"""

    cmd = [
        sys.executable,
        "-m",
        "servers.mcp.stdio_server",
    ]

    if args.api_key:
        cmd.extend(["--api-key", args.api_key])
    if args.base_url:
        cmd.extend(["--base-url", args.base_url])
    if args.permission_tool:
        cmd.append("--permission-tool")
    if args.git_diff:
        cmd.append("--git-diff")
    if args.agent_instance_id:
        cmd.extend(["--agent-instance-id", args.agent_instance_id])
    if args.disable_tools:
        cmd.append("--disable-tools")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[INFO] MCP server stopped by user")
        sys.exit(0)


def add_runner_arguments(parser: argparse.ArgumentParser) -> None:
    """Arguments shared by both default and terminal subcommands."""

    parser.add_argument(
        "--api-key", help="API key for authentication (uses stored key if not provided)"
    )
    parser.add_argument(
        "--base-url",
        default="https://api.vibecodeanywhere.com:8443",
        help="Base URL of the Vicoa API server",
    )
    parser.add_argument(
        "--auth-url",
        default="https://vibecodeanywhere.com",
        help="Base URL of the Vicoa frontend for authentication",
    )
    parser.add_argument(
        "--agent",
        choices=AGENT_CHOICES,
        default="claude",
        help="Which AI agent to use (default: claude code)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Name of the omnara agent (defaults to the name of the underlying agent)",
    )
    parser.add_argument(
        "--agent-instance-id",
        type=str,
        help="Pre-existing agent instance ID to use for this session",
    )
    parser.add_argument(
        "--no-relay",
        action="store_true",
        help="Disable WebSocket relay streaming (run local-only session)",
    )
    parser.add_argument(
        "--relay-url",
        default=None,
        help="Relay WebSocket URL (default: wss://relay.omnara.com/agent for prod, ws://localhost:8080/agent for local)",
    )


def add_global_arguments(parser: argparse.ArgumentParser) -> None:
    """Add global arguments that work across all subcommands."""

    parser.add_argument(
        "--auth",
        action="store_true",
        help="Authenticate or re-authenticate with Omnara",
    )
    parser.add_argument(
        "--reauth",
        action="store_true",
        help="Force re-authentication even if API key exists",
    )
    parser.add_argument(
        "--version", action="store_true", help="Show version information"
    )
    parser.add_argument(
        "--set-default",
        nargs="?",
        const="__USE_AGENT__",
        help=(
            "Set default agent for future runs. Use without a value to use the current --agent, "
            "or pass an agent name (claude|amp|codex)."
        ),
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Name of the vicoa agent (defaults to the name of the underlying agent)",
    )
    parser.add_argument(
        "--permission-mode",
        choices=["acceptEdits", "bypassPermissions", "default", "plan"],
        help="Permission mode to use for the session",
    )
    parser.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Bypass all permission checks. Recommended only for sandboxes with no internet access.",
    )
    parser.add_argument(
        "--idle-delay",
        type=float,
        default=3.5,
        help="Delay in seconds before considering Claude idle (default: 3.5)",
    )
    add_runner_arguments(parser)


def main():
    """Main entry point with subcommand support"""
    # Create main parser
    parser = argparse.ArgumentParser(
        description="Vicoa - AI Agent Dashboard and Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start Claude chat (default)
  vicoa
  vicoa --api-key YOUR_API_KEY
  vicoa --no-relay                    # Run local-only without relay

  # Start Amp chat
  vicoa --agent=amp
  vicoa --agent=amp --api-key YOUR_API_KEY

  # Run agent directly without relay (legacy)
  omnara legacy
  omnara legacy --agent=amp

  # Start headless Claude (controlled via web dashboard)
  vicoa headless
  vicoa headless --prompt "Help me debug this codebase"
  vicoa headless --permission-mode acceptEdits --allowed-tools Read,Write,Bash

  # Start webhook server with Cloudflare tunnel
  vicoa serve

  # Start local webhook server (no tunnel)
  vicoa serve --no-tunnel
  vicoa serve --no-tunnel --port 8080

  # Run MCP stdio server
  vicoa mcp
  vicoa mcp --git-diff

  # Authenticate
  vicoa --auth

  # Show version
  omnara --version

  # Set default agent for future runs
  omnara --set-default codex
  # or equivalently
  omnara --agent codex --set-default
        """,
    )

    # Add global arguments
    add_global_arguments(parser)

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'serve' subcommand
    serve_parser = subparsers.add_parser(
        "serve", help="Start webhook server for Claude Code integration"
    )
    serve_parser.add_argument(
        "--no-tunnel",
        action="store_true",
        help="Run locally without tunnel (default: uses Cloudflare tunnel)",
    )
    serve_parser.add_argument(
        "--port", type=int, help="Port to run the webhook server on (default: 6662)"
    )
    # All permission-related args will be passed through as unknown_args
    # No need to explicitly define them here
    serve_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose logging and screen output capture (-L flag)",
    )

    # 'mcp' subcommand
    mcp_parser = subparsers.add_parser("mcp", help="Run MCP stdio server")
    mcp_parser.add_argument(
        "--permission-tool",
        action="store_true",
        help="Enable Claude Code permission prompt tool",
    )
    mcp_parser.add_argument(
        "--git-diff",
        action="store_true",
        help="Enable git diff capture for log_step and ask_question",
    )
    mcp_parser.add_argument(
        "--agent-instance-id",
        type=str,
        help="Pre-existing agent instance ID to use for this session",
    )
    mcp_parser.add_argument(
        "--api-key",
        type=str,
        help="API key to use for the MCP server",
    )
    mcp_parser.add_argument(
        "--disable-tools",
        action="store_true",
        help="Disable all tools except the permission tool",
    )

    # 'terminal' subcommand
    terminal_parser = subparsers.add_parser(
        "terminal",
        help="Run agent with WebSocket relay streaming",
    )
    add_runner_arguments(terminal_parser)

    # 'headless' subcommand
    headless_parser = subparsers.add_parser(
        "headless",
        help="Run Claude Code in headless mode (controlled via web dashboard)",
    )
    # Add the same global arguments to headless subcommand
    headless_parser.add_argument(
        "--api-key", help="API key for authentication (uses stored key if not provided)"
    )
    headless_parser.add_argument(
        "--base-url",
        default="https://api.vibecodeanywhere.com:8443",
        help="Base URL of the Vicoa API server",
    )
    headless_parser.add_argument(
        "--auth-url",
        default="https://vibecodeanywhere.com",
        help="Base URL of the Vicoa frontend for authentication",
    )
    headless_parser.add_argument(
        "--prompt",
        default="You are starting a coding session",
        help="Initial prompt for headless Claude (default: 'You are starting a coding session')",
    )
    headless_parser.add_argument(
        "--permission-mode",
        choices=["acceptEdits", "bypassPermissions", "default", "plan"],
        help="Permission mode for Claude Code",
    )
    headless_parser.add_argument(
        "--allowed-tools",
        type=str,
        help="Comma-separated list of allowed tools (e.g., 'Read,Write,Bash')",
    )
    headless_parser.add_argument(
        "--disallowed-tools",
        type=str,
        help="Comma-separated list of disallowed tools",
    )
    headless_parser.add_argument(
        "--cwd",
        type=str,
        help="Working directory for headless Claude (defaults to current directory)",
    )

    # Parse arguments
    args, unknown_args = parser.parse_known_args()

    # Handle setting default agent before any further processing
    if getattr(args, "set_default", None) is not None:
        desired: str
        used_paired_form = args.set_default == "__USE_AGENT__"
        if used_paired_form:
            desired = getattr(args, "agent", "claude").lower()
        else:
            desired = str(args.set_default).lower()
        if desired not in AGENT_CHOICES:
            print(
                f"Invalid agent '{desired}'. Valid options: {', '.join(AGENT_CHOICES)}"
            )
            sys.exit(2)
        save_user_config({"default_agent": desired})
        print(f"✓ Default agent set to '{desired}'.")
        # Paired form (--agent X --set-default) continues to launch the agent
        # Standalone form (--set-default X) exits immediately
        if not used_paired_form:
            sys.exit(0)

    # Handle version flag
    if args.version:
        print(f"vicoa version {get_current_version()}")
        sys.exit(0)

    # Handle auth flag
    if args.auth or args.reauth:
        try:
            if args.reauth:
                print("Re-authenticating...")
            else:
                print("Starting authentication...")
            api_key = authenticate_via_browser(args.auth_url)
            save_api_key(api_key)
            print("Authentication successful! API key saved.")
            sys.exit(0)
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            sys.exit(1)

    # If user did not explicitly specify --agent, honor stored default
    provided_agent_flag = any(
        a == "--agent" or a.startswith("--agent=") for a in sys.argv[1:]
    )
    if not provided_agent_flag:
        cfg = load_user_config()
        default_agent = cfg.get("default_agent")
        if isinstance(default_agent, str) and default_agent in AGENT_CHOICES:
            args.agent = default_agent

    # Check for updates
    check_for_updates()

    # Handle subcommands
    if args.command == "serve":
        cmd_serve(args, unknown_args)
    elif args.command == "mcp":
        cmd_mcp(args)
    elif args.command == "headless":
        cmd_headless(args, unknown_args)
    elif args.command == "terminal":
        run_agent_chat(args, unknown_args)
    else:
        # Default behavior: run agent locally without relay
        run_agent_default(args, unknown_args)


if __name__ == "__main__":
    main()
