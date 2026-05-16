"""
Constants used for power monitoring and management.

This module defines constants used to control the behavior of a power management
system. These parameters determine the thresholds and time intervals for monitoring
and switching off devices based on power consumption levels.
"""
POWER_THRESHOLD = 15  # Threshold in Watts
DURATION_BELOW_THRESHOLD = 900  # Time in seconds before monitoring
DURATION_MONITORING_THRESHOLD = 120  # Time in seconds before switching off
PAUSE_CHECK = 5
