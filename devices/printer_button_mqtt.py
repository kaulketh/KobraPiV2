"""
This module provides functionality for controlling a printer and light
via MQTT and GPIO on a Raspberry Pi. It manages button interactions,
LED status updates, and MQTT communication for toggling and monitoring
device states. The program handles events such as short and long button
presses to perform specific actions, such as toggling the printer and light.

Classes and functions handle MQTT connection, message processing for
device states, LED control for visual indication, and managing user
interaction through a physical button.

Attributes:
    BUTTON_PIN (int): The GPIO pin number connected to the physical button.
    LED_PIN (int): The GPIO pin number connected to the LED.
    BROKER (str): The address of the MQTT broker.
    PRINTER_TOPIC (str): The MQTT topic for printer state communication.
    LIGHT_TOPIC (str): The MQTT topic for light state communication.
    PORT (int): The port number for MQTT connection.
    KEEP_ALIVE (int): The keepalive interval for the MQTT connection.
    RECONNECT_DELAY (int): The delay (in seconds) before attempting MQTT reconnection.

Functions:
    on_connect(client, userdata, flags, reason_code, props):
        Handles the MQTT connection event and subscribes to relevant topics.

    on_disconnect(client, userdata, reason_code, props):
        Handles the MQTT disconnection event and implements automatic reconnection.

    on_message(client, userdata, msg):
        Handles incoming MQTT messages to update the state of printer and light.

    update_led():
        Updates the LED state based on the printer state.

    waiting_animation():
        Performs a blinking animation on the LED until the printer state is known.

    toggle_printer_and_light():
        Sends MQTT commands to toggle both printer and light states.

    toggle_light_only():
        Sends an MQTT command to toggle only the light state.
"""
import sys
import threading
import time

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

printer_state = False
light_state = False
printer_known = False
light_known = False
stop_event = threading.Event()
long_press_triggered = False
press_time = 0
LONG_PRESS = 1.5

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

    sys.stdout.write(f"{msg.topic} -> {payload}\n")


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
    sys.stdout.write("Flash light until printer status is known\n")
    while not printer_known and not stop_event.is_set():
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(0.2)


# ---------------- ACTIONS ----------------

def toggle_printer_and_light():
    client.publish(f"cmnd/{PRINTER_TOPIC}/{POWER_SUFFIX}", "TOGGLE")
    client.publish(f"cmnd/{LIGHT_TOPIC}/{POWER_SUFFIX}", "TOGGLE")


def toggle_light_only():
    client.publish(f"cmnd/{LIGHT_TOPIC}/{POWER_SUFFIX}", "TOGGLE")


def set_all(on: bool):
    cmd = "ON" if on else "OFF"
    client.publish(f"cmnd/{PRINTER_TOPIC}/{POWER_SUFFIX}", cmd)
    client.publish(f"cmnd/{LIGHT_TOPIC}/{POWER_SUFFIX}", cmd)


# ---------------- START ----------------

client.connect(BROKER, PORT, KEEP_ALIVE)
client.loop_start()

# Start background standby flashing
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

            # only if no long press → Short Press
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
