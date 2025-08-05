import json
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import requests
import os
import zipfile
import tempfile
import shutil
from pathlib import Path

# Global configuration object
config = {}

# GitHub repository information
GITHUB_REPO = "pimoroni/keybow-firmware"  # Example - you can change this
GITHUB_API_BASE = "https://api.github.com/repos"

# Preset configurations for easy setup
PRESET_LAYERS = {
    "Numpad": {
        "color": [255, 0, 255],
        "keys": {
            "9": {"code": "KEYPAD_ZERO"},
            "10": {"code": "KEYPAD_ONE"},
            "11": {"code": "KEYPAD_TWO"},
            "12": {"code": "KEYPAD_THREE"},
            "13": {"code": "KEYPAD_FOUR"},
            "14": {"code": "KEYPAD_FIVE"},
            "15": {"code": "KEYPAD_SIX"}
        }
    },
    "Media Controls": {
        "color": [255, 255, 0],
        "keys": {
            "9": {"code": "VOLUME_DECREMENT"},
            "10": {"code": "VOLUME_INCREMENT"},
            "11": {"code": "MUTE"},
            "12": {"code": "PLAY_PAUSE"},
            "13": {"code": "SCAN_PREVIOUS_TRACK"},
            "14": {"code": "SCAN_NEXT_TRACK"},
            "15": {"code": "STOP"}
        }
    },
    "Gaming": {
        "color": [0, 255, 0],
        "keys": {
            "9": {"code": "W"},
            "10": {"code": "A"},
            "11": {"code": "S"},
            "12": {"code": "D"},
            "13": {"code": "SPACE"},
            "14": {"code": "SHIFT"},
            "15": {"code": "CONTROL"}
        }
    },
    "Programming": {
        "color": [128, 0, 255],
        "keys": {
            "9": {"code": "CTRL+C"},
            "10": {"code": "CTRL+V"},
            "11": {"code": "CTRL+X"},
            "12": {"code": "CTRL+Z"},
            "13": {"code": "CTRL+A"},
            "14": {"code": "CTRL+S"},
            "15": {"code": "CTRL+F"}
        }
    }
}

PRESET_APPS = {
    "Chrome": {"shortcut": "WIN+R", "command": "chrome.exe"},
    "Edge": {"shortcut": "WIN+R", "command": "msedge.exe"},
    "Notepad": {"shortcut": "WIN+R", "command": "notepad"},
    "Calculator": {"shortcut": "WIN+R", "command": "calc"},
    "Paint": {"shortcut": "WIN+R", "command": "mspaint"},
    "File Explorer": {"shortcut": "WIN+R", "command": "explorer"},
    "Command Prompt": {"shortcut": "WIN+R", "command": "cmd"},
    "PowerShell": {"shortcut": "WIN+R", "command": "powershell"},
    "Control Panel": {"shortcut": "WIN+R", "command": "control"},
    "Task Manager": {"shortcut": "WIN+R", "command": "taskmgr"},
    "Settings": {"shortcut": "WIN+R", "command": "ms-settings:"},
    "Device Manager": {"shortcut": "WIN+R", "command": "devmgmt.msc"},
    "Services": {"shortcut": "WIN+R", "command": "services.msc"}
}

def check_for_updates():
    """Check for updates from GitHub"""
    try:
        # Get the latest commit info for the main branch
        response = requests.get(f"{GITHUB_API_BASE}/{GITHUB_REPO}/commits/main")
        if response.status_code == 200:
            commit_data = response.json()
            latest_commit = commit_data['sha'][:8]  # Short commit hash
            commit_date = commit_data['commit']['author']['date'][:10]  # Date only
            
            # Get the raw content of code.py
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/code.py"
            
            # Show update dialog
            update_dialog = tk.Toplevel()
            update_dialog.title("Update Available")
            update_dialog.geometry("500x300")
            
            tk.Label(update_dialog, text=f"Latest commit: {latest_commit}", font=("Arial", 12, "bold")).pack(pady=10)
            tk.Label(update_dialog, text=f"Date: {commit_date}").pack(pady=5)
            tk.Label(update_dialog, text="Would you like to download and install the latest firmware?").pack(pady=5)
            
            # Show commit message
            notes_text = tk.Text(update_dialog, height=8, width=60)
            notes_text.pack(pady=10, padx=10)
            notes_text.insert(tk.END, commit_data['commit']['message'])
            notes_text.config(state=tk.DISABLED)
            
            def download_update():
                try:
                    update_dialog.destroy()
                    download_and_install_firmware(raw_url, latest_commit)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to download update: {e}")
            
            def skip_update():
                update_dialog.destroy()
            
            button_frame = tk.Frame(update_dialog)
            button_frame.pack(pady=10)
            tk.Button(button_frame, text="Download & Install", command=download_update, bg="green", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Skip", command=skip_update).pack(side=tk.LEFT, padx=5)
            
        else:
            messagebox.showinfo("No Updates", "No updates available or unable to check for updates.")
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to check for updates: {e}")

def download_and_install_firmware(raw_url, commit_hash):
    """Download and install firmware from GitHub"""
    try:
        # Create progress dialog
        progress_dialog = tk.Toplevel()
        progress_dialog.title("Downloading Firmware")
        progress_dialog.geometry("400x150")
        progress_dialog.transient()
        
        tk.Label(progress_dialog, text=f"Downloading firmware commit {commit_hash}...").pack(pady=10)
        progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()
        
        status_label = tk.Label(progress_dialog, text="Downloading...")
        status_label.pack(pady=5)
        
        progress_dialog.update()
        
        # Download the firmware file directly
        status_label.config(text="Downloading code.py from GitHub...")
        progress_dialog.update()
        
        response = requests.get(raw_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download: HTTP {response.status_code}")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name
        
        status_label.config(text="Installing firmware...")
        progress_dialog.update()
        
        # Copy to Keybow directory
        keybow_path = get_keybow_path()
        if keybow_path:
            shutil.copy2(tmp_file_path, os.path.join(keybow_path, 'code.py'))
            messagebox.showinfo("Success", f"Firmware updated to commit {commit_hash}!\nPlease restart your Keybow2040.")
        else:
            # If we can't find the Keybow path, save to a known location
            save_path = os.path.join(os.path.expanduser("~"), "Downloads", f"keybow_firmware_{commit_hash}.py")
            shutil.copy2(tmp_file_path, save_path)
            messagebox.showinfo("Success", f"Firmware downloaded to: {save_path}\nPlease copy this file to your Keybow2040 manually.")
        
        # Cleanup
        os.unlink(tmp_file_path)
        
        progress_dialog.destroy()
        
    except Exception as e:
        progress_dialog.destroy()
        messagebox.showerror("Error", f"Failed to install firmware: {e}")

def get_keybow_path():
    """Try to find the Keybow2040 mount point"""
    possible_paths = [
        "/media/*/KEYBOW2040",  # Linux
        "/Volumes/KEYBOW2040",  # macOS
        "C:/KEYBOW2040",        # Windows
        "D:/KEYBOW2040",        # Windows alternative
    ]
    
    for path_pattern in possible_paths:
        if '*' in path_pattern:
            import glob
            matches = glob.glob(path_pattern)
            if matches:
                return matches[0]
        elif os.path.exists(path_pattern):
            return path_pattern
    
    return None

def upload_config_to_board():
    """Upload the current config to the Keybow2040 board"""
    try:
        keybow_path = get_keybow_path()
        if not keybow_path:
            messagebox.showerror("Error", "Could not find Keybow2040. Please make sure it's connected and mounted.")
            return
        
        # Save current config
        config_path = os.path.join(keybow_path, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        messagebox.showinfo("Success", f"Config uploaded to Keybow2040!\nPath: {config_path}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to upload config: {e}")

def load_config():
    path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if not path:
        return
    try:
        with open(path, "r") as f:
            global config
            config = json.load(f)
        update_layer_list()
        if config.get("layers"):
            layer_select.set(list(config['layers'].keys())[0])
            show_keys()
        messagebox.showinfo("Success", "Config loaded successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load config: {e}")

def update_layer_list():
    layer_select['values'] = list(config.get('layers', {}).keys())
    if layer_select['values']:
        layer_select.current(0)

def show_keys(*_):
    layer_id = layer_select.get()
    keys_text.delete("1.0", tk.END)
    if layer_id in config.get("layers", {}):
        keys = config["layers"][layer_id]["keys"]
        for k, v in keys.items():
            if isinstance(v, dict):
                key_type = v.get("type", "key")
                if key_type == "app":
                    shortcut = v.get("shortcut", "")
                    command = v.get("command", "")
                    color = v.get("color")
                    line = f"Key {k}: APP - {shortcut} -> {command}"
                    if color:
                        line += f" [{color[0]}, {color[1]}, {color[2]}]"
                    keys_text.insert(tk.END, line + "\n")
                else:
                    code = v.get("code", "")
                    color = v.get("color")
                    line = f"Key {k}: {code}"
                    if color:
                        line += f" [{color[0]}, {color[1]}, {color[2]}]"
                    keys_text.insert(tk.END, line + "\n")
            else:
                keys_text.insert(tk.END, f"Key {k}: {v}\n")

def update_keys():
    layer_id = layer_select.get()
    keys = {}
    for line in keys_text.get("1.0", tk.END).splitlines():
        if line.strip():
            try:
                key_part, value_part = line.split(":", 1)
                key = key_part.strip().replace("Key", "").strip()

                # Handle app type keys
                if "APP -" in value_part:
                    app_part = value_part.split("APP -", 1)[1].strip()
                    if "->" in app_part:
                        shortcut_part, command_part = app_part.split("->", 1)
                        shortcut = shortcut_part.strip()
                        command = command_part.strip()
                        
                        color = None
                        if "[" in command and "]" in command:
                            command, color_part = command.rsplit("[", 1)
                            command = command.strip()
                            color = json.loads("[" + color_part.strip())
                        
                        keys[key] = {
                            "type": "app",
                            "shortcut": shortcut,
                            "command": command
                        }
                        if color:
                            keys[key]["color"] = color
                    else:
                        keys[key] = {
                            "type": "app",
                            "shortcut": app_part
                        }
                else:
                    if "[" in value_part and "]" in value_part:
                        code_part, color_part = value_part.split("[", 1)
                        code = code_part.strip()
                        color = json.loads("[" + color_part.strip())
                        keys[key] = {"code": code, "color": color}
                    else:
                        code = value_part.strip()
                        keys[key] = {"code": code}
            except Exception as e:
                print(f"Skipping invalid line: {line} ({e})")
                continue
    if layer_id in config.get("layers", {}):
        config["layers"][layer_id]["keys"] = keys

def add_preset_layer():
    """Add a preset layer"""
    dialog = tk.Toplevel()
    dialog.title("Add Preset Layer")
    dialog.geometry("400x300")
    
    tk.Label(dialog, text="Select a preset layer:").pack(pady=10)
    
    preset_var = tk.StringVar()
    preset_combo = ttk.Combobox(dialog, textvariable=preset_var, values=list(PRESET_LAYERS.keys()), state="readonly")
    preset_combo.pack(pady=5)
    
    tk.Label(dialog, text="Layer ID (1-8):").pack()
    layer_id_entry = tk.Entry(dialog)
    layer_id_entry.pack()
    
    def add_preset():
        try:
            layer_id = layer_id_entry.get().strip()
            preset_name = preset_var.get()
            
            if not layer_id or not preset_name:
                messagebox.showerror("Error", "Please fill in all fields!")
                return
            
            if not layer_id.isdigit() or int(layer_id) < 1 or int(layer_id) > 8:
                messagebox.showerror("Error", "Layer ID must be 1-8!")
                return
            
            # Initialize layers if not exists
            if "layers" not in config:
                config["layers"] = {}
            
            # Add the preset layer
            config["layers"][layer_id] = {
                "name": preset_name,
                **PRESET_LAYERS[preset_name]
            }
            
            update_layer_list()
            layer_select.set(layer_id)
            show_keys()
            dialog.destroy()
            messagebox.showinfo("Success", f"Added {preset_name} layer!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add preset layer: {e}")
    
    tk.Button(dialog, text="Add Preset Layer", command=add_preset).pack(pady=10)

def add_apps_layer():
    """Add a complete apps layer with common applications"""
    dialog = tk.Toplevel()
    dialog.title("Add Apps Layer")
    dialog.geometry("500x400")
    
    tk.Label(dialog, text="Layer ID (1-8):").pack()
    layer_id_entry = tk.Entry(dialog)
    layer_id_entry.pack()
    
    tk.Label(dialog, text="Select apps to include:").pack(pady=10)
    
    # Create checkboxes for each app
    app_vars = {}
    for app_name in PRESET_APPS.keys():
        var = tk.BooleanVar(value=True)  # Default to selected
        app_vars[app_name] = var
        tk.Checkbutton(dialog, text=app_name, variable=var).pack(anchor=tk.W)
    
    def add_apps_layer():
        try:
            layer_id = layer_id_entry.get().strip()
            
            if not layer_id:
                messagebox.showerror("Error", "Please enter a layer ID!")
                return
            
            if not layer_id.isdigit() or int(layer_id) < 1 or int(layer_id) > 8:
                messagebox.showerror("Error", "Layer ID must be 1-8!")
                return
            
            # Initialize layers if not exists
            if "layers" not in config:
                config["layers"] = {}
            
            # Create apps layer
            apps_keys = {}
            key_num = 9
            for app_name, var in app_vars.items():
                if var.get():  # If app is selected
                    apps_keys[str(key_num)] = {
                        "type": "app",
                        **PRESET_APPS[app_name],
                        "color": [255, 128, 0]
                    }
                    key_num += 1
                    if key_num > 15:  # Max 7 apps
                        break
            
            config["layers"][layer_id] = {
                "name": "Apps",
                "color": [255, 0, 0],
                "keys": apps_keys
            }
            
            update_layer_list()
            layer_select.set(layer_id)
            show_keys()
            dialog.destroy()
            messagebox.showinfo("Success", f"Added Apps layer with {len(apps_keys)} apps!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add apps layer: {e}")
    
    tk.Button(dialog, text="Add Apps Layer", command=add_apps_layer).pack(pady=10)

def add_app_key():
    """Add a new app key with a dialog"""
    dialog = tk.Toplevel()
    dialog.title("Add App Key")
    dialog.geometry("400x350")
    
    tk.Label(dialog, text="Key Number (9-15):").pack()
    key_entry = tk.Entry(dialog)
    key_entry.pack()
    
    tk.Label(dialog, text="Or select from presets:").pack(pady=5)
    preset_var = tk.StringVar()
    preset_combo = ttk.Combobox(dialog, textvariable=preset_var, values=list(PRESET_APPS.keys()), state="readonly")
    preset_combo.pack(pady=5)
    
    tk.Label(dialog, text="Shortcut (e.g., WIN+R):").pack()
    shortcut_entry = tk.Entry(dialog)
    shortcut_entry.pack()
    
    tk.Label(dialog, text="Command (e.g., notepad):").pack()
    command_entry = tk.Entry(dialog)
    command_entry.pack()
    
    tk.Label(dialog, text="Color (e.g., [255,0,0] or 'red') (optional):").pack()
    color_entry = tk.Entry(dialog)
    color_entry.pack()
    
    # Color examples
    examples_frame = tk.Frame(dialog)
    examples_frame.pack(pady=5)
    tk.Label(examples_frame, text="Examples: red, blue, [255,0,0], 255,0,0", fg="gray").pack()
    
    def on_preset_select(*args):
        if preset_var.get() in PRESET_APPS:
            app_config = PRESET_APPS[preset_var.get()]
            shortcut_entry.delete(0, tk.END)
            shortcut_entry.insert(0, app_config["shortcut"])
            command_entry.delete(0, tk.END)
            command_entry.insert(0, app_config["command"])
    
    preset_combo.bind('<<ComboboxSelected>>', on_preset_select)
    
    def save_app():
        try:
            key = key_entry.get().strip()
            shortcut = shortcut_entry.get().strip()
            command = command_entry.get().strip()
            color_text = color_entry.get().strip()
            
            if not key or not shortcut:
                messagebox.showerror("Error", "Key number and shortcut are required!")
                return
            
            if not key.isdigit() or int(key) < 9 or int(key) > 15:
                messagebox.showerror("Error", "Key number must be 9-15!")
                return
            
            app_config = {
                "type": "app",
                "shortcut": shortcut
            }
            
            if command:
                app_config["command"] = command
            
            if color_text:
                color = parse_color(color_text)
                if color is None:
                    messagebox.showerror("Error", "Invalid color format! Use [R,G,B], 'red', or R,G,B")
                    return
                app_config["color"] = color
            
            # Add to current layer
            layer_id = layer_select.get()
            if layer_id in config.get("layers", {}):
                config["layers"][layer_id]["keys"][key] = app_config
                show_keys()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "No layer selected!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add app key: {e}")
    
    tk.Button(dialog, text="Add App Key", command=save_app).pack(pady=10)

def parse_color(color_text):
    """Parse color from text input, supporting both RGB format and color names"""
    color_text = color_text.strip().lower()
    
    # Common color names
    color_names = {
        'red': [255, 0, 0],
        'green': [0, 255, 0],
        'blue': [0, 0, 255],
        'yellow': [255, 255, 0],
        'cyan': [0, 255, 255],
        'magenta': [255, 0, 255],
        'white': [255, 255, 255],
        'black': [0, 0, 0],
        'orange': [255, 165, 0],
        'purple': [128, 0, 128],
        'pink': [255, 192, 203],
        'brown': [165, 42, 42],
        'gray': [128, 128, 128],
        'grey': [128, 128, 128]
    }
    
    # Try color name first
    if color_text in color_names:
        return color_names[color_text]
    
    # Try JSON format [R, G, B]
    try:
        return json.loads(color_text)
    except:
        pass
    
    # Try comma-separated format
    try:
        parts = color_text.split(',')
        if len(parts) == 3:
            return [int(parts[0].strip()), int(parts[1].strip()), int(parts[2].strip())]
    except:
        pass
    
    return None

def add_layer():
    """Add a new layer"""
    dialog = tk.Toplevel()
    dialog.title("Add Layer")
    dialog.geometry("350x250")
    
    tk.Label(dialog, text="Layer ID (1-8):").pack()
    layer_id_entry = tk.Entry(dialog)
    layer_id_entry.pack()
    
    tk.Label(dialog, text="Layer Name:").pack()
    layer_name_entry = tk.Entry(dialog)
    layer_name_entry.pack()
    
    tk.Label(dialog, text="Default Color (e.g., [255,0,0] or 'red'):").pack()
    color_entry = tk.Entry(dialog)
    color_entry.pack()
    
    # Color examples
    examples_frame = tk.Frame(dialog)
    examples_frame.pack(pady=5)
    tk.Label(examples_frame, text="Examples: red, blue, [255,0,0], 255,0,0", fg="gray").pack()
    
    def save_layer():
        try:
            layer_id = layer_id_entry.get().strip()
            layer_name = layer_name_entry.get().strip()
            color_text = color_entry.get().strip()
            
            if not layer_id:
                messagebox.showerror("Error", "Layer ID is required!")
                return
            
            if not layer_id.isdigit() or int(layer_id) < 1 or int(layer_id) > 8:
                messagebox.showerror("Error", "Layer ID must be 1-8!")
                return
            
            # Initialize layers if not exists
            if "layers" not in config:
                config["layers"] = {}
            
            new_layer = {
                "name": layer_name or f"Layer {layer_id}",
                "keys": {}
            }
            
            if color_text:
                color = parse_color(color_text)
                if color is None:
                    messagebox.showerror("Error", "Invalid color format! Use [R,G,B], 'red', or R,G,B")
                    return
                new_layer["color"] = color
            
            config["layers"][layer_id] = new_layer
            update_layer_list()
            layer_select.set(layer_id)
            show_keys()
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add layer: {e}")
    
    tk.Button(dialog, text="Add Layer", command=save_layer).pack(pady=10)

def save_config():
    update_keys()
    path = filedialog.asksaveasfilename(defaultextension=".json")
    if not path:
        return
    try:
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
        messagebox.showinfo("Success", "Config saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save config: {e}")

# GUI setup
app = tk.Tk()
app.title("Keybow Configurator - Enhanced")
app.geometry("900x700")

# Top frame for controls
top_frame = tk.Frame(app)
top_frame.pack(fill=tk.X, padx=10, pady=5)

# File operations
file_frame = tk.LabelFrame(top_frame, text="File Operations")
file_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

tk.Button(file_frame, text="Load Config", command=load_config).pack(side=tk.LEFT, padx=5)
tk.Button(file_frame, text="Save Config", command=save_config).pack(side=tk.LEFT, padx=5)

# Board operations
board_frame = tk.LabelFrame(top_frame, text="Board Operations")
board_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

tk.Button(board_frame, text="Upload Config", command=upload_config_to_board, bg="blue", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(board_frame, text="Check Updates", command=check_for_updates, bg="orange", fg="white").pack(side=tk.LEFT, padx=5)

# Layer operations
layer_frame = tk.LabelFrame(top_frame, text="Layer Operations")
layer_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

tk.Button(layer_frame, text="Add Layer", command=add_layer).pack(side=tk.LEFT, padx=5)
tk.Button(layer_frame, text="Add Preset Layer", command=add_preset_layer).pack(side=tk.LEFT, padx=5)
tk.Button(layer_frame, text="Add Apps Layer", command=add_apps_layer).pack(side=tk.LEFT, padx=5)

# Key operations
key_frame = tk.LabelFrame(top_frame, text="Key Operations")
key_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

tk.Button(key_frame, text="Add App Key", command=add_app_key).pack(side=tk.LEFT, padx=5)

# Layer selection
layer_select_frame = tk.Frame(app)
layer_select_frame.pack(fill=tk.X, padx=10, pady=5)
tk.Label(layer_select_frame, text="Layer:").pack(side=tk.LEFT)
layer_select = ttk.Combobox(layer_select_frame, state="readonly")
layer_select.pack(side=tk.LEFT, padx=5)
layer_select.bind('<<ComboboxSelected>>', show_keys)

# Keys display
keys_frame = tk.Frame(app)
keys_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

tk.Label(keys_frame, text="Keys Configuration (Format: Key X: CODE or Key X: APP - SHORTCUT -> COMMAND)").pack()

keys_text = tk.Text(keys_frame, width=80, height=25)
keys_text.pack(fill=tk.BOTH, expand=True)

# Instructions
instructions = """
Quick Start Guide:
1. Use "Add Preset Layer" to quickly add common layer types (Numpad, Media, Gaming, Programming)
2. Use "Add Apps Layer" to create a complete apps layer with common applications
3. Use "Add App Key" to add individual app shortcuts
4. Use "Upload Config" to send your config directly to the Keybow2040 board
5. Use "Check Updates" to automatically update the firmware from GitHub
6. Edit keys directly in the text area or use the buttons above
7. Layer IDs must be 1-8, Key numbers must be 9-15 for content
"""
tk.Label(app, text=instructions, justify=tk.LEFT, fg="blue").pack(padx=10, pady=5)

app.mainloop()
