"""
This module manages the configuration and setup of ESP32 cameras and provides
functionality for initializing their parameters and retrieving camera
information.

The module defines default configurations for camera settings such as clock,
quality, and resolution. It facilitates communication with remote ESP32
cameras by sending setup requests and retrieving configuration details.

Attributes:
    CAMERA_CLOCK (int): External clock frequency for the camera in MHz.
    CAMERA_QUALITY (int): Quality level for the camera images (range 4-63).
    CAMERA_RESOLUTION (str): Default camera resolution identifier.
    CAMERA_RESOLUTIONS (dict): Mapping of resolution identifiers to their
        attributes including value, width, and height.
    CAMERA_RES (int): Resolution value corresponding to CAMERA_RESOLUTION.
    CAMERA_WIDTH (int): Width of the camera resolution in pixels.
    CAMERA_HEIGHT (int): Height of the camera resolution in pixels.
    CAMERA_REQUESTS (dict): URLs for configuring the camera settings.
    ESP32_CAMERAS (dict): Dictionary of configured ESP32 cameras with their
        names and IP addresses.

Functions:
    setup_cameras():
        Configures connected ESP32 cameras based on predefined settings if
        the camera group state is "on".

    cameras():
        Retrieves metadata regarding the configured ESP32 cameras.

"""
import sys

import requests

import auth
from .tasmota import fetch_state

CAMERA_CLOCK = 10  # XCLK max 20
CAMERA_QUALITY = 4  # 4-63
CAMERA_RESOLUTION = "XGA"

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
