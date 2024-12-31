import uasyncio as asyncio  # https://docs.micropython.org/en/latest/library/asyncio.html
from machine import Pin  # https://docs.micropython.org/en/latest/library/machine.html
from utils.log import log  # logging function
from src.config import config  # Config() instance
from src.rlock import Rlock  # re-entrant asyncio.Lock()


class Relay:
    """Manage a GPIO connected Relay. (Singleton per PIN)"""

    _instances = {}

    def __new__(cls, *args, **kwargs):
        instance = super(Relay, cls).__new__(cls)
        instance.pin_number = None
        instance.pin = None
        instance.lock = Rlock()
        instance.initialized = False
        return instance

    async def initialize(self, pin_number):
        """
        Initialize the Relay with a specific pin number.
        If a relay with the given pin already exists, return that instance.
        """

        if not pin_number or int(pin_number) == 0:
            log(
                "ERROR",
                f"Relay.initialize(pin={pin_number}): invalid pin_number = {pin_number}",
            )
            return None

        if pin_number in Relay._instances:
            existing_instance = Relay._instances[pin_number]
            log("WARN", f"Relay.initialize(pin={pin_number}): using existing instance")
            return existing_instance

        try:
            async with self.lock:
                if not self.initialized:
                    self.pin_number = pin_number
                    self.pin = Pin(self.pin_number, Pin.OUT)
                    self.pin.value(0)
                    self.initialized = True
                    Relay._instances[pin_number] = self
                    log("INFO", f"Relay.initialize(pin={pin_number}): successful")
                return self

        except (ValueError, TypeError) as e:
            log("ERROR", f"Relay.initialize(): failed: {e}")
            return None

        except Exception as e:
            log("ERROR", f"Relay.initialize(pin={pin_number}): failed: {e}")
            return None

    async def activate(self):
        """Activate the relay"""

        async with self.lock:
            try:
                self.pin.value(1)
                log("VERBOSE", f"Relay.activate(pin={self.pin_number})")
            except Exception as e:
                log("ERROR", f"Relay.activate(pin={self.pin_number}): failed: {e}")

    async def deactivate(self):
        """Deactivate the relay"""

        async with self.lock:
            try:
                self.pin.value(0)
                log("VERBOSE", f"Relay.deactivate(pin={self.pin_number})")
            except Exception as e:
                log("ERROR", f"Relay.deactivate(pin={self.pin_number}): failed: {e}")

    async def toggle(self, relay_time=None):
        """Toggle the relay state"""

        async with self.lock:
            try:
                if relay_time == None:
                    relay_time = await config.get_int("relay_time", 1200)

                log("INFO", f"Relay.toggle(pin={self.pin_number}, time={relay_time})")
                await self.activate()
                await asyncio.sleep_ms(relay_time)
                await self.deactivate()

            except (ValueError, TypeError) as e:
                log("ERROR", f"Relay.toggle(): failed: {e}")
            except Exception as e:
                log(
                    "ERROR",
                    f"Relay.toggle(pin={self.pin_number}, time={relay_time}): failed: {e}",
                )


relay_open = Relay()
relay_close = Relay()
