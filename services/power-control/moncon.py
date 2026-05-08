import os
import sys
import time

import requests
import telepot

# add a parent directory (..) to sys.path to avoid possible import problems
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import auth
import devices

TASMOTA_SOCKETS = devices.TASMOTA_SOCKETS
POWER_THRESHOLD = 15  # Threshold in Watts
DURATION_BELOW_THRESHOLD = 600  # Time in seconds before monitoring
DURATION_MONITORING_THRESHOLD = 60  # Time in seconds before switching off
PAUSE_CHECK = 5

# Telegram configuration
TELEGRAM_TOKEN = auth.telegram_token
CHAT_ID = auth.telegram_chat_id
bot = telepot.Bot(TELEGRAM_TOKEN)
BOT_NAME = "[Power consumption monitor] "


def _get_power_usage(device_url=TASMOTA_SOCKETS.get("printer").get("url")):
    try:
        response = requests.get(device_url, params={"cmnd": "Status 8"})
        response.raise_for_status()
        data = response.json()
        power = data.get("StatusSNS", {}).get("ENERGY", {}).get("Power")
        return float(power) if power is not None else DURATION_BELOW_THRESHOLD
    except requests.RequestException as e:
        sys.stderr.write(f"Error when retrieving the power consumption: {e}\n")
        return None


def _turn_off_devices(devices=None):
    if devices is None:
        devices = TASMOTA_SOCKETS
    for device in list(devices.keys())[1:]:
        try:
            response = requests.get(
                devices.get(device).get('url'), params={"cmnd": "Power 0"})
            response.raise_for_status()
            message = (f"Device \"{devices.get(device).get('name')}\" "
                       f"switched off.")
            sys.stdout.write(f"{message}\n")
            _send_telegram_message(message)
            time.sleep(PAUSE_CHECK)
        except requests.RequestException as e:
            sys.stderr.write(f"Error during switch-off: {e}\n")


def monitor_and_control():
    _send_telegram_message("Start observing printer power consumption.")
    below_threshold_start = None

    while True:
        power = _get_power_usage()
        if power is None:
            sys.stdout.write("Can't get power consumption!\n")
        else:
            sys.stdout.write(f"Current power consumption: {power} Watts\n")

            if 0 < power <= POWER_THRESHOLD:
                if below_threshold_start is None:
                    below_threshold_start = time.time()
                    _send_telegram_message(
                        f"Printer power consumption is less or equal than "
                        f"{POWER_THRESHOLD} Watts, "
                        f"precise interval monitoring started.")
                elif (
                        time.time() - below_threshold_start >=
                        DURATION_BELOW_THRESHOLD):
                    _monitor_value()
                    _send_telegram_message(
                        f"Threshold value has been undercut for more than "
                        f"{DURATION_BELOW_THRESHOLD // 60} minutes. "
                        f"Devices will be switched off shortly.")
                    _turn_off_devices()
                    # reset after switching off
                    below_threshold_start = None
                    _send_telegram_message("Observing done - Standby!")
            else:
                # Reset if consumption rises above the threshold value
                below_threshold_start = None
        # Pause between checks
        time.sleep(PAUSE_CHECK)


def _send_telegram_message(message):
    bot.sendMessage(CHAT_ID, f"{BOT_NAME}\n{message}")


def _monitor_value(get_value=POWER_THRESHOLD,
                   duration=DURATION_MONITORING_THRESHOLD):
    """
    Monitors a value and triggers a reaction only if it remains constant 
    for 'duration' seconds or decreases.

    :param get_value: Function that returns the current value
    :param duration: Time the value must remain unchanged or decrease
    """
    last_value = get_value
    start_time = time.time()
    _send_telegram_message(
        f"Monitor power if it remains constant "
        f"for {duration} seconds or decreases.")
    while True:
        current_value = get_value

        if current_value < last_value:
            sys.stdout.write("Value has decreased, reacting immediately!\n")
            break
        elif current_value != last_value:
            # Value changed, reset the timer
            start_time = time.time()
            last_value = current_value

        elif time.time() - start_time >= duration:
            sys.stdout.write(
                f"Minimum value ({current_value}W) "
                f"has remained constant for {duration} seconds. "
                f"Triggering reaction.\n")
            break
        time.sleep(0.1)  # Small delay to reduce CPU usage


if __name__ == "__main__":
    monitor_and_control()
