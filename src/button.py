from machine import Pin  # https://docs.micropython.org/en/latest/library/machine.html
from utils.log import log  # logging function
from src.config import config  # Config() instance
from src.rlock import Rlock  # re-entrant asyncio.Lock()


class Button:
    """Represent a physical push button attached to a GPIO pin.

    Each button instance corresponds to a single pin and is stored in a
    registry so multiple parts of the program referencing the same pin share the
    same object.  The class tracks how many buttons have been created to derive a
    postfix used by the configuration system.
    """

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
        """Set up the button on the given GPIO pin.

        If an instance for ``pin_number`` already exists it is reused.  The pin
        is configured as input with a pull-up resistor and the activation state
        is read from the configuration.

        Args:
            pin_number (int): GPIO pin number to which the button is connected.

        Returns:
            Button | None: The initialized instance or ``None`` on failure.
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
        """Check whether the button is currently pressed.

        Returns:
            bool: ``True`` when the button is active and the pin reads low.
        """

        if self.is_activated:
            log("VERBOSE", f"Button.is_pressed()")
            return not self.pin.value()


button = Button()
button_2 = Button()
