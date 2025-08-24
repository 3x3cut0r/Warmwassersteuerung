import uasyncio as asyncio  # https://docs.micropython.org/en/latest/library/asyncio.html


class Rlock:
    """A re-entrant lock compatible with ``uasyncio``.

    The lock keeps track of the task currently holding it and allows the same
    task to acquire it multiple times without deadlocking. Other tasks are
    suspended until the owning task releases the lock the same number of times
    it was acquired.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._owner = None
        self._count = 0

    async def acquire(self):
        """Acquire the lock, waiting if necessary."""
        current_task = asyncio.current_task()
        if self._owner == current_task:
            # Already owned by current task, just increment count
            self._count += 1
        else:
            # Need to acquire the underlying lock
            await self._lock.acquire()
            self._owner = current_task
            self._count = 1

    def release(self):
        """Release the lock and wake a waiting task if appropriate."""

        if self._owner != asyncio.current_task():
            raise RuntimeError("INFO: RLock(): released by self")
        self._count -= 1
        if self._count == 0:
            self._owner = None
            self._lock.release()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.release()
