#!/usr/bin/env python3
"""
AgentSphere CLI - Connect to sandboxes with SSH-like functionality
"""

import click
import sys
import os
import json
import struct
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import asyncio
import select
import socket
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _setup_logging() -> logging.Logger:
    """
    Setup logging with cross-platform support.
    Ensures log file writing always succeeds with fallback options.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Log format
    log_format = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    # Try to create log file handler with multiple fallback locations
    log_file = None
    log_dir = None

    # 1. Try user home directory first
    try:
        log_dir = Path.home() / '.agentsphere-cli'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'agentsphere-cli.log'
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    except Exception as e:
        # 2. Fallback: try temp directory
        try:
            import tempfile
            log_dir = Path(tempfile.gettempdir()) / 'agentsphere-cli'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / 'agentsphere-cli.log'
            file_handler = RotatingFileHandler(
                str(log_file),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(log_format)
            logger.addHandler(file_handler)
        except Exception:
            # 3. Final fallback: only console output
            pass

    # Always add console handler
    return logger


logger = _setup_logging()


# Add the agentsphere-python-sdk-back to Python path
sdk_path = '/Users/shaohua.li/Documents/work/agentsphere-python-sdk-back'
sys.path.insert(0, sdk_path)

try:
    from agentsphere import Sandbox, PtySize, CommandHandle
    from agentsphere_base.sandbox_sync.commands.pty import Pty
except ImportError as e:
    print(f"Error importing agentsphere: {e}")
    print("Make sure the agentsphere SDK is available at:", sdk_path)
    sys.exit(1)

console = Console()


# TLV Protocol implementation for AgentSphere CLI
class TLVSign:
    """TLV message type/signature enumeration"""
    REGISTER = 1      # Register sandbox ID (A → B)
    EXECUTE = 2       # Execute command (B → A)
    GET_OUTPUT = 3    # Get history output (B → A)
    PTY_CLOSE = 4     # Close PTY connection (A → B, B exits)

    @classmethod
    def description(cls, sign: int) -> str:
        """Get human-readable description for a sign value"""
        # Mapping of sign values to names
        sign_map = {
            1: "REGISTER",
            2: "EXECUTE",
            3: "GET_OUTPUT",
            4: "PTY_CLOSE"
        }
        return sign_map.get(sign, "UNKNOWN")


class TLVMessage:
    """Represents a TLV message structure"""
    def __init__(self, sign: int, content: Dict[str, Any]):
        self.sign = sign
        self.content = content

    def to_bytes(self) -> bytes:
        """Convert TLV message to bytes format"""
        # Serialize content to JSON
        content_json = json.dumps(self.content, separators=(',', ':'), ensure_ascii=False)
        content_bytes = content_json.encode('utf-8')

        # Pack structure: length(64bit, big-endian):sign(8bit):content
        length = len(content_bytes)
        packed_header = struct.pack('!QB', length, self.sign)

        return packed_header + content_bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> 'TLVMessage':
        """Create TLV message from bytes"""
        if len(data) < 9:  # Minimum size: 8 bytes length + 1 byte sign
            raise ValueError("Data too short for TLV message")

        # Unpack header
        length, sign = struct.unpack('!QB', data[:9])

        # Validate length
        if len(data) < 9 + length:
            raise ValueError(f"Data length mismatch. Expected {9 + length} bytes, got {len(data)}")

        # Extract and parse content
        content_bytes = data[9:9+length]
        try:
            content = json.loads(content_bytes.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in TLV content: {e}")

        return cls(sign=sign, content=content)

    def __str__(self) -> str:
        return f"TLVMessage(sign={TLVSign.description(self.sign)}, content={self.content})"


class TLVClient:
    """Helper class for TLV client operations"""

    def __init__(self, socket):
        self.socket = socket
        self.buffer = b""

    def send_tlv_message(self, message: TLVMessage) -> None:
        """Send a TLV message to the socket

        Args:
            message: TLVMessage to send
        """
        try:
            data = message.to_bytes()
            self.socket.send(data)
            logger.info(f"[dim]Sent TLV message: {message}[/dim]")
        except Exception as e:
            logger.info(f"[red]Failed to send TLV message: {e}[/red]")
            raise

    def receive_tlv_message(self, timeout: Optional[float] = None) -> TLVMessage:
        """Receive a TLV message from the socket

        Args:
            timeout: Optional receive timeout in seconds

        Returns:
            Received TLVMessage

        Raises:
            ValueError: If message is malformed
            ConnectionError: If connection is lost
        """
        import select

        # Read until we have at least 9 bytes (header)
        while len(self.buffer) < 9:
            try:
                data = self.socket.recv(4096)
                if not data:
                    raise ConnectionError("Connection closed by peer")
                self.buffer += data
            except Exception as e:
                logger.info(f"[red]Failed to receive data: {e}[/red]")
                raise

        # Parse length and sign from header
        length, sign = struct.unpack('!QB', self.buffer[:9])

        # Check if we have the complete message
        message_size = 9 + length
        if len(self.buffer) < message_size:
            # Read more data until we have the complete message
            while len(self.buffer) < message_size:
                if timeout is not None:
                    readable, _, _ = select.select([self.socket], [], [], timeout)
                    if not readable:
                        raise TimeoutError("Receive timeout")

                try:
                    data = self.socket.recv(4096)
                    if not data:
                        raise ConnectionError("Connection closed by peer")
                    self.buffer += data
                except Exception as e:
                    logger.info(f"[red]Failed to receive data: {e}[/red]")
                    raise

        # Extract complete message and update buffer
        message_data = self.buffer[:message_size]
        self.buffer = self.buffer[message_size:]

        try:
            message = TLVMessage.from_bytes(message_data)
            logger.info(f"[dim]Received TLV message: {message}[/dim]")
            return message
        except Exception as e:
            logger.info(f"[red]Failed to parse TLV message: {e}[/red]")
            raise


def get_terminal_size() -> PtySize:
    """Get current terminal size"""
    import shutil
    size = shutil.get_terminal_size()
    return PtySize(rows=size.lines, cols=size.columns)


class TcpSession:
    """TCP session for proxying data to sandbox PTY with TLV protocol support"""

    def __init__(self, port: str, sandbox: Sandbox, sandbox_id: str):
        self.port = port
        self.tcp_socket = None
        self.session: Optional[CommandHandle] = None
        self.sandbox = sandbox
        self.tlv_client: Optional[TLVClient] = None
        self.sandbox_id = sandbox_id
        self.registered = False
        self.tcp_thread = None
        self.running = False
        self.tcp_lock = threading.Lock()
        self.stdout_buffer = b""

    def _connect_tcp(self) -> bool:
        """Establish TCP connection - called in separate thread"""
        try:
            host = "127.0.0.1"
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((host, int(self.port)))
            logger.info(f"[green]Connected to TCP server: {host}:{self.port}[/green]")

            # Initialize TLV client
            self.tlv_client = TLVClient(self.tcp_socket)

            # Register with server
            register_message = TLVMessage(
                sign=TLVSign.REGISTER,
                content={
                    "sandbox_id": self.sandbox_id,
                    "client_type": "agentsphere-cli",
                    "timestamp": time.time()
                }
            )

            self.tlv_client.send_tlv_message(register_message)

            # Wait for registration response
            try:
                response = self.tlv_client.receive_tlv_message(timeout=10.0)
                if response.sign == TLVSign.REGISTER and response.content.get("success"):
                    logger.info(f"[green]Registered with server as {self.sandbox_id}[/green]")
                    self.registered = True
                else:
                    logger.info(f"[red]Registration failed: {response.content}[/red]")
                    return False
            except TimeoutError:
                logger.info("[red]Registration timeout[/red]")
                return False

            return True
        except Exception as e:
            logger.info(f"[red]TCP connection failed: {e}[/red]")
            return False

    def _handle_tcp_messages(self):
        """Handle incoming TCP messages in dedicated thread"""
        logger.info("[dim]TCP message handler started[/dim]")

        while self.running and self.tcp_socket:
            try:
                if self.tlv_client:
                    # Handle TLV protocol messages
                    try:
                        message = self.tlv_client.receive_tlv_message(timeout=1.0)
                        if message.sign == TLVSign.EXECUTE:
                            # Execute command received from server
                            command = message.content.get("command")
                            if command and self.session:
                                # Send command to PTY
                                self.sandbox.pty.send_stdin(self.session.pid, (command + "\n").encode('utf-8'))

                        elif message.sign == TLVSign.GET_OUTPUT:
                            # Server requested output - send stdout_buffer content and clear it
                            try:
                                # Prepare response with buffered output
                                response = TLVMessage(
                                    sign=TLVSign.GET_OUTPUT,
                                    content={
                                        "output": self.stdout_buffer.decode('utf-8', errors='replace'),
                                        "timestamp": time.time(),
                                        "sandbox_id": self.sandbox_id,
                                    }
                                )

                                # Send response to server
                                self.tlv_client.send_tlv_message(response)
                                # Clear the buffer after sending
                                self.stdout_buffer = b""
                            except Exception as e:
                                logger.info(f"[red]Failed to send output buffer: {e}[/red]")

                        elif message.sign == TLVSign.PTY_CLOSE:
                            # Server sent PTY_CLOSE command - gracefully close PTY and exit
                            sandbox_id = message.content.get("sandbox_id", "unknown")
                            logger.info(f"[yellow]Received PTY_CLOSE message from server for sandbox: {sandbox_id}[/yellow]")
                            logger.info("[yellow]Gracefully closing PTY...[/yellow]")

                            try:
                                # Step 1: Send exit command to PTY to gracefully close it
                                if self.session and self.sandbox:
                                    logger.info("[dim]Sending 'exit' command to PTY...[/dim]")
                                    self.sandbox.pty.send_stdin(self.session.pid, b"exit\n")
                                    # Give PTY some time to close gracefully
                                    time.sleep(0.2)
                                    logger.info("[dim]PTY exit command sent[/dim]")

                                # Step 2: Clean up and exit
                                logger.info("[yellow]Exiting application...[/yellow]")
                                self._cleanup()
                                sys.exit(0)

                            except Exception as e:
                                logger.info(f"[red]Error during PTY close: {e}[/red]")
                                sys.exit(1)

                    except TimeoutError:
                        # No message received, continue
                        continue
                    except ValueError as e:
                        logger.info(f"[yellow]TLV parse error: {e}[/yellow]")
                        continue

            except Exception as e:
                logger.info(f"[red]TCP handler error: {e}[/red]")
                break


    async def connect(self) -> bool:
        """Connect to TCP server and start message handler thread"""
        try:
            # Start TCP connection in background
            self.running = True
            connect_success = False

            # First establish connection
            connect_success = self._connect_tcp()

            if not connect_success:
                return False

            # Create PTY session
            size = get_terminal_size()
            self.session = self.sandbox.pty.create(size=size, timeout=0)
            logger.info("PTY session created")
            # Start TCP message handler thread
            self.tcp_thread = threading.Thread(target=self._handle_tcp_messages, daemon=True)
            self.tcp_thread.start()
            logger.info("TCP message handler thread started")

            return True
        except Exception as e:
            console.print(f"[red]Failed to connect to TCP server: {e}[/red]")
            return False


    def _stdin_reader(self) -> None:
        """Read from stdin and send to PTY for local echo"""
        try:
            while True:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    data = sys.stdin.buffer.read(1)
                    if not data:
                        break

                    # Send to PTY session (for local echo) - always needed
                    if self.session:
                        try:
                            self.sandbox.pty.send_stdin(self.session.pid, data)
                        except Exception as e:
                            logger.info(f"[red]PTY local echo error: {e}[/red]")
                            break
        except (EOFError, KeyboardInterrupt):
            pass
        except Exception as e:
            logger.info(f"[red]Stdin reader error: {e}[/red]")

    async def start(self) -> None:
        """Start TCP-PTY proxy session"""
        # Set up terminal settings
        sys.stdout.reconfigure(encoding='utf-8')
        if sys.stdin.isatty():
            import termios
            import tty
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            sys.stdin.flush()

        # Start stdin reader thread for local echo
        stdin_reader_thread = threading.Thread(target=self._stdin_reader, daemon=True)
        stdin_reader_thread.start()

        try:
            # Wait for PTY session to complete
            # The TCP message handler is already running in separate thread
            await self.session.wait(on_pty=self._handle_pty_data)
        except Exception as err:
            if hasattr(err, 'exitCode'):
                if err.exitCode == -1 and hasattr(err, 'error') and 'signal: killed' in str(err.error):
                    return
                if err.exitCode == 130:  # User interrupted
                    console.print("[yellow]PTY session was killed by user[/yellow]")
                    return
            console.print(f"[red]PTY error: {err}[/red]")
            raise
        finally:
            self._cleanup()

    def _handle_pty_data(self, data: bytes) -> None:
        """Handle data from PTY session and display to stdout"""
        # Buffer data to stdout_buffer
        self.stdout_buffer += data

        # Also write to stdout for display
        sys.stdout.buffer.write(data)
        sys.stdout.flush()

    def _cleanup(self) -> None:
        """Clean up TCP session"""
        if self.tcp_socket:
            self.tcp_socket.close()
        if hasattr(self, 'old_settings') and sys.stdin.isatty():
            import termios
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)


class TerminalSession:
    """Interactive terminal session for sandbox PTY"""

    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox
        self.session: Optional[CommandHandle] = None
        self.resize_listener = None
        self.stdin_listener = None

    async def start(self) -> None:
        """Start the interactive terminal session"""
        # Set up terminal settings
        sys.stdout.reconfigure(encoding='utf-8')
        if sys.stdin.isatty():
            import termios
            import tty
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            sys.stdin.flush()

        # Create PTY session
        size = get_terminal_size()
        self.session = self.sandbox.pty.create(size=size, timeout=0)

        # Set up event listeners
        self._setup_listeners()

        try:
            # Wait for command with PTY output handler
            await self.session.wait(on_pty=self._handle_data)
        except Exception as err:
            if hasattr(err, 'exitCode'):
                if err.exitCode == -1 and hasattr(err, 'error') and 'signal: killed' in str(err.error):
                    return
                if err.exitCode == 130:  # User interrupted
                    console.print("[yellow]Terminal session was killed by user[/yellow]")
                    return
            console.print(f"[red]Terminal error: {err}[/red]")
            raise
        finally:
            self._cleanup()

    def _handle_data(self, data: bytes) -> None:
        """Handle data from PTY session"""
        sys.stdout.buffer.write(data)
        sys.stdout.flush()

    def _setup_listeners(self) -> None:
        """Set up terminal event listeners"""
        import signal
        import threading
        import select

        def handle_resize(signum, frame):
            size = get_terminal_size()
            if self.session:
                try:
                    self.sandbox.pty.resize(self.session.pid, size)
                except Exception as e:
                    console.print(f"[red]Resize error: {e}[/red]")

        # Set up signal handler for resize
        signal.signal(signal.SIGWINCH, handle_resize)

        # Start stdin reader in separate thread
        stdin_thread = threading.Thread(target=self._stdin_reader, daemon=True)
        stdin_thread.start()

    def _stdin_reader(self) -> None:
        """Read from stdin and send to PTY session"""
        try:
            while True:
                # Use select to check if there's data available
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    data = sys.stdin.buffer.read(1)
                    if not data:
                        break
                    if self.session:
                        try:
                            self.sandbox.pty.send_stdin(self.session.pid, data)
                        except Exception as e:
                            console.print(f"[red]Send input error: {e}[/red]")
                            break
        except (EOFError, KeyboardInterrupt):
            pass
        except Exception as e:
            console.print(f"[red]Input error: {e}[/red]")

    def _cleanup(self) -> None:
        """Clean up terminal session"""
        # Restore terminal settings
        if hasattr(self, 'old_settings') and sys.stdin.isatty():
            import termios
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

        console.print()

        # Clean up signal handlers
        import signal
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)




@click.command()
@click.argument('sandbox_id', required=False)
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--domain', default='agentsphere.run', help='AgentSphere domain')
@click.option('--api-key', help='API key for authentication')
@click.option('--port', help='TCP connection port (e.g., 5555). If provided, sandbox_id is ignored.')
def connect(sandbox_id: str, debug: bool, domain: str, api_key: Optional[str], port: Optional[str]):
    """Wrapper for async connect function"""
    return asyncio.run(_async_connect(sandbox_id, debug, domain, api_key, port))


@click.group()
def cli():
    """AgentSphere CLI - Connect to sandboxes with SSH-like functionality"""
    pass

cli.add_command(connect)


async def _async_connect(sandbox_id: str, debug: bool, domain: str, api_key: Optional[str], port: Optional[str]):
    """Async connect function"""
    # Validate arguments
    if not port and not sandbox_id:
        console.print("[red]Error: Either --port or sandbox_id must be provided[/red]")
        return 1

    # Set up environment variables
    if debug:
        os.environ['AGENTSPHERE_DEBUG'] = 'true'

    if api_key:
        os.environ['AGENTSPHERE_API_KEY'] = api_key

    if domain != 'agentsphere.run':
        os.environ['AGENTSPHERE_DOMAIN'] = domain

    if port:
        # TCP mode
        protocol_mode = "TLV"

        console.print(Panel.fit(
            Text(f"Connecting to TCP server on port {port} ({protocol_mode} mode)...", style="blue"),
            title="AgentSphere CLI"
        ))

        try:
            # TCP mode
            sandbox = Sandbox.connect(sandbox_id)
            if not sandbox.is_running():
                console.print("[red]Error: Sandbox is not running[/red]")
                return 1
            session = TcpSession(port, sandbox, sandbox_id)
            if not await session.connect():
                return 1

            console.print("[green]Connected! Type commands and press Enter. Press Ctrl+C to exit.[/green]")

            return await session.start()
        except KeyboardInterrupt:
            console.print("\n[yellow]Connection terminated by user[/yellow]")
            return 0
        except Exception as e:
            console.print(f"[red]Connection error: {e}[/red]")
            return 1
    else:
        # Sandbox mode
        try:
            sandbox = Sandbox.connect(sandbox_id)

            # Check if sandbox exists and is running
            if not sandbox.is_running():
                console.print("[red]Error: Sandbox is not running[/red]")
                return 1

            console.print("[green]Connected! Type commands and press Enter. Press Ctrl+C to exit.[/green]")
            console.print()

            session = TerminalSession(sandbox)
            return asyncio.run(session.start())
        except KeyboardInterrupt:
            console.print("\n[yellow]Connection terminated by user[/yellow]")
            return 0
        except Exception as e:
            console.print(f"[red]Connection error: {e}[/red]")
            return 1

if __name__ == '__main__':
    cli()
