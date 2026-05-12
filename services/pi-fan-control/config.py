"""
Controls the fan based on temperature thresholds.

This script defines constants for controlling a fan using GPIO pins based
on temperature readings. It specifies the pin used to control the fan,
temperature thresholds for turning the fan on and off, and the interval
at which temperature checks should occur.

Attributes:
    FAN_PIN (int): The GPIO pin (BCM mode) controlling the fan.
    MAX (int): The maximum temperature in degrees Celsius. The fan is
        turned on if the temperature exceeds this value.
    MIN (int): The minimum temperature in degrees Celsius. The fan is
        turned off if the temperature drops below this value.
    CHECK_INTERVAL (int): The interval in seconds for checking the
        temperature. Should be greater than 10.
"""
FAN_PIN = 27  # BCM
# temperature thresholds
MAX = 68
MIN = 63
CHECK_INTERVAL = 30  # >10 !!!
