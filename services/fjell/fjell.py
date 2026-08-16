import json
import os
import sys
from time import sleep

import adafruit_dht
import board

# to import own necessary modules
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
import power_control
import yeti

SENSOR = adafruit_dht.DHT22(board.D24, use_pulseio=True)
POLLING_INTERVAL = 120  # min 3 seconds
CACHE_FILE = "/tmp/dht_cache.json"

last_humidity = None
last_temperature = None


def load_cached_values():
    global last_humidity, last_temperature

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        last_humidity = data["humidity"]
        last_temperature = data["temperature"]

        sys.stdout.write(
            f"Loaded cached DHT22 values: "
            f"{last_temperature:.1f} °C, "
            f"{last_humidity:.1f} %\n"
        )

    except (FileNotFoundError, KeyError, ValueError, TypeError,
            json.JSONDecodeError):
        sys.stderr.write("No valid cached DHT22 values available.\n")


def save_cached_values(humidity, temperature):
    data = {
        "humidity": humidity,
        "temperature": temperature
    }

    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file)

    except OSError as e:
        sys.stderr.write(
            f"Could not save DHT22 cache: {e}\n"
        )


def get_values() -> tuple:
    global last_humidity, last_temperature

    for attempt in range(3):
        try:
            temperature = SENSOR.temperature
            humidity = SENSOR.humidity

            if temperature is not None and humidity is not None:
                last_temperature = temperature
                last_humidity = humidity

                save_cached_values(
                    humidity,
                    temperature
                )

                break

        except RuntimeError as e:
            sys.stderr.write(
                f"DHT22 read error "
                f"(attempt {attempt + 1}/3): {e}\n"
            )

            sleep(2)

    else:
        sys.stderr.write(
            "DHT22 read failed after 3 attempts. "
            "Using cached values.\n"
        )

    if last_humidity is None or last_temperature is None:
        humidity_str = "--.-%"
        temperature_str = "--.-'C"
    else:
        humidity_str = f"{last_humidity:04.1f}%"
        temperature_str = f"{last_temperature:04.1f}'C"

    return humidity_str, temperature_str


def post_to_fjell(humidity_str, temperature_str):
    summary = (
        f"Printer ON, "
        f"Enclosure temp. {temperature_str}  "
        f"and hum. {humidity_str}"
    )

    sys.stdout.write(f"{summary}\n")
    yeti.FJELL.marquee(summary, yeti.FJELL.mode.once)
    # yeti.FJELL.beep(3500, 500)


def main():
    if power_control.get_power_usage() > 0:
        humidity_str, temperature_str = get_values()

        post_to_fjell(
            humidity_str,
            temperature_str
        )
    sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    load_cached_values()
    while True:
        main()
