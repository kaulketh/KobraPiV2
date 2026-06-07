"""
A module to initialize and manage fan control based on temperature thresholds.

This script initializes fan control by configuring the fan pin, temperature
thresholds, and polling interval. The control is implemented through the
FanControl class which is imported from the control module. Configuration
values are fetched from the config module. Errors during execution are logged
to standard error with the traceback details.
"""
import sys
import traceback

import config
from control import FanControl

if __name__ == '__main__':
    try:
        FanControl(fan_pin=config.FAN_PIN,
                   thresholds=(config.MIN, config.MAX),
                   poll=config.CHECK_INTERVAL)
    except Exception as e:
        t = traceback.format_exc()
        sys.stderr.write(f"!!! Error occurs\n{t}\n{e}\n")
