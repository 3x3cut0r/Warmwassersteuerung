import network
import uasyncio as asyncio  # https://docs.micropython.org/en/latest/library/asyncio.html
from utils.log import log  # logging function
from src.config import config  # Config() instance
from src.lcd import lcd  # LCD() instance


class WiFi:
    """Manage the WiFi connection. (Singleton)"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(WiFi, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            self.wifi = None
            self.wifi_is_activated = False
            self.ssid = None
            self.password = None
            self.max_attempts = 10
            self.show_message = 1
            self.initialized = False

    async def initialize(self):
        """Initialize the Wifi module"""

        if self.initialized:
            return
        try:
            self.wifi = network.WLAN(network.STA_IF)
            self.wifi_is_activated = True
            network.country(await config.get("wifi_country", "DE"))
            self.ssid = await config.get("wifi_ssid", "ssid")
            self.password = await config.get("wifi_password", "password")
            self.max_attempts = await config.get_int("wifi_max_attempts", 10)
            log("INFO", "WiFi.initialize(): successful")
            self.initialized = True

        except Exception as e:
            log("ERROR", f"WiFi.initialize(): failed: {e}")

    async def connect(self):
        """Connect to the WiFi"""

        if self.wifi_is_activated:
            log("INFO", f"WiFi.connect(ssid={self.ssid})")

            if self.ssid is not None:

                # Activate and Connect WiFi
                try:
                    self.wifi.active(True)
                    self.wifi.connect(self.ssid, self.password)
                except OSError as e:
                    log("ERROR", f"WiFi.connect(): failed: {e}")
                    log("INFO", "WiFi.wifi_is_activated(False)")
                    self.wifi_is_activated = False

                # Wait until connection is established
                attempts = 0
                while (
                    self.wifi_is_activated
                    and not self.wifi.isconnected()
                    and attempts < self.max_attempts
                ):
                    await asyncio.sleep(1)
                    attempts += 1
                    await lcd.print(2, 0, "verbinde WLAN ... {:02d}".format(attempts))

                if self.wifi.isconnected():
                    if self.show_message >= 1:
                        log("INFO", f"WiFi.wifi.ifconfig(): {self.wifi.ifconfig()}")
                        await lcd.print(2, 0, "WLAN wurde verbunden")
                        await asyncio.sleep(3)
                    self.show_message = 0
                else:
                    log("WARN", "WiFi.connect(): failed")
                    await lcd.print(2, 0, "WLAN nicht verbunden")
            else:
                log("ERROR", f"WiFi.connect(): no SSID found")
                await lcd.print(2, 0, "keine SSID gefunden!")
                self.wifi_is_activated = False

            await asyncio.sleep(5)
            await lcd.print(2, 0, " ")

    def is_activated(self):
        log("INFO", f"WiFi.is_activated()")
        return self.wifi_is_activated

    def is_connected(self):
        try:
            log("INFO", f"WiFi.is_connected(): {self.wifi.isconnected()}")
            return self.wifi.isconnected()
        except Exception as error:
            log("ERROR", f"WiFi.is_connected(): failed: {error}")
            return False


wifi = WiFi()
