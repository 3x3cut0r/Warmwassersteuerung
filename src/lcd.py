from machine import (
    I2C,
    Pin,
)  # https://docs.micropython.org/en/latest/library/machine.html
from utils.log import log  # logging function
from utils.get_bool import get_bool  # Convert value to bool
from src.config import config  # Config() instance
from src.machine_i2c_lcd import I2cLcd  # I2C LCD
from src.rlock import Rlock  # re-entrant asyncio.Lock()


class LCD:
    """Manage the LCD. (Singleton)"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LCD, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.i2c = None
            self.lcd = None
            self.lines = []
            self.cols = 20
            self.rows = 4
            self.freq = 100000
            self.addr = int("0x27", 16)
            self.sda_pin = 20
            self.scl_pin = 21
            self.lock = Rlock()
            self.initialized = False

    async def initialize(self):
        """Initialize the LCD

        Args:
            None: This function does not support arguments.

        Returns:
            self: A LCD() object.
        """

        if self.initialized:
            return
        try:
            async with self.lock:

                # Setup LCD
                self.sda_pin = await config.get_int("LCD_PIN_SDA", 20)
                self.scl_pin = await config.get_int("LCD_PIN_SCL", 21)
                self.freq = await config.get_int("LCD_FREQ", 100000)
                addr = await config.get("LCD_ADDR", "0x27")
                self.addr = int(str(addr), 16)
                self.cols = await config.get_int("LCD_COLS", 20)
                if self.cols > 20:
                    self.cols = 20
                self.rows = await config.get_int("LCD_ROWS", 4)
                if self.rows > 4:
                    self.rows = 4

                # Empty lines list
                self.lines = [" " * self.cols for _ in range(self.rows)]

                # Setup I2C
                sda_pin = Pin(self.sda_pin)
                scl_pin = Pin(self.scl_pin)
                self.i2c = I2C(0, sda=sda_pin, scl=scl_pin, freq=self.freq)

                # Initialize LCD
                self.lcd = I2cLcd(self.i2c, self.addr, self.rows, self.cols)

                # Add custom characters
                arrow_up = [
                    0b00100,
                    0b01110,
                    0b11111,
                    0b00100,
                    0b00100,
                    0b00100,
                    0b00100,
                    0b00100,
                ]
                arrow_down = [
                    0b00100,
                    0b00100,
                    0b00100,
                    0b00100,
                    0b00100,
                    0b11111,
                    0b01110,
                    0b00100,
                ]
                self.lcd.custom_char(0, bytearray(arrow_up))
                self.lcd.custom_char(1, bytearray(arrow_down))

                # Configure LCD backlight
                lcd_i2c_backlight = await config.get_bool("lcd_i2c_backlight", True)
                await self.set_backlight(lcd_i2c_backlight)

                # Hide LCD cursor
                await self.set_cursor(False)

                # Disable LCD blink cursor
                await self.blink_cursor(False)

                # Clear LCD
                await self.clear()

                log("INFO", "LCD.initialize(): successful")
                self.initialized = True

                return self

        except (ValueError, TypeError) as e:
            log("ERROR", f"LCD.initialize(): failed: {e}")
            return None

        except Exception as e:
            log(
                "ERROR",
                f"LCD.initialize(sda={self.sda_pin}, scl={self.scl_pin}, addr={self.addr}, rows={self.rows}, cols={self.cols}): failed: {e}",
            )
            return None

    async def set_backlight(self, value=True):
        """
        Manage the LCD backlight

        Args:
            value (bool): The value to set the backlight.

        Returns:
            None: This function does not return a value.
        """

        async with self.lock:
            try:
                if get_bool(value, "set_backlight"):
                    self.lcd.backlight_on()
                else:
                    self.lcd.backlight_off()
                log("INFO", f"LCD.set_backlight({value})")

            except Exception as e:
                log("ERROR", f"LCD.set_backlight({value}): failed: {e}")

    async def set_cursor(self, value=True):
        """set the LCD cursor"""

        async with self.lock:
            try:
                if get_bool(value):
                    self.lcd.show_cursor()
                else:
                    self.lcd.hide_cursor()
                log("INFO", f"LCD.set_cursor({value})")

            except Exception as e:
                log("ERROR", f"LCD.set_cursor({value}): failed: {e}")

    async def blink_cursor(self, value=True):
        """Turn on/off the LCD blink cursor"""

        async with self.lock:
            try:
                if get_bool(value):
                    self.lcd.blink_cursor_on()
                else:
                    self.lcd.blink_cursor_off()
                log("INFO", f"LCD.blink_cursor({value})")

            except Exception as e:
                log("ERROR", f"LCD.blink_cursor({value}): failed: {e}")

    async def clear(self):
        """Clear the LCD screen"""

        async with self.lock:
            try:
                if self.initialized:
                    self.lcd.clear()
                    log("INFO", f"LCD.clear()")

            except Exception as e:
                log("ERROR", f"LCD.clear(): failed: {e}")

    # Check if line is out of range
    def check_line(self, line, function="set_line"):
        if line > self.rows - 1:
            log(
                "WARN",
                f"LCD.{function}(line={line}): out of range. set {self.rows - 1}",
            )
            line = self.rows - 1
        return line

    # Check if column is out of range
    def check_cols(self, column, function="set_line"):
        if column > self.cols - 1:
            log(
                "WARN",
                f"LCD.{function}(column={column}): out of range. set {self.cols - 1}",
            )
            column = self.cols - 1
        return column

    # Convert utf-8 characters to HD44780A00 characters
    # Get dual number from the HD44780A00 table: https://de.wikipedia.org/wiki/HD44780#Schrift_und_Zeichensatz
    # Convert dual number to octal number: https://www.arndt-bruenner.de/mathe/scripts/Zahlensysteme.htm
    def convert_HD44780A00(self, string=""):
        """Convert utf-8 characters to HD44780A00 characters"""

        replacements = {
            "ß": "\342",  # HD44780A00 for ß
            "°": "\337",  # HD44780A00 for °
            "ä": "\341",  # HD44780A00 for ä
            "ö": "\357",  # HD44780A00 for ö
            "ü": "\365",  # HD44780A00 for ü
        }
        for original, replacement in replacements.items():
            string = string.replace(original, replacement)
        return string

    def ljust(self, string="", width=0, fillchar=" "):
        """Fill string with fillchar until width is reached. Place string on the left side."""

        if len(str(string)) >= int(width):
            return str(string)
        return str(string + str(fillchar) * (int(width) - len(str(string))))

    def rjust(self, string="", width=0, fillchar=" "):
        """Fill string with fillchar until width is reached. Place string on the right side."""

        if len(str(string)) >= int(width):
            return str(string)
        return str(str(fillchar) * (int(width) - len(str(string))) + string)

    def fill(self, string="", cursor=0, padding=" "):
        """Fill string with spaces up to 20 chars"""

        return self.ljust(str(string), (self.cols - int(cursor)), str(padding))

    async def get_line(self, line=0):
        """Return LCD line"""

        async with self.lock:
            try:
                return self.lines[self.check_line(line, "get_line")]

            except (ValueError, TypeError) as e:
                log("ERROR", f"LCD.get_line(): {e}")
                return ""
            except Exception as e:
                log("ERROR", f"LCD.get_line({line}): {e}")
                return ""

    async def get_lines(self):
        """Return LCD lines"""

        async with self.lock:
            try:
                return self.lines

            except Exception as e:
                log("ERROR", f"LCD.get_lines(): {e}")
                return []

    async def set_lines(self, line=0, message=""):
        """Set LCD lines"""

        async with self.lock:
            try:
                self.lines[self.check_line(line, "set_lines")] = str(message)

            except Exception as e:
                log("ERROR", f"LCD.set_lines(): {e}")

    async def set_line(self, line=0, cursor=0, message=""):
        """Set LCD line"""

        async with self.lock:
            try:
                line = self.check_line(line, "set_line")
                cursor = self.check_cols(cursor, "set_line")
                message = str(message)
                current_line = self.lines[line]

                # Set parts
                part1 = current_line[:cursor]
                part2 = message
                part3 = current_line[(cursor + len(message)) :]

                self.lines[line] = str(part1 + part2 + part3)[: self.cols]

            except Exception as e:
                log("ERROR", f"LCD.set_line(): {e}")

    async def print(self, line=0, cursor=0, message="", fill=True):
        """Print a message on a given LCD line and cursor position"""

        line = self.check_line(line, "set_line")
        cursor = self.check_cols(cursor, "set_line")
        message = str(message)

        # Fill message
        if fill:
            message = self.fill(message, cursor)

        # Set LCD line
        await self.set_line(line, cursor, message)

        # Convert utf-8 characters to HD44780A00 characters
        message = self.convert_HD44780A00(message)

        # Print LCD
        async with self.lock:
            try:
                if self.initialized:
                    self.lcd.move_to(cursor, line)  # self.lcd.move_to(col, row)
                    self.lcd.putstr(message)
                    self.lcd.hide_cursor()

            except Exception as e:
                log("ERROR", f"LCD.print(): {e}")

    async def print_char(self, line=0, cursor=0, char=0):
        """Print a character on a given LCD line and cursor position"""

        try:
            line = self.check_line(line, "set_line")
            cursor = self.check_cols(cursor, "set_line")
            char = int(char)

            # Get char for lines
            char_string = ""
            if char == 0:
                char_string = "↑"
            elif char == 1:
                char_string = "↓"
            else:
                char_string = "-"

            current_line = await self.get_line(line)
            await self.set_lines(
                line,
                current_line[:cursor] + char_string + current_line[cursor + 1 :],
            )

            async with self.lock:
                if self.initialized:
                    self.lcd.move_to(cursor, line)  # self.lcd.move_to(col, row)
                    self.lcd.putchar(chr(char))

        except Exception as e:
            log("ERROR", f"LCD.print_char(): {e}")


lcd = LCD()
