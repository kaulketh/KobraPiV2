"""
This module provides utility functions to control and monitor system services using systemd commands.

The functions in this module allow users to start, stop, restart, enable, disable, and retrieve information about
services. It also includes functionality to ensure that a service is running and appropriately enabled.

Functions:
- control_service: Executes a specific action on a given service.
- enable: Enables a service.
- disable: Disables a service.
- start: Starts a service.
- stop: Stops a service.
- restart: Restarts a service.
- get_info: Retrieves information about a service, including its status and description.
- ensure_running: Ensures a service is running and enabled.
"""
import subprocess
import sys
from time import sleep

ACTIONS = "stop", "start", "restart", "enable", "disable"
STR_ACTIVE = "active"
STR_INACTIVE = "inactive"


def __get_pro_state(service, name):
    return subprocess.run(['systemctl', name, service],
                          capture_output=True, text=True).stdout.strip()


def control_service(action: str, service: str):
    subprocess.run(['sudo', 'systemctl', action, service])


def enable(service: str):
    control_service(ACTIONS[3], service)


def disable(service: str):
    control_service(ACTIONS[4], service)


def start(service: str):
    control_service(ACTIONS[1], service)


def stop(service: str):
    control_service(ACTIONS[0], service)


def restart(service: str):
    control_service(ACTIONS[2], service)


def get_info(service):
    state = __get_pro_state(service, "is-active")
    enabled = __get_pro_state(service, "is-enabled")
    des = subprocess.run(
        ['systemctl', "show", service, "--property=Description"],
        capture_output=True, text=True).stdout.strip()
    des = des.replace("Description=", "").strip()
    return {"status": state, "enabled": enabled, "description": des}


def ensure_running(service):
    sleep_time = 3

    def is_active():
        return get_info(service)["status"] == STR_ACTIVE

    if not is_active():
        if get_info(service)["enabled"] == "enabled":
            restart(service)
            sleep(sleep_time)
            if is_active():
                sys.stdout.write(f"Service '{service}' restarted.\n")
                return
        else:
            enable(service)
            if get_info(service)["enabled"] == "enabled":
                start(service)
                sleep(sleep_time)
                if is_active():
                    sys.stdout.write(
                        f"Service '{service}' re-enabled an started.\n")
                    return
    else:
        sys.stdout.write(f"Service '{service}' is running = {is_active()}\n")
        return
