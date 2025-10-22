"""Microsandbox execution environment that runs code in containerized sandboxes."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Self

from anyenv.code_execution.base import ExecutionEnvironment
from anyenv.code_execution.models import ExecutionResult


if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

    from anyenv.code_execution.models import Language, ServerInfo


class MicrosandboxExecutionEnvironment(ExecutionEnvironment):
    """Executes code in a Microsandbox containerized environment."""

    def __init__(
        self,
        lifespan_handler: AbstractAsyncContextManager[ServerInfo] | None = None,
        server_url: str | None = None,
        namespace: str = "default",
        api_key: str | None = None,
        memory: int = 512,
        cpus: float = 1.0,
        timeout: float = 180.0,
        language: Language = "python",
        image: str | None = None,
    ):
        """Initialize Microsandbox environment.

        Args:
            lifespan_handler: Async context manager for tool server (optional)
            server_url: Microsandbox server URL (defaults to MSB_SERVER_URL env var)
            namespace: Sandbox namespace
            api_key: API key for authentication (uses MSB_API_KEY env var if None)
            memory: Memory limit in MB
            cpus: CPU limit
            timeout: Sandbox start timeout in seconds
            language: Programming language to use
            image: Custom Docker image (uses default for language if None)
        """
        super().__init__(lifespan_handler=lifespan_handler)
        self.server_url = server_url
        self.namespace = namespace
        self.api_key = api_key
        self.memory = memory
        self.cpus = cpus
        self.timeout = timeout
        self.language = language
        self.image = image
        self.sandbox = None

    async def __aenter__(self) -> Self:
        """Setup Microsandbox environment."""
        # Start tool server via base class
        await super().__aenter__()

        # Import here to avoid import issues if microsandbox package not installed
        try:
            from microsandbox import NodeSandbox, PythonSandbox
        except ImportError as e:
            error_msg = (
                "microsandbox package is required for MicrosandboxExecutionEnvironment. "
                "Install it with: pip install microsandbox"
            )
            raise ImportError(error_msg) from e

        # Select appropriate sandbox type based on language
        match self.language:
            case "python":
                sandbox_class = PythonSandbox
            case "javascript" | "typescript":
                sandbox_class = NodeSandbox
            case _:
                sandbox_class = PythonSandbox
        # Create sandbox with context manager
        self.sandbox = await sandbox_class.create(
            server_url=self.server_url,  # type: ignore
            namespace=self.namespace,
            api_key=self.api_key,
        ).__aenter__()

        # Configure sandbox resources if needed
        # Note: Microsandbox handles resource config during start()
        # which is already called by the context manager

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cleanup sandbox."""
        if self.sandbox:
            import contextlib

            with contextlib.suppress(Exception):
                # Exit the context manager properly
                await self.sandbox.stop()

        # Cleanup server via base class
        await super().__aexit__(exc_type, exc_val, exc_tb)

    async def execute(self, code: str) -> ExecutionResult:
        """Execute code in the Microsandbox environment."""
        if not self.sandbox:
            error_msg = "Microsandbox environment not properly initialized"
            raise RuntimeError(error_msg)

        start_time = time.time()

        try:
            # Execute code using sandbox.run() method
            execution = await self.sandbox.run(code)
            duration = time.time() - start_time

            # Get output and error from execution
            stdout = await execution.output()
            stderr = await execution.error()

            # Check if execution was successful
            success = not execution.has_error()

            if success:
                return ExecutionResult(
                    result=stdout if stdout else None,
                    duration=duration,
                    success=True,
                    stdout=stdout,
                    stderr=stderr,
                )

            return ExecutionResult(
                result=None,
                duration=duration,
                success=False,
                error=stderr or "Code execution failed",
                error_type="ExecutionError",
                stdout=stdout,
                stderr=stderr,
            )

        except Exception as e:  # noqa: BLE001
            duration = time.time() - start_time
            return ExecutionResult(
                result=None,
                duration=duration,
                success=False,
                error=str(e),
                error_type=type(e).__name__,
            )

    async def execute_command(self, command: str) -> ExecutionResult:
        """Execute a terminal command in the Microsandbox environment."""
        if not self.sandbox:
            error_msg = "Microsandbox environment not properly initialized"
            raise RuntimeError(error_msg)

        start_time = time.time()

        try:
            # Parse command into command and args
            import shlex

            parts = shlex.split(command)
            if not parts:
                error_msg = "Empty command provided"
                raise ValueError(error_msg)  # noqa: TRY301

            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            # Execute command using sandbox.command.run() method
            execution = await self.sandbox.command.run(cmd, args)
            duration = time.time() - start_time

            # Get output and error from command execution
            stdout = await execution.output()
            stderr = await execution.error()

            # Check success based on exit code
            success = execution.success

            return ExecutionResult(
                result=stdout if success else None,
                duration=duration,
                success=success,
                error=stderr if not success else None,
                error_type="CommandError" if not success else None,
                stdout=stdout,
                stderr=stderr,
            )

        except Exception as e:  # noqa: BLE001
            duration = time.time() - start_time
            return ExecutionResult(
                result=None,
                duration=duration,
                success=False,
                error=str(e),
                error_type=type(e).__name__,
            )

    # Note: Streaming methods not implemented as Microsandbox doesn't
    # support real-time streaming
    # The base class will raise NotImplementedError for execute_stream()
    # and execute_command_stream()
