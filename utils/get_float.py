from utils.log import log  # logging function


def get_float(
    value, default=0.0, decimal=None, log_class="Utils", log_function="get_float"
):
    """Convert arbitrary input to a ``float`` with optional rounding.

    The function tries to interpret ``value`` as a floating point number. If the
    conversion fails, ``default`` is returned and a log message is emitted. When
    ``decimal`` is provided, the converted value is rounded to the specified
    precision.

    Args:
        value: Input that should represent a numeric value.
        default (float): Value used when conversion is not possible.
        decimal (int, optional): Decimal places used for rounding the result.
        log_class (str): Name of the calling class/module for log output.
        log_function (str): Name of the calling function for log output.

    Returns:
        float: Parsed numeric value or the ``default`` fallback.
    """

    # Check if default is a valid float
    if not isinstance(default, float):
        log(
            "VERBOSE",
            f"{log_class}.{log_function}({value}): default({default}) not float: set to 0.0",
        )
        default = float(0.0)

    # Check if decimal is a valid int
    if decimal is not None and not isinstance(decimal, int):
        log(
            "VERBOSE",
            f"{log_class}.{log_function}({value}): decimal({decimal}) not int: set to None",
        )
        decimal = None

    try:
        # Convert to float
        value = float(value)

        # Round
        if decimal is not None:
            return round(value, int(decimal))

        return value

    except (ValueError, TypeError) as e:
        log("ERROR", f"{log_class}.{log_function}(): failed: {e}: set {default}")
        return default
    except Exception as e:
        log("ERROR", f"{log_class}.{log_function}({value}): failed: {e}: set {default}")
        return default
