import subprocess

# systemd services
SYSTEMD = ["3d_control.service",
           "power_control.service",
           "kobra_bot.service",
           "fan_control.service"]

ACTIONS = ["start", "stop", "restart"]


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
