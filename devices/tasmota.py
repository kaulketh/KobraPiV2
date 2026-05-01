"""
This module provides utilities to interact with Tasmota smart sockets.

It includes functionality to retrieve the states and power consumption of
connected devices, as well as manage device communication over HTTP.

Attributes:
    TASMOTA_SOCKETS (dict): A dictionary containing information about
        Tasmota smart sockets, including their names and URLs.
"""
import sys

import requests

import auth

TASMOTA_SOCKETS = {
    "main": {"name": "Main", "url": f"http://{auth.tsm_ips[0]}/cm"},
    "cams": {"name": "Video", "url": f"http://{auth.tsm_ips[1]}/cm"},
    "lights": {"name": "Light", "url": f"http://{auth.tsm_ips[2]}/cm"},
    "printer": {"name": "Printer", "url": f"http://{auth.tsm_ips[3]}/cm"}
}


def sockets():
    return {device_id: {
        "name": info["name"],
        "state": fetch_state(device_id),
        "power": fetch_power(device_id)
    }
        for device_id, info in TASMOTA_SOCKETS.items()
    }


def fetch_state(device_id):
    try:
        response = requests.get(TASMOTA_SOCKETS[device_id]["url"],
                                params={"cmnd": "Power"})
        response.raise_for_status()
        state = response.json().get("POWER1", "OFF")
        return "on" if state == "ON" else "off"
    except requests.RequestException as e:
        sys.stderr.write(f"Error during request device {device_id}: {e}\n")
        return "unknown"


def fetch_socket_states():
    states = {}
    for device_id, info in TASMOTA_SOCKETS.items():
        try:
            response = requests.get(info["url"], params={"cmnd": "Power"})
            response_data = response.json()
            sys.stdout.write(
                f"{info['url']} {response_data} "
                f"{response_data.get('POWER1')}\n")
            states[device_id] = {
                "name": info["name"],
                "state": "on" if response_data.get("POWER1") == "ON" else "off"
            }
        except requests.RequestException:
            states[device_id] = {
                "name": info["name"],
                "state": "unknown"
            }
    return states


def fetch_power(dev_id):
    try:
        resp = requests.get(TASMOTA_SOCKETS[dev_id]["url"],
                            params={"cmnd": "Status 8"})
        resp.raise_for_status()
        pwr = resp.json().get("StatusSNS", {}).get("ENERGY", {}).get("Power")
        return float(pwr) if pwr is not None else 0.0
    except requests.RequestException as e:
        sys.stderr.write(
            f"Error during requesting power data of device {dev_id}: {e}\n")
        return 0.0
