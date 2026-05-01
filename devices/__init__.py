"""Module for importing ESP32-CAM and Tasmota-related functionalities.

This module aggregates features or functionality from the `esp32cam` and
`tasmota` modules, intended for use in external integrations or applications.

Imported modules:
- esp32cam: Provides tools and utilities for working with ESP32-CAM devices.
- tasmota: Provides access to functions used for integrating Tasmota-based
  devices.
"""
from .esp32cam import *
from .tasmota import *
