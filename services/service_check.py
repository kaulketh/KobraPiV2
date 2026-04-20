import auth
from .services import ensure_running

SYSTEMD = auth.systemd[0], auth.systemd[1], auth.systemd[2], auth.systemd[3]

for svc in SYSTEMD:
    ensure_running(svc)
