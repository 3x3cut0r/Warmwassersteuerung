import uasyncio as asyncio  # https://docs.micropython.org/en/latest/library/asyncio.html
from machine import Pin  # https://docs.micropython.org/en/latest/library/machine.html
from onewire import OneWire  # OneWire
from ds18x20 import DS18X20  # DS180B20
from dht import DHT11  # DHT11
from utils.log import log  # logging function
from src.config import config  # Config() instance
from src.rlock import Rlock  # re-entrant asyncio.Lock()


class TempSensor:
    """Abstraction for temperature sensors with per-pin singleton behavior."""

    _instances = {}
    count = 0

    def __new__(cls, *args, **kwargs):
        instance = super(TempSensor, cls).__new__(cls)
        instance.count = None
        instance.postfix = ""
        instance.pin_number = None
        instance.pin = None
        instance.sensor = None
        instance.type = None
        instance.resolution = 11
        # Set temp sensor resolution
        # bits   resolution        time
        #    9       0,5 °C    93,75 ms
        #   10      0,25 °C   187,50 ms
        #   11     0,125 °C   375,00 ms
        #   12   0,00626 °C   750,00 ms
        instance.resolution_time = 375
        instance.lock = Rlock()
        instance.initialized = False
        return instance

    async def initialize(self, pin_number, resolution=11, type="ds18x20"):
        """Initialize the sensor on ``pin_number`` with a given resolution.

        If a sensor for the pin already exists the existing instance is
        returned. Supported ``type`` values are ``"ds18x20"`` and ``"dht11"``.

        Args:
            pin_number (int): GPIO pin the sensor is connected to.
            resolution (int): Desired resolution for DS18X20 sensors.
            type (str): Sensor type identifier.

        Returns:
            TempSensor | None: Initialized instance or ``None`` on error.
        """

        if not pin_number or int(pin_number) == 0:
            log(
                "ERROR",
                f"TempSensor.initialize(pin={pin_number}, type={type}): invalid pin_number = {pin_number}",
            )
            return None

        if pin_number in TempSensor._instances:
            existing_instance = TempSensor._instances[pin_number]
            log(
                "WARN",
                f"TempSensor.initialize(pin={pin_number}): using existing instance",
            )
            return existing_instance

        try:
            async with self.lock:
                if not self.initialized:
                    self.pin_number = pin_number
                    self.pin = Pin(self.pin_number)
                    self.type = str(type).lower()

                    # Limits the resolution to valid values
                    self.resolution = max(9, min(resolution, 12))

                    # Initialize sensor with from type
                    if self.type == "ds18x20":
                        self.sensor = DS18X20(OneWire(self.pin))
                    elif self.type == "dht11":
                        self.sensor = DHT11(self.pin)
                    else:
                        log(
                            "ERROR",
                            f"TempSensor.initialize(pin={self.pin_number}, type={self.type}): failed: type is not supported",
                        )
                        return self

                    self.resolution_time = int(750 / (2 ** (12 - self.resolution)))
                    self.set_resolution()
                    TempSensor._instances[pin_number] = self
                    TempSensor.count += 1
                    self.count = TempSensor.count
                    self.postfix = f"_{self.count}" if self.count > 1 else ""
                    self.initialized = True
                    log(
                        "INFO",
                        f"TempSensor.initialize(pin={self.pin_number}, type={self.type}): successful",
                    )
                return self

        except (ValueError, TypeError) as e:
            log("ERROR", f"TempSensor.initialize(): failed: {e}")
            return None

        except Exception as e:
            log(
                "ERROR",
                f"TempSensor.initialize(pin={self.pin_number}, type={self.type}): failed: {e}",
            )
            return None

    def set_resolution(self, resolution=11):
        """Set the measurement resolution for DS18X20 sensors."""

        try:
            # Limits the resolution to valid values
            self.resolution = max(9, min(resolution, 12))

            # Resolution only supported on ds18x20
            if self.type == "ds18x20":

                # Scan for available temp sensors
                roms = self.sensor.scan()

                # Set resolution
                byte_string_map = {
                    9: b"\x00\x00\x1f",
                    10: b"\x00\x00\x3f",
                    11: b"\x00\x00\x5f",
                    12: b"\x00\x00\x7f",
                }
                byte_string = byte_string_map[self.resolution]
                for rom in roms:
                    self.sensor.write_scratch(rom, byte_string)
                log(
                    "INFO",
                    f"TempSensor.set_resolution(pin={self.pin_number}, resolution={resolution}): successful",
                )

        except (ValueError, TypeError) as e:
            log(
                "ERROR",
                f"TempSensor.set_resolution(): failed: {e}",
            )
        except Exception as e:
            log(
                "ERROR",
                f"TempSensor.set_resolution(pin={self.pin_number}, resolution={resolution}): failed: {e}",
            )

    async def get_temp(self):
        """Read the temperature value from the sensor.

        Returns:
            float: Temperature in degrees Celsius or ``-127.0`` on failure.
        """

        async with self.lock:
            try:
                if self.initialized:
                    if self.type == "ds18x20":
                        roms = self.sensor.scan()
                        if not roms:
                            raise OSError("No sensors found")
                        self.sensor.convert_temp()
                        await asyncio.sleep_ms(self.resolution_time)
                        temp = self.sensor.read_temp(roms[0])

                    elif self.type == "dht11":
                        self.sensor.measure()
                        temp = self.sensor.temperature()

                    else:
                        raise ValueError("sensor type not supported")

                    temp = round(float(temp), 1)
                    await config.set(f"current_temp{self.postfix}", temp)
                    log(
                        "VERBOSE",
                        f"TempSensor.get_temp(pin={self.pin_number}): temp = {temp}°C",
                    )
                    return temp

            except Exception as e:
                await config.set(f"current_temp{self.postfix}", -127.0)
                log(
                    "ERROR",
                    f"TempSensor.get_temp(pin={self.pin_number}): failed: {e}",
                )
                return -127.0

    async def get_humidity(self):
        """Read the humidity value from the sensor if supported.

        Returns:
            float: Relative humidity or ``-1`` when unavailable or on error.
        """

        async with self.lock:
            try:
                if self.initialized:
                    if self.type == "dht11":
                        humidity = self.sensor.humidity()

                    else:
                        raise ValueError("sensor does not support humidity")

                    humidity = round(humidity, 0)
                    await config.set(f"current_humidity{self.postfix}", humidity)
                    log(
                        "VERBOSE",
                        f"TempSensor.get_humidity(pin={self.pin_number}): humidity = {humidity}g/m",
                    )
                    return humidity

            except Exception as e:
                await config.set(f"current_humidity{self.postfix}", -1)
                log(
                    "ERROR",
                    f"TempSensor.get_humidity(pin={self.pin_number}): failed: {e}",
                )
                return -1


temp_sensor = TempSensor()
temp_sensor_2 = TempSensor()
