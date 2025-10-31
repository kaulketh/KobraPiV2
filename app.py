import os
import platform
import subprocess
import sys
import time
from datetime import datetime

import psutil
import requests
from PIL import Image, ExifTags
from flask import Flask, jsonify, Blueprint, render_template, redirect, \
    url_for
from flask_cors import CORS

from auth import AUTH, CHAT_ID, KOBRA_BOT
from devices import sockets, TASMOTA_SOCKETS, cameras, setup_cameras, \
    fetch_state, fetch_socket_states, fetch_power
from gunicorn_config import workers
from services import ACTIONS, SYSTEMD, get_info
from www import INDEX, MADE, CAMS, SRVCS, \
    POWER, STATUS, NAVI, ROOT, STR_SLASH, PRIVAT, REPO, REPO_RELEASE, \
    REPO_COMMIT

# Flask configuration
APPLICATION_ROOT = f"{STR_SLASH}{ROOT}"
app = Flask("Kobra2+Control",
            static_url_path=APPLICATION_ROOT,
            static_folder='www/static',
            template_folder='www/templates')
app_host = "0.0.0.0"
app.config["APPLICATION_ROOT"] = APPLICATION_ROOT
CORS(app)
kobra_bp = Blueprint(ROOT, __name__, url_prefix=APPLICATION_ROOT)
images = os.listdir(os.path.join(app.static_folder, "images"))

# setup gallery
global img_orientation
GALLERY = os.path.join(app.static_folder, 'gallery')
THUMBS = os.path.join(GALLERY, 'thumbs')
os.makedirs(THUMBS, exist_ok=True)
gallery = os.listdir(GALLERY)
gallery.sort(reverse=True)
thumbs = []


def __correct_orientation(image_path):
    global img_orientation
    image = Image.open(image_path)
    try:
        for img_orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[img_orientation] == 'Orientation':
                break
        exif = image.getexif()
        if exif is not None and img_orientation in exif:
            if exif[img_orientation] == 3:
                image = image.rotate(180, expand=True)
            elif exif[img_orientation] == 6:
                image = image.rotate(270, expand=True)
            elif exif[img_orientation] == 8:
                image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return image


def __create_thumbnail(image_path, thumbnail_path, size=(200, 150)):
    """correct orientation and create a thumbnail for each gallery image."""
    img = __correct_orientation(image_path)
    img.thumbnail(size)
    img.save(thumbnail_path)


for filename in gallery:
    if filename.endswith(('.jpg', '.png', '.jpeg', '.gif')):
        full_path = os.path.join(GALLERY, filename)
        thumb_path = os.path.join(THUMBS, filename)
        # create a thumbnail if not exists
        if not os.path.exists(thumb_path):
            __create_thumbnail(full_path, thumb_path)
        thumbs.append(filename)
thumbs.sort()


# end setup gallery


def __get_version():
    version_info = ""
    u_str = ""  # "-"

    def commit_hash():
        c_hash = ""
        c_url = REPO_COMMIT
        c_response = requests.get(c_url)
        if c_response.status_code == 200:
            c_hash += c_response.json()["sha"][:7]  # 7 digits only
        else:
            c_hash += u_str
        return c_hash

    url = REPO_RELEASE
    response = requests.get(url)
    if response.status_code == 200:
        version_info += response.json()["tag_name"]
    else:
        version_info += u_str
    return f"{version_info} {commit_hash()}"


# Server routes
# make available in all routes
@kobra_bp.app_context_processor
def inject_context():
    return dict(
        version=__get_version(),
        navigation=NAVI,
        status_path=STATUS.path,
        pfx=APPLICATION_ROOT,
        images=images,
        gallery=gallery,
        thumbnails=thumbs,
        repo=REPO
    )


# custom jinja2 filter
@kobra_bp.app_template_filter('gallery_image')
def gallery_image(file):
    name, _ = file.rsplit('.', 1)  # remove extension
    parts = name.split(' ', 1)  # split after 1st space
    if len(parts) == 2:
        return f"{parts[0]}<br>{parts[1]}"
    return parts[0]  # name if no spaces


# GET requests
@kobra_bp.route(CAMS.path, methods=['GET'])
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


@kobra_bp.route(INDEX.path, methods=['GET'])
def index():
    return render_template(INDEX.template, active_page=INDEX.id,
                           title=INDEX.title)


@kobra_bp.route(MADE.path, methods=['GET'])
def made():
    return render_template(
        MADE.template,
        active_page=MADE.id,
        title=MADE.title,
        info=MADE.info)


@kobra_bp.route(POWER.path, methods=['GET'])
def power():
    devs = fetch_socket_states()
    return render_template(
        POWER.template,
        active_page=POWER.id,
        devices=devs,
        title=POWER.title)


@kobra_bp.route(PRIVAT.path, methods=['GET'])
def privacy():
    return render_template(
        PRIVAT.template,
        active_page=PRIVAT.id,
        title=PRIVAT.title)


@kobra_bp.route(SRVCS.path, methods=['GET'])
def services():
    statuses = {service: get_info(service) for service in SYSTEMD}
    return render_template(
        SRVCS.template,
        active_page=SRVCS.id,
        title=SRVCS.title,
        service_statuses=statuses)


# POST requests
@kobra_bp.route(f"{SRVCS.path}/<action>/<service>", methods=['POST'])
@AUTH.login_required
def control(action, service):
    if service in SYSTEMD and action in ACTIONS:
        subprocess.run(['sudo', 'systemctl', action, service])
        url = f"{ROOT}.{SRVCS.id}" if service != SYSTEMD[
            0] else f"{ROOT}.{INDEX.id}"
        return redirect(url_for(url))


@kobra_bp.route(f"{STR_SLASH}toggle/<device_id>", methods=["POST"])
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
@kobra_bp.route(STATUS.path, methods=["GET"])
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


@kobra_bp.route('/debug')
def debug():
    return render_template("debug.html",
                           timestamp=datetime.now().strftime(
                               "%Y-%m-%d %H:%M:%S"),
                           osinfo=platform.platform(),
                           python_version=platform.python_version(),
                           hostname=os.uname().nodename
                           )


# Register kobra blueprint and filter for run
app.register_blueprint(kobra_bp)
app.jinja_env.filters['gallery_image'] = gallery_image

# Message Gunicorn's workers start
if os.getpid() % workers == 0:
    KOBRA_BOT.sendMessage(CHAT_ID,
                          f"[Webserver] "
                          f"https://kauli.hopto.org/kobra\n"
                          f"{workers} "
                          f"workers are doing the job.")

if __name__ == "__main__":
    app.run(debug=False, host=app_host, threaded=True)
