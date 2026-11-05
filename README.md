# Warmwassersteuerung

**Dieses Projekt ist für einen Raspberry Pi Pico W zur automatischen Regulierung der Temperatur eines Wasserbehälters durch Relais.**

## Projektbeschreibung

Die Relais regeln, je nach eingestellter Soll-Temperatur, durch Öffnen oder Schließen der Kaltwasserzufuhr die Temperatur des Wasserbehälters.

Komponenten:

- 2 Relais (Ventil öffnen / schließen)
- 2 Temperatursensoren (DS18B20 oder DHT11)
- 4-zeiliges I²C-LCD (PCF8574)
- Onboard-LED
- Asynchrone Weboberfläche zur Konfiguration und manuellen Steuerung

## Voraussetzungen

- Raspberry Pi Pico W mit **MicroPython**-Firmware (inkl. der Module `onewire`, `ds18x20`, `dht`, `uasyncio`)
- [ampy](https://github.com/scientifichackers/ampy) (Adafruit MicroPython Tool) zum Kopieren der Dateien
- Micro-USB-Kabel

## Live Demo auf wokwi.com

[Pico W](https://wokwi.com/projects/383802859950189569)

[Arduino Uno (deprecated)](https://wokwi.com/projects/346219906817065556)  
[ESP32-S3 (deprecated)](https://wokwi.com/projects/391176792254662657)

## Kopiere das Projekt auf den Pico

```bash
# Erstelle die config.json
cp config.example.json config.json
# Passe die config.json nach deinen Wünschen an
# (Pin-Vorlagen für verschiedene Boards liegen unter configs/)

# Kopiere das Projekt auf den Pico:

# MacOS
./scripts/copy_pico-mac.sh /dev/cu.usbmodem11301

# Windows
scripts\copy_pico-win.cmd COM3
```

## Starte das Projekt auf dem Pico (für debugging Zwecke, um Lognachrichten zu sehen)

```bash
# MacOS
ampy --port /dev/cu.usbmodem11301 run main.py

# Windows
ampy --port COM3 run main.py
```

## Weboberfläche

Nach dem Start verbindet sich der Pico W mit dem konfigurierten WLAN und stellt
eine Weboberfläche auf **Port 80** bereit (z. B. `http://<pico-ip>/`):

- Anzeige von Ist-Temperatur, Soll-Temperatur, Timer und LCD-Inhalt
- Ändern der Konfiguration (`/config/save`)
- Manuelles Öffnen (`/relay/open`) und Schließen (`/relay/close`) der Relais
- Zurücksetzen des Geräts (`/machine/reset`)

## Änderungshistorie

### v1.1.3

- Fix: `utils/error_logger.py` wird nun von allen Kopierskripten auf das Gerät kopiert (fehlte zuvor und führte zu einem `ImportError` beim Start)
- Fix: Die konfigurierte Sensorauflösung wird nun korrekt gesetzt (`set_resolution()` überschrieb sie zuvor immer mit dem Standardwert 11)
- Fix: `Config.get_bool()` berücksichtigt nun den `default`-Parameter
- Fix: Fehlende Keys (`TEMP_SENSOR_TYPE`, `TEMP_SENSOR_2_TYPE`, `TEMP_SENSOR_2_RESOLUTION_BIT`) in den Config-Vorlagen unter `configs/` ergänzt
- Neu: `AGENTS.md` mit Richtlinien für AI-Coding-Agenten
- Verbesserung: `.gitignore` auf das Projekt zugeschnitten (Python/MicroPython statt generischem NodeJS/Java-Template)
- Verbesserung: README korrigiert und ergänzt (u. a. Voraussetzungen, Weboberfläche, falscher Windows-Skriptname)

### v1.1.2

- Neu: Fehler-Logger mit getrennten Logdateien für main und Webserver
- Verbesserung: Docstrings und Kommentare überarbeitet
- Verbesserung: Zugriff auf Temperatursensoren refaktoriert
- Fix: Relais-Zeit-Anpassungslogik und Logging-Probleme behoben

### v1.1.1

- Fix: LCD.print() und LCD.clear() prüfen nun ob das LCD initialisiert wurde
- Fix: LCD.lines werden nun auch ohne angeschlossenes LCD auf der Webseite angezeigt
- Kopierskripte wurden vereinheitlicht

### v1.1.0

- Neu: komplettes Redesign der Basiskomponenten:
  - alle Komponenten sind jetzt Klassen, die meisten von ihnen Singletons oder Singletons pro PIN
  - kritische Klassen haben jetzt eine Sperre (Rlock), um den Zugriff von verschiedenen Threads gleichzeitig zu schützen
  - Es wurden mehr try/except-Blöcke eingebaut um mehr Fehler abzufangen
  - die meisten Funktionen sind nun asynchron
- Neu: `config.json` muss nun aus der `config.example.json` manuell vor dem Kopieren erstellt werden
  <br><br>
- Fix: WLAN-Verbindung wird nun schneller aufgebaut
- Fix: Das Abrufen der `index.html` ist nun deutlich performanter
- Fix: Die `index.html` zeigt nun wieder die Buttons an und die Standardwerte wurden korrigiert
  <br><br>
- Die `webserver.py` wurde nach `./` verschoben
- Kopierskripte wurden nach `./scripts` verschoben
- Einige Hilfsfunktionen wurden nach `./utils` verschoben
- Die `config_backup.json` wurde entfernt
- Lognachrichten wurden vereinheitlicht und standardmäßig reduziert (mehr VERBOSE Nachrichten)
- Kommentare wurden vereinheitlicht

### v1.0.0

- Initiales Release
