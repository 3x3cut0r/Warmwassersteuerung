import gc  # https://docs.micropython.org/en/latest/library/gc.html
import re  # https://docs.micropython.org/en/latest/library/re.html
import uasyncio as asyncio  # https://docs.micropython.org/en/latest/library/asyncio.html
from machine import (
    reset,
)  # https://docs.micropython.org/en/latest/library/machine.html#machine.reset
from utils.get_bool import get_bool
from utils.get_float import get_float
from utils.get_int import get_int
from utils.log import log  # logging function
from utils.log_level import log_level
from utils.error_logger import append_log
from src.config import config  # Config() instance
from src.lcd import lcd  # LCD() instance
from src.wifi import wifi  # WiFi() instance
from src.functions import print_nominal_temp
from src.relay import relay_open, relay_close


def encode_utf8(content=""):
    try:
        return str(content).encode("utf-8")
    except:
        return content


def is_checked(value):
    """Return " checked", if value is true"""

    return " checked" if str(value).lower() in ["true", "1", "yes", "on"] else ""


def is_true(value):
    """Return "true", if value is true"""

    return "true" if str(value).lower() in ["true", "1", "yes", "on"] else "false"


async def replace_placeholder(content="", line_number=0, config_data={}):
    """Replace placeholder in index.html file"""

    # Load complete LCD lines
    lcd_lines = await lcd.get_lines() or [""] * 4

    # Assign line numbers to placeholders and their keys
    line_to_placeholder = {
        # LCD LINE NUMBERS
        13: ("LCD_LINE_1", lcd_lines[0].replace(" ", "&nbsp;")),
        14: ("LCD_LINE_2", lcd_lines[1].replace(" ", "&nbsp;")),
        15: ("LCD_LINE_3", lcd_lines[2].replace(" ", "&nbsp;")),
        16: ("LCD_LINE_4", lcd_lines[3].replace(" ", "&nbsp;")),
        # MANUAL CONTROL
        21: (
            "highlighted",
            (
                " highlighted"
                if float(config_data.get("current_temp", -127.0))
                > float(config_data.get("nominal_max_temp", 57.0))
                else ""
            ),
        ),
        22: ("manual_relay_time", config_data.get("manual_relay_time", "")),
        23: (
            "highlighted",
            (
                " highlighted"
                if float(config_data.get("current_temp", -127.0))
                < float(config_data.get("nominal_min_temp", 42.0))
                else ""
            ),
        ),
        # CONFIGURATION
        29: ("nominal_min_temp", config_data.get("nominal_min_temp", "")),
        31: ("nominal_max_temp", config_data.get("nominal_max_temp", "")),
        33: ("delay_before_start_1", config_data.get("delay_before_start_1", "0")),
        35: ("init_relay_time", config_data.get("init_relay_time", "")),
        37: ("delay_before_start_2", config_data.get("delay_before_start_2", "0")),
        39: ("relay_time", config_data.get("relay_time", "")),
        41: ("update_time", config_data.get("update_time", "")),
        43: ("temp_update_interval", config_data.get("temp_update_interval", "")),
        45: (
            "lcd_i2c_backlight",
            is_checked(config_data.get("lcd_i2c_backlight", "false")),
        ),
        47: (
            "lcd_i2c_backlight",
            is_true(config_data.get("lcd_i2c_backlight", "false")),
        ),
        48: (
            "buttons_activated",
            is_checked(config_data.get("buttons_activated", "false")),
        ),
        50: (
            "buttons_activated",
            is_true(config_data.get("buttons_activated", "false")),
        ),
        52: ("log_level_OFF", (" selected" if log_level.get() == "OFF" else "")),
        53: ("log_level_ERROR", (" selected" if log_level.get() == "ERROR" else "")),
        54: ("log_level_WARN", (" selected" if log_level.get() == "WARN" else "")),
        55: ("log_level_INFO", (" selected" if log_level.get() == "INFO" else "")),
        56: (
            "log_level_VERBOSE",
            (" selected" if log_level.get() == "VERBOSE" else ""),
        ),
        59: ("interval", config_data.get("interval", "")),
        61: (
            "temp_sampling_interval",
            config_data.get("temp_sampling_interval", 10000),
        ),
        63: (
            "temp_change_high_threshold_temp",
            config_data.get("temp_change_high_threshold_temp", 1.0),
        ),
        65: (
            "temp_change_high_threshold_relay_time_multiplier",
            config_data.get("temp_change_high_threshold_relay_time_multiplier", 1.5),
        ),
        67: (
            "temp_change_high_threshold_update_time_multiplier",
            config_data.get("temp_change_high_threshold_update_time_multiplier", 0.5),
        ),
        69: ("wifi_max_attempts", config_data.get("wifi_max_attempts", "10")),
        # INFO
        73: ("wifi_ssid", config_data.get("wifi_ssid", "")),
        75: ("previous_millis", config_data.get("previous_millis", "0")),
        77: (
            "temp_last_measurement_time",
            config_data.get("temp_last_measurement_time", "0"),
        ),
        79: ("current_temp", config_data.get("current_temp", "-127.0")),
        81: (
            "temp_last_measurement",
            config_data.get("temp_last_measurement", "-127.0"),
        ),
        83: ("temp_increasing", config_data.get("temp_increasing", "")),
        85: ("temp_change_category", config_data.get("temp_change_category", "LOW")),
        88: ("TEMP_SENSOR_PIN", config_data.get("TEMP_SENSOR_PIN", "0")),
        90: ("TEMP_SENSOR_2_PIN", config_data.get("TEMP_SENSOR_2_PIN", "0")),
        92: (
            "TEMP_SENSOR_RESOLUTION_BIT",
            config_data.get("TEMP_SENSOR_RESOLUTION_BIT", "0"),
        ),
        94: ("LCD_PIN_SDA", config_data.get("LCD_PIN_SDA", "0")),
        96: ("LCD_PIN_SCL", config_data.get("LCD_PIN_SCL", "0")),
        98: ("LCD_ADDR", config_data.get("LCD_ADDR", "0")),
        100: ("LCD_FREQ", config_data.get("LCD_FREQ", "0")),
        102: ("LCD_COLS", config_data.get("LCD_COLS", "0")),
        104: ("LCD_ROWS", config_data.get("LCD_ROWS", "0")),
        106: ("RELAY_OPEN_PIN", config_data.get("RELAY_OPEN_PIN", "0")),
        108: ("RELAY_CLOSE_PIN", config_data.get("RELAY_CLOSE_PIN", "0")),
        110: ("BUTTON_TEMP_UP_PIN", config_data.get("BUTTON_TEMP_UP_PIN", "0")),
        112: ("BUTTON_TEMP_DOWN_PIN", config_data.get("BUTTON_TEMP_DOWN_PIN", "0")),
        # HIDDEN
        115: ("manual_relay_time", config_data.get("manual_relay_time", "0")),
        # RESET
        120: (
            "boot_normal",
            (
                " checked"
                if str(config_data.get("boot_normal", "false")).lower()
                in ["true", "1", "yes", "on"]
                else ""
            ),
        ),
        122: (
            "boot_normal",
            (
                "true"
                if str(config_data.get("boot_normal", "false")).lower()
                in ["true", "1", "yes", "on"]
                else "false"
            ),
        ),
    }

    # Replace keys
    if line_number in line_to_placeholder:
        key, value = line_to_placeholder[line_number]
        placeholder = f"!!!--{key}--!!!"
        content = content.replace(placeholder, str(value))

    return content


def parse_form_data(body):
    """Parse form data"""

    parsed_data = {}
    for pair in body.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            parsed_data[key] = value
        else:
            parsed_data[pair] = None
    return parsed_data


async def manage_wifi_connection():
    """Manage wifi connection"""

    await wifi.initialize()
    await wifi.connect()

    while True:
        await asyncio.sleep(30)

        if not wifi.is_connected():
            await wifi.connect()


async def stream_file(writer, file_name, chunk_size=1024):
    """Stream file with a given chunk_size"""

    file_name_präfix = "../web/"
    try:
        with open(file_name_präfix + file_name, "rb", encoding="utf-8") as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                await writer.awrite(chunk)

    except OSError as e:
        log("ERROR", f"Webserver.stream_file({file_name}, {chunk_size}): {e}")


async def generate_index_html(writer):
    """Get index.html"""

    web_path = "/web/"
    file_path = web_path + "index.html"
    line_number = 0

    # Load complete config
    config_data = await config.get_config()

    if config_data != {}:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line_number += 1
                line = await replace_placeholder(line, line_number, config_data)
                await writer.awrite(encode_utf8(line))
    else:
        log("ERROR", f"Webserver.generate_index_html(): failed")


async def handle_post(body, requested_path="/config/save"):
    """Handle post from index.html"""

    # Response_content
    response_content = ""

    # Parse form data
    form_data = parse_form_data(body)
    log("INFO", f"Webserver.handle_post(): form data: {form_data}")

    error = False

    # Load complete config
    config_data = await config.get_config()

    # Update config
    for key, value in form_data.items():
        if config_data.get(key) is None:
            error = "key " + key + " not found in config.json"
        else:
            if config_data.get(key) != value:
                config_data[key] = value

    # Save config
    await config.save()

    # Print nominal temp
    await print_nominal_temp()

    # Set lcd backlight
    await lcd.set_backlight(get_bool(config_data.get("lcd_i2c_backlight")))

    # Set log level
    log_level.set(config_data.get("log_level", "OFF"))

    # /relay/open
    if requested_path == "/relay/open":
        current_temp = get_float(config_data.get("current_temp", -127.0))
        manual_relay_time = get_int(config_data.get("manual_relay_time", 1200))
        if manual_relay_time > 10000:
            manual_relay_time = 10000
        timer = get_int(config_data.get("timer"))
        puffer_time = (manual_relay_time / 1000) + 3
        if error:
            response_content = f'<span style="color: orange;">WARN: Ventil wurde nicht ge&ouml;ffnet: {error}</span>'
            log(
                "WARN",
                f"Relay.toggle(time={manual_relay_time}): manual trigger failed: {error}",
            )
        elif timer <= puffer_time:
            response_content = f'<span style="color: orange;">WARN: Ventil wurde nicht ge&ouml;ffnet: der Timer ist zu nahe an 0.</span>'
            log(
                "ERROR",
                f"Relay.toggle(time={manual_relay_time}): manual trigger failed: Timer near by 0.",
            )
        elif not (0 < current_temp <= 120):
            response_content = f'<span style="color: red;">ERROR: Ventil wurde nicht ge&ouml;ffnet: Temp Fehler!</span>'
            log(
                "ERROR",
                f"Relay.toggle(time={manual_relay_time}): manual trigger failed: temp error.",
            )
        else:
            response_content = f'<span style="color: green;">INFO: Ventil wird f&uuml;r {manual_relay_time}ms ge&ouml;ffnet.</span>'
            log("INFO", f"Relay.toggle(time={manual_relay_time}): manual trigger")
            await relay_open.toggle(manual_relay_time)

    # /relay/close
    if requested_path == "/relay/close":
        current_temp = get_float(config_data.get("current_temp", -127.0))
        manual_relay_time = get_int(config_data.get("manual_relay_time", 1200))
        if manual_relay_time > 10000:
            manual_relay_time = 10000
        timer = get_int(config_data.get("timer"))
        puffer_time = (manual_relay_time / 1000) + 3
        if error:
            response_content = f'<span style="color: orange;">WARN: Ventil wurde nicht geschlossen: {error}</span>'
            log(
                "WARN",
                f"Relay.toggle(time={manual_relay_time}): manual trigger failed: {error}",
            )
        elif timer <= puffer_time:
            response_content = f'<span style="color: orange;">WARN: Ventil wurde nicht geschlossen: der Timer ist zu nahe an 0.</span>'
            log(
                "ERROR",
                f"Relay.toggle(time={manual_relay_time}): manual trigger failed: Timer near by 0.",
            )
        elif not (0 < current_temp <= 120):
            response_content = f'<span style="color: red;">ERROR: Ventil wurde nicht geschlossen: Temp Fehler!</span>'
            log(
                "ERROR",
                f"Relay.toggle(time={manual_relay_time}): manual trigger failed: temp error.",
            )
        else:
            response_content = f'<span style="color: green;">INFO: Ventil wird f&uuml;r {manual_relay_time}ms geschlossen.</span>'
            log("INFO", f"Relay.toggle(time={manual_relay_time}): manual trigger")
            await relay_close.toggle(manual_relay_time)

    # /config/save
    elif requested_path == "/config/save":
        if error:
            response_content = f'<span style="color: orange;">WARN: Konfiguration nur teilweise aktualisiert: {error}</span>'
            log("WARN", f"config.json partially updated: {error}")
        else:
            response_content = f'<span style="color: green;">INFO: Konfiguration erfolgreich aktualisiert</span>'
            log("INFO", "config.json successfully updated")

    # /machine/reset
    elif requested_path == "/machine/reset":
        if error:
            response_content = f'<span style="color: orange;">WARN: Boot Normal Option wurde nicht richtig &uuml;bermittelt und bleibt unber&uuml;hrt: {error}</span>'
            log("WARN", f"boot_normal NOT updated: {error}")
        else:
            response_content = f'<span style="color: green;">INFO: Reset erkannt. Starte neu ...</span>'
            log("INFO", "reset()")

    # Add back button and return script
    if requested_path in [
        "/relay/open",
        "/relay/close",
        "/config/save",
        "/machine/reset",
    ]:
        response_content += """
            <br /><br />
            <a href="/"><button type="button">zur&uuml;ck</button></a>
            <script>
                setTimeout(function() {
                    window.location.href = '/';
                }, 4000); // 4000 Millisekunden = 4 Sekunden
            </script>
        """

    return response_content


async def send_response(writer, content_type, content=None):
    """Send response"""

    writer.write(encode_utf8(f"HTTP/1.1 200 OK\nContent-Type: {content_type}\n\n"))
    if content:
        await writer.awrite(encode_utf8(content))


async def handle_post_request(writer, request_body, requested_path):
    """Handle post request"""

    response_content = await handle_post(request_body, requested_path)
    await send_response(writer, "text/html", response_content)


async def handle_client(reader, writer):
    """Handle client"""

    reset_pico = False

    # Get request
    request_lines = []
    content_length = 0
    while True:
        line = await reader.readline()
        if line == b"\r\n":
            break
        request_lines.append(line.decode("utf-8"))
        if line.lower().startswith(b"content-length:"):
            content_length = int(line.decode().split()[1])

    # Get request header
    request_header = "".join(request_lines)

    # Read body if present
    request_body = ""
    if content_length > 0:
        remaining_length = content_length
        while remaining_length > 0:
            chunk = await reader.read(min(remaining_length, 1024))
            if not chunk:
                break
            request_body += chunk.decode("utf-8")
            remaining_length -= len(chunk)

    # Process request
    match = re.search(
        r"^(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH) /[^ ]*", request_header
    )
    if match:
        result = match.group(0)
    else:
        result = ""
    log("INFO", f"Webserver.handle_client(): {result}")

    requested_path = request_header.split(" ")[1]

    # /index.html
    if requested_path in ["/", "/index.html"]:
        await send_response(writer, "text/html")
        await generate_index_html(writer)

    # /relay/open, /relay/close, /config/save
    elif (
        requested_path in ["/relay/open", "/relay/close", "/config/save"]
        and "POST" in request_header.split(" ")[0]
    ):
        await handle_post_request(writer, request_body, requested_path)

    # /machine/reset
    elif requested_path == "/machine/reset" and "POST" in request_header.split(" ")[0]:
        await handle_post_request(writer, request_body, requested_path)
        reset_pico = True

    # /styles.css
    elif requested_path == "/styles.css":
        await send_response(writer, "text/css")
        await stream_file(writer, "styles.css", chunk_size=1024)

    # 404 Not Found
    else:
        response = "HTTP/1.1 404 Not Found\n\n"
        await writer.awrite(encode_utf8(response))

    # Clean up and close
    await writer.drain()
    await writer.wait_closed()

    # Release memory
    log("VERBOSE", "Webserver.gc.collect()")
    gc.collect()

    # Reset pico
    if reset_pico:
        reset()


async def webserver():
    """Run a webserver on port 0.0.0.0:80"""

    try:
        print("INFO: --------------------------")
        print("INFO: Webserver()")
        print("INFO: --------------------------")

        host = "0.0.0.0"
        port = 80
        asyncio.create_task(manage_wifi_connection())
        print(f"INFO: Webserver.start_server({host}, {port})")
        server = await asyncio.start_server(handle_client, host, port)  # type: ignore

    except Exception as e:
        # Print error message
        message = f"Webserver(): {str(e)}\n"
        print(f"ERROR: {message}")

        # Append error message to log file
        append_log(message, "/web_error.log")


if __name__ == "__main__":
    # Create asyncio event loop
    loop = asyncio.get_event_loop()

    # Run webserver() as task
    loop.create_task(webserver())

    # Run event loop forever
    loop.run_forever()
