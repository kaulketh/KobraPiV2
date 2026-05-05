import os
import sys
import time
import traceback

import RPi.GPIO as GPIO


class FanControl:

    def __init__(self, fan_pin: int, thresholds: tuple, poll: float):
        GPIO.setwarnings(False)
        self.__RL = 10  # request limit
        self.__wait = poll if poll > self.__RL else self.__RL
        self.__thds = thresholds  # min, max
        self.__pin = fan_pin
        self.__out = sys.stdout
        self.toggle(False)  # Start with the fan off
        self.__temperatures = None
        self.__run()

    def toggle(self, level=None):
        new_level = level if level is not None else not self.__pih
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.__pin, GPIO.OUT)
        GPIO.output(self.__pin, new_level)
        self.__out.write(
            f">>> Toggle GPIO{self.__pin} >> {new_level}\n")

    @property
    def __pih(self) -> bool:
        """
        "Pin Is High", state of GPIO channel (HIGH=1=True or LOW=0=False)
        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.__pin, GPIO.OUT)
        lvl = GPIO.input(self.__pin)
        is_high = bool(lvl)
        self.__out.write(
            f"<<< State GPIO{self.__pin} >> {is_high} ({lvl})\n")
        return is_high

    @property
    def __t_via_file(self) -> float:
        """
        CPU temperature

        Reading the "/sys/class/thermal/thermal_zone0/temp" file, which provides
        the CPU temperature in milli degrees Celsius on a Raspberry Pi, has a
        relatively low impact on system performance compared to using
        vcgencmd measure_temp.
        You can read this file to obtain the CPU temperature quite frequently
        without causing significant overhead. The actual frequency depends on
        your application's requirements, but generally querying this file
        every few seconds (e.g., 1-5 seconds) should not cause any performance
        issues.
        Keep in mind that reading the temperature too frequently might not be
        necessary for many applications.
        Temperature changes relatively slowly compared to other sensor data,
        so intervals of a few seconds should be adequate for most temperature-
        based control systems.
        Always consider balancing the frequency of readings with the actual
        need of your application to avoid unnecessary CPU usage, especially
        if you're performing other resource-intensive tasks simultaneously.
        --Based loosely on ChatGPT--
        """
        _path = "/sys/class/thermal/thermal_zone0/temp"
        with open(_path, "r") as file:
            result = float(file.read()) / 1_000
        self.__out.write(f"<<< {_path} >> {result}\n")
        return result

    @property
    def __t_via_gpu(self) -> float:
        """
        CPU's temperature via GPU core temperature

        Calling "vcgencmd measure_temp" too frequently might not be advisable
        due to potential performance impacts.
        While it's a convenient command to retrieve the Raspberry Pi's
        CPU temperature, querying it too often could cause unnecessary
        overhead. The command vcgencmd measure_temp is a part of the Raspberry
        Pi's firmware and interacts with the VideoCore GPU, which in turn
        reads the CPU's temperature.
        Typically, calling this command every few seconds (e.g., 5 seconds)
        should not cause significant issues.
        However, if you're querying it more frequently (e.g., multiple times
        per second), it might affect the system's performance, especially if
        you're running resource-intensive tasks simultaneously.
        Consider optimizing your temperature reading frequency based on your
        specific application's requirements.
        For most temperature-controlled applications,
        checking the temperature every few seconds (e.g., 5-10 seconds)
        should be sufficient to monitor and control a fan or other cooling
        systems effectively without imposing a notable performance burden on
        the Raspberry Pi.
        --Based loosely on ChatGPT--
        """
        _cmd = "vcgencmd measure_temp"
        result = os.popen(_cmd).readline()
        self.__out.write(f"<<< {_cmd} >> {result}")
        return float(result.replace("temp=", "").replace("'C\n", ""))

    def __run(self):
        def operate(msg_part, level):
            self.toggle(level)
            self.__out.write(f">>> Temperature {msg_part}\n")

        while True:
            # noinspection PyBroadException
            try:
                t1, t2 = self.__t_via_file, self.__t_via_gpu
                high = t1 >= self.__thds[1] or t2 >= self.__thds[1]
                low = t1 <= self.__thds[0] and t2 <= self.__thds[0]

                if high and not self.__pih:
                    operate("NOK, fan on", True)
                if low and self.__pih:
                    operate("OK, fan off", False)

            except Exception as e:
                t = traceback.format_exc()
                self.__out.write(
                    f"!!! {self.__t_via_file}, {self.__t_via_gpu} ")
                sys.stderr.write(
                    f"!!! Interrupted, power off fan! \n{t}\n{e}\n")
                self.__out.write("!!! Interrupted, cancelling...\n")
                self.toggle(False)
                GPIO.cleanup()
            time.sleep(self.__wait)


if __name__ == '__main__':
    pass
