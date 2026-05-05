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
