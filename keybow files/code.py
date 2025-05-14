import json
import time
from pmk import PMK
from pmk.platform.keybow2040 import Keybow2040 as Hardware
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Setup
keybow = PMK(Hardware())
keys = keybow.keys
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)
consumer = ConsumerControl(usb_hid.devices)

# Load configuration
try:
    with open("/config.json") as f:
        config = json.load(f)
except Exception as e:
    print("Failed to load config.json:", e)
    while True:
        pass  # Freeze if config fails to load

# Key setup
modifier = keys[0]
selectors = {1: keys[1], 2: keys[2], 3: keys[3]}
current_layer = 1
fired = False
short_debounce, long_debounce = 0.03, 0.15
debounce = short_debounce

# Parse key logic to handle both Keycode and ConsumerControlCode
def parse_key(key):
    if hasattr(Keycode, key):
        return getattr(Keycode, key)
    elif hasattr(ConsumerControlCode, key):
        return getattr(ConsumerControlCode, key)
    else:
        return key  # Assume plain string if not recognized

# Set LEDs for the selected layer
def set_layer_leds(layer):
    layer_conf = config["layers"].get(str(layer), {})
    default_color = tuple(layer_conf.get("color", [0, 0, 255]))
    keys_to_set = layer_conf.get("keys", {})

    # Reset all LEDs
    for i in range(4, 16):
        keys[i].set_led(0, 0, 0)

    for k, v in keys_to_set.items():
        k_int = int(k)
        if isinstance(v, dict) and "color" in v:
            keys[k_int].set_led(*v["color"])
        else:
            keys[k_int].set_led(*default_color)

# Initialize LEDs for the starting layer
set_layer_leds(current_layer)

# Main loop
while True:
    keybow.update()

    # Handle modifier (layer switch) logic
    if modifier.held:
        keys[0].led_off()  # Turn off modifier LED
        for i in selectors:
            color = config["layers"].get(str(i), {}).get("color", [0, 0, 0])
            keys[i].set_led(*color)
            if selectors[i].pressed:
                current_layer = i
                set_layer_leds(i)  # Update LEDs for the new layer
    else:
        for i in selectors:
            keys[i].led_off()  # Turn off layer selector LEDs
        keys[0].set_led(0, 255, 0)  # Green LED for modifier when not held

    # Handle key presses for the current layer
    keys_conf = config["layers"].get(str(current_layer), {}).get("keys", {})
    for k, v in keys_conf.items():
        k_int = int(k)
        if keys[k_int].pressed and not fired:
            fired = True
            key_val = v["code"] if isinstance(v, dict) and "code" in v else v
            parsed = parse_key(key_val)
            if isinstance(parsed, int):
                debounce = short_debounce
                keyboard.send(parsed)
            elif isinstance(parsed, ConsumerControlCode):
                debounce = short_debounce
                consumer.send(parsed)
            else:
                debounce = long_debounce
                layout.write(parsed)

    # Reset the "fired" flag after the debounce time
    if fired and time.monotonic() - keybow.time_of_last_press > debounce:
        fired = False
