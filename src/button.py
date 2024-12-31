from machine import Pin  # https://docs.micropython.org/en/latest/library/machine.html
from utils.log import log  # logging function
from src.config import config  # Config() instance
from src.rlock import Rlock  # re-entrant asyncio.Lock()


class Button:
    """Manage a GPIO connected Button. (Singleton per PIN)"""

    _instances = {}
    count = 0

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.count = None
        instance.postfix = ""
        instance.pin_number = None
        instance.pin = None
        instance.is_activated = False
        instance.lock = Rlock()
        instance.initialized = False
        return instance

    async def initialize(self, pin_number):
        """
        Initialize the Button with a specific pin number.
        If a button with the given pin already exists, return that instance.

        Args:
            pin_number (int): The buttons GPIO pin number.

        Returns:
            self: A Button() object.
        """

        if not pin_number or int(pin_number) == 0:
            log(
                "ERROR",
                f"Button.initialize(pin={pin_number}): invalid pin_number = {pin_number}",
            )
            return None

        if pin_number in Button._instances:
            existing_instance = Button._instances[pin_number]
            log("WARN", f"Button.initialize(pin={pin_number}): using existing instance")
            return existing_instance

        try:
            async with self.lock:
                if not self.initialized:
                    self.pin_number = pin_number
                    self.pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
                    Button._instances[pin_number] = self
                    Button.count += 1
                    self.count = Button.count
                    self.postfix = f"_{self.count}" if self.count > 1 else ""
                    self.is_activated = await config.get_bool(
                        "buttons_activated", False
                    )
                    log("INFO", f"Relay.initialize(pin={pin_number}): successful")
                    self.initialized = True
                return self

        except (ValueError, TypeError) as e:
            log("ERROR", f"Button.initialize(): failed: {e}")
            return None

        except Exception as e:
            log("ERROR", f"Button.initialize(pin={pin_number}): failed: {e}")
            return None

    def is_pressed(self):
        """Return True if the button is pressed"""

        if self.is_activated:
            log("VERBOSE", f"Button.is_pressed()")
            return not self.pin.value()


button = Button()
button_2 = Button()
