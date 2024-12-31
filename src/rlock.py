import uasyncio as asyncio  # https://docs.micropython.org/en/latest/library/asyncio.html


class Rlock:
    """Manage re-entrant asyncio.Lock()"""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._owner = None
        self._count = 0

    async def acquire(self):
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
