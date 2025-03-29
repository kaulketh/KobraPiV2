import os
import subprocess

import auth

# systemd services
SYSTEMD = [auth.systemd[0], auth.systemd[1], auth.systemd[2], auth.systemd[3]]
ACTIONS = ["start", "stop", "restart"]


def __sudo_control(action, service):
    os.system(f"sudo systemctl {action} {service}")


def start(service):
    __sudo_control(ACTIONS[0], service)


def stop(service):
    __sudo_control(ACTIONS[1], service)


def restart(service: str):
    __sudo_control(ACTIONS[2], service)


def status(service):
    __sudo_control("status", service)


def get_service_status(service):
    status = subprocess.run(['systemctl', 'is-active', service],
                            capture_output=True, text=True).stdout.strip()
    enabled = subprocess.run(['systemctl', 'is-enabled', service],
                             capture_output=True, text=True).stdout.strip()
    description = subprocess.run(
        ['systemctl', 'show', service, '--property=Description'],
        capture_output=True, text=True).stdout.strip()
    description = description.replace("Description=", "").strip()
    return {"status": status, "enabled": enabled, "description": description}
