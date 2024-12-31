from utils.log_level import LOG_LEVELS, log_level


def log(level="INFO", message=""):
    """
    Output a message on console if the log_level set is equal or higher than the level given.

    Args:
        level (str): The log level of the message, e.g. "OFF", "INFO", "VERBOSE", "WARN" or "ERROR".
        message (str): The message text to be logged.

    Returns:
        None: This function does not return a value.
    """

    # Make level uppercase
    level = str(level).upper()

    # Exit early if logging is disabled or  log_level is invalid
    if log_level.get() == "OFF" or level not in LOG_LEVELS:
        return

    # Exit early if the message's log level is lower than the current log level
    if LOG_LEVELS.get(level, -1) > LOG_LEVELS[log_level.get()]:
        return

    # Convert VERBOSE to INFO
    if level == "VERBOSE":
        level = "INFO"

    # Print the log message
    print(f"{level}: {message}")
