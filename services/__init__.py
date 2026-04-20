"""
Module for managing system services using systemctl.

This module provides utility functions to start, stop, restart, and retrieve
information about system services by interfacing with systemctl. The functions
in this module require superuser privileges to perform their actions.

Attributes:
ACTIONS: A tuple containing valid service actions, including 'stop', 'start',
         and 'restart'.
STR_ACTIVE: A string constant representing the active state of a service.
STR_INACTIVE: A string constant representing the inactive state of a service.
SYSTEMD: A tuple containing systemd authentication credentials sourced
         from the auth module.
"""
import subprocess
from time import sleep

import auth

ACTIONS = "stop", "start", "restart", "enable", "disable"
STR_ACTIVE = "active"
STR_INACTIVE = "inactive"



def __get_pro_state(service, name, prop_des=None):
    return subprocess.run(['systemctl', name, service, prop_des],
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
    description = __get_pro_state(service, "show", "--property=Description")
    description = description.replace("Description=", "").strip()
    return {"status": state, "enabled": enabled, "description": description}


def ensure_running(service):
    sleep_time = 3

    def is_active():
        return get_info(service)["status"] == STR_ACTIVE

    if not is_active():
        if get_info(service)["enabled"] == "enabled":
            restart(service)
            sleep(sleep_time)
            if is_active():
                return
        else:
            enable(service)
            if get_info(service)["enabled"] == "enabled":
                start(service)
                sleep(sleep_time)
                if is_active():
                    return
