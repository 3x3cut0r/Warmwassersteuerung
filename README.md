# Warmwassersteuerung

**Dieses Projekt ist für einen Raspberry Pi Pico W zur automatischen Regulierung der Temperatur eines Wasserbeulers durch Relais.**

## Projektbeschreibung

Die Relais regeln, je nach eingestellter Soll-Temperatur, durch öffnen oder schließen der Kaltwasserzufuhr die Temperatur des Wasserbeulers.

## Live Demo auf wokwi.com

[Pico W](https://wokwi.com/projects/383802859950189569)

[Arduino Uno (depricated)](https://wokwi.com/projects/346219906817065556)  
[ESP32-S3 (depricated)](https://wokwi.com/projects/391176792254662657)

## Kopiere das Projekt auf den Pico

```bash
# Erstelle die config.json
cp config.example.json config.json
# Passe die config.json nach deinen Wünschen an

# Kopiere das Projekt auf den Pico:

# MacOS
./scripts/copy_pico-mac.sh /dev/cu.usbmodem11301

# Windows
./scripts/copy_pico-win.sh COM3
```

## Starte das Projekt auf dem Pico (für debugging Zwecke, um Lognachrichten zu sehen)

```bash
# MacOS
ampy --port /dev/cu.usbmodem11301 run main.py

# Windows
ampy --port COM3 run main.py
```

## Änderungshistorie

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

- Neu: komplettes Redisign der Basiskomponenten:
  - alle Komponenten sind jetzt Klassen, die meisten von ihnen Singletons oder Singletons pro PIN
  - kritische Klassen haben jetzt eine Sperre (Rlock), um den Zugriff von verschiedenen Threads gleichzeitig zu schützen
  - Es wurden mehr try/except-Blöcke eingebaut um mehr Fehler abzufangen
  - die meisten Funktionen sind nun asynchron
- Neu: `config.json` muss nun aus der `config.example.json` manuell vor dem Kopieren erstellt werden
  <br><br>
- Fix: Wlan Verbindung wird nun schneller aufgebaut
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
