"""
Provides functionality to control IoT devices, retrieve snapshots, and manage services via a Telegram bot.

This module includes functions to handle incoming messages and button clicks on the Telegram bot, toggle IoT devices,
and retrieve statuses for systemd services and connected devices. It also provides methods for capturing
snapshots from cameras and sending notifications or updates to the bot user.

Functions:
- __service_keyboard: Generates the keyboard for managing systemd services.
- __power_keyboard: Generates the keyboard for controlling power consumption and devices.
- _take_snapshots: Captures and rotates snapshots from connected cameras.
- _toggle_tasmota: Toggles the state of a Tasmota-configured device.
- _toggle_service: Starts or stops a systemd service based on its current state.
- _get_pwr: Retrieves power consumption data for a given IoT device.
- admin: Checks if the given chat ID matches the authorized admin ID.
- state_update: Gathers and sends the current status of services and devices to the bot.
- on_message: Handles incoming messages sent to the Telegram bot.
- on_callback_query: Handles button clicks received by the Telegram bot.
- main: Runs the bot's update handling and polling loop.
"""
import io
import os
import sys
import time
import traceback

import requests
from PIL import Image
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

# add a parent directory (..) to sys.path to avoid possible import problems
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import auth
import devices
import services

kobra_bot = auth.KOBRA_BOT
chat_id = auth.CHAT_ID

BOT_NAME = "[Printer control] "
BOT_NAME_VIEW = "[3D print area] "
STATE_CMD = "start", "/start", "/status", "status", "/state", "state"
POWER_ON_CMD = "on", "power on", "power_on", "start", "start power", "start power on"
POWER_OFF_CMD = "off", "power off", "power_off", "stop", "stop power", "stop power off"
cams = devices.ESP32_CAMERAS
socks = devices.TASMOTA_SOCKETS
srvcs = auth.systemd

global cams_powered

icon_na = "\U000026AB"  # black
icon_off = "\U000026AA"  # heavy white
icon_on = "\U0001F7E0"  # orange
icon_failed = "\U00002B55"  # heavy red
icon_active = "\U0001F7E2"  # green
emoticon_confused = "\U0001F615"
emoticon_rolling_eyes = "\U0001F644"
emoticon_worried = "\U0001F61F"


def __service_keyboard():
    status_text = "_Systemd services_\n"
    btns = []
    log = ""
    for s in srvcs:
        state = services.get_info(s)['status']
        # "active", "inactive", "failed", etc.
        if state == services.STR_ACTIVE:
            icon = icon_active
        elif state == services.STR_INACTIVE:
            icon = icon_off
        else:
            icon = icon_failed
        text = f"{icon} {s}"
        log += f"{s}={state}\n"
        btns.append(InlineKeyboardButton(text=f"{text}",
                                         callback_data=f"service:{s}"))
    mrkup = InlineKeyboardMarkup(inline_keyboard=[btns])
    sys.stdout.write(log)
    return status_text, mrkup


def __power_keyboard():
    global cams_powered
    cams_powered = False
    tasmota_btns = []
    snapshot_btn = [
        InlineKeyboardButton(text="Print area", callback_data="snapshots")]

    status_text = f"_Consumption_\n"
    log = ""
    for key, data in socks.items():
        pwr = _get_pwr(data['url'])
        if pwr == "N/A":
            icon = icon_na
        elif pwr > 0:
            icon = icon_on
        else:
            icon = icon_off
        if data['name'] == "Video":
            cams_powered = pwr > 0
        status_text += f"{data['name']} {pwr}W | "
        log += f"{data['name']} {pwr}W\n"
        tasmota_btns.append(
            InlineKeyboardButton(text=f"{icon} {data['name']}",
                                 callback_data=f"tasmota:{key}"))
        time.sleep(.500)
    # Snapshot button only when cams are powered!
    if cams_powered:
        mrkup = InlineKeyboardMarkup(
            inline_keyboard=[tasmota_btns, snapshot_btn])
    else:
        mrkup = InlineKeyboardMarkup(inline_keyboard=[tasmota_btns])
    sys.stdout.write(log)
    return status_text, mrkup


def _take_snapshots(cid, loop_delay=1):
    for cam, props in cams.items():
        try:
            img_url = f"http://{cams.get(cam).get('ip')}/capture"
            response = requests.get(img_url, timeout=5)

            if response.status_code == 200:
                filename = f"snapshot{cams.get(cam).get('name')}.jpg"
                with open(filename, "wb") as f:
                    f.write(response.content)

                # load picture and rotate clockwise 90°
                image = Image.open(filename)
                rotated_image = image.rotate(-90, expand=True)

                # store into Bytes object to send directly
                image_io = io.BytesIO()
                rotated_image.save(image_io, format="JPEG")
                image_io.seek(0)
                # send
                kobra_bot.sendPhoto(
                    cid,
                    photo=image_io,
                    caption=f"{BOT_NAME_VIEW} "
                            f"{cams.get(cam).get('name')} view",
                    disable_notification=True)
            else:
                kobra_bot.sendMessage(cid,
                                      f"{BOT_NAME_VIEW}\n"
                                      f"Error when retrieving the image"
                                      f"({cams.get(cam).get('name')})")
        except Exception as e:
            sys.stderr.write(f"{e}\n")
            kobra_bot.sendMessage(
                cid,
                f"{BOT_NAME_VIEW} "
                f"couldn't take snapshot from "
                f"{cams.get(cam).get('name').lower()}")
        finally:
            time.sleep(loop_delay)


def _toggle_tasmota(cid, socket_key, delay=3):
    if admin(cid):
        socket = socks[socket_key]
        toggle_url = f"{socket['url']}?cmnd=Power TOGGLE"
        requests.get(toggle_url)
        time.sleep(delay)


def _toggle_service(cid, service, delay=3):
    status = services.get_info(service)['status']
    sys.stdout.write(f"{service} is {status}\n")
    if admin(cid):
        if status == services.STR_ACTIVE:
            services.stop(service)
        if status == services.STR_INACTIVE:
            services.restart(service)
    sys.stdout.write(
        f"change state of {service} to "
        f"{services.get_info(service)['status']}\n")
    time.sleep(delay)


def _get_pwr(url):
    pwr_url = f"{url}?cmnd=Status%208"
    rspns = requests.get(pwr_url).json()
    return rspns.get("StatusSNS", {}).get("ENERGY", {}).get("Power", "N/A")


def admin(ci):
    return str(ci) == chat_id


def state_update(cid):
    if admin(cid):
        headline = "*Gathering status information...*\n"
        kobra_bot.sendMessage(cid, headline, parse_mode="Markdown")
        pt, pm = __power_keyboard()
        st, sm = __service_keyboard()
        kobra_bot.sendMessage(cid, st, reply_markup=sm, parse_mode="Markdown")
        kobra_bot.sendMessage(cid, pt, reply_markup=pm, parse_mode="Markdown")


def on_message(msg):
    """Responds to incoming messages"""
    cid = msg["chat"]["id"]
    text = msg.get("text", "").lower()
    if admin(cid):
        sys.stdout.write(f"Message from {cid}: {text}\n")
        if text in STATE_CMD:
            state_update(cid)
        elif text in POWER_ON_CMD:
            # TODO: power on light, printer and cameras
            kobra_bot.sendMessage(cid, emoticon_rolling_eyes)
        elif text in POWER_OFF_CMD:
            # TODO power off all but not main power supply
            kobra_bot.sendMessage(cid, emoticon_rolling_eyes)

        else:
            kobra_bot.sendMessage(cid, emoticon_rolling_eyes)
    else:
        kobra_bot.sendMessage(cid, emoticon_worried)


def on_callback_query(msg):
    """Responds to button clicks"""
    query_id, cid, data = (msg["id"],
                           msg["message"]["chat"]["id"],
                           msg["data"])
    if admin(cid):
        sys.stdout.write(f"Button pressed: {data}\n")

        if data.startswith("tasmota:"):
            socket_key = data.split(":")[1]
            kobra_bot.answerCallbackQuery(
                query_id, text=f"Toggle {socket_key.title()}.")
            _toggle_tasmota(cid, socket_key)
            sys.stdout.write(f"toggle socket {socket_key}\n")
        if data.startswith("service:"):
            service = data.split(":")[1]
            kobra_bot.answerCallbackQuery(
                query_id, text=f"Toggle {service}")
            _toggle_service(cid, service)
            sys.stdout.write(f"toggle service {service}\n")
        elif data == "snapshots":
            global cams_powered
            if cams_powered:
                msg = "Took snapshots."
                _take_snapshots(cid)
            else:
                msg = "Make sure that cameras are available and switched on!"
            kobra_bot.answerCallbackQuery(query_id, text=msg)
            sys.stdout.write(f"{msg}\n")
    state_update(cid)


def main():
    def handle_update(update):
        if 'my_chat_member' in update:
            sys.stderr.write(f"Ignoring 'my_chat_member' update: {update}\n")
            return  # avoid crash
        if 'message' in update:
            on_message(update['message'])
        elif 'callback_query' in update:
            on_callback_query(update['callback_query'])

    def poll_updates():
        last_update_id = None
        backoff = 1  # start with 1 second
        max_backoff = 60  # cap at 60 seconds
        while True:
            try:
                updates = kobra_bot.getUpdates(
                    offset=last_update_id,
                    timeout=10,
                    allowed_updates=['message', 'callback_query'])

                # If we reach this point → success → reset backoff
                backoff = 1
                for update in updates:
                    # increase offset
                    last_update_id = update["update_id"] + 1
                    handle_update(update)

            except KeyboardInterrupt:
                sys.stderr.write('Loop interrupted\n')
                exit()

            except Exception as e:
                sys.stderr.write(
                    f"Polling error: {traceback.format_exc()}\n")
                sys.stderr.write(f"{e}\n")

                # Apply exponential backoff
                sys.stderr.write(f"Retrying in {backoff} seconds...\n")
                time.sleep(backoff)  # cooldown

                # Increase backoff for next time
                backoff = min(backoff * 2, max_backoff)
                continue  # DO NOT EXIT

            # Normal delay between polls
            time.sleep(1)  # avoid API overload

    msg = "Bot is running..."
    text = f"{BOT_NAME}\n{msg}"
    kobra_bot.sendMessage(chat_id=chat_id, text=text)
    sys.stdout.write(f"{text}\n")
    state_update(chat_id)
    # main loop
    poll_updates()


if __name__ == '__main__':
    main()
