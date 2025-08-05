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
# Support up to 8 layers with more keys per layer
# Use keys 1-8 as layer selectors, keys 9-15 for layer content
selectors = {i: keys[i] for i in range(1, 9)}
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

# Function to launch apps using keyboard shortcuts
def launch_app(app_config):
    """Launch an app using keyboard shortcuts"""
    if isinstance(app_config, dict) and "shortcut" in app_config:
        shortcut = app_config["shortcut"]
        # Parse the shortcut (e.g., "WIN+R" or "CTRL+ALT+T")
        keys_to_press = []
        
        # Handle modifier keys
        if "WIN" in shortcut.upper():
            keys_to_press.append(Keycode.WINDOWS)
        if "CTRL" in shortcut.upper():
            keys_to_press.append(Keycode.CONTROL)
        if "ALT" in shortcut.upper():
            keys_to_press.append(Keycode.ALT)
        if "SHIFT" in shortcut.upper():
            keys_to_press.append(Keycode.SHIFT)
        
        # Handle the main key
        main_key = shortcut.split("+")[-1].strip()
        if hasattr(Keycode, main_key):
            keys_to_press.append(getattr(Keycode, main_key))
        elif len(main_key) == 1:
            # Single character key
            keys_to_press.append(ord(main_key.upper()))
        
        # Press all keys together
        if keys_to_press:
            keyboard.press(*keys_to_press)
            time.sleep(0.1)  # Hold for a moment
            keyboard.release_all()
            
        # If there's a command to type after the shortcut
        if "command" in app_config:
            time.sleep(0.5)  # Wait for dialog to open
            layout.write(app_config["command"])
            keyboard.send(Keycode.ENTER)
    
    elif isinstance(app_config, str):
        # Simple string - treat as direct command
        layout.write(app_config)
        keyboard.send(Keycode.ENTER)

# Set LEDs for the selected layer
def set_layer_leds(layer):
    try:
        layer_conf = config["layers"].get(str(layer), {})
        default_color = tuple(layer_conf.get("color", [0, 0, 255]))
        keys_to_set = layer_conf.get("keys", {})

        # Reset all LEDs for layer content keys (9-15)
        for i in range(9, 16):
            keys[i].set_led(0, 0, 0)

        for k, v in keys_to_set.items():
            try:
                k_int = int(k)
                if isinstance(v, dict) and "color" in v:
                    keys[k_int].set_led(*v["color"])
                else:
                    keys[k_int].set_led(*default_color)
            except Exception as e:
                print(f"Error setting LED for key {k}: {e}")
                continue
    except Exception as e:
        print(f"Error in set_layer_leds for layer {layer}: {e}")
        # Turn off all content LEDs if there's an error
        for i in range(9, 16):
            keys[i].set_led(0, 0, 0)

# Initialize LEDs for the starting layer
set_layer_leds(current_layer)

# Main loop
while True:
    keybow.update()

    # Handle modifier (layer switch) logic
    if modifier.held:
        keys[0].led_off()  # Turn off modifier LED
        for i in selectors:
            try:
                # Only show layer selector if the layer exists in config
                if str(i) in config["layers"]:
                    color = config["layers"][str(i)].get("color", [0, 0, 0])
                    keys[i].set_led(*color)
                    if selectors[i].pressed:
                        current_layer = i
                        set_layer_leds(i)  # Update LEDs for the new layer
                else:
                    # Turn off LED for non-existent layers
                    keys[i].led_off()
            except Exception as e:
                # If there's an error, turn off the LED and continue
                keys[i].led_off()
                print(f"Error with layer {i}: {e}")
    else:
        for i in selectors:
            if i == current_layer:
                # Show current layer with a dim indicator
                try:
                    if str(i) in config["layers"]:
                        color = config["layers"][str(i)].get("color", [0, 0, 0])
                        # Dim the color to 1/4 brightness
                        dim_color = [c // 4 for c in color]
                        keys[i].set_led(*dim_color)
                    else:
                        keys[i].led_off()
                except:
                    keys[i].led_off()
            else:
                keys[i].led_off()  # Turn off other layer selector LEDs
        keys[0].set_led(0, 255, 0)  # Green LED for modifier when not held

    # Handle key presses for the current layer
    try:
        keys_conf = config["layers"].get(str(current_layer), {}).get("keys", {})
        for k, v in keys_conf.items():
            try:
                k_int = int(k)
                if keys[k_int].pressed and not fired:
                    fired = True
                    
                    # Check if this is an app launch key
                    if isinstance(v, dict) and "type" in v and v["type"] == "app":
                        debounce = long_debounce
                        launch_app(v)
                    else:
                        # Handle regular keys
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
            except Exception as e:
                print(f"Error handling key {k}: {e}")
                continue
    except Exception as e:
        print(f"Error in key press handling for layer {current_layer}: {e}")

    # Reset the "fired" flag after the debounce time
    if fired and time.monotonic() - keybow.time_of_last_press > debounce:
        fired = False
