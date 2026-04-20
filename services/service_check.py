"""
A module to ensure specific services are running using systemd and service management tools.

This program iterates over a list of systemd-managed services and ensures that they are in
the running state. It imports authentication and service management modules to aid in this
process.
"""

import os
import sys

# add a parent directory (..) to sys.path to avoid possible import problems
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import auth
import services

if __name__ == '__main__':
    for svc in auth.systemd:
        services.ensure_running(svc)
