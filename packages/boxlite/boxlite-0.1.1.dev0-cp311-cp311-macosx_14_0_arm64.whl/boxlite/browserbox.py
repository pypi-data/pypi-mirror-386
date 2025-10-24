"""
BrowserBox - Secure web browser container (example).

This is a future specialized box showing how to extend BaseBox.
"""

from typing import Optional
from .basebox import BaseBox


class BrowserBox(BaseBox):
    """
    Secure container for browser automation (future implementation).

    Example of how to create specialized boxes by inheriting from BaseBox.

    Usage:
        >>> runtime = boxlite.Boxlite(boxlite.Options())
        >>> browser = BrowserBox.create(runtime)
        >>> await browser.navigate("https://example.com")
    """

    def __init__(
        self,
        image: str = "browserbox:latest",
        memory_mib: Optional[int] = 2048,  # Browsers need more memory
        cpus: Optional[int] = None,
        home_dir: Optional[str] = None,
        **kwargs
    ):
        """
        Create a new BrowserBox with its own internal runtime.

        Args:
            image: Container image with browser (default: browserbox:latest)
            memory_mib: Memory limit in MiB (default: 2048 for browsers)
            cpus: Number of CPU cores
            home_dir: Runtime home directory (optional)
            **kwargs: Additional configuration options
        """
        super().__init__(image, memory_mib, cpus, home_dir, **kwargs)

    @classmethod
    def create(
        cls,
        runtime,
        image: str = "browserbox:latest",
        memory_mib: Optional[int] = 2048,
        cpus: Optional[int] = None,
        **kwargs
    ):
        """
        Create a BrowserBox using an existing runtime.

        Args:
            runtime: Existing Boxlite runtime instance
            image: Container image with browser
            memory_mib: Memory limit in MiB (default: 2048)
            cpus: Number of CPU cores
            **kwargs: Additional configuration options

        Returns:
            BrowserBox instance
        """
        return super(BrowserBox, cls).create(runtime, image, memory_mib, cpus, **kwargs)

    async def navigate(self, url: str) -> str:
        """
        Navigate browser to URL (example method).

        Args:
            url: URL to navigate to

        Returns:
            Page content or status
        """
        # Example implementation - would use actual browser automation
        return await self.execute("curl", "-L", url)

    async def screenshot(self, path: str) -> str:
        """
        Take a screenshot (example method).

        Args:
            path: Path to save screenshot

        Returns:
            Status message
        """
        # Example implementation - would use actual browser automation
        return await self.execute("echo", "Screenshot would be saved to", path)

    async def eval_js(self, script: str) -> str:
        """
        Evaluate JavaScript in browser context (example method).

        Args:
            script: JavaScript code to execute

        Returns:
            Execution result
        """
        # Example implementation - would use actual browser automation
        return await self.execute("echo", "Would evaluate JS:", script)
