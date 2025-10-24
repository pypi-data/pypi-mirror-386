"""
BaseBox - Foundation for specialized container types.

Provides common functionality for all specialized boxes (CodeBox, BrowserBox, etc.)
"""

from typing import Optional
import sys
import os
import fcntl


class BaseBox:
    """
    Base class for specialized container types.

    This class encapsulates the common patterns:
    1. Dual constructor (convenience vs explicit runtime)
    2. Async context manager support
    3. Stdio blocking mode restoration
    4. Runtime lifecycle management

    Subclasses should override:
    - _create_box_options(): Return BoxOptions for their specific use case
    - Add domain-specific methods (e.g., CodeBox.run(), BrowserBox.navigate())
    """

    def __init__(
        self,
        image: str,
        memory_mib: Optional[int] = None,
        cpus: Optional[int] = None,
        home_dir: Optional[str] = None,
        **kwargs
    ):
        """
        Create a specialized box with its own internal runtime.

        This is the convenience constructor that creates a runtime automatically.
        For better resource management when creating multiple boxes, use create() instead.

        Args:
            image: Container image to use
            memory_mib: Memory limit in MiB
            cpus: Number of CPU cores
            home_dir: Runtime home directory (optional)
            **kwargs: Additional configuration options
        """
        try:
            from .boxlite import Boxlite, Options
        except ImportError as e:
            raise ImportError(
                f"BoxLite native extension not found: {e}. "
                "Please install with: pip install boxlite"
            )

        # Create runtime options
        runtime_opts = Options(
            home_dir=home_dir,
            engine=kwargs.get('engine', 'libkrun')
        )

        # Create the runtime (this acquires the lock)
        self._runtime = Boxlite(runtime_opts)
        self._owns_runtime = True

        # Create box using subclass-defined options
        box_opts = self._create_box_options(image, memory_mib, cpus, **kwargs)
        self._box = self._runtime.create(box_opts)

    @classmethod
    def create(
        cls,
        runtime,  # Type: Boxlite, but avoid import at module level
        image: str,
        memory_mib: Optional[int] = None,
        cpus: Optional[int] = None,
        **kwargs
    ):
        """
        Create a specialized box using an existing runtime.

        This is the recommended approach when creating multiple boxes,
        as it shares a single runtime instance.

        Args:
            runtime: Existing Boxlite runtime instance
            image: Container image to use
            memory_mib: Memory limit in MiB
            cpus: Number of CPU cores
            **kwargs: Additional configuration options

        Returns:
            Specialized box instance

        Example:
            >>> runtime = boxlite.Boxlite(boxlite.Options())
            >>> box1 = SomeBox.create(runtime, image="custom:latest")
            >>> box2 = SomeBox.create(runtime, image="custom:latest", memory_mib=1024)
        """
        # Create instance without going through __init__
        instance = cls.__new__(cls)
        instance._runtime = runtime
        instance._owns_runtime = False

        # Create box using subclass-defined options
        box_opts = instance._create_box_options(image, memory_mib, cpus, **kwargs)
        instance._box = runtime.create(box_opts)

        return instance

    def _create_box_options(self, image: str, memory_mib: Optional[int], cpus: Optional[int], **kwargs):
        """
        Create BoxOptions for this specialized box.

        Subclasses should override this to provide their specific defaults.

        Args:
            image: Container image
            memory_mib: Memory limit
            cpus: CPU cores
            **kwargs: Additional options

        Returns:
            BoxOptions instance
        """
        try:
            from .boxlite import BoxOptions
        except ImportError as e:
            raise ImportError(
                f"BoxLite native extension not found: {e}. "
                "Please install with: pip install boxlite"
            )

        return BoxOptions(
            image=image,
            cpus=cpus,
            memory_mib=memory_mib,
            working_dir=kwargs.get('working_dir'),
            env=kwargs.get('env', [])
        )

    async def __aenter__(self):
        """Async context manager entry."""
        self._box.__enter__()
        # Tokio runtime sets stdout/stderr to non-blocking mode
        # Restore blocking mode to prevent BlockingIOError when printing
        self._restore_blocking_mode()
        return self

    def _restore_blocking_mode(self):
        """Restore blocking mode on stdout/stderr after Tokio sets them to non-blocking."""
        for fd in [sys.stdout.fileno(), sys.stderr.fileno()]:
            try:
                flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                if flags & os.O_NONBLOCK:
                    fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
            except (OSError, AttributeError):
                # Ignore errors (e.g., when stdout/stderr is not a real file)
                pass

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        result = self._box.__exit__(exc_type, exc_val, exc_tb)

        # Close runtime if we own it
        if self._owns_runtime:
            self._runtime.close()

        return result

    @property
    def id(self) -> str:
        """Get the box ID."""
        return self._box.id

    def info(self):
        """Get box information."""
        return self._box.info()

    async def execute(self, command: str, *args) -> str:
        """
        Execute a command in the container.

        Args:
            command: Command to execute
            *args: Command arguments

        Returns:
            Command output as string
        """
        result = await self._box.execute(command, list(args) if args else None)
        if isinstance(result, list):
            return '\n'.join(f"[{stream}] {text}" for stream, text in result if text.strip())
        return str(result)

    def shutdown(self):
        """
        Shutdown the box and release resources.

        Note: Usually not needed as context manager handles cleanup.
        """
        self._box.shutdown()
        if self._owns_runtime:
            self._runtime.close()
