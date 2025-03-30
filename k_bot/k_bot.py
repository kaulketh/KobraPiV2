import io
import os
import sys
import time
import traceback

import requests
from PIL import Image
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

# This adds the parent directory (..) to sys.path
# so that Python can find own modules.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import auth, devices, services

kobra_bot = auth.KOBRA_BOT
chat_id = auth.CHAT_ID
BOT_NAME = "[Printer control] "
BOT_NAME_VIEW = "[3D print area] "
cams = devices.ESP32_CAMERAS
socks = devices.TASMOTA_SOCKETS
srvcs = services.SYSTEMD

global cams_powered

icon_na = "\U000026AB"  # black
icon_off = "\U000026AA"  # heavy white
icon_on = "\U0001F7E0"  # orange
icon_failed = "\U00002B55"  # heavy red
icon_active = "\U0001F7E2"  # green


def __service_info():
    info = "_Services_\n"
    for s in srvcs:
        name = s.replace('_', " ")  # .replace('.service', '')
        state = services.get_status(s)['status']
        # "active", "inactive", "failed", etc.
        if state == "active":
            icon = icon_active
        elif state == "inactive":
            icon = icon_off
        else:
            icon = icon_failed
        # info += f"{name}{icon}  "
        info += f"{icon} {name}\n"
    return info


def __build_keyboard():
    global cams_powered
    cams_powered = False
    tasmota_btns = []
    snapshot_btn = [
        InlineKeyboardButton(text="Print area", callback_data="snapshots")]

    status_text = "*Server status and printer information*\n"
    status_text += f"{__service_info()}\n"
    status_text += "_Consumption_\n"
    for key, data in socks.items():
        pwr = _get_pwr(data['url'])
        # sys.stdout.write(f"{data['name']} - {data['url']}: {pwr}\n")
        if pwr == "N/A":
            icon = icon_na
        elif pwr > 0:
            icon = icon_on
        else:
            icon = icon_off
        if data['name'] == "Video":
            cams_powered = pwr > 0
        status_text += f"{data['name']} {pwr}W | "
        tasmota_btns.append(
            InlineKeyboardButton(text=f"{icon} {data['name']}",
                                 callback_data=f"tasmota:{key}"))
        time.sleep(.500)
        # sys.stdout.write(f"get socket state: {key}\n")
    # Snapshot button only, when cams are powered!
    if cams_powered:
        mrkup = InlineKeyboardMarkup(
            inline_keyboard=[tasmota_btns, snapshot_btn])
    else:
        mrkup = InlineKeyboardMarkup(inline_keyboard=[tasmota_btns])
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
                    caption=f"{BOT_NAME_VIEW}\n"
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
                f"snapshot: {cams.get(cam).get('name').lower()}"
                f" cam\nError: {e}")
        finally:
            time.sleep(loop_delay)


def _toggle_tasmota(cid, socket_key, delay=3):
    if admin(cid):
        socket = socks[socket_key]
        toggle_url = f"{socket['url']}?cmnd=Power TOGGLE"
        requests.get(toggle_url)
        time.sleep(delay)


def _get_pwr(url):
    pwr_url = f"{url}?cmnd=Status%208"
    rspns = requests.get(pwr_url).json()
    return rspns.get("StatusSNS", {}).get("ENERGY", {}).get("Power", "N/A")


def admin(ci):
    return str(ci) == chat_id


def state_update(cid):
    if admin(cid):
        text, keyb = __build_keyboard()
        kobra_bot.sendMessage(cid, text, reply_markup=keyb,
                              parse_mode="Markdown")
        sys.stdout.write(f"Update {text}\n")


def on_message(msg):
    """Responds to incoming messages"""
    cid = msg["chat"]["id"]
    text = msg.get("text", "")
    if admin(cid):
        sys.stdout.write(f"Message from {cid}: {text}\n")
        # Telegram in-app commands (refer 'app_commands.list')
        if text in {"start", "/start", "/status", "/state"}:
            pass
        # if text == "/reboot":
        #     kobra_bot.sendMessage(cid, "Reboot device.")
        #     os.system("sudo reboot")
        if text == "/restart":
            kobra_bot.sendMessage(cid, "Restart bot service.")
            services.restart(srvcs[2])
        if text == "/stop":
            kobra_bot.sendMessage(cid, "Stop bot service.")
            services.stop(srvcs[2])
        if text == "/restart_power":
            kobra_bot.sendMessage(cid, "Restart consumption observer.")
            services.restart(srvcs[1])
        if text == "/stop_power":
            kobra_bot.sendMessage(cid, "Stop consumption observer.")
            services.stop(srvcs[1])
        if text == "/restart_webserver":
            kobra_bot.sendMessage(cid, "Restart web server.")
            services.restart(srvcs[0])
        if text == "/stop_webserver":
            kobra_bot.sendMessage(cid, "Stop web server.")
            services.stop(srvcs[0])
    state_update(cid)


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
                query_id, text=f"Toggled {socket_key.title()}.")
            _toggle_tasmota(cid, socket_key)
            sys.stdout.write(f"toggle socket {socket_key}\n")
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
        # if 'my_chat_member' in update:
        #     sys.stderr.write(f"Ignoring 'my_chat_member' update: {update}\n")
        #     return  # Verhindert Absturz
        if 'message' in update:
            on_message(update['message'])
        elif 'callback_query' in update:
            on_callback_query(update['callback_query'])

    def poll_updates():
        last_update_id = None
        while True:
            try:
                updates = kobra_bot.getUpdates(
                    offset=last_update_id,
                    timeout=10,
                    allowed_updates=['message', 'callback_query'])
                for update in updates:
                    # Setzt den Offset hoch
                    last_update_id = update["update_id"] + 1
                    handle_update(update)
            except KeyboardInterrupt:
                sys.stderr.write('Loop interrupted\n')
                exit()
            except Exception as e:
                sys.stderr.write(
                    f"Any error occurs: {traceback.format_exc()}\n")
                sys.stderr.write(f"{e}\n")
                exit()
            finally:
                pass
            time.sleep(1)  # Verhindert Überlastung der API

    msg = "Bot is running..."
    kobra_bot.sendMessage(chat_id=chat_id, text=f"{BOT_NAME}\n{msg}")
    sys.stdout.write(f"{msg}\n")
    state_update(chat_id)
    # main loop
    poll_updates()


if __name__ == '__main__':
    main()
