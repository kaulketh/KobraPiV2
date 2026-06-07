"""
This script monitors the power consumption of a device, such as a printer, using data
from Tasmota-enabled sockets. It implements real-time power monitoring, triggers
actions when power usage falls below a configurable threshold for a sustained period,
and integrates with Telegram for notifications.

The script interacts with Tasmota devices to retrieve power consumption data and can
control devices by turning them off based on the observed power usage patterns. It also
provides updates and notifications through a Telegram bot.

Constants:
    TASMOTA_SOCKETS: dict
        A dictionary of Tasmota-enabled devices, identified by their names.
    POWER_THRESHOLD: int
        The power consumption threshold (in watts) to monitor.
    DURATION_BELOW_THRESHOLD: int
        The duration (in seconds) the power consumption must remain below the threshold
        before actions are triggered.
    DURATION_MONITORING_THRESHOLD: float
        The refined monitoring duration (in seconds) derived from the below-threshold
        duration.
    PAUSE_CHECK: int
        The time pause (in seconds) between successive checks on power usage.
    TELEGRAM_TOKEN: str
        Token for the Telegram bot.
    CHAT_ID: int
        Identifier of the Telegram chat for communication.
    BOT_NAME: str
        Name prefix for the Telegram bot messages.
"""
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
DURATION_BELOW_THRESHOLD = 900  # Time in seconds before monitoring
DURATION_MONITORING_THRESHOLD = DURATION_BELOW_THRESHOLD // 7.5  # Time in seconds before switching off
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
    """
    Monitors and controls printer power consumption by observing its usage against a defined threshold,
    and taking actions such as sending notifications and switching off devices when necessary conditions are met.

    Raises
    ------
    Exception
        If there is an unexpected error during the monitoring loop execution.
    """
    _send_telegram_message("Start observing printer power consumption.")
    below_threshold_start = None

    while True:
        try:
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
                            f"{POWER_THRESHOLD} Watts.\n"
                            f"Precise interval monitoring started.")
                    elif (
                            time.time() - below_threshold_start >=
                            DURATION_BELOW_THRESHOLD):
                        _monitor_value()
                        _send_telegram_message(
                            f"Threshold value has been undercut for more than "
                            f"{int((DURATION_BELOW_THRESHOLD + DURATION_MONITORING_THRESHOLD) // 60)} minutes. "
                            f"Devices will be switched off now.")
                        _turn_off_devices()
                        # reset after switching off
                        below_threshold_start = None
                        _send_telegram_message("Observing done - Standby!")
                else:
                    # Reset if consumption rises above the threshold value
                    below_threshold_start = None
        except Exception as e:
            sys.stdout.write(f"Main loop crashed: {e}\n")
            time.sleep(10)
        # Pause between checks
        time.sleep(PAUSE_CHECK)


def _send_telegram_message(message, retries=3):
    """
    Attempts to send a message via Telegram with a specified number of retries.

    This function interfaces with a Telegram bot to send a message to a specific chat ID. If the sending fails,
    it will retry a defined number of times, waiting for a short delay between each retry. Any errors encountered
    during the process are logged to the system output. If all retry attempts fail, the function returns False.

    Parameters:
    message : str
        The message content to be sent via Telegram.
    retries : int, optional
        The number of retry attempts for sending the message (default is 3).

    Returns:
    bool
        True if the message is successfully sent, False if all retry attempts fail.
    """
    for attempt in range(retries):
        try:
            bot.sendMessage(CHAT_ID, f"{BOT_NAME}\n{message}")
            return True

        except Exception as e:
            sys.stdout.write(
                f"Telegram error ({attempt + 1}/{retries}): {e}\n")

            if attempt < retries - 1:
                time.sleep(2)

    return False


def _monitor_value(get_value=POWER_THRESHOLD,
                   duration=DURATION_MONITORING_THRESHOLD):
    """
    Monitors a value over time to detect if it remains constant for a specified duration or decreases.

    This function repeatedly checks the output of the `get_value` function and evaluates whether the observed value
    has decreased or remained constant for the specified `duration`. If the value decreases or remains constant
    for the given `duration`, corresponding notifications and actions are triggered.

    Parameters:
        get_value: Callable
            A function or callable that returns the current value being monitored.
        duration: float
            The monitoring duration, in seconds, for which the value should stay constant before triggering a reaction.
    """
    last_value = get_value
    start_time = time.time()
    _send_telegram_message(
        f"Monitor power if it remains constant "
        f"for {int(duration)} seconds or decreases.")
    while True:

        current_value = get_value

        if current_value < last_value:
            sys.stdout.write(
                "Value has decreased, reacting immediately!\n")
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
