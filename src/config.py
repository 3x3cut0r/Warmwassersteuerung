import ujson  # https://docs.micropython.org/en/latest/library/json.html
from utils.log import log  # logging function
from utils.get_bool import get_bool
from utils.get_float import get_float
from utils.get_int import get_int
from src.rlock import Rlock  # re-entrant asyncio.Lock()


class Config:
    """Manage the project configuration. (Singleton)"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls)

        return cls._instance

    def __init__(self, file_name="config.json"):
        if not hasattr(self, "initialized"):
            self.root_path = "/"
            self.file_name = file_name
            self.file_path = self.root_path + self.file_name
            self.config = {}
            self.lock = Rlock()
            self.load()
            self.reset()
            log("INFO", f"Config({self.file_path}): initialized")
            self.initialized = True

    def load(self):
        """Load the configuration from file"""
        try:
            log("INFO", f"Config.load({self.file_path})")
            with open(self.file_path, "r", encoding="utf-8") as file:
                self.config = ujson.load(file)
                return self.config
        except OSError:
            log("ERROR", f"Config.load({self.file_path}): not found: return " + "\{\}")
            self.config = {}  # Set empty object
            return self.config

    def reset(self):
        """Reset some configuration settings"""

        log("INFO", f"Config.reset()")
        self.config["temp_last_measurement"] = 0
        self.config["temp_last_measurement_time"] = 0
        self.config["temp_change_category"] = "LOW"

    async def save(self):
        """Save the configuration to file"""
        async with self.lock:
            try:
                log("INFO", f"Config.save(): {self.file_path}")
                with open(self.file_path, "w", encoding="utf-8") as file:
                    ujson.dump(self.config, file)
            except Exception as e:
                log(
                    "ERROR",
                    f"Config.save({self.file_path}): {e}",
                )

    async def get_config(self):
        """Return the complete configuration as dictionary"""
        async with self.lock:
            try:
                log("INFO", f"Config.get_config()")
                return self.config
            except Exception as e:
                log("ERROR", f"Config.get_config(): {e}")

    async def get(self, key, default=None):
        """Return the value for a given key"""
        async with self.lock:
            return self.config.get(key, default)

    async def get_bool(self, key, default=False):
        """Return the bool value for a given key"""
        async with self.lock:
            return get_bool(self.config.get(key), "Config", "get_bool")

    async def get_int(self, key, default=0):
        """Return the int value for a given key"""
        async with self.lock:
            return get_int(self.config.get(key), default, "Config", "get_int")

    async def get_float(self, key, default=0.0, decimal=None):
        """Return the float value for a given key"""
        async with self.lock:
            return get_float(
                self.config.get(key), default, decimal, "Config", "get_float"
            )

    async def set(self, key, value):
        """Save the value for a given key"""
        async with self.lock:
            try:
                self.config[str(key)] = value
            except Exception as e:
                log("ERROR", f"Config.set(): failed: {e}")


config = Config()
