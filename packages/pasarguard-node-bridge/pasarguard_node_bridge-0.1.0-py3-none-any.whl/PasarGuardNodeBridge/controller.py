import ssl
import asyncio
import logging
from enum import IntEnum
from uuid import UUID
from typing import Optional

from PasarGuardNodeBridge.common.service_pb2 import User


class PriorityUserQueue(asyncio.PriorityQueue):
    """Priority queue that tracks pending user emails to avoid duplicate entries.
    Lower priority number = higher priority (0 is highest)
    """

    def __init__(self, maxsize=0):
        super().__init__(maxsize)
        self._email_count: dict[str, int] = {}  # Track count of each email in queue
        self._closed = False
        self._counter = 0  # Ensures FIFO for same priority

    async def close(self):
        """Close the queue and prevent further operations"""
        self._closed = True
        while not self.empty():
            try:
                self.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def put(self, item, priority: int = 5):
        """Add user to queue with priority and track their email.
        Priority: 0 (highest) to 10 (lowest), default is 5
        """
        if self._closed:
            return
        if item and hasattr(item, "email"):
            self._email_count[item.email] = self._email_count.get(item.email, 0) + 1
        # Use counter to ensure FIFO for same priority
        self._counter += 1
        await super().put((priority, self._counter, item))

    def put_nowait(self, item, priority: int = 5):
        """Add user to queue without waiting with priority and track their email"""
        if self._closed:
            return
        if item and hasattr(item, "email"):
            self._email_count[item.email] = self._email_count.get(item.email, 0) + 1
        self._counter += 1
        super().put_nowait((priority, self._counter, item))

    def _update_email_count(self, item):
        """Update email count when removing a user from queue"""
        if item and hasattr(item, "email"):
            if item.email in self._email_count:
                self._email_count[item.email] -= 1
                if self._email_count[item.email] <= 0:
                    del self._email_count[item.email]

    async def get(self):
        """Remove and return user from queue, updating email count.
        Returns the actual item, not the priority tuple.
        """
        if self._closed:
            return
        priority_tuple = await super().get()
        if priority_tuple is None:
            return None
        # Extract item from (priority, counter, item) tuple
        _, _, item = priority_tuple
        self._update_email_count(item)
        return item

    def get_nowait(self):
        """Remove and return user from queue without waiting, updating email count"""
        if self._closed:
            return
        priority_tuple = super().get_nowait()
        if priority_tuple is None:
            return None
        # Extract item from (priority, counter, item) tuple
        _, _, item = priority_tuple
        self._update_email_count(item)
        return item

    def has_email(self, email: str) -> bool:
        """Check if a user with this email is already queued"""
        return email in self._email_count and self._email_count[email] > 0


class NodeAPIError(Exception):
    def __init__(self, code, detail):
        self.code = code
        self.detail = detail

    def __str__(self):
        return f"NodeAPIError(code={self.code}, detail={self.detail})"


class Health(IntEnum):
    NOT_CONNECTED = 0
    BROKEN = 1
    HEALTHY = 2
    INVALID = 3


class Controller:
    def __init__(
        self,
        server_ca: str,
        api_key: str,
        name: str = "default",
        extra: dict | None = None,
        logger: logging.Logger | None = None,
    ):
        self.name = name
        if extra is None:
            extra = {}
        if logger is None:
            logger = logging.getLogger(self.name)
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            logger.addHandler(handler)
        self.logger = logger
        try:
            self.api_key = UUID(api_key)

            self.ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.ctx.set_alpn_protocols(["h2"])
            self.ctx.load_verify_locations(cadata=server_ca)
            self.ctx.check_hostname = True

        except ssl.SSLError as e:
            raise NodeAPIError(-1, f"SSL initialization failed: {str(e)}")

        except (ValueError, TypeError) as e:
            raise NodeAPIError(-2, f"Invalid API key format: {str(e)}")

        self._health = Health.NOT_CONNECTED
        self._user_queue: Optional[PriorityUserQueue] = PriorityUserQueue(maxsize=10000)
        self._notify_queue: Optional[asyncio.Queue] = asyncio.Queue(maxsize=10)
        self._tasks: list[asyncio.Task] = []
        self._node_version = ""
        self._core_version = ""
        self._extra = extra

        # Hard reset mechanism for critical failures
        self._hard_reset_event = asyncio.Event()
        self._user_sync_failure_count = 0
        self._hard_reset_threshold = 5
        self._failure_count_lock = asyncio.Lock()  # Only for incrementing counters

        # Separate locks for different resources to reduce contention
        self._health_lock = asyncio.Lock()
        self._queue_lock = asyncio.Lock()
        self._version_lock = asyncio.Lock()
        self._task_lock = asyncio.Lock()

        self._shutdown_event = asyncio.Event()

    async def set_health(self, health: Health):
        should_notify = False

        async with self._health_lock:
            if self._health is Health.INVALID:
                return
            if health == Health.BROKEN and self._health != Health.BROKEN:
                should_notify = self._notify_queue is not None
            self._health = health

        # Notify outside the lock to avoid blocking
        if should_notify:
            try:
                await asyncio.wait_for(self._notify_queue.put(None), timeout=0.5)
            except asyncio.TimeoutError:
                self.logger.warning(f"[{self.name}] Timeout notifying queue about health change to {health.name}")
            except asyncio.QueueFull:
                self.logger.warning(f"[{self.name}] Queue full, cannot notify about health change to {health.name}")
            except AttributeError as e:
                self.logger.error(f"[{self.name}] Notify queue unavailable | Error: AttributeError - {str(e)}")
            except Exception as e:
                error_type = type(e).__name__
                self.logger.error(
                    f"[{self.name}] Unexpected error notifying queue | Error: {error_type} - {str(e)}", exc_info=True
                )

    async def get_health(self) -> Health:
        async with self._health_lock:
            return self._health

    def requires_hard_reset(self) -> bool:
        """Check if hard reset is required due to critical failures.

        This is a synchronous, non-blocking check using Event.is_set().
        """
        return self._hard_reset_event.is_set()

    async def _increment_user_sync_failure(self):
        """Increment user sync failure counter and check if hard reset is needed."""
        async with self._failure_count_lock:
            self._user_sync_failure_count += 1
            if self._user_sync_failure_count >= self._hard_reset_threshold:
                if not self._hard_reset_event.is_set():
                    self._hard_reset_event.set()
                    self.logger.critical(
                        f"[{self.name}] HARD RESET REQUIRED: User sync failed {self._user_sync_failure_count} times in a row"
                    )

    async def _reset_user_sync_failure_count(self):
        """Reset user sync failure counter on successful sync."""
        async with self._failure_count_lock:
            self._user_sync_failure_count = 0

    async def update_user(self, user: User):
        async with self._queue_lock:
            if self._user_queue:
                await self._user_queue.put(user)

    async def update_users(self, users: list[User]):
        async with self._queue_lock:
            if not self._user_queue or not users:
                return
            for user in users:
                await self._user_queue.put(user)

    async def requeue_user_with_deduplication(self, user: User):
        """
        Requeue a user only if there's no existing version in the queue.
        Uses the UserQueue's email tracking to prevent duplicate entries.
        """
        async with self._queue_lock:
            if not self._user_queue:
                return

            # Only requeue if user is not already in queue
            if not self._user_queue.has_email(user.email):
                try:
                    await self._user_queue.put(user)
                except asyncio.QueueFull:
                    pass

    async def flush_user_queue(self):
        async with self._queue_lock:
            if self._user_queue:
                await self._user_queue.close()
                self._user_queue = PriorityUserQueue(10000)

    async def node_version(self) -> str:
        async with self._version_lock:
            return self._node_version

    async def core_version(self) -> str:
        async with self._version_lock:
            return self._core_version

    async def get_extra(self) -> dict:
        async with self._version_lock:
            return self._extra

    async def connect(self, node_version: str, core_version: str, tasks: list | None = None):
        if tasks is None:
            tasks = []

        # Clear shutdown event first (no lock needed)
        self._shutdown_event.clear()

        # Reset hard reset event and failure counters
        self._hard_reset_event.clear()
        async with self._failure_count_lock:
            self._user_sync_failure_count = 0

        # Cleanup tasks with task lock
        async with self._task_lock:
            await self._cleanup_tasks()

        # Set health
        async with self._health_lock:
            self._health = Health.HEALTHY

        # Set versions
        async with self._version_lock:
            self._node_version = node_version
            self._core_version = core_version

        # Create new tasks
        async with self._task_lock:
            for t in tasks:
                task = asyncio.create_task(t())
                self._tasks.append(task)

    async def disconnect(self):
        await self.set_health(Health.NOT_CONNECTED)

        # Set shutdown event (no lock needed)
        self._shutdown_event.set()

        # Cleanup tasks
        async with self._task_lock:
            await self._cleanup_tasks()

        # Cleanup queues
        async with self._queue_lock:
            await self._cleanup_queues()

        # Clear versions
        async with self._version_lock:
            self._node_version = ""
            self._core_version = ""

    async def _cleanup_tasks(self):
        """Clean up all background tasks properly - must be called with task_lock held"""
        if self._tasks:
            for task in self._tasks:
                if not task.done():
                    task.cancel()

            try:
                results = await asyncio.wait_for(asyncio.gather(*self._tasks, return_exceptions=True), timeout=5.0)
                # Log any exceptions from tasks
                for i, result in enumerate(results):
                    if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                        error_type = type(result).__name__
                        self.logger.error(
                            f"[{self.name}] Task {i} raised exception during cleanup | "
                            f"Error: {error_type} - {str(result)}"
                        )
            except asyncio.TimeoutError:
                self.logger.warning(f"[{self.name}] Timeout waiting for {len(self._tasks)} tasks to cleanup")

            self._tasks.clear()

    async def _cleanup_queues(self):
        """Properly clean up all queues - must be called with queue_lock held"""
        if self._user_queue:
            try:
                await asyncio.wait_for(self._user_queue.put(None), timeout=0.1)
            except (asyncio.TimeoutError, asyncio.QueueFull):
                pass

            while not self._user_queue.empty():
                try:
                    self._user_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

            self._user_queue = PriorityUserQueue(maxsize=10000)

        if self._notify_queue:
            try:
                await asyncio.wait_for(self._notify_queue.put(None), timeout=0.1)
            except (asyncio.TimeoutError, asyncio.QueueFull):
                pass

            while not self._notify_queue.empty():
                try:
                    self._notify_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

            self._notify_queue = asyncio.Queue(maxsize=10)

    def is_shutting_down(self) -> bool:
        """Check if the node is shutting down"""
        return self._shutdown_event.is_set()
