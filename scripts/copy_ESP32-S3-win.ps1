# .\upload_project_to_BPI-ESP32S3.ps1 -port COM1 -config

param(
    [switch]$copy,
    [string]$port,
    [switch]$config,
    [switch]$clean
)

function RemoveProjectFiles {
    Write-Host "Entferne Projektdateien..."
    python -m mpremote connect $port rm :boot.py
    python -m mpremote connect $port rm :main.py
    python -m mpremote connect $port rm :webserver.py
    if ($config) {
        Write-Host "Entferne config.json"
        python -m mpremote connect $port rm :config.json
    }
    python -m mpremote connect $port rm :error.log

    python -m mpremote connect $port rm :utils/get_bool.py
    python -m mpremote connect $port rm :utils/get_float.py
    python -m mpremote connect $port rm :utils/get_int.py
    python -m mpremote connect $port rm :utils/log_level.py
    python -m mpremote connect $port rm :utils/log.py
    python -m mpremote connect $port rmdir :utils

    python -m mpremote connect $port rm :src/button.py
    python -m mpremote connect $port rm :src/config.py
    python -m mpremote connect $port rm :src/functions.py
    python -m mpremote connect $port rm :src/lcd_api.py
    python -m mpremote connect $port rm :src/lcd.py
    python -m mpremote connect $port rm :src/led.py
    python -m mpremote connect $port rm :src/machine_i2c_lcd.py
    python -m mpremote connect $port rm :src/relay.py
    python -m mpremote connect $port rm :src/rlock.py
    python -m mpremote connect $port rm :src/temp.py
    python -m mpremote connect $port rm :src/wifi.py
    python -m mpremote connect $port rmdir :src

    python -m mpremote connect $port rm :web/index.html
    python -m mpremote connect $port rm :web/styles.css
    python -m mpremote connect $port rmdir :web
    Write-Host "Projektdateien entfernt"
}

function CopyProjectFiles {
    Write-Host "Kopiere Projektdateien..."
    python -m mpremote connect $port cp ./boot.py :boot.py
    python -m mpremote connect $port cp ./main.py :main.py
    python -m mpremote connect $port cp ./webserver.py :webserver.py
    if ($config) {
        Write-Host "Kopiere config.json"
        python -m mpremote connect $port cp ./config.json :config.json
    }
    python -m mpremote connect $port cp ./error.log :error.log

    Write-Host "  Erstelle utils..."
    python -m mpremote connect $port mkdir utils
    python -m mpremote connect $port cp ./utils/get_bool.py :utils/get_bool.py
    python -m mpremote connect $port cp ./utils/get_float.py :utils/get_float.py
    python -m mpremote connect $port cp ./utils/get_int.py :utils/get_int.py
    python -m mpremote connect $port cp ./utils/log.py :utils/log.py
    python -m mpremote connect $port cp ./utils/log_level.py :utils/log_level.py

    Write-Host "  Erstelle src..."
    python -m mpremote connect $port mkdir src
    python -m mpremote connect $port cp ./src/button.py :src/button.py
    python -m mpremote connect $port cp ./src/config.py :src/config.py
    python -m mpremote connect $port cp ./src/functions.py :src/functions.py
    python -m mpremote connect $port cp ./src/lcd_api.py :src/lcd_api.py
    python -m mpremote connect $port cp ./src/lcd.py :src/lcd.py
    python -m mpremote connect $port cp ./src/led.py :src/led.py
    python -m mpremote connect $port cp ./src/machine_i2c_lcd.py :src/machine_i2c_lcd.py
    python -m mpremote connect $port cp ./src/relay.py :src/relay.py
    python -m mpremote connect $port cp ./src/rlock.py :src/rlock.py
    python -m mpremote connect $port cp ./src/temp.py :src/temp.py
    python -m mpremote connect $port cp ./src/wifi.py :src/wifi.py

     Write-Host "  Erstelle web..."
    python -m mpremote connect $port mkdir web
    python -m mpremote connect $port cp ./web/index.html :web/index.html
    python -m mpremote connect $port cp ./web/styles.css :web/styles.css
    Write-Host "Projektdateien kopiert"
}

function ListProjectFiles {
    Write-Host "Liste Projektdateien..."
    python -m mpremote connect $port ls
    python -m mpremote connect $port ls :utils
    python -m mpremote connect $port ls :src
    python -m mpremote connect $port ls :web
}

cd ..

if (-not $port) {
    Write-Host "Bitte geben Sie einen COM-Port mit '-port COM1' an."
    exit
}

if (-not $copy) { RemoveProjectFiles }

if ($clean) { exit }

CopyProjectFiles

ListProjectFiles
