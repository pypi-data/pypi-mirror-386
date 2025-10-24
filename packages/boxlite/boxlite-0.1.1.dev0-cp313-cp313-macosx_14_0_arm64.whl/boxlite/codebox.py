"""
CodeBox - Secure Python code execution container.

Provides a simple, secure environment for running untrusted Python code.
"""

from typing import Optional
from .basebox import BaseBox


class CodeBox(BaseBox):
    """
    Secure container for executing Python code.

    CodeBox provides an isolated environment for running untrusted Python code
    with built-in safety and result formatting.

    Usage Pattern 1 - Explicit runtime (recommended for multiple boxes):
        >>> runtime = boxlite.Boxlite(boxlite.Options())
        >>> codebox = CodeBox.create(runtime, memory_mib=512)
        >>> result = await codebox.run("print('Hello, World!')")

    Usage Pattern 2 - Convenience constructor (creates internal runtime):
        >>> async with CodeBox() as cb:
        ...     result = await cb.run("print('Hello, World!')")
    """

    def __init__(
        self,
        image: str = "python:slim",
        memory_mib: Optional[int] = None,
        cpus: Optional[int] = None,
        home_dir: Optional[str] = None,
        **kwargs
    ):
        """
        Create a new CodeBox with its own internal runtime.

        This is the convenience constructor that creates a runtime automatically.
        For better resource management when creating multiple boxes, use create() instead.

        Args:
            image: Container image with Python (default: python:slim)
            memory_mib: Memory limit in MiB (default: system default)
            cpus: Number of CPU cores (default: system default)
            home_dir: Runtime home directory (optional)
            **kwargs: Additional configuration options
        """
        super().__init__(image, memory_mib, cpus, home_dir, **kwargs)

    @classmethod
    def create(
        cls,
        runtime,
        image: str = "python:slim",
        memory_mib: Optional[int] = None,
        cpus: Optional[int] = None,
        **kwargs
    ):
        """
        Create a CodeBox using an existing runtime.

        This is the recommended approach when creating multiple boxes,
        as it shares a single runtime instance.

        Args:
            runtime: Existing Boxlite runtime instance
            image: Container image with Python (default: python:slim)
            memory_mib: Memory limit in MiB
            cpus: Number of CPU cores
            **kwargs: Additional configuration options

        Returns:
            CodeBox instance

        Example:
            >>> runtime = boxlite.Boxlite(boxlite.Options())
            >>> cb1 = CodeBox.create(runtime)
            >>> cb2 = CodeBox.create(runtime, memory_mib=1024)
        """
        return super(CodeBox, cls).create(runtime, image, memory_mib, cpus, **kwargs)

    async def run(self, code: str, timeout: Optional[int] = None) -> str:
        """
        Execute Python code in the secure container.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds (not yet implemented)

        Returns:
            Execution output as a string

        Example:
            >>> async with CodeBox() as cb:
            ...     result = await cb.run("print('Hello, World!')")
            ...     print(result)
            [stdout] Hello, World!

        Note:
            Uses python3 from the container image.
            For custom Python paths, use execute() directly:
                await cb.execute("/path/to/python", "-c", code)
        """
        # Execute Python code using python3 -c
        return await self.execute("/usr/local/bin/python", "-c", code)

    async def run_script(self, script_path: str) -> str:
        """
        Execute a Python script file in the container.

        Args:
            script_path: Path to the Python script on the host

        Returns:
            Execution output as a string
        """
        with open(script_path, 'r') as f:
            code = f.read()
        return await self.run(code)

    async def install_package(self, package: str) -> str:
        """
        Install a Python package in the container using pip.

        Args:
            package: Package name (e.g., 'requests', 'numpy==1.24.0')

        Returns:
            Installation output

        Example:
            >>> async with CodeBox() as cb:
            ...     await cb.install_package("requests")
            ...     result = await cb.run("import requests; print(requests.__version__)")
        """
        return await self.execute("pip", "install", package)

    async def install_packages(self, *packages: str) -> str:
        """
        Install multiple Python packages.

        Args:
            *packages: Package names to install

        Returns:
            Installation output

        Example:
            >>> async with CodeBox() as cb:
            ...     await cb.install_packages("requests", "numpy", "pandas")
        """
        return await self.execute("pip", "install", *packages)
