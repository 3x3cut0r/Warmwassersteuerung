from src.lcd_api import LcdApi
from time import sleep_ms

# The PCF8574 has a jumper selectable address: 0x20 - 0x27
DEFAULT_I2C_ADDR = 0x27

# Defines shifts or masks for the various LCD line attached to the PCF8574

MASK_RS = 0x01
MASK_RW = 0x02
MASK_E = 0x04
SHIFT_BACKLIGHT = 3
SHIFT_DATA = 4


class I2cLcd(LcdApi):
    """Driver for HD44780 character LCDs accessed through a PCF8574 I²C expander."""

    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.i2c.writeto(self.i2c_addr, bytearray([0]))
        sleep_ms(20)  # Allow LCD time to powerup
        # Send reset 3 times
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        sleep_ms(5)  # need to delay at least 4.1 msec
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        sleep_ms(1)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        sleep_ms(1)
        # Put LCD into 4 bit mode
        self.hal_write_init_nibble(self.LCD_FUNCTION)
        sleep_ms(1)
        LcdApi.__init__(self, num_lines, num_columns)
        cmd = self.LCD_FUNCTION
        if num_lines > 1:
            cmd |= self.LCD_FUNCTION_2LINES
        self.hal_write_command(cmd)

    def hal_write_init_nibble(self, nibble):
        """Send a high-order nibble during LCD initialization.

        This helper is used only while switching the display into 4‑bit mode.

        Args:
            nibble (int): Upper four bits to transmit to the LCD.
        """
        byte = ((nibble >> 4) & 0x0F) << SHIFT_DATA
        self.i2c.writeto(self.i2c_addr, bytearray([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))

    def hal_backlight_on(self):
        """Turn the LCD backlight on via the PCF8574 expander."""
        self.i2c.writeto(self.i2c_addr, bytearray([1 << SHIFT_BACKLIGHT]))

    def hal_backlight_off(self):
        """Turn the LCD backlight off via the PCF8574 expander."""
        self.i2c.writeto(self.i2c_addr, bytearray([0]))

    def hal_write_command(self, cmd):
        """Send a command byte to the LCD controller.

        The data is latched on the falling edge of the enable line. For
        ``cmd`` values ``<= 3`` an additional delay is inserted to satisfy the
        controller's timing requirements for *home* and *clear* commands.

        Args:
            cmd (int): Command byte to transmit.
        """
        byte = (self.backlight << SHIFT_BACKLIGHT) | (((cmd >> 4) & 0x0F) << SHIFT_DATA)
        self.i2c.writeto(self.i2c_addr, bytearray([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))
        byte = (self.backlight << SHIFT_BACKLIGHT) | ((cmd & 0x0F) << SHIFT_DATA)
        self.i2c.writeto(self.i2c_addr, bytearray([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))
        if cmd <= 3:
            # The home and clear commands require a worst case delay of 4.1 msec
            sleep_ms(5)

    def hal_write_data(self, data):
        """Transmit a data byte to be displayed by the LCD.

        Args:
            data (int): Character code to write to the display.
        """
        byte = (
            MASK_RS
            | (self.backlight << SHIFT_BACKLIGHT)
            | (((data >> 4) & 0x0F) << SHIFT_DATA)
        )
        self.i2c.writeto(self.i2c_addr, bytearray([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))
        byte = (
            MASK_RS
            | (self.backlight << SHIFT_BACKLIGHT)
            | ((data & 0x0F) << SHIFT_DATA)
        )
        self.i2c.writeto(self.i2c_addr, bytearray([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytearray([byte]))
