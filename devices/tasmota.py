import sys

import requests

# Sockets
TASMOTA_SOCKETS = {
    "main": {"name": "Main", "url": "http://192.168.0.114/cm"},
    "cams": {"name": "Video", "url": "http://192.168.0.111/cm"},
    "lights": {"name": "Light", "url": "http://192.168.0.113/cm"},
    "printer": {"name": "Printer", "url": "http://192.168.0.112/cm"}
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


def fetch_power(device_id):
    try:
        response = requests.get(TASMOTA_SOCKETS[device_id]["url"],
                                params={"cmnd": "Status 8"})
        response.raise_for_status()
        pwr = response.json().get("StatusSNS", {}).get("ENERGY", {}).get(
            "Power")
        return float(pwr) if pwr is not None else 0.0
    except requests.RequestException as e:
        sys.stderr.write(
            f"Error during requesting power data of device {device_id}: {e}\n")
        return 0.0
