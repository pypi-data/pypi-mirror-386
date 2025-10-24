"""A generic FastAPI server implementation."""

from typing import TYPE_CHECKING

from lazy_bear import LazyLoader

if TYPE_CHECKING:
    import threading

    from fastapi import FastAPI
    import uvicorn
else:
    FastAPI = LazyLoader("fastapi").to("FastAPI")
    uvicorn = LazyLoader("uvicorn")
    threading = LazyLoader("threading")


def run_server(app: FastAPI, host: str, port: int, log_level: str = "error") -> None:
    """Run the FastAPI server in a new event loop.

    Args:
        app: The FastAPI application instance to run.
        host: The host address to bind the server to.
        port: The port number to bind the server to.
        log_level: The logging level for the server.
    """
    uvicorn.run(app, host=host, port=port, log_level=log_level)


class FastAPIServer:
    """A generic FastAPI server implementation."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the FastAPI generic server."""
        self.host: str = host
        self.port: int = port
        self.app: FastAPI = FastAPI()
        self._server_thread: threading.Thread | None = None
        self._running: bool = False

    async def start(self) -> None:
        """Start the server in a separate thread."""
        if self.running:
            return

        self.server_thread = threading.Thread(target=run_server, args=(self.app, self.host, self.port))
        self.server_thread.daemon = True
        self.server_thread.start()
        self.running = True

    async def stop(self, timeout: int = 1) -> None:
        """Stop the server."""
        if not self.running:
            return
        self.running = False
        if self.server_thread is not None:
            self.server_thread.join(timeout=timeout)
            self.server_thread = None

    @property
    def running(self) -> bool:
        """Check if the server is running."""
        return self._running and self._server_thread is not None and self._server_thread.is_alive()

    @running.setter
    def running(self, value: bool) -> None:
        """Set the running state of the server."""
        self._running = value

    @property
    def server_thread(self) -> threading.Thread | None:
        """Get the server thread."""
        return self._server_thread

    @server_thread.setter
    def server_thread(self, thread: threading.Thread | None) -> None:
        """Set the server thread."""
        self._server_thread = thread


__all__ = ["FastAPIServer"]
