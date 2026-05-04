"""
This module provides functionality to manage a printer and enclosure light system using
an MQTT-based communication protocol and GPIO interactions on a Raspberry Pi. It allows
users to control printer and light power states with a physical button and visualize
printer status through an LED.

Classes and Functions:
- on_connect: Handles MQTT connection event.
- on_disconnect: Handles MQTT disconnection and retries connecting.
- on_message: Handles MQTT message reception and updates states.
- update_led: Updates LED state based on printer state.
- waiting_animation: Provides a flashing animation while printer state is unknown.
- toggle_light_only: Toggles only the light state.
- set_all: Toggles both printer and light states based on a desired state.
"""
import sys
import threading
import time

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

# Main setup
printer_state = False
light_state = False
printer_known = False
light_known = False
stop_event = threading.Event()
long_press_triggered = False
press_time = 0
LONG_PRESS = 2

# GPIO Setup
BUTTON_PIN = 17
LED_PIN = 22
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.LOW)

# MQTT Setup
BROKER = "localhost"
PRINTER_TOPIC = "printer_power"
LIGHT_TOPIC = "enclosure_light"
POWER_SUFFIX = "POWER1"
PORT = 1883
KEEP_ALIVE = 60
RECONNECT_DELAY = 5
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)


# ---------------- MQTT ----------------
def on_connect(client, userdata, flags, reason_code, props):
    _ = userdata, flags, props  # unused
    sys.stdout.write(f"MQTT connected: {reason_code}\n")

    client.subscribe(f"stat/{PRINTER_TOPIC}/{POWER_SUFFIX}")
    client.subscribe(f"stat/{LIGHT_TOPIC}/{POWER_SUFFIX}")

    # Initial State (fallback if no retained)
    client.publish(f"cmnd/{PRINTER_TOPIC}/{POWER_SUFFIX}", "")
    client.publish(f"cmnd/{LIGHT_TOPIC}/{POWER_SUFFIX}", "")


def on_disconnect(client, userdata, reason_code, props):
    _ = client, userdata, props  # unused
    sys.stdout.write(f"MQTT disconnected: {reason_code}\n")
    while True:
        try:
            sys.stdout.write("Reconnecting MQTT...\n")
            client.reconnect()
            return
        except:
            time.sleep(RECONNECT_DELAY)


def on_message(client, userdata, msg):
    _ = client, userdata  # unused
    global printer_state, light_state, printer_known, light_known

    payload = msg.payload.decode()

    if msg.topic == f"stat/{PRINTER_TOPIC}/{POWER_SUFFIX}":
        printer_state = (payload == "ON")
        printer_known = True
        update_led()

    elif msg.topic == f"stat/{LIGHT_TOPIC}/{POWER_SUFFIX}":
        light_state = (payload == "ON")
        light_known = True

    sys.stdout.write(f"{msg.topic} = {payload}\n")


client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect


# ---------------- LED ----------------
def update_led():
    if not printer_known:
        return
    GPIO.output(LED_PIN, GPIO.HIGH if printer_state else GPIO.LOW)


def waiting_animation():
    """Flashes until a status is known"""
    while not printer_known and not stop_event.is_set():
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(0.2)


# ---------------- ACTIONS ----------------
def toggle_light_only():
    client.publish(f"cmnd/{LIGHT_TOPIC}/{POWER_SUFFIX}", "TOGGLE")


def set_all(on: bool):
    cmd = "ON" if on else "OFF"
    client.publish(f"cmnd/{PRINTER_TOPIC}/{POWER_SUFFIX}", cmd)
    client.publish(f"cmnd/{LIGHT_TOPIC}/{POWER_SUFFIX}", cmd)


# ---------------- START ----------------
client.connect(BROKER, PORT, KEEP_ALIVE)
client.loop_start()
blink_thread = threading.Thread(target=waiting_animation, daemon=True)
blink_thread.start()

# ---------------- MAIN LOOP ----------------
try:
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            press_time = time.time()
            long_press_triggered = False

            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                duration = time.time() - press_time

                if duration >= LONG_PRESS and not long_press_triggered:
                    if not printer_known:
                        sys.stdout.write(
                            "Printer state unknown → ignore long press\n")
                        long_press_triggered = True
                        break  # option: break while-loop
                    sys.stdout.write("Long press → All (state based)\n")
                    set_all(not printer_state)
                    long_press_triggered = True
                time.sleep(0.01)

            # only if no long press → short Press
            if not long_press_triggered:
                sys.stdout.write("Short press → Light\n")
                toggle_light_only()
            time.sleep(0.3)  # debounce!
        time.sleep(0.05)

except KeyboardInterrupt:
    stop_event.set()
    blink_thread.join(timeout=1)
    client.loop_stop()
    GPIO.cleanup()
