from utils.log import log  # logging function


def get_int(value, default=0, log_class="Utils", log_function="get_int"):
    """Convert a value to ``int`` with error handling and logging.

    Args:
        value: Object that should represent an integer.
        default (int): Fallback when conversion fails.
        log_class (str): Name of the calling class/module for log messages.
        log_function (str): Name of the calling function for log messages.

    Returns:
        int: Converted integer or ``default`` if conversion fails.
    """

    # Check if default is a valid float
    if not isinstance(default, int):
        log(
            "VERBOSE",
            f"{log_class}.{log_function}({value}): default({default}) not int: set to 0",
        )
        default = int(0)

    try:
        if value is None:
            log(
                "VERBOSE",
                f"{log_class}.{log_function}({value}): value is None: set to {default}",
            )
            return default
        else:
            # Convert to int
            return int(value)

    except (ValueError, TypeError) as e:
        log("ERROR", f"{log_class}.{log_function}(): failed: {e}: set {default}")
        return default
    except Exception as e:
        log("ERROR", f"{log_class}.{log_function}({value}): failed: {e}: set {default}")
        return default
