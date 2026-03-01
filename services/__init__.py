import os
import subprocess

import auth

ACTIONS = "stop", "start", "restart"
STR_ACTIVE = "active"
STR_INACTIVE = "inactive"
SYSTEMD = auth.systemd[0], auth.systemd[1], auth.systemd[2], auth.systemd[3]


def __sudo_control(action: str, service: str):
    os.system(f"sudo systemctl {action} {service}")


def start(service: str):
    __sudo_control(ACTIONS[1], service)


def stop(service: str):
    __sudo_control(ACTIONS[0], service)


def restart(service: str):
    __sudo_control(ACTIONS[2], service)


def get_info(service):
    state = subprocess.run(['systemctl', 'is-active', service],
                           capture_output=True, text=True).stdout.strip()
    enabled = subprocess.run(['systemctl', 'is-enabled', service],
                             capture_output=True, text=True).stdout.strip()
    description = subprocess.run(
        ['systemctl', 'show', service, '--property=Description'],
        capture_output=True, text=True).stdout.strip()
    description = description.replace("Description=", "").strip()
    return {"status": state, "enabled": enabled, "description": description}
