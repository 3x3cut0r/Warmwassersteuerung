from utils.log import log  # logging function


def get_bool(value, log_class="Utils", log_function="get_bool"):
    """Return the bool value of a given value"""

    try:
        if isinstance(value, bool):
            return value

        if isinstance(value, int):
            if value >= 1:
                return True
            else:
                return False

        if isinstance(value, str):
            if value.lower() in ["true", "1", "yes", "on"]:
                return True
            elif value.lower() in ["false", "0", "no", "off", None]:
                return False

        log("VERBOSE", f"{log_class}.{log_function}(): value not supported: set False")
        return False

    except (ValueError, TypeError) as e:
        log("ERROR", f"{log_class}.{log_function}(): failed: {e}: set False")
        return False
    except Exception as e:
        log("ERROR", f"{log_class}.{log_function}({value}): failed: {e}: set False")
        return False
