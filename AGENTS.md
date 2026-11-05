# AGENTS.md

Guidelines for AI coding agents working in this repository.

## Project Overview

Hot water control ("Warmwassersteuerung") for a Raspberry Pi Pico W running
**MicroPython**. Two relays open/close the cold water supply of a hot water
tank to keep the temperature between configurable min/max values. Sensors:
2x DS18B20 (OneWire) or DHT11, a 4-line I2C LCD (PCF8574), an onboard LED and
optional buttons (currently disabled). An async web server on port 80
serves a configuration UI and manual relay controls.

**This is MicroPython, not CPython.** There is no pip, no standard-library
`asyncio` (use `uasyncio`), and the device is memory constrained. Never add
dependencies that are not already vendored or shipped with the firmware.

## Repository Layout

| Path | Purpose |
|---|---|
| `main.py` | Entry point: hardware init, start phases, control loop |
| `webserver.py` | Async HTTP server, form handling, manual relay control |
| `src/` | Hardware abstraction classes (config, lcd, relay, temp, wifi, ...) |
| `utils/` | Helper functions (logging, type conversion, error logger) |
| `web/` | Static web assets (`index.html` template with `!!!--KEY--!!!` placeholders, CSS) |
| `configs/` | Board-specific config templates (Pico, deprecated ESP32-S3) |
| `scripts/` | Deployment scripts (ampy / mpremote) |
| `docs/` | Pinout diagrams |
| `config.example.json` | Template for the device-side `config.json` |

Vendored libraries (do not restyle or refactor): `src/lcd_api.py`,
`src/machine_i2c_lcd.py`.

## Code Style

- Indentation: 4 spaces. Naming: `snake_case` functions/variables,
  `PascalCase` classes, `UPPER_CASE` config keys for hardware settings,
  lowercase keys for runtime state.
- Comments, docstrings and log messages: English. User-facing texts
  (LCD lines, web UI, README): German.
- All I/O-bound APIs are `async def`; protect shared state with
  `src/rlock.py` (`Rlock`, re-entrant asyncio lock).
- Hardware classes follow the singleton or singleton-per-pin pattern
  (`_instances` registry keyed by pin). Module-level instances are created
  at the bottom of each module (e.g. `temp_sensor = TempSensor()`).
- Error handling: `try/except` with `utils/log.py` logging and a safe
  return value (`None` / default). Never let an exception escape `main()`
  without setting `boot_normal = 0` and saving the config (crash-recovery
  mechanism in `main.py`).
- Type hints only in `utils/*` (MicroPython's RAM is limited; keep them
  elsewhere only where they add clarity).

## Configuration

- Runtime config lives in `config.json` on the device (git-ignored),
  created from `config.example.json`. Access it exclusively through
  `src/config.py` (`config.get`, `config.get_int`, `config.get_float`,
  `config.get_bool`, `config.set`, `config.save`).
- `config.set()` only changes memory; `config.save()` persists to flash.
  Persist only when necessary (flash wear).
- When adding a new config key, add it to `config.example.json` and to the
  board templates in `configs/` if applicable.

## Deployment

Deployment scripts copy files to the device via `ampy` (Pico) or
`mpremote` (ESP32-S3, deprecated):

```bash
./scripts/copy_pico-mac.sh /dev/cu.usbmodem11301   # macOS
scripts\copy_pico-win.cmd COM3                     # Windows
```

**Whenever you add, rename or move a `.py` file, update the file lists in
ALL deploy scripts** (`scripts/copy_pico-mac.sh`, `scripts/copy_pico-win.cmd`,
`scripts/copy_ESP32-S3-win.ps1`). A missing file causes an `ImportError` on
the device at boot.

## Verification

There are no tests, CI or linters configured. Minimum checks before
finishing:

```bash
# Syntax check every touched file (imports are not executed, so
# MicroPython-only modules do not matter here):
python3 -m py_compile main.py webserver.py src/*.py utils/*.py

# Shell scripts:
bash -n scripts/copy_pico-mac.sh
```

Full behavior verification requires the physical device (or the Wokwi
simulator linked in README.md).

## Known Pitfalls

- `machine.Pin(0)` is valid; do not reject pin `0` in validation code.
- DS18B20 uses OneWire, not I2C (the LCD is the I2C device).
- `uasyncio` has no `asyncio.Lock` re-entrance — always use `Rlock`.
- The web UI writes form values into the config; keep types consistent
  (strings vs. numbers) when adding new form fields.
