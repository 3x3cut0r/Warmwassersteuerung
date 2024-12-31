from utils.log import log  # logging function


def get_int(value, default=0, log_class="Utils", log_function="get_int"):
    """Return the int value of a given value"""

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
