"""Subprocess transport implementation using Claude Code CLI."""

import json
import logging
import os
import platform
import re
import shutil
import sys
import tempfile
from collections.abc import AsyncIterable, AsyncIterator
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path
from subprocess import PIPE
from typing import Any

import anyio
import anyio.abc
from anyio.abc import Process
from anyio.streams.text import TextReceiveStream, TextSendStream

from ..._errors import CLIConnectionError, CLINotFoundError, ProcessError
from ..._errors import CLIJSONDecodeError as SDKJSONDecodeError
from ..._version import __version__
from ...types import ClaudeAgentOptions
from . import Transport

logger = logging.getLogger(__name__)

_DEFAULT_MAX_BUFFER_SIZE = 1024 * 1024  # 1MB buffer limit
MINIMUM_CLAUDE_CODE_VERSION = "2.0.0"

# Platform-specific command line length limits
# Windows cmd.exe has a limit of 8191 characters, use 8000 for safety
# Other platforms have much higher limits
_CMD_LENGTH_LIMIT = 8000 if platform.system() == "Windows" else 100000


class SubprocessCLITransport(Transport):
    """Subprocess transport using Claude Code CLI."""

    def __init__(
        self,
        prompt: str | AsyncIterable[dict[str, Any]],
        options: ClaudeAgentOptions,
    ):
        self._prompt = prompt
        self._is_streaming = not isinstance(prompt, str)
        self._options = options
        self._cli_path = (
            str(options.cli_path) if options.cli_path is not None else self._find_cli()
        )
        self._cwd = str(options.cwd) if options.cwd else None
        self._process: Process | None = None
        self._stdout_stream: TextReceiveStream | None = None
        self._stdin_stream: TextSendStream | None = None
        self._stderr_stream: TextReceiveStream | None = None
        self._stderr_task_group: anyio.abc.TaskGroup | None = None
        self._ready = False
        self._exit_error: Exception | None = None  # Track process exit errors
        self._max_buffer_size = (
            options.max_buffer_size
            if options.max_buffer_size is not None
            else _DEFAULT_MAX_BUFFER_SIZE
        )
        self._temp_files: list[str] = []  # Track temporary files for cleanup

    def _find_cli(self) -> str:
        """Find Claude Code CLI binary."""
        if cli := shutil.which("claude"):
            return cli

        locations = [
            Path.home() / ".npm-global/bin/claude",
            Path("/usr/local/bin/claude"),
            Path.home() / ".local/bin/claude",
            Path.home() / "node_modules/.bin/claude",
            Path.home() / ".yarn/bin/claude",
        ]

        for path in locations:
            if path.exists() and path.is_file():
                return str(path)

        raise CLINotFoundError(
            "Claude Code not found. Install with:\n"
            "  npm install -g @anthropic-ai/claude-code\n"
            "\nIf already installed locally, try:\n"
            '  export PATH="$HOME/node_modules/.bin:$PATH"\n'
            "\nOr provide the path via ClaudeAgentOptions:\n"
            "  ClaudeAgentOptions(cli_path='/path/to/claude')"
        )

    def _build_command(self) -> list[str]:
        """Build CLI command with arguments."""
        cmd = [self._cli_path, "--output-format", "stream-json", "--verbose"]

        if self._options.system_prompt is None:
            pass
        elif isinstance(self._options.system_prompt, str):
            cmd.extend(["--system-prompt", self._options.system_prompt])
        else:
            if (
                self._options.system_prompt.get("type") == "preset"
                and "append" in self._options.system_prompt
            ):
                cmd.extend(
                    ["--append-system-prompt", self._options.system_prompt["append"]]
                )

        if self._options.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(self._options.allowed_tools)])

        if self._options.max_turns:
            cmd.extend(["--max-turns", str(self._options.max_turns)])

        if self._options.disallowed_tools:
            cmd.extend(["--disallowedTools", ",".join(self._options.disallowed_tools)])

        if self._options.model:
            cmd.extend(["--model", self._options.model])

        if self._options.permission_prompt_tool_name:
            cmd.extend(
                ["--permission-prompt-tool", self._options.permission_prompt_tool_name]
            )

        if self._options.permission_mode:
            cmd.extend(["--permission-mode", self._options.permission_mode])

        if self._options.continue_conversation:
            cmd.append("--continue")

        if self._options.resume:
            cmd.extend(["--resume", self._options.resume])

        if self._options.settings:
            cmd.extend(["--settings", self._options.settings])

        if self._options.add_dirs:
            # Convert all paths to strings and add each directory
            for directory in self._options.add_dirs:
                cmd.extend(["--add-dir", str(directory)])

        if self._options.mcp_servers:
            if isinstance(self._options.mcp_servers, dict):
                # Process all servers, stripping instance field from SDK servers
                servers_for_cli: dict[str, Any] = {}
                for name, config in self._options.mcp_servers.items():
                    if isinstance(config, dict) and config.get("type") == "sdk":
                        # For SDK servers, pass everything except the instance field
                        sdk_config: dict[str, object] = {
                            k: v for k, v in config.items() if k != "instance"
                        }
                        servers_for_cli[name] = sdk_config
                    else:
                        # For external servers, pass as-is
                        servers_for_cli[name] = config

                # Pass all servers to CLI
                if servers_for_cli:
                    cmd.extend(
                        [
                            "--mcp-config",
                            json.dumps({"mcpServers": servers_for_cli}),
                        ]
                    )
            else:
                # String or Path format: pass directly as file path or JSON string
                cmd.extend(["--mcp-config", str(self._options.mcp_servers)])

        if self._options.include_partial_messages:
            cmd.append("--include-partial-messages")

        if self._options.fork_session:
            cmd.append("--fork-session")

        if self._options.agents:
            agents_dict = {
                name: {k: v for k, v in asdict(agent_def).items() if v is not None}
                for name, agent_def in self._options.agents.items()
            }
            agents_json = json.dumps(agents_dict)
            cmd.extend(["--agents", agents_json])

        sources_value = (
            ",".join(self._options.setting_sources)
            if self._options.setting_sources is not None
            else ""
        )
        cmd.extend(["--setting-sources", sources_value])

        # Add plugin directories
        if self._options.plugins:
            for plugin in self._options.plugins:
                if plugin["type"] == "local":
                    cmd.extend(["--plugin-dir", plugin["path"]])
                else:
                    raise ValueError(f"Unsupported plugin type: {plugin['type']}")

        # Add extra args for future CLI flags
        for flag, value in self._options.extra_args.items():
            if value is None:
                # Boolean flag without value
                cmd.append(f"--{flag}")
            else:
                # Flag with value
                cmd.extend([f"--{flag}", str(value)])

        # Add prompt handling based on mode
        if self._is_streaming:
            # Streaming mode: use --input-format stream-json
            cmd.extend(["--input-format", "stream-json"])
        else:
            # String mode: use --print with the prompt
            cmd.extend(["--print", "--", str(self._prompt)])

        # Check if command line is too long (Windows limitation)
        cmd_str = " ".join(cmd)
        if len(cmd_str) > _CMD_LENGTH_LIMIT and self._options.agents:
            # Command is too long - use temp file for agents
            # Find the --agents argument and replace its value with @filepath
            try:
                agents_idx = cmd.index("--agents")
                agents_json_value = cmd[agents_idx + 1]

                # Create a temporary file
                # ruff: noqa: SIM115
                temp_file = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False, encoding="utf-8"
                )
                temp_file.write(agents_json_value)
                temp_file.close()

                # Track for cleanup
                self._temp_files.append(temp_file.name)

                # Replace agents JSON with @filepath reference
                cmd[agents_idx + 1] = f"@{temp_file.name}"

                logger.info(
                    f"Command line length ({len(cmd_str)}) exceeds limit ({_CMD_LENGTH_LIMIT}). "
                    f"Using temp file for --agents: {temp_file.name}"
                )
            except (ValueError, IndexError) as e:
                # This shouldn't happen, but log it just in case
                logger.warning(f"Failed to optimize command line length: {e}")

        return cmd

    async def connect(self) -> None:
        """Start subprocess."""
        if self._process:
            return

        if not os.environ.get("CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK"):
            await self._check_claude_version()

        cmd = self._build_command()
        try:
            # Merge environment variables: system -> user -> SDK required
            process_env = {
                **os.environ,
                **self._options.env,  # User-provided env vars
                "CLAUDE_CODE_ENTRYPOINT": "sdk-py",
                "CLAUDE_AGENT_SDK_VERSION": __version__,
            }

            if self._cwd:
                process_env["PWD"] = self._cwd

            # Pipe stderr if we have a callback OR debug mode is enabled
            should_pipe_stderr = (
                self._options.stderr is not None
                or "debug-to-stderr" in self._options.extra_args
            )

            # For backward compat: use debug_stderr file object if no callback and debug is on
            stderr_dest = PIPE if should_pipe_stderr else None

            self._process = await anyio.open_process(
                cmd,
                stdin=PIPE,
                stdout=PIPE,
                stderr=stderr_dest,
                cwd=self._cwd,
                env=process_env,
                user=self._options.user,
            )

            if self._process.stdout:
                self._stdout_stream = TextReceiveStream(self._process.stdout)

            # Setup stderr stream if piped
            if should_pipe_stderr and self._process.stderr:
                self._stderr_stream = TextReceiveStream(self._process.stderr)
                # Start async task to read stderr
                self._stderr_task_group = anyio.create_task_group()
                await self._stderr_task_group.__aenter__()
                self._stderr_task_group.start_soon(self._handle_stderr)

            # Setup stdin for streaming mode
            if self._is_streaming and self._process.stdin:
                self._stdin_stream = TextSendStream(self._process.stdin)
            elif not self._is_streaming and self._process.stdin:
                # String mode: close stdin immediately
                await self._process.stdin.aclose()

            self._ready = True

        except FileNotFoundError as e:
            # Check if the error comes from the working directory or the CLI
            if self._cwd and not Path(self._cwd).exists():
                error = CLIConnectionError(
                    f"Working directory does not exist: {self._cwd}"
                )
                self._exit_error = error
                raise error from e
            error = CLINotFoundError(f"Claude Code not found at: {self._cli_path}")
            self._exit_error = error
            raise error from e
        except Exception as e:
            error = CLIConnectionError(f"Failed to start Claude Code: {e}")
            self._exit_error = error
            raise error from e

    async def _handle_stderr(self) -> None:
        """Handle stderr stream - read and invoke callbacks."""
        if not self._stderr_stream:
            return

        try:
            async for line in self._stderr_stream:
                line_str = line.rstrip()
                if not line_str:
                    continue

                # Call the stderr callback if provided
                if self._options.stderr:
                    self._options.stderr(line_str)

                # For backward compatibility: write to debug_stderr if in debug mode
                elif (
                    "debug-to-stderr" in self._options.extra_args
                    and self._options.debug_stderr
                ):
                    self._options.debug_stderr.write(line_str + "\n")
                    if hasattr(self._options.debug_stderr, "flush"):
                        self._options.debug_stderr.flush()
        except anyio.ClosedResourceError:
            pass  # Stream closed, exit normally
        except Exception:
            pass  # Ignore other errors during stderr reading

    async def close(self) -> None:
        """Close the transport and clean up resources."""
        self._ready = False

        # Clean up temporary files first (before early return)
        for temp_file in self._temp_files:
            with suppress(Exception):
                Path(temp_file).unlink(missing_ok=True)
        self._temp_files.clear()

        if not self._process:
            return

        # Close stderr task group if active
        if self._stderr_task_group:
            with suppress(Exception):
                self._stderr_task_group.cancel_scope.cancel()
                await self._stderr_task_group.__aexit__(None, None, None)
            self._stderr_task_group = None

        # Close streams
        if self._stdin_stream:
            with suppress(Exception):
                await self._stdin_stream.aclose()
            self._stdin_stream = None

        if self._stderr_stream:
            with suppress(Exception):
                await self._stderr_stream.aclose()
            self._stderr_stream = None

        if self._process.stdin:
            with suppress(Exception):
                await self._process.stdin.aclose()

        # Terminate and wait for process
        if self._process.returncode is None:
            with suppress(ProcessLookupError):
                self._process.terminate()
                # Wait for process to finish with timeout
                with suppress(Exception):
                    # Just try to wait, but don't block if it fails
                    await self._process.wait()

        self._process = None
        self._stdout_stream = None
        self._stdin_stream = None
        self._stderr_stream = None
        self._exit_error = None

    async def write(self, data: str) -> None:
        """Write raw data to the transport."""
        # Check if ready (like TypeScript)
        if not self._ready or not self._stdin_stream:
            raise CLIConnectionError("ProcessTransport is not ready for writing")

        # Check if process is still alive (like TypeScript)
        if self._process and self._process.returncode is not None:
            raise CLIConnectionError(
                f"Cannot write to terminated process (exit code: {self._process.returncode})"
            )

        # Check for exit errors (like TypeScript)
        if self._exit_error:
            raise CLIConnectionError(
                f"Cannot write to process that exited with error: {self._exit_error}"
            ) from self._exit_error

        try:
            await self._stdin_stream.send(data)
        except Exception as e:
            self._ready = False  # Mark as not ready (like TypeScript)
            self._exit_error = CLIConnectionError(
                f"Failed to write to process stdin: {e}"
            )
            raise self._exit_error from e

    async def end_input(self) -> None:
        """End the input stream (close stdin)."""
        if self._stdin_stream:
            with suppress(Exception):
                await self._stdin_stream.aclose()
            self._stdin_stream = None

    def read_messages(self) -> AsyncIterator[dict[str, Any]]:
        """Read and parse messages from the transport."""
        return self._read_messages_impl()

    async def _read_messages_impl(self) -> AsyncIterator[dict[str, Any]]:
        """Internal implementation of read_messages."""
        if not self._process or not self._stdout_stream:
            raise CLIConnectionError("Not connected")

        json_buffer = ""

        # Process stdout messages
        try:
            async for line in self._stdout_stream:
                line_str = line.strip()
                if not line_str:
                    continue

                # Accumulate partial JSON until we can parse it
                # Note: TextReceiveStream can truncate long lines, so we need to buffer
                # and speculatively parse until we get a complete JSON object
                json_lines = line_str.split("\n")

                for json_line in json_lines:
                    json_line = json_line.strip()
                    if not json_line:
                        continue

                    # Keep accumulating partial JSON until we can parse it
                    json_buffer += json_line

                    if len(json_buffer) > self._max_buffer_size:
                        buffer_length = len(json_buffer)
                        json_buffer = ""
                        raise SDKJSONDecodeError(
                            f"JSON message exceeded maximum buffer size of {self._max_buffer_size} bytes",
                            ValueError(
                                f"Buffer size {buffer_length} exceeds limit {self._max_buffer_size}"
                            ),
                        )

                    try:
                        data = json.loads(json_buffer)
                        json_buffer = ""
                        yield data
                    except json.JSONDecodeError:
                        # We are speculatively decoding the buffer until we get
                        # a full JSON object. If there is an actual issue, we
                        # raise an error after exceeding the configured limit.
                        continue

        except anyio.ClosedResourceError:
            pass
        except GeneratorExit:
            # Client disconnected
            pass

        # Check process completion and handle errors
        try:
            returncode = await self._process.wait()
        except Exception:
            returncode = -1

        # Use exit code for error detection
        if returncode is not None and returncode != 0:
            self._exit_error = ProcessError(
                f"Command failed with exit code {returncode}",
                exit_code=returncode,
                stderr="Check stderr output for details",
            )
            raise self._exit_error

    async def _check_claude_version(self) -> None:
        """Check Claude Code version and warn if below minimum."""
        version_process = None
        try:
            with anyio.fail_after(2):  # 2 second timeout
                version_process = await anyio.open_process(
                    [self._cli_path, "-v"],
                    stdout=PIPE,
                    stderr=PIPE,
                )

                if version_process.stdout:
                    stdout_bytes = await version_process.stdout.receive()
                    version_output = stdout_bytes.decode().strip()

                    match = re.match(r"([0-9]+\.[0-9]+\.[0-9]+)", version_output)
                    if match:
                        version = match.group(1)
                        version_parts = [int(x) for x in version.split(".")]
                        min_parts = [
                            int(x) for x in MINIMUM_CLAUDE_CODE_VERSION.split(".")
                        ]

                        if version_parts < min_parts:
                            warning = (
                                f"Warning: Claude Code version {version} is unsupported in the Agent SDK. "
                                f"Minimum required version is {MINIMUM_CLAUDE_CODE_VERSION}. "
                                "Some features may not work correctly."
                            )
                            logger.warning(warning)
                            print(warning, file=sys.stderr)
        except Exception:
            pass
        finally:
            if version_process:
                with suppress(Exception):
                    version_process.terminate()
                with suppress(Exception):
                    await version_process.wait()

    def is_ready(self) -> bool:
        """Check if transport is ready for communication."""
        return self._ready
