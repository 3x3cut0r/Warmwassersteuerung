import uasyncio as asyncio  # https://docs.micropython.org/en/latest/library/asyncio.html
import time  # https://docs.micropython.org/en/latest/library/time.html
from utils.log import log  # logging function
from src.config import config  # Config() instance
from src.lcd import lcd  # LCD() instance
from src.relay import relay_open, relay_close  # Relay() instance
from src.temp import temp_sensor, temp_sensor_2  # TemperatureSensor() instance


# ==================================================
# Functions
# ==================================================


# Categorize temp change
async def categorize_temp_change(temp_change=0.0):
    # Load config
    high_threshold = await config.get_float("temp_change_high_threshold_temp", 1.0)
    # Medium_threshold = await config.get_float("temp_change_medium_threshold", 0.3)

    # Set category
    abs_temp_change = abs(temp_change)
    if abs_temp_change >= high_threshold:
        category = "HIGH"  # TempChangeCategory.HIGH
    # elif abs_temp_change >= medium_threshold:
    #     category = "MEDIUM"  # TempChangeCategory.MEDIUM
    else:
        category = "LOW"  # TempChangeCategory.LOW

    old_category = await config.get("temp_change_category")
    if old_category != category:
        log("INFO", f"Main.categorize_temp_change({temp_change}) -> {category}")

    await config.set("temp_change_category", category)

    # Temp increasing?
    arrow_direction = 0 if temp_change > 0 else 1
    await config.set("temp_increasing", 0 if temp_change <= 0 else 1)
    await lcd.print(2, 0, f"Temperatur   {category}")
    await lcd.print_char(2, 11, arrow_direction)

    return category


# Adjust relay time based on temp category
async def adjust_relay_time_based_on_temp_category():
    # Load config
    relay_time = await config.get_int("relay_time", 1200)
    temp_increasing = await config.get_bool("temp_increasing", False)

    # Only on temp_increasing = true
    if temp_increasing:
        temp_category = await config.get("temp_change_category", "LOW")

        if temp_category == "HIGH":
            # Shorter opening time for rapid temperature changes
            multiplier = await config.get_float(
                "temp_change_high_threshold_relay_time_multiplier", 1.5
            )

        # elif temp_category == "MEDIUM":
        #     # Moderate opening time for normal temperature changes
        #     multiplier = await config.get_float(
        #         "temp_change_medium_threshold_relay_time_multiplier", 1.25
        #     )

        new_relay_time = int(relay_time * multiplier)

        if new_relay_time != relay_time:
            log("INFO", f"Main.adjust_relay_time() -> {new_relay_time}")

        return new_relay_time

    # Normal opening time for slow temperature changes
    return relay_time


# Adjust update time based on temp category
async def adjust_update_time_based_on_temp_category():
    # Load config
    update_time = await config.get_int("update_time", 120)
    temp_increasing = await config.get_bool("temp_increasing", False)

    # Only on temp_increasing = true
    if temp_increasing:
        temp_category = await config.get("temp_change_category", "LOW")

        if temp_category == "HIGH":
            # Temp measurement takes place very often
            multiplier = await config.get_float(
                "temp_change_high_threshold_update_time_multiplier", 0.5
            )

        # elif temp_category == "MEDIUM":
        #     # Moderate opening time for normal temperature changes
        #     multiplier = await config.get_float(
        #         "temp_change_medium_threshold_update_time_multiplier", 0.75
        #     )

        new_update_time = int(update_time * multiplier)

        if new_update_time != update_time:
            log("INFO", f"Main.adjust_update_time() -> {new_update_time}")

        return new_update_time

    # Temp measurement takes place normally
    return update_time


# Convert utf-8 characters to HD44780 characters
# Get dual number from the HD44780 table: https://de.wikipedia.org/wiki/HD44780#Schrift_und_Zeichensatz
# Convert dual number to octal number: https://www.arndt-bruenner.de/mathe/scripts/Zahlensysteme.htm
def convert_utf8(string=""):
    replacements = {
        "ß": "\u00DF",  # Unicode for ß
        "°": "\u00B0",  # Unicode for °
        "ä": "\u00E4",  # Unicode for ä
        "ö": "\u00F6",  # Unicode for ö
        "ü": "\u00FC",  # Unicode for ü
    }
    for original, replacement in replacements.items():
        string = string.replace(original, replacement)
    return string


# Update current temp on lcd
async def update_temp(sensor_number=1):
    # Set sensor postfix
    sensor_postfix = f"_{sensor_number}" if sensor_number > 1 else ""

    # Read temp
    current_temp = await globals()[f"temp_sensor{sensor_postfix}"].get_temp()

    if current_temp is not None:
        # Set LCD columns once
        lcd_cols_half = int(lcd.cols / 2)

        # Format the temperature string
        current_temp_string = lcd.rjust(f"{current_temp:.1f} °C", lcd_cols_half)
        current_temp_string_utf8 = convert_utf8(current_temp_string)

        log("INFO", f"Functions.update_temp({sensor_number}): {current_temp:.1f} °C")

        # Print temp on LCD
        # ....................
        # temp 2     temp 1
        # -127.0 °C  -127.0 °C
        temp_pos = max(lcd.cols - len(current_temp_string), 0)
        if sensor_number > 1:
            temp_pos = max(lcd_cols_half - len(current_temp_string), 0)
        await lcd.print(0, temp_pos, current_temp_string_utf8, False)


# Print nominal temp
async def print_nominal_temp():
    # Load config
    min_temp = await config.get_float("nominal_min_temp", 42.0)
    max_temp = await config.get_float("nominal_max_temp", 57.0)

    # Set lower and upper bounds for nominal temperatures
    nominal_min_temp = max(0.0, min(120.0, min_temp))
    nominal_max_temp = max(nominal_min_temp, min(120.0, max_temp))

    # Format nominal temperature string
    nominal_temp = f"{nominal_min_temp:.1f} - {nominal_max_temp:.1f} °C"

    # Calculate the position for displaying the temperature
    temp_pos = lcd.cols - len(nominal_temp)

    # Print the formatted temperature on LCD
    await lcd.print(1, 0, "Soll:")
    await lcd.print(1, temp_pos, nominal_temp)


# Open relays depending on temp
async def open_relays(relay_time):

    # Load config
    current_temp = await config.get_float("current_temp", -127.0)
    nominal_min_temp = await config.get_float("nominal_min_temp", 42.0)
    nominal_max_temp = await config.get_float("nominal_max_temp", 58.0)

    # Set stop timer
    await config.set("stop_timer", relay_time // 1000 + 1)

    # Only switch if the temperature can be read
    if 0 < current_temp <= 120:

        if current_temp < nominal_min_temp:
            # Increase temp
            await lcd.print(3, 0, "schließe Ventil  >>>")
            await relay_close.toggle(relay_time)

        elif current_temp > nominal_max_temp:
            # Decrease temp
            await lcd.print(3, 0, "öffne Ventil     >>>")
            await relay_open.toggle(relay_time)

        else:
            # Do nothing
            await lcd.print(3, 0, "Soll Temp erreicht !")

    else:
        # Print error
        await lcd.print(3, 0, "Fehler: Temp Fehler!")
        await asyncio.sleep(2)


# Update temp display
async def update_temp_display(rate, message, symbol):
    if rate >= 3:
        await lcd.print(2, 0, f"{message}   {symbol * 3}")
    elif rate >= 0.5:
        await lcd.print(2, 0, f"{message}    {symbol * 2}")
    else:
        await lcd.print(2, 0, f"{message}     {symbol}")

    await asyncio.sleep(2)
    await lcd.print(2, 0, f"                    ")


# # Update nominal temp
# async def update_nominal_temp(button_pin):
#     button_long = 0
#     rate = 0.1
#
#     # Load config
#     temp_up_pin = await config.get_int("BUTTON_TEMP_UP_PIN", 1)
#     temp_down_pin = await config.get_int("BUTTON_TEMP_DOWN_PIN", 2)
#     nominal_min_temp = await config.get_float("nominal_min_temp", 42.0)
#     nominal_max_temp = await config.get_float("nominal_max_temp", 58.0)
#
#     # While button is pressed
#     while check_button(button_pin):
#         # Increase temp on temp up button
#         if button_pin == temp_up_pin:
#             nominal_min_temp += rate
#             nominal_max_temp += rate
#             await update_temp_display(rate, "TempUp Pressed", "+")
#
#         # Decrease temp on temp down button
#         elif button_pin == temp_down_pin:
#             nominal_min_temp -= rate
#             nominal_max_temp -= rate
#             await update_temp_display(rate, "TempDown Pressed", "-")
#
#         # Update config values and print nominal temp
#         await config.set("nominal_min_temp", nominal_min_temp)
#         await config.set("nominal_max_temp", nominal_max_temp)
#         await print_nominal_temp()
#
#         # Adjust rate and sleep
#         await asyncio.sleep(0.5)
#         button_long += 1
#         if button_long == 5:
#             rate = 1
#         elif button_long == 10:
#             rate = 1  # Adjust rate as needed
#
#     # Save config
#     await config.save()


# Check buttons
# async def check_buttons():
#     # Check if buttons_activated = 1
#     if await config.get_bool("buttons_activated", False):
#         # Update nomianl temp
#         await update_nominal_temp(await config.get_int("BUTTON_TEMP_UP_PIN", 1))
#         await update_nominal_temp(await config.get_int("BUTTON_TEMP_DOWN_PIN", 2))


# Format time
def format_time(secs):
    hours = secs // 3600
    mins = (secs % 3600) // 60
    secs = secs % 60
    if hours > 0:
        return f"{hours:02d}h {mins:02d}m {secs:02d}s"
    else:
        return f"{mins:02d}m {secs:02d}s"


# Update timer
async def update_timer(secs, message="Regle in:"):
    stop_timer = await config.get_int("stop_timer", 0)
    if stop_timer >= 0:
        log("VERBOSE", f"Functions.stop_timer({stop_timer})")
        await config.set("stop_timer", (stop_timer - 1))
    else:
        log("VERBOSE", f"Functions.update_timer({secs})")
        await config.set("timer", secs)

        time = format_time(secs)
        cursor = lcd.cols - len(time)

        await lcd.print(3, 0, message)
        await lcd.print(3, cursor, time)


# Wait start
async def wait_start(secs=0, lcd_text="Starte in:"):
    log("VERBOSE", f"Functions.wait_start({secs})")

    # Load config
    previous_millis = 0
    interval = await config.get_int("interval", 930)
    temp_update_interval = await config.get_int("temp_update_interval", 5)

    while secs > 0:
        current_millis = time.ticks_ms()
        if time.ticks_diff(current_millis, previous_millis) > interval:
            # Update timer
            await update_timer(secs, lcd_text)

            # Temp update on interval
            if secs % temp_update_interval == 0:
                await update_temp()
                await update_temp(2)

            # # Check buttons
            # await check_buttons()

            # Decrease secs
            secs -= 1
            previous_millis = current_millis

        await asyncio.sleep(0.1)
