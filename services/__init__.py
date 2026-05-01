"""
A utility module for managing and monitoring Linux system services using `systemctl`.

This module provides functions to control, monitor, and ensure the stability of system
services. It integrates with Telegram for alert notifications. The module supports
basic service actions such as start, stop, restart, enable, and disable, and also provides
status information about services.

It assumes the presence of an imported `auth` module providing required Telegram credentials
(TELEGRAM_TOKEN and CHAT_ID) and a `bot` module for updating the bot state.
"""
import os
import subprocess
import sys
from time import sleep

import requests

# add a parent directory (..) to sys.path to avoid possible import problems
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import auth
import bot

ACTIONS = "stop", "start", "restart", "enable", "disable"
STR_ACTIVE = "active"
STR_INACTIVE = "inactive"

t_token = auth.TELEGRAM_TOKEN
t_cid = auth.CHAT_ID


def __send_alert(message: str):
    url = f"https://api.telegram.org/bot{t_token}/sendMessage"
    payload = {"chat_id": t_cid, "text": message}
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response:
            bot.state_update(t_cid)
    except Exception as e:
        sys.stderr(f"Telegram error: {e}")


def __get_property(service, name):
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


def get_service_status(service):
    result = "unknown", "unknown"
    try:
        state = __get_property(service, "is-active")
        enabled = __get_property(service, "is-enabled")
        result = state, enabled
    except subprocess.CalledProcessError:
        pass
    return result


def get_service_info(service):
    state, enabled = get_service_status(service)
    des = subprocess.run(
        ['systemctl', "show", service, "--property=Description"],
        capture_output=True, text=True).stdout.strip()
    des = des.replace("Description=", "").strip()
    return {"status": state, "enabled": enabled, "description": des}


def ensure_running(service):
    sleep_time = 3

    def is_active():
        return get_service_info(service)["status"] == STR_ACTIVE

    # Service is running → nothing to do
    if is_active():
        return

    # Service is NOT running → send alert
    __send_alert(
        f"⚠️ Service '{service}' is not active. Attempting recovery...")

    # If enabled → restart
    if get_service_info(service)["enabled"] == "enabled":
        restart(service)
        sleep(sleep_time)
        if is_active():
            __send_alert(
                f"✅ Service '{service}' has been successfully restarted.")
            return
        else:
            __send_alert(f"❌ Service '{service}' could NOT be restarted!")
            return

    # If disabled → enable + start
    enable(service)
    if get_service_info(service)["enabled"] == "enabled":
        start(service)
        sleep(sleep_time)
        if is_active():
            __send_alert(
                f"🔧 Service '{service}' was enabled and started successfully.")
            return
        else:
            __send_alert(
                f"❌ Service '{service}' could NOT be started even after enabling!")
            return
