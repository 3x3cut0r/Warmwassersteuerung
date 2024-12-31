from machine import Pin  # https://docs.micropython.org/en/latest/library/machine.html
from utils.log import log  # logging function
from utils.get_bool import get_bool  # Convert value to bool
from src.config import config  # Config() instance
from src.rlock import Rlock  # re-entrant asyncio.Lock()


class LED:
    """Manage the LED light. (Singleton)"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LED, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.pin = None
            self.value = False
            self.lock = Rlock()
            self.initialized = False

    async def initialize(self):
        """Initialize the LED."""

        if self.initialized:
            return
        try:
            async with self.lock:
                self.value = await config.get_bool("LED", True)
                self.pin = Pin("LED", Pin.OUT)
                self.pin.value(self.value)
                log("INFO", f"LED.initialize({self.value}): successful")
                self.initialized = True

        except (ValueError, TypeError) as e:
            log("ERROR", f"LED.initialize(): failed: {e}")
            return None

        except Exception as e:
            log("ERROR", f"LED.initialize({self.value}): failed: {e}")

    async def set(self, value):
        """Set the LED state."""

        async with self.lock:
            try:
                value = get_bool(value)
                self.pin.value(value)
                self.value = value
                await config.set("LED", value)
                log("INFO", f"LED.set({value})")

            except Exception as e:
                log("ERROR", f"LED.set({value}): failed: {e}")

    async def activate(self):
        """Activates the LED."""

        await self.set(True)
        log("INFO", "LED.activate()")

    async def deactivate(self):
        """Deactivates the LED."""

        await self.set(False)
        log("INFO", "LED.deactivate()")

    async def toggle(self):
        """Toggles the LED state."""

        await self.set(not self.value)


led = LED()
