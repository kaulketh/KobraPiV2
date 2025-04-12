import io
import os
import sys
import time
import traceback

import requests
from PIL import Image
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

# add parent directory (..) to sys.path to avoid possible import problems
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
    # Snapshot button only, when cams are powered!
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
        headline = "*Gathering server status and printer information...*\n"
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
        if text in {"start", "/start", "/status", "status", "/state", "state"}:
            state_update(cid)
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
        while True:
            try:
                updates = kobra_bot.getUpdates(
                    offset=last_update_id,
                    timeout=10,
                    allowed_updates=['message', 'callback_query'])
                for update in updates:
                    # increase offset
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
