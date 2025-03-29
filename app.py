import os
import platform
import subprocess
import sys
import time

import psutil
import requests
from flask import Flask, jsonify, Blueprint, render_template, redirect, \
    url_for
from flask_cors import CORS

from auth import AUTH, CHAT_ID
from devices import sockets, TASMOTA_SOCKETS, cameras, setup_cameras, \
    fetch_state, fetch_socket_states, fetch_power
from gunicorn_config import workers
from services import ACTIONS, SYSTEMD, get_service_status
from www import ABOUT, INDEX, MADE, CAMS, SRVCS, \
    POWER, STATUS, NAVI, ROOT, SLASH

VERSION = "101274d9"

# Flask configuration
APPLICATION_ROOT = f"{SLASH}{ROOT}"
app = Flask("Kobra2+Control",
            static_url_path=APPLICATION_ROOT,
            static_folder='www/static',
            template_folder='www/templates')
app_host = "0.0.0.0"
app.config["APPLICATION_ROOT"] = APPLICATION_ROOT
CORS(app)
kobra = Blueprint(ROOT, __name__, url_prefix=APPLICATION_ROOT)
images = os.listdir(os.path.join(app.static_folder, "images"))
gallery = os.listdir(os.path.join(app.static_folder, "gallery"))


# Server routes
# make available in all routes
@kobra.app_context_processor
def inject_context():
    return dict(
        version=VERSION,
        navigation=NAVI,
        status_path=STATUS.path,
        pfx=APPLICATION_ROOT,
        images=images,
        gallery=gallery
    )


# page requests
@kobra.route(ABOUT.path, methods=['GET'])
def about():
    return render_template(
        ABOUT.template,
        active_page=ABOUT.id,
        title=ABOUT.title)


@kobra.route(CAMS.path, methods=['GET'])
def cams():
    cams_on = fetch_power(CAMS.id) > 0
    if cams_on:
        setup_cameras()
        _cameras = cameras()
    else:
        _cameras = {}
    return render_template(
        CAMS.template,
        active_page=CAMS.id,
        title=CAMS.title,
        info=CAMS.info,
        hint=CAMS.hint,
        cams_on=cams_on,
        cams=_cameras)


@kobra.route(INDEX.path, methods=['GET'])
def index():
    return render_template(INDEX.template, active_page=INDEX.id,
                           title=INDEX.title)


@kobra.route(MADE.path, methods=['GET'])
def made():
    return render_template(
        MADE.template,
        active_page=MADE.id,
        title=MADE.title,
        info=MADE.info)


@kobra.route(POWER.path, methods=['GET'])
def power():
    devs = fetch_socket_states()
    return render_template(
        POWER.template,
        active_page=POWER.id,
        devices=devs,
        title=POWER.title)


@kobra.route(SRVCS.path, methods=['GET'])
def services():
    statuses = {service: get_service_status(service) for service in SYSTEMD}
    return render_template(
        SRVCS.template,
        active_page=SRVCS.id,
        title=SRVCS.title,
        service_statuses=statuses)


# POST requests
@kobra.route(f"{SRVCS.path}/<action>/<service>", methods=['POST'])
@AUTH.login_required
def control(action, service):
    if service in SYSTEMD and action in ACTIONS:
        subprocess.run(['sudo', 'systemctl', action, service])
        url = f"{ROOT}.{SRVCS.id}" if service != SYSTEMD[
            0] else f"{ROOT}.{INDEX.id}"
        return redirect(url_for(url))


@kobra.route(f"{SLASH}toggle/<device_id>", methods=["POST"])
@AUTH.login_required
def toggle(device_id):
    if device_id not in TASMOTA_SOCKETS:
        return jsonify({"error": "unknown device"}), 404

    current_state = fetch_state(device_id)
    if current_state == "unknown":
        return jsonify({"error": "device not reachable"}), 500

    new_state = "OFF" if current_state == "on" else "ON"

    try:
        response = requests.get(TASMOTA_SOCKETS[device_id]["url"],
                                params={"cmnd": f"Power1 {new_state}"})
        response.raise_for_status()
        return jsonify({"state": "on" if new_state == "ON" else "off"})
    except requests.RequestException as e:
        sys.stderr.write(f"Error during toggling device {device_id}: {e}\n")
        return jsonify({"error": "Toggling failed"}), 500
    finally:
        try:
            if current_state == "off" and device_id == CAMS.id:
                setup_cameras()
        except requests.exceptions.ConnectionError as e:
            sys.stderr.write(f"Error during update camera devices: {e}\n")


# repeating status request
@kobra.route(STATUS.path, methods=["GET"])
def status():
    def get_cpu_temp():
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return round(int(f.read()) / 1000, None)  # temperature in °C
        except FileNotFoundError:
            return None  # if not available

    uptime_seconds = time.time() - psutil.boot_time()
    uptime = time.strftime("%Hh %Mm %Ss", time.gmtime(uptime_seconds))

    return jsonify(
        {"devices": sockets(),
         "system": {
             "cpu": round(psutil.cpu_percent(), None),
             "cpuTemp": get_cpu_temp(),
             "cpuCores": psutil.cpu_count(logical=False),
             "cpuThreads": psutil.cpu_count(logical=True),
             "cpuFq": psutil.cpu_freq().current if psutil.cpu_freq() else None,
             "ram": round(psutil.virtual_memory().percent, None),
             "ramGB": round(psutil.virtual_memory().total / (1024 ** 3), None),
             "os": platform.system(),
             "osVersion": platform.release(),
             "kernel": platform.version(),
             "uptime": uptime
         }
         }
    )


# Register kobra blueprint for run
app.register_blueprint(kobra)

# Message Gunicorn's workers start
if os.getpid() % workers == 0:
    kobra_bot.sendMessage(CHAT_ID,
                          f"[Webserver] "
                          f"https://kauli.hopto.org/kobra\n"
                          f"{workers} "
                          f"workers are doing the job.")

if __name__ == "__main__":
    app.run(debug=False, host=app_host, threaded=True)
