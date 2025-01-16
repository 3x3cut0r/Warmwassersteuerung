# ==================================================
# Hot water control
# ==================================================
#
# Components:
#   - 4 line LCD
#   - 2 Relays
#   - 2 Buttons (optional)
#   - 1 DS18B20 I2C temperature sensor
#
#   Copyright (C) 2024, 3x3cut0r
#
#   Published under the MIT license.
#
import gc  # https://docs.micropython.org/en/latest/library/gc.html
import time  # https://docs.micropython.org/en/latest/library/time.html
import uasyncio as asyncio  # https://docs.micropython.org/en/latest/library/asyncio.html
from machine import (
    reset,
)  # https://docs.micropython.org/en/latest/library/machine.html#machine.reset

from webserver import webserver
from utils.log import log  # logging function
from utils.log_level import log_level
from src.config import config  # Config() instance
from src.lcd import lcd  # LCD() instance
from src.led import led  # LED() instance
from src.relay import relay_open, relay_close
from src.temp import temp_sensor, temp_sensor_2

# from src.button import button, button_2
from src.functions import (
    categorize_temp_change,
    adjust_relay_time_based_on_temp_category,
    adjust_update_time_based_on_temp_category,
    update_temp,
    print_nominal_temp,
    open_relays,
    # check_buttons,
    update_timer,
    wait_start,
)


async def main():
    try:
        print("INFO: --------------------------")
        print("INFO: Main()")
        print("INFO: --------------------------")

        # Initialize LogLevel
        level = await config.get("log_level", "OFF")
        log_level.initialize(level)

        # Initialize LED
        await led.initialize()

        # Initialize LCD
        await lcd.initialize()

        # Initialize relays
        open_relay_pin = await config.get_int("RELAY_OPEN_PIN")
        close_relay_pin = await config.get_int("RELAY_CLOSE_PIN")
        await relay_open.initialize(open_relay_pin)
        await relay_close.initialize(close_relay_pin)

        # Initialize temp sensor 1
        temp_sensor_pin = await config.get_int("TEMP_SENSOR_PIN")
        temp_sensor_type = await config.get("TEMP_SENSOR_TYPE")
        temp_sensor_resolution = await config.get_int("TEMP_SENSOR_RESOLUTION_BIT")
        await temp_sensor.initialize(
            temp_sensor_pin,
            resolution=temp_sensor_resolution,
            type=temp_sensor_type,
        )

        # Initialize temp sensor 2
        temp_sensor_2_pin = await config.get_int("TEMP_SENSOR_2_PIN")
        temp_sensor_2_type = await config.get("TEMP_SENSOR_2_TYPE")
        temp_sensor_resolution = await config.get_int("TEMP_SENSOR_2_RESOLUTION_BIT")
        await temp_sensor_2.initialize(
            temp_sensor_2_pin,
            resolution=temp_sensor_resolution,
            type=temp_sensor_2_type,
        )

        # Initialize buttons
        # button_pin = await config.get_int("BUTTON_TEMP_UP_PIN")
        # button_2_pin = await config.get_int("BUTTON_TEMP_DOWN_PIN")
        # await button.initialize(button_pin)
        # await button_2.initialize(button_2_pin)

        # Update temp
        await update_temp()
        await update_temp(2)
        temp_last_measurement = await config.get_float("current_temp", -127.0)
        await config.set("temp_last_measurement", temp_last_measurement)

        # Print nominal temp
        await print_nominal_temp()

        if await config.get_bool("boot_normal", True):

            # Wait start 1
            delay_before_start_1 = await config.get_int("delay_before_start_1")
            log("INFO", f"Main.wait_start(1/2: {delay_before_start_1})")
            await wait_start(delay_before_start_1, "Start 1/2:")

            # Open relay initial
            init_relay_time = await config.get_int("init_relay_time")
            await relay_open.toggle(init_relay_time)

            # Wait start 2
            delay_before_start_2 = await config.get_int("delay_before_start_2")
            log("INFO", f"Main.wait_start(2/2: {delay_before_start_2})")
            await wait_start(delay_before_start_2, "Start 2/2:")

        # Open relay
        relay_time = await config.get_int("relay_time", 1800)
        await open_relays(relay_time)

        # Set normal boot to True
        await config.set("boot_normal", 1)

        # Init time values
        previous_millis = 0
        interval = await config.get_int("interval", 930)
        update_time = await config.get_int("update_time", 120)
        temp_update_interval = await config.get_int("temp_update_interval", 5)

        # ==================================================
        # Main loop
        # ==================================================
        log("INFO", "--------------------------")
        log("INFO", "Main.loop()")
        log("INFO", "--------------------------")

        while True:
            current_millis = time.ticks_ms()

            # Adjust temp category
            if time.ticks_diff(
                current_millis, await config.get_int("temp_last_measurement_time")
            ) >= await config.get_int("temp_sampling_interval"):

                # Update temp
                await update_temp()
                # await update_temp(2)  # temp_sensor >= 2 not used for adjustments
                temp_change = await config.get_float(
                    "current_temp", -127.0
                ) - await config.get_float("temp_last_measurement")

                # Categorize temp change
                _ = await categorize_temp_change(temp_change)

                # Update last measurement temp
                await config.set(
                    "temp_last_measurement",
                    await config.get_float("current_temp", -127.0),
                )

                # Update last measurement temp time
                await config.set("temp_last_measurement_time", current_millis)

                # Release memory
                log("VERBOSE", "Main.gc.collect()")
                gc.collect()

            # Main
            if time.ticks_diff(current_millis, previous_millis) > interval:

                if update_time > 0:
                    # Update timer
                    await update_timer(update_time)

                    # Update temp on temp update interval
                    if update_time % temp_update_interval == 0:
                        await update_temp()
                        await update_temp(2)

                    update_time -= 1

                    # # Check buttons
                    # await check_buttons()

                    # Print mem alloc
                    log(
                        "VERBOSE",
                        "Main.gc.mem_alloc(): {} Bytes".format(gc.mem_alloc()),
                    )

                else:

                    # Update temp
                    await update_temp()
                    await update_temp(2)

                    # Set and adjust relay_time based on temp category
                    relay_time = await adjust_relay_time_based_on_temp_category()

                    # Set and adjust update_time based on temp category
                    update_time = await adjust_update_time_based_on_temp_category()

                    # Open relays
                    await open_relays(relay_time)

                    # Print allocated memory
                    log(
                        "VERBOSE",
                        "Main.gc.mem_alloc(): {} Bytes".format(gc.mem_alloc()),
                    )

                # Update previous millis
                previous_millis = current_millis
                await config.set("previous_millis", previous_millis)

            await asyncio.sleep(0.1)

    except Exception as e:

        # Print error message
        message = f"ERROR: main.py: {str(e)}\n"
        print(message)

        # Set normal boot to False
        await config.set("boot_normal", 0)
        await config.save()

        # Write error.log
        with open("/error.log", "r+", encoding="utf-8") as file:
            lines = file.readlines()
            lines.append(message)
            if len(lines) > 1024:
                lines = lines[-1024:]
            file.seek(0)
            file.writelines(lines)
            file.truncate()

        # Reset pico
        reset()


if __name__ == "__main__":

    # Create asyncio event loop
    loop = asyncio.get_event_loop()

    # Run webserver() as task
    loop.create_task(webserver())

    # Run main() as task
    loop.create_task(main())

    # Run event loop forever
    loop.run_forever()
