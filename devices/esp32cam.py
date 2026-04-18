"""
This module provides functionality to set up and retrieve information about ESP32 cameras.

The module supports configuring camera parameters such as resolution, quality, and clock
frequency, and allows accessing metadata about connected ESP32 cameras. It interacts
with external systems to fetch the state of cameras and sends HTTP requests to configure
the cameras.

Attributes:
    CAMERA_CLOCK (int): Clock frequency for the ESP32 cameras, with a maximum of 20.
    CAMERA_QUALITY (int): Quality setting for the ESP32 cameras, ranging between 4-63.
    CAMERA_RESOLUTION (str): Default resolution identifier for the ESP32 cameras.
    CAMERA_RESOLUTIONS (dict): A mapping of resolution identifiers to their respective
        attributes such as value, width, and height.
    CAMERA_RES (int): Numerical value of the default camera resolution.
    CAMERA_WIDTH (int): Width of the default camera resolution.
    CAMERA_HEIGHT (int): Height of the default camera resolution.
    CAMERA_REQUESTS (dict): Mapping of camera setup actions to their corresponding
        HTTP request URLs.
    ESP32_CAMERAS (dict): Dictionary containing information about ESP32 cameras, such
        as name and IP address.

Functions:
    setup_cameras(): Configures the connected cameras based on predefined settings
        if the camera state is enabled. Handles any connection or configuration errors.
    cameras(): Retrieves metadata about the configured ESP32 cameras, including their
        dimensions, names, and identifiers.
"""
import sys

import requests

import auth
from .tasmota import fetch_state

CAMERA_CLOCK = 10  # XCLK max 20
CAMERA_QUALITY = 4  # 4-63
CAMERA_RESOLUTION = "VGA"

CAMERA_RESOLUTIONS = {
    "VGA": {"value": 10, "width": 640, "height": 480},
    "SVGA": {"value": 11, "width": 800, "height": 600},
    "XGA": {"value": 12, "width": 1024, "height": 768},
    "HD": {"value": 13, "width": 1280, "height": 720},
    "SXGA": {"value": 14, "width": 1280, "height": 1024},
    "UXGA": {"value": 15, "width": 1600, "height": 1200}
}

CAMERA_RES = CAMERA_RESOLUTIONS.get(CAMERA_RESOLUTION).get("value")
CAMERA_WIDTH = CAMERA_RESOLUTIONS.get(CAMERA_RESOLUTION).get('width')
CAMERA_HEIGHT = CAMERA_RESOLUTIONS.get(CAMERA_RESOLUTION).get('height')

CAMERA_REQUESTS = {
    "resolution": f"/control?var=framesize&val={CAMERA_RES}",
    "quality": f"/control?var=quality&val={CAMERA_QUALITY}",
    "xclk": f"/xclk?xclk={CAMERA_CLOCK}"
}

ESP32_CAMERAS = {
    "cam1": {"name": "Left", "ip": auth.cam_ips[0]},
    "cam2": {"name": "Back", "ip": auth.cam_ips[1]},
    "cam3": {"name": "Right", "ip": auth.cam_ips[2]}
}


def setup_cameras():
    if fetch_state("cams") == "on":
        for _, info in ESP32_CAMERAS.items():
            try:
                sys.stdout.write(f"#### Camera {info['ip']}\n")
                for key in list(CAMERA_REQUESTS.keys()):
                    url = f"http://{info['ip']}{CAMERA_REQUESTS.get(key)}"
                    requests.get(url)
                    sys.stdout.write(f"\tsetup {key} {url}\n")
            except requests.RequestException:
                sys.stderr.write(f"Error: {info['ip']}\n")
    else:
        pass


def cameras():
    cams = {}
    for cam, info in ESP32_CAMERAS.items():
        cams[info['ip']] = {}
        cams[info['ip']]["width"] = CAMERA_WIDTH
        cams[info['ip']]["height"] = CAMERA_HEIGHT
        cams[info['ip']]['name'] = info['name']
        cams[info['ip']]['sfx'] = cam
    return cams
