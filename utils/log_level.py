LOG_LEVELS = {"OFF": 0, "ERROR": 1, "WARN": 2, "INFO": 3, "VERBOSE": 4}


class LogLevel:
    """LogLevel from config. (Singleton)"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LogLevel, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.level = "OFF"
            self.initialized = False

    def initialize(self, level):
        """Initialize the LogLevel"""

        if self.initialized:
            print(f"WARN: LogLevel.initialize(): already initialized")
            return
        try:
            if str(level).upper() in LOG_LEVELS:
                self.level = str(level).upper()
                print(f"INFO: LogLevel.initialize({level}): successful")
                self.initialized = True

        except (ValueError, TypeError) as e:
            self.level = "OFF"
            print(f"ERROR: LogLevel.initialize(): failed: {e}")
        except Exception as e:
            self.level = "OFF"
            print(f"ERROR: LogLevel.initialize({level}): failed: {e}")

    def get(self):
        return self.level

    def set(self, level):
        try:
            if str(level).upper() in LOG_LEVELS:
                self.level = str(level).upper()

        except Exception as e:
            print(f"ERROR: LogLevel.set(): failed: {e}")


log_level = LogLevel()
