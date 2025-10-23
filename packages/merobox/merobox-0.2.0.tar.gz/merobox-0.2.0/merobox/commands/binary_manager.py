"""
Binary Manager - Manages Calimero nodes as native processes (no Docker).
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


class BinaryManager:
    """Manages Calimero nodes as native binary processes."""

    def __init__(self, binary_path: Optional[str] = None, require_binary: bool = True):
        """
        Initialize the BinaryManager.

        Args:
            binary_path: Path to the merod binary. If None, searches PATH.
            require_binary: If True, exit if binary not found. If False, set to None gracefully.
        """
        if binary_path:
            self.binary_path = binary_path
        else:
            self.binary_path = self._find_binary(require=require_binary)

        self.processes = {}  # node_name -> subprocess.Popen
        self.pid_file_dir = Path("./data/.pids")
        self.pid_file_dir.mkdir(parents=True, exist_ok=True)

    def _find_binary(self, require: bool = True) -> Optional[str]:
        """Find the merod binary in PATH or common locations.

        Args:
            require: If True, exit if not found. If False, return None gracefully.
        """
        # Check PATH
        from shutil import which

        binary = which("merod")
        if binary:
            console.print(f"[green]✓ Found merod binary in PATH: {binary}[/green]")
            return binary

        # Check common locations
        common_paths = [
            "/usr/local/bin/merod",
            "/usr/bin/merod",
            os.path.expanduser("~/bin/merod"),
            "./merod",
            "../merod",
        ]

        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                console.print(f"[green]✓ Found merod binary: {path}[/green]")
                return path

        # Not found - either exit or return None
        if require:
            console.print(
                "[red]✗ merod binary not found. Please install or specify --binary-path[/red]"
            )
            console.print(
                "[yellow]Searched: PATH and common locations (/usr/local/bin, /usr/bin, ~/bin, ./)[/yellow]"
            )
            console.print("\n[yellow]Install via Homebrew (macOS):[/yellow]")
            console.print("  brew tap calimero-network/homebrew-tap")
            console.print("  brew install merod")
            console.print("  merod --version")
            sys.exit(1)
        else:
            return None

    def _get_pid_file(self, node_name: str) -> Path:
        """Get the PID file path for a node."""
        return self.pid_file_dir / f"{node_name}.pid"

    def _save_pid(self, node_name: str, pid: int):
        """Save process PID to file."""
        pid_file = self._get_pid_file(node_name)
        pid_file.write_text(str(pid))

    def _load_pid(self, node_name: str) -> Optional[int]:
        """Load process PID from file."""
        pid_file = self._get_pid_file(node_name)
        if pid_file.exists():
            try:
                return int(pid_file.read_text().strip())
            except (ValueError, OSError):
                return None
        return None

    def _remove_pid_file(self, node_name: str):
        """Remove PID file."""
        pid_file = self._get_pid_file(node_name)
        if pid_file.exists():
            pid_file.unlink()

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running."""
        try:
            os.kill(pid, 0)  # Signal 0 checks if process exists
            return True
        except (OSError, ProcessLookupError):
            return False

    def run_node(
        self,
        node_name: str,
        port: int = 2428,
        rpc_port: int = 2528,
        chain_id: str = "testnet-1",
        data_dir: Optional[str] = None,
        image: Optional[str] = None,  # Ignored in binary mode
        auth_service: bool = False,  # Ignored in binary mode
        auth_image: Optional[str] = None,  # Ignored in binary mode
        auth_use_cached: bool = False,  # Ignored in binary mode
        webui_use_cached: bool = False,  # Ignored in binary mode
        log_level: str = "debug",
        foreground: bool = False,
    ) -> bool:
        """
        Run a Calimero node as a native binary process.

        Args:
            node_name: Name of the node
            port: P2P port
            rpc_port: RPC port
            chain_id: Chain ID
            data_dir: Data directory (defaults to ./data/{node_name})
            log_level: Rust log level

        Returns:
            True if successful, False otherwise
        """
        try:
            # Default ports if None provided
            if port is None:
                port = 2428
            if rpc_port is None:
                rpc_port = 2528

            # Check if node is already running
            existing_pid = self._load_pid(node_name)
            if existing_pid and self._is_process_running(existing_pid):
                console.print(
                    f"[yellow]Node {node_name} is already running (PID: {existing_pid})[/yellow]"
                )
                console.print("[yellow]Stopping existing process...[/yellow]")
                self.stop_node(node_name)

            # Prepare data directory
            if data_dir is None:
                data_dir = f"./data/{node_name}"

            data_path = Path(data_dir)
            data_path.mkdir(parents=True, exist_ok=True)

            # Create node-specific subdirectory
            node_data_dir = data_path / node_name
            node_data_dir.mkdir(parents=True, exist_ok=True)

            # Prepare log file (not used when foreground)
            log_dir = data_path / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{node_name}.log"

            console.print(f"[cyan]Starting node {node_name}...[/cyan]")
            console.print(f"[cyan]  Binary: {self.binary_path}[/cyan]")
            console.print(f"[cyan]  Data dir: {node_data_dir}[/cyan]")
            console.print(f"[cyan]  P2P port: {port}[/cyan]")
            console.print(f"[cyan]  RPC port: {rpc_port}[/cyan]")
            console.print(f"[cyan]  Log file: {log_file}[/cyan]")

            # Prepare environment
            env = os.environ.copy()
            env["CALIMERO_HOME"] = str(node_data_dir.absolute())
            env["NODE_NAME"] = node_name
            env["RUST_LOG"] = log_level

            # First-time init if needed (config.toml not present)
            config_file = node_data_dir / "config.toml"
            if not config_file.exists():
                console.print(
                    f"[yellow]Initializing node {node_name} (first run)...[/yellow]"
                )
                init_cmd = [
                    self.binary_path,
                    "--home",
                    str(node_data_dir.absolute()),
                    "--node-name",
                    node_name,
                    "init",
                    "--server-port",
                    str(rpc_port),
                    "--swarm-port",
                    str(port),
                ]
                with open(log_file, "a") as log_f:
                    try:
                        subprocess.run(
                            init_cmd,
                            check=True,
                            env=env,
                            stdout=log_f,
                            stderr=subprocess.STDOUT,
                        )
                        console.print(
                            f"[green]✓ Node {node_name} initialized successfully[/green]"
                        )
                    except subprocess.CalledProcessError as e:
                        console.print(
                            f"[red]✗ Failed to initialize node {node_name}: {e}[/red]"
                        )
                        console.print(f"[yellow]Check logs: {log_file}[/yellow]")
                        return False

            # Build run command (ports are taken from config created during init)
            cmd = [
                self.binary_path,
                "--home",
                str(node_data_dir.absolute()),
                "--node-name",
                node_name,
                "run",
            ]

            if foreground:
                # Start attached in foreground (inherit stdio)
                try:
                    process = subprocess.Popen(
                        cmd,
                        env=env,
                    )
                    self.processes[node_name] = process
                    self._save_pid(node_name, process.pid)
                    console.print(
                        f"[green]✓ Node {node_name} started (foreground) (PID: {process.pid})[/green]"
                    )
                    # Wait until process exits
                    process.wait()
                    # Cleanup pid file on exit
                    self._remove_pid_file(node_name)
                    return True
                except Exception as e:
                    console.print(
                        f"[red]✗ Failed to start node {node_name}: {str(e)}[/red]"
                    )
                    return False
            else:
                # Start detached with logs to file
                with open(log_file, "a") as log_f:
                    process = subprocess.Popen(
                        cmd,
                        env=env,
                        stdin=subprocess.DEVNULL,
                        stdout=log_f,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )

                # Save process info
                self.processes[node_name] = process
                self._save_pid(node_name, process.pid)

                console.print(
                    f"[green]✓ Node {node_name} started successfully (PID: {process.pid})[/green]"
                )
                console.print(f"[cyan]  View logs: tail -f {log_file}[/cyan]")
                console.print(
                    f"[cyan]  Admin Dashboard: http://localhost:{rpc_port}/admin-dashboard[/cyan]"
                )

                # Wait a moment to check if process stays alive
                time.sleep(2)
                if not self._is_process_running(process.pid):
                    console.print(f"[red]✗ Node {node_name} crashed immediately![/red]")
                    console.print(f"[yellow]Check logs: {log_file}[/yellow]")
                    return False

                # Quick bind check for admin port
                try:
                    import socket

                    with socket.create_connection(
                        ("127.0.0.1", int(rpc_port)), timeout=1.5
                    ):
                        console.print(
                            f"[green]✓ Admin server reachable at http://localhost:{rpc_port}/admin-dashboard[/green]"
                        )
                except Exception:
                    console.print(
                        f"[yellow]⚠ Admin server not reachable yet on http://localhost:{rpc_port}. It may take a few seconds. Check logs if it persists.[/yellow]"
                    )

                return True

        except Exception as e:
            console.print(f"[red]✗ Failed to start node {node_name}: {str(e)}[/red]")
            return False

    def stop_node(self, node_name: str) -> bool:
        """Stop a running node."""
        try:
            # Check if we have the process object
            if node_name in self.processes:
                process = self.processes[node_name]
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    console.print(f"[green]✓ Stopped node {node_name}[/green]")
                except subprocess.TimeoutExpired:
                    console.print(f"[yellow]Force killing node {node_name}...[/yellow]")
                    process.kill()
                    process.wait()
                del self.processes[node_name]
                self._remove_pid_file(node_name)
                return True

            # Try loading PID from file
            pid = self._load_pid(node_name)
            if pid and self._is_process_running(pid):
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)

                # Check if still running
                if self._is_process_running(pid):
                    console.print(f"[yellow]Force killing node {node_name}...[/yellow]")
                    os.kill(pid, signal.SIGKILL)

                self._remove_pid_file(node_name)
                console.print(f"[green]✓ Stopped node {node_name}[/green]")
                return True
            else:
                console.print(f"[yellow]Node {node_name} is not running[/yellow]")
                self._remove_pid_file(node_name)
                return False

        except Exception as e:
            console.print(f"[red]✗ Failed to stop node {node_name}: {str(e)}[/red]")
            return False

    def stop_all_nodes(self) -> int:
        """Stop all running nodes. Returns count of stopped nodes."""
        stopped = 0

        # Stop tracked processes
        for node_name in list(self.processes.keys()):
            if self.stop_node(node_name):
                stopped += 1

        # Also check PID files
        for pid_file in self.pid_file_dir.glob("*.pid"):
            node_name = pid_file.stem
            if node_name not in self.processes:
                if self.stop_node(node_name):
                    stopped += 1

        return stopped

    def list_nodes(self) -> list:
        """List all running nodes."""
        nodes = []

        # Check PID files
        for pid_file in self.pid_file_dir.glob("*.pid"):
            node_name = pid_file.stem
            pid = self._load_pid(node_name)
            if pid and self._is_process_running(pid):
                rpc_port = self._read_rpc_port(node_name) or "unknown"
                nodes.append(
                    {
                        "name": node_name,
                        "pid": pid,
                        "status": "running",
                        "mode": "binary",
                        "rpc_port": rpc_port,
                        "admin_url": (
                            f"http://localhost:{rpc_port}/admin-dashboard"
                            if isinstance(rpc_port, int)
                            or (isinstance(rpc_port, str) and rpc_port.isdigit())
                            else ""
                        ),
                    }
                )

        return nodes

    def _read_rpc_port(self, node_name: str) -> Optional[int]:
        """Best-effort read RPC port from config.toml under the node data dir."""
        try:
            node_dir = Path(f"./data/{node_name}") / node_name
            config_path = node_dir / "config.toml"
            if not config_path.exists():
                return None
            import re

            with open(config_path) as f:
                content = f.read()
            # Try a few common patterns
            patterns = [
                r"server_port\s*=\s*(\d+)",
                r"server-port\s*=\s*(\d+)",
                r"server\.port\s*=\s*(\d+)",
                r"admin_port\s*=\s*(\d+)",
                r"rpc_port\s*=\s*(\d+)",
            ]
            for pat in patterns:
                m = re.search(pat, content)
                if m:
                    try:
                        return int(m.group(1))
                    except ValueError:
                        pass
            return None
        except Exception:
            return None

    def is_node_running(self, node_name: str) -> bool:
        """Check if a node is running."""
        pid = self._load_pid(node_name)
        return pid is not None and self._is_process_running(pid)

    def get_node_logs(self, node_name: str, lines: int = 50) -> Optional[str]:
        """Get the last N lines of node logs."""
        data_dir = Path(f"./data/{node_name}")
        log_file = data_dir / "logs" / f"{node_name}.log"

        if not log_file.exists():
            return None

        try:
            # Read last N lines
            with open(log_file) as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            console.print(f"[red]Error reading logs: {e}[/red]")
            return None

    def follow_node_logs(self, node_name: str, tail: int = 100) -> bool:
        """Stream logs for a node in real time (tail -f behavior)."""
        from rich.console import Console

        data_dir = Path(f"./data/{node_name}")
        log_file = data_dir / "logs" / f"{node_name}.log"

        console = Console()

        try:
            # Wait briefly if log file doesn't exist yet
            timeout_seconds = 10
            start_time = time.time()
            while (
                not log_file.exists() and (time.time() - start_time) < timeout_seconds
            ):
                time.sleep(0.25)

            if not log_file.exists():
                console.print(
                    f"[yellow]No logs found for {node_name}. Ensure the node is running and check {log_file}[/yellow]"
                )
                return False

            with open(log_file) as f:
                # Seek to show last `tail` lines first
                if tail is not None and tail > 0:
                    try:
                        # Read last N lines efficiently
                        f.seek(0, os.SEEK_END)
                        file_size = f.tell()
                        block_size = 1024
                        data = ""
                        bytes_to_read = min(file_size, block_size)
                        while bytes_to_read > 0 and data.count("\n") <= tail:
                            f.seek(f.tell() - bytes_to_read)
                            data = f.read(bytes_to_read) + data
                            f.seek(f.tell() - bytes_to_read)
                            if f.tell() == 0:
                                break
                            bytes_to_read = min(f.tell(), block_size)
                        lines_buf = data.splitlines()[-tail:]
                        for line in lines_buf:
                            console.print(line)
                    except Exception:
                        # Fallback: read all and slice
                        f.seek(0)
                        lines_buf = f.readlines()[-tail:]
                        for line in lines_buf:
                            console.print(line.rstrip("\n"))

                # Now follow appended content
                f.seek(0, os.SEEK_END)
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.25)
                        continue
                    console.print(line.rstrip("\n"))

        except KeyboardInterrupt:
            return True
        except Exception as e:
            console.print(f"[red]Error streaming logs: {e}[/red]")
            return False

    def run_multiple_nodes(
        self,
        count: int,
        base_port: int = 2428,
        base_rpc_port: int = 2528,
        chain_id: str = "testnet-1",
        prefix: str = "calimero-node",
        image: Optional[str] = None,  # Ignored in binary mode
        auth_service: bool = False,  # Not supported in binary mode
        auth_image: Optional[str] = None,  # Ignored
        auth_use_cached: bool = False,  # Ignored
        webui_use_cached: bool = False,  # Ignored
        log_level: str = "debug",
    ) -> bool:
        """
        Start multiple nodes with sequential naming.

        Args:
            count: Number of nodes to start
            base_port: Base P2P port (each node gets base_port + index)
            base_rpc_port: Base RPC port (each node gets base_rpc_port + index)
            chain_id: Blockchain chain ID
            prefix: Node name prefix
            image: Ignored (binary mode doesn't use Docker images)
            auth_service: Not supported in binary mode
            auth_use_cached: Ignored
            webui_use_cached: Ignored
            log_level: RUST_LOG level

        Returns:
            True if all nodes started successfully
        """
        if auth_service:
            console.print(
                "[yellow]⚠ Auth service is not supported in binary mode (--no-docker)[/yellow]"
            )

        console.print(f"[cyan]Starting {count} nodes with prefix '{prefix}'...[/cyan]")

        success_count = 0
        # Default base ports if None provided
        if base_port is None:
            base_port = 2428
        if base_rpc_port is None:
            base_rpc_port = 2528

        for i in range(count):
            node_name = f"{prefix}-{i+1}"
            port = base_port + (i * 100)  # Space out ports
            rpc_port = base_rpc_port + (i * 100)

            if self.run_node(
                node_name=node_name,
                port=port,
                rpc_port=rpc_port,
                chain_id=chain_id,
                log_level=log_level,
            ):
                success_count += 1
            else:
                console.print(f"[red]✗ Failed to start node {node_name}[/red]")
                return False

        console.print(
            f"\n[bold green]✓ Successfully started all {success_count} node(s)[/bold green]"
        )
        return True

    def force_pull_image(self, image: str) -> bool:
        """
        No-op for binary mode (no Docker images to pull).

        Args:
            image: Ignored

        Returns:
            True (always succeeds as it's a no-op)
        """
        # Binary mode doesn't use Docker images
        return True

    def verify_admin_binding(self, node_name: str) -> bool:
        """
        Verify admin API binding for a node.

        Args:
            node_name: Name of the node to verify

        Returns:
            True if node is running (admin API verification not implemented for binary mode)
        """
        # For binary mode, just check if the process is running
        return self.is_node_running(node_name)
