#!/usr/bin/env python3
"""
Sphinx CLI

Command-line interface for AI-powered Jupyter notebook interactions.
"""

import argparse
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import shutil
import urllib.request
import urllib.error

import backoff


logger = logging.getLogger(__name__)


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages."""

    COLORS = {
        'DEBUG': '\033[32m',
        'INFO': '\033[36m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[31m',
    }
    RESET = '\033[0m'

    def format(self, record):
        formatted = super().format(record)
        color = self.COLORS.get(record.levelname, self.RESET)
        return f"{color}{formatted}{self.RESET}"


def setup_logging(verbose: bool = False, log_level: Optional[str] = None) -> None:
    """Set up logging configuration.

    Args:
        verbose: Show detailed info messages
        log_level: Log level to use when verbose is enabled (debug, info, warn, error, fatal).
                   Only takes effect if verbose is True. Defaults to info when verbose is True.
    """
    logger.handlers.clear()
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = ColoredFormatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if verbose:
        # Verbose mode: use log_level if specified, otherwise default to info
        if log_level is not None:
            # Map headless log levels to Python logging levels
            level_map = {
                'fatal': logging.CRITICAL,
                'error': logging.ERROR,
                'warn': logging.WARNING,
                'info': logging.INFO,
                'debug': logging.DEBUG
            }
            level = level_map.get(log_level.lower(), logging.INFO)
            logger.setLevel(level)
        else:
            logger.setLevel(logging.INFO)
    else:
        # Non-verbose mode: always ERROR
        logger.setLevel(logging.ERROR)

    logger.propagate = False


def setup_nodeenv() -> tuple[Path, Path, Path]:
    """
    Set up a persistent nodeenv environment and find the CLI file.

    Returns:
        tuple: (nodeenv_dir, node_exe, cjs_file) where:
               - nodeenv_dir is the persistent directory
               - node_exe is the path to the node executable
               - cjs_file is the path to the sphinx-cli.cjs file
    """
    # Get the directory where this script is located
    script_dir = Path(__file__).parent

    # Look for the sphinx-cli.cjs file
    cjs_file = script_dir / "sphinx-cli.cjs"
    if not cjs_file.exists():
        raise FileNotFoundError("sphinx-cli.cjs not found")

    # Create a persistent directory for nodeenv
    nodeenv_dir = Path.home() / ".sphinx" / ".env.cli"
    nodeenv_dir.mkdir(parents=True, exist_ok=True)

    # Create nodeenv environment
    nodeenv_path = nodeenv_dir / "nodeenv"
    if not nodeenv_path.exists():
        try:
            subprocess.run([
                sys.executable, "-m", "nodeenv", str(nodeenv_path), "--node", "24.9.0"
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error creating nodeenv: {e}")

    # Get the node executable path
    if os.name == 'nt':  # Windows
        node_exe = nodeenv_path / "Scripts" / "node.exe"
    else:  # Unix-like
        node_exe = nodeenv_path / "bin" / "node"

    return nodeenv_dir, node_exe, cjs_file


def check_jupyter_dependencies() -> None:
    """Check if required Jupyter dependencies are installed."""
    missing_deps = []

    try:
        import jupyter_server
    except ImportError:
        missing_deps.append("jupyter-server")

    try:
        import ipykernel
    except ImportError:
        missing_deps.append("ipykernel")

    if missing_deps:
        deps_str = " ".join(missing_deps)
        raise ImportError(
            f"Missing required dependencies: {deps_str}\n"
            f"Please install them with: pip install {deps_str}\n"
        )



def run_sphinx_chat(
    notebook_filepath: str,
    prompt: str,
    *,
    sphinx_url: str = "https://api.prod.sphinx.ai",
    jupyter_server_url: Optional[str] = None,
    jupyter_server_token: Optional[str] = None,
    jupyter_server_port: int = 8888,
    verbose: bool = False,
    log_level: Optional[str] = None,
    no_memory_read: bool = False,
    no_memory_write: bool = False,
    no_package_installation: bool = False,
    no_collapse_exploratory_cells: bool = False,
    sphinx_rules_path: Optional[str] = None
) -> int:
    """
    Run a Sphinx chat session with an embedded Jupyter server.

    Args:
        sphinx_url: The URL of the Sphinx service
        notebook_filepath: Path to the notebook file
        prompt: Prompt to create a thread
        jupyter_server_url: URL of existing Jupyter server (if None, will start new server)
        jupyter_server_token: Token for existing Jupyter server (if None, will generate new token)
        jupyter_server_port: Port for the Jupyter server (only used if starting new server)
        verbose: Whether to show info-level messages
        log_level: Log level when verbose is enabled (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        no_memory_read: Disable memory read
        no_memory_write: Disable memory write
        no_package_installation: Disable package installation
        no_collapse_exploratory_cells: Disable collapsing exploratory cells
        sphinx_rules_path: Path to Sphinx rules file

    Returns:
        Exit code from the headless CLI (0 for success)
    """
    setup_logging(verbose=verbose, log_level=log_level)

    if jupyter_server_url is None:
        logger.info("Checking dependencies...")
        try:
            check_jupyter_dependencies()
            logger.info("Dependencies available")
        except ImportError as e:
            logger.error(f"{e}")
            return 1
    
    jupyter_process = None
    temp_dir = None
    jupyter_token = None
    server_url = None
    
    try:
        if jupyter_server_url is not None:
            if not jupyter_server_url.startswith(('http://', 'https://')):
                if ':' in jupyter_server_url:
                    server_url = f"http://{jupyter_server_url}"
                else:
                    server_url = f"http://{jupyter_server_url}:8888"
            else:
                server_url = jupyter_server_url

            jupyter_token = jupyter_server_token

            logger.info(f"Using existing server: {server_url}")
            if jupyter_token:
                logger.info(f"Using token: {jupyter_token[:8]}...")

            logger.info("Testing server connection...")

            def _probe(url: str) -> str:
                try:
                    with urllib.request.urlopen(url, timeout=10) as resp:
                        return f"OK {resp.status}"
                except urllib.error.HTTPError as e:
                    return f"HTTP {e.code}"
                except Exception as e:
                    return f"ERR {type(e).__name__}: {e}"

            test_url = f"{server_url}/api/status"
            if jupyter_token:
                test_url = f"{server_url}/api/status?token={jupyter_token}"

            logger.info(f"Testing: {test_url}")

            status_try = _probe(test_url)
            logger.info(f"Response: {status_try}")

            if not status_try.startswith("OK 200"):
                raise RuntimeError(f"Server is not accessible: {status_try}\n"
                                 f"Please check:\n"
                                 f"1. Server is running at {server_url}\n"
                                 f"2. Token is correct (if provided)\n"
                                 f"3. Server allows connections from this host")

            logger.info("Server is ready")
        else:
            logger.info("Starting server...")
            logger.info(f"Using Python: {sys.executable}")

            temp_dir = tempfile.mkdtemp(prefix="sphinx_jupyter_")

            import secrets
            jupyter_token = secrets.token_hex(32)

            jupyter_log_level = "INFO"  # Need INFO level to capture port information

            server_cmd = [
                sys.executable, "-m", "jupyter", "server",
                "--no-browser",
                f"--port={jupyter_server_port}",
                f"--IdentityProvider.token={jupyter_token}",
                f"--ServerApp.log_level={jupyter_log_level}",
            ]

            # Capture stderr to read which port the server actually uses
            jupyter_process = subprocess.Popen(
                server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=temp_dir,
                text=True,
                bufsize=1,
            )

            def _probe(url: str) -> str:
                try:
                    with urllib.request.urlopen(url, timeout=5) as resp:
                        return f"OK {resp.status}"
                except urllib.error.HTTPError as e:
                    return f"HTTP {e.code}"
                except Exception as e:
                    return f"ERR {type(e).__name__}: {e}"

            # Parse server output to find the actual port
            import re
            import threading

            actual_port = None
            port_detected = threading.Event()

            def read_server_output():
                nonlocal actual_port
                try:
                    for line in jupyter_process.stderr:
                        # Look for any URL with a port, e.g.:
                        # "http://localhost:8889/", "http://0.0.0.0:8889/", "http://some-host:8889/"
                        if actual_port is None:
                            # Match any http/https URL followed by :PORT
                            port_match = re.search(r'https?://[^:]+:(\d+)', line)
                            if port_match:
                                actual_port = int(port_match.group(1))
                                port_detected.set()
                                logger.info(f"Detected server started on port {actual_port}")
                                break
                except Exception:
                    pass

            # Start background thread to monitor server output
            output_thread = threading.Thread(target=read_server_output, daemon=True)
            output_thread.start()

            # Wait for port detection with timeout
            if not port_detected.wait(timeout=10):
                # Fallback: assume the requested port if we couldn't detect it
                actual_port = jupyter_server_port
                logger.warning(f"Could not detect port from server output, assuming {jupyter_server_port}")

            if actual_port != jupyter_server_port:
                logger.info(f"Port {jupyter_server_port} was busy, server started on port {actual_port}")

            base = f"http://localhost:{actual_port}"
            server_url = base

            @backoff.on_exception(backoff.expo, Exception, max_time=15)
            def check_ready():
                if jupyter_process.poll() is not None:
                    error_msg = f"Server exited early with code {jupyter_process.returncode}"
                    raise RuntimeError(error_msg)
                status_try = _probe(f"{base}/api/status?token={jupyter_token}")
                if not status_try.startswith("OK 200"):
                    raise Exception(f"Server is not ready: {status_try}")

            check_ready()

            logger.info(f"Server ready at {server_url}")

        # Convert notebook path to absolute path
        notebook_abs_path = str(Path(notebook_filepath).resolve())

        # Set up nodeenv environment and get CLI file
        nodeenv_dir, node_exe, cjs_file = setup_nodeenv()

        node_args = [
            "chat",
            "--jupyter-server-url", server_url,
            "--sphinx-url", sphinx_url,
            "--notebook-filepath", notebook_abs_path,
            "--prompt", prompt,
        ]

        # Only add token if we have one
        if jupyter_token:
            node_args.extend(["--jupyter-server-token", jupyter_token])

        if no_memory_read:
            node_args.append("--no-memory-read")

        if no_memory_write:
            node_args.append("--no-memory-write")

        if no_package_installation:
            node_args.append("--no-package-installation")

        if no_collapse_exploratory_cells:
            node_args.append("--no-collapse-exploratory-cells")

        if sphinx_rules_path:
            node_args.append(f"--sphinx-rules-path={sphinx_rules_path}")

        if verbose:
            node_args.append("--verbose")

        if log_level:
            node_args.extend(["--log-level", log_level])

        # Run the sphinx-cli.cjs with node
        cmd = [str(node_exe), str(cjs_file)] + node_args

        # Use Popen to stream output in real-time
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        # Stream output in real-time
        output_lines = []
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                print(line)
                output_lines.append(line)

        # Wait for process to complete and get return code
        return_code = process.wait()

        # If process failed and we have no output, provide helpful error info
        if return_code != 0 and not output_lines:
            logger.error(f"Process failed with exit code {return_code}")
            logger.error("No output was captured. This might indicate:")
            logger.error("1. The sphinx-cli.cjs file is not executable")
            logger.error("2. Node.js is not properly installed in the nodeenv")
            logger.error("3. The CLI command failed silently")
            logger.info(f"Command that failed: {' '.join(cmd)}")
            logger.info(f"Working directory: {os.getcwd()}")
            # Try to get stderr for more info
            try:
                stderr_output = process.stderr.read()
                if stderr_output:
                    logger.error(f"Stderr output: {stderr_output}")
            except:
                pass

        return return_code

    except subprocess.CalledProcessError as e:
        logger.error(f"Headless CLI failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    finally:
        # Cleanup - only stop server if we started it
        if jupyter_process:
            logger.info("Stopping Jupyter server...")
            try:
                jupyter_process.terminate()
                jupyter_process.wait(timeout=10)
            except Exception as e:
                logger.warning(f"Warning: Error stopping Jupyter server: {e}")
                try:
                    jupyter_process.kill()
                except:
                    pass

        if temp_dir:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Warning: Error cleaning up temp directory: {e}")

        logger.info("Cleanup completed")


def run_login(verbose: bool = False, log_level: Optional[str] = None) -> int:
    """Run the login command."""
    try:
        # Set up logging
        setup_logging(verbose=verbose, log_level=log_level)

        # Set up nodeenv environment and get CLI file
        nodeenv_dir, node_exe, cjs_file = setup_nodeenv()

        # Run the login command
        cmd = [str(node_exe), str(cjs_file), "login"]

        # Run the command and stream output in real-time
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        # Stream output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        # Wait for process to complete and get return code
        return_code = process.wait()
        return return_code

    except Exception as e:
        logger.error(f"Login error: {e}")
        return 1


def run_logout(verbose: bool = False, log_level: Optional[str] = None) -> int:
    """Run the logout command."""
    try:
        # Set up logging
        setup_logging(verbose=verbose, log_level=log_level)

        # Set up nodeenv environment and get CLI file
        nodeenv_dir, node_exe, cjs_file = setup_nodeenv()

        # Run the logout command
        cmd = [str(node_exe), str(cjs_file), "logout"]

        # Run the command and stream output in real-time
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        # Stream output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        # Wait for process to complete and get return code
        return_code = process.wait()
        return return_code

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return 1


def run_status(verbose: bool = False, log_level: Optional[str] = None) -> int:
    """Run the status command."""
    try:
        # Set up logging
        setup_logging(verbose=verbose, log_level=log_level)

        # Set up nodeenv environment and get CLI file
        nodeenv_dir, node_exe, cjs_file = setup_nodeenv()

        # Run the status command
        cmd = [str(node_exe), str(cjs_file), "status"]

        # Run the command and stream output in real-time
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        # Stream output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        # Wait for process to complete and get return code
        return_code = process.wait()
        return return_code

    except Exception as e:
        logger.error(f"Status error: {e}")
        return 1


def main():
    """The Sphinx CLI."""
    parser = argparse.ArgumentParser(
        description="Sphinx CLI - Start Jupyter server and invoke Sphinx from your command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Authentication commands
  sphinx-cli login
  sphinx-cli logout
  sphinx-cli status
  
  # Chat commands (requires authentication)
  sphinx-cli chat --notebook-filepath ./notebook.ipynb --prompt "Create a model to predict y from x"
  sphinx-cli chat --notebook-filepath ./notebook.ipynb --prompt "Analyze this data" --jupyter-server-url http://localhost:8888 --jupyter-server-token your_token_here
  
  # Using existing Jupyter server (URL formats supported):
  # - localhost:8888 (will be converted to http://localhost:8888)
  # - http://localhost:8888
  # - https://your-server.com:8888
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    login_parser = subparsers.add_parser('login', help='Authenticate with Sphinx')
    login_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed messages"
    )
    login_parser.add_argument(
        "-l", "--log-level",
        type=str.lower,
        choices=["debug", "info", "warn", "error", "fatal"],
        help="Log level when verbose is enabled (default: info)"
    )

    logout_parser = subparsers.add_parser('logout', help='Clear authentication')
    logout_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed messages"
    )
    logout_parser.add_argument(
        "-l", "--log-level",
        type=str.lower,
        choices=["debug", "info", "warn", "error", "fatal"],
        help="Log level when verbose is enabled (default: info)"
    )

    status_parser = subparsers.add_parser('status', help='Check authentication status')
    status_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed messages"
    )
    status_parser.add_argument(
        "-l", "--log-level",
        type=str.lower,
        choices=["debug", "info", "warn", "error", "fatal"],
        help="Log level when verbose is enabled (default: info)"
    )

    chat_parser = subparsers.add_parser('chat', help='Start a chat session')

    chat_parser.add_argument(
        "--notebook-filepath",
        required=True,
        help="Path to notebook file"
    )
    chat_parser.add_argument(
        "--prompt",
        required=True,
        help="Chat prompt"
    )

    chat_parser.add_argument(
        "--sphinx-url",
        default="https://api.prod.sphinx.ai",
        help="Sphinx service URL"
    )

    chat_parser.add_argument(
        "--jupyter-server-url",
        help="Existing Jupyter server URL (optional)"
    )

    chat_parser.add_argument(
        "--jupyter-server-token",
        help="Jupyter server token (if using existing server)"
    )

    chat_parser.add_argument(
        '--no-memory-read',
        action='store_true',
        help='Disable memory read (default: enabled)'
    )

    chat_parser.add_argument(
        '--no-memory-write',
        action='store_true',
        help='Disable memory write (default: enabled)'
    )

    chat_parser.add_argument(
        '--no-package-installation',
        action='store_true',
        help='Disable package installation (default: enabled)'
    )

    chat_parser.add_argument(
        '--no-collapse-exploratory-cells',
        action='store_true',
        help='Disable collapsing exploratory cells (default: enabled)'
    )

    chat_parser.add_argument(
        '--sphinx-rules-path',
        help='Path to rules file'
    )

    chat_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed messages"
    )
    chat_parser.add_argument(
        "-l", "--log-level",
        type=str.lower,
        choices=["debug", "info", "warn", "error", "fatal"],
        help="Log level when verbose is enabled (default: info)"
    )

    args = parser.parse_args()

    if args.command == 'login':
        try:
            exit_code = run_login(verbose=args.verbose, log_level=args.log_level)
            sys.exit(exit_code)
        except KeyboardInterrupt:
            logger.warning("\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    elif args.command == 'logout':
        try:
            exit_code = run_logout(verbose=args.verbose, log_level=args.log_level)
            sys.exit(exit_code)
        except KeyboardInterrupt:
            logger.warning("\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    elif args.command == 'status':
        try:
            exit_code = run_status(verbose=args.verbose, log_level=args.log_level)
            sys.exit(exit_code)
        except KeyboardInterrupt:
            logger.warning("\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    elif args.command == 'chat':
        try:
            exit_code = run_sphinx_chat(
                sphinx_url=args.sphinx_url,
                notebook_filepath=args.notebook_filepath,
                prompt=args.prompt,
                jupyter_server_url=args.jupyter_server_url,
                jupyter_server_token=args.jupyter_server_token,
                verbose=args.verbose,
                log_level=args.log_level,
                no_memory_read=args.no_memory_read,
                no_memory_write=args.no_memory_write,
                no_package_installation=args.no_package_installation,
                no_collapse_exploratory_cells=args.no_collapse_exploratory_cells,
                sphinx_rules_path=args.sphinx_rules_path
            )
            sys.exit(exit_code)
        except KeyboardInterrupt:
            logger.warning("\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
