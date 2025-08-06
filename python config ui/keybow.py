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
current_layer_display = None  # For updating the layer display

# GitHub repository information
GITHUB_REPO = "BenCos17/keybow"
GITHUB_API_BASE = "https://api.github.com/repos"
FIRMWARE_PATH = "keybow%20files/code.py"  # Path to your firmware file in the repository (URL encoded)

# Keybow2040 layout - 4x4 grid (modifier key 0 in bottom left)
KEYBOW_LAYOUT = [
    [12, 13, 14, 15],
    [8,  9,  10, 11],
    [4,  5,  6,  7],
    [0,  1,  2,  3]
]

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

def create_key_map():
    """Create a visual key map showing the Keybow2040 layout with actual functions"""
    map_window = tk.Toplevel()
    map_window.title("Keybow2040 Key Map")
    map_window.geometry("800x700")
    
    # Title
    tk.Label(map_window, text="Keybow2040 Layout with Functions", font=("Arial", 16, "bold")).pack(pady=10)
    
    # Layer selection
    layer_frame = tk.Frame(map_window)
    layer_frame.pack(pady=5)
    tk.Label(layer_frame, text="Select Layer:").pack(side=tk.LEFT)
    layer_var = tk.StringVar(value="1")
    layer_combo = ttk.Combobox(layer_frame, textvariable=layer_var, values=list(range(1, 9)), state="readonly", width=5)
    layer_combo.pack(side=tk.LEFT, padx=5)
    
    # Create the 4x4 grid
    grid_frame = tk.Frame(map_window)
    grid_frame.pack(pady=10)
    
    key_buttons = {}
    for row in range(4):
        for col in range(4):
            key_num = KEYBOW_LAYOUT[row][col]
            btn = tk.Button(grid_frame, text=str(key_num), width=12, height=4, 
                          font=("Arial", 10, "bold"))
            btn.grid(row=row, column=col, padx=2, pady=2)
            key_buttons[key_num] = btn
    
    def update_key_functions():
        """Update the key map to show actual functions"""
        try:
            layer_id = layer_var.get()
            if not layer_id or layer_id not in config.get("layers", {}):
                # Show default layout
                for key_num, btn in key_buttons.items():
                    if key_num == 0:
                        btn.config(bg="lightgreen", text="0\nModifier\n(Hold to\nswitch layers)")
                    elif key_num <= 8:
                        btn.config(bg="lightblue", text=f"{key_num}\nLayer\nSelector")
                    else:
                        btn.config(bg="lightgray", text=f"{key_num}\nContent\nKey")
                return
            
            layer_data = config["layers"][layer_id]
            layer_name = layer_data.get("name", f"Layer {layer_id}")
            layer_color = layer_data.get("color", [0, 0, 0])
            keys = layer_data.get("keys", {})
            
            # Update title to show current layer
            map_window.title(f"Keybow2040 Key Map - {layer_name}")
            
            # Update all keys
            for key_num, btn in key_buttons.items():
                if key_num == 0:
                    btn.config(bg="lightgreen", text="0\nModifier\n(Hold to\nswitch layers)")
                elif key_num <= 8:
                    # Layer selector
                    if str(key_num) in config.get("layers", {}):
                        selector_name = config["layers"][str(key_num)].get("name", f"Layer {key_num}")
                        btn.config(bg="lightblue", text=f"{key_num}\n{selector_name}")
                    else:
                        btn.config(bg="lightgray", text=f"{key_num}\nNot\nConfigured")
                else:
                    # Content key
                    if str(key_num) in keys:
                        key_data = keys[str(key_num)]
                        if isinstance(key_data, dict):
                            key_type = key_data.get("type", "key")
                            if key_type == "app":
                                command = key_data.get("command", "")
                                # Truncate long commands
                                if len(command) > 12:
                                    command = command[:9] + "..."
                                btn.config(bg="orange", text=f"{key_num}\nAPP\n{command}")
                            else:
                                code = key_data.get("code", "")
                                # Truncate long codes
                                if len(code) > 12:
                                    code = code[:9] + "..."
                                btn.config(bg="lightyellow", text=f"{key_num}\n{code}")
                        else:
                            # Simple string
                            if len(str(key_data)) > 12:
                                display_text = str(key_data)[:9] + "..."
                            else:
                                display_text = str(key_data)
                            btn.config(bg="lightyellow", text=f"{key_num}\n{display_text}")
                    else:
                        btn.config(bg="lightgray", text=f"{key_num}\nNot\nConfigured")
        
        except Exception as e:
            print(f"Error updating key map: {e}")
    
    # Bind layer selection to update function
    layer_combo.bind('<<ComboboxSelected>>', lambda e: update_key_functions())
    
    # Legend
    legend_frame = tk.Frame(map_window)
    legend_frame.pack(pady=10)
    
    tk.Label(legend_frame, text="Legend:", font=("Arial", 12, "bold")).pack()
    
    legend_items = [
        ("Green", "Modifier key - Hold to switch layers"),
        ("Blue", "Layer selectors - Choose which layer to use"),
        ("Orange", "App launchers - Launch applications"),
        ("Yellow", "Regular keys - Standard keyboard functions"),
        ("Gray", "Not configured - No function assigned")
    ]
    
    for color, desc in legend_items:
        item_frame = tk.Frame(legend_frame)
        item_frame.pack(anchor=tk.W, pady=2)
        color_label = tk.Label(item_frame, text="■", fg=color, font=("Arial", 12, "bold"), width=2)
        color_label.pack(side=tk.LEFT)
        tk.Label(item_frame, text=desc, font=("Arial", 9)).pack(side=tk.LEFT)
    
    # Instructions
    instructions = """
How to use:
1. Select a layer from the dropdown to see its functions
2. Hold Key 0 (modifier) to enter layer selection mode
3. Press Keys 1-8 to select a layer
4. Release both keys to activate the layer
5. Use Keys 9-15 for the layer's functions
    """
    tk.Label(map_window, text=instructions, justify=tk.LEFT, fg="blue").pack(pady=10)
    
    # Initial update
    update_key_functions()

def create_layer_indicator():
    """Create a visual indicator showing current layer and available layers"""
    indicator_window = tk.Toplevel()
    indicator_window.title("Current Layer Status")
    indicator_window.geometry("800x600")
    
    # Title
    tk.Label(indicator_window, text="Layer Status & Key Functions", font=("Arial", 16, "bold")).pack(pady=10)
    
    # Main content frame
    main_frame = tk.Frame(indicator_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # Left side - Layer selection
    left_frame = tk.Frame(main_frame)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
    
    # Current layer display
    current_frame = tk.Frame(left_frame)
    current_frame.pack(pady=10)
    tk.Label(current_frame, text="Current Layer:", font=("Arial", 12, "bold")).pack()
    
    global current_layer_display
    current_layer_display = tk.Label(current_frame, text="None", font=("Arial", 14), fg="red")
    current_layer_display.pack()
    
    # Available layers
    layers_frame = tk.Frame(left_frame)
    layers_frame.pack(pady=10)
    tk.Label(layers_frame, text="Available Layers:", font=("Arial", 12, "bold")).pack()
    
    # Create layer buttons
    layer_buttons = {}
    for layer_id in range(1, 9):
        btn = tk.Button(layers_frame, text=f"Layer {layer_id}", width=10, height=2)
        btn.pack(pady=2)
        layer_buttons[layer_id] = btn
    
    # Right side - Key functions display
    right_frame = tk.Frame(main_frame)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    tk.Label(right_frame, text="Key Functions:", font=("Arial", 12, "bold")).pack()
    
    # Create key function display
    key_functions_text = tk.Text(right_frame, width=50, height=20, font=("Consolas", 10))
    key_functions_text.pack(fill=tk.BOTH, expand=True)
    
    def update_layer_display(layer_id):
        """Update the current layer display"""
        if current_layer_display:
            if layer_id in config.get("layers", {}):
                layer_name = config["layers"][layer_id].get("name", f"Layer {layer_id}")
                layer_color = config["layers"][layer_id].get("color", [0, 0, 0])
                current_layer_display.config(text=f"{layer_id}: {layer_name}", fg="green")
                
                # Update layer button colors
                for lid, btn in layer_buttons.items():
                    if lid == layer_id:
                        btn.config(bg="lightgreen")
                    elif lid in config.get("layers", {}):
                        btn.config(bg="lightblue")
                    else:
                        btn.config(bg="lightgray")
            else:
                current_layer_display.config(text=f"{layer_id}: Not configured", fg="orange")
    
    def update_key_functions(layer_id):
        """Update the key functions display"""
        key_functions_text.delete("1.0", tk.END)
        
        if layer_id not in config.get("layers", {}):
            key_functions_text.insert(tk.END, "Layer not configured\n")
            return
        
        layer_data = config["layers"][layer_id]
        layer_name = layer_data.get("name", f"Layer {layer_id}")
        layer_color = layer_data.get("color", [0, 0, 0])
        
        # Header
        key_functions_text.insert(tk.END, f"Layer {layer_id}: {layer_name}\n")
        key_functions_text.insert(tk.END, f"Color: {layer_color}\n")
        key_functions_text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Key functions
        keys = layer_data.get("keys", {})
        if not keys:
            key_functions_text.insert(tk.END, "No keys configured for this layer\n")
            return
        
        # Sort keys by number
        sorted_keys = sorted(keys.items(), key=lambda x: int(x[0]))
        
        for key_num, key_data in sorted_keys:
            if isinstance(key_data, dict):
                key_type = key_data.get("type", "key")
                if key_type == "app":
                    shortcut = key_data.get("shortcut", "")
                    command = key_data.get("command", "")
                    color = key_data.get("color")
                    key_functions_text.insert(tk.END, f"Key {key_num}: APP\n")
                    key_functions_text.insert(tk.END, f"  Shortcut: {shortcut}\n")
                    key_functions_text.insert(tk.END, f"  Command: {command}\n")
                    if color:
                        key_functions_text.insert(tk.END, f"  Color: {color}\n")
                else:
                    code = key_data.get("code", "")
                    color = key_data.get("color")
                    key_functions_text.insert(tk.END, f"Key {key_num}: {code}\n")
                    if color:
                        key_functions_text.insert(tk.END, f"  Color: {color}\n")
            else:
                key_functions_text.insert(tk.END, f"Key {key_num}: {key_data}\n")
            key_functions_text.insert(tk.END, "\n")
    
    def on_layer_click(layer_id):
        """Handle layer button clicks"""
        update_layer_display(layer_id)
        update_key_functions(layer_id)
        # Update the main app's layer selection
        if hasattr(app, 'layer_select'):
            app.layer_select.set(str(layer_id))
            show_keys()
    
    # Bind layer buttons
    for layer_id, btn in layer_buttons.items():
        btn.config(command=lambda lid=layer_id: on_layer_click(lid))
    
    # Update button
    def refresh_display():
        current_layer = layer_select.get() if hasattr(app, 'layer_select') else "1"
        update_layer_display(current_layer)
        update_key_functions(current_layer)
    
    tk.Button(left_frame, text="Refresh Display", command=refresh_display).pack(pady=10)
    
    # Initial update
    refresh_display()

def check_for_updates():
    """Check for updates from GitHub"""
    try:
        # Get the latest commit info for the main branch
        response = requests.get(f"{GITHUB_API_BASE}/{GITHUB_REPO}/commits/main")
        if response.status_code == 200:
            commit_data = response.json()
            latest_commit = commit_data['sha'][:8]  # Short commit hash
            commit_date = commit_data['commit']['author']['date'][:10]  # Date only
            
            # Get the raw content of the firmware file
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{FIRMWARE_PATH}"
            
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
            try:
                shutil.copy2(tmp_file_path, os.path.join(keybow_path, 'code.py'))
                messagebox.showinfo("Success", f"Firmware updated to commit {commit_hash}!\nPlease restart your Keybow2040.")
            except PermissionError:
                # Handle permission denied error
                error_dialog = tk.Toplevel()
                error_dialog.title("Permission Error")
                error_dialog.geometry("500x400")
                
                tk.Label(error_dialog, text="Permission Denied!", font=("Arial", 14, "bold"), fg="red").pack(pady=10)
                
                solution_text = """
The Keybow2040 is currently read-only or locked by Windows.

Solutions to try:

1. **Unplug and replug** the Keybow2040 USB cable
   - This often fixes the permission issue

2. **Eject and reconnect** the Keybow2040:
   - Right-click the Keybow2040 drive in File Explorer
   - Select "Eject"
   - Unplug and replug the USB cable

3. **Check if Keybow2040 is in use**:
   - Close any programs that might be accessing it
   - Make sure no file explorer windows are open to the drive

4. **Try manual installation**:
   - The firmware has been saved to Downloads
   - Copy it manually to your Keybow2040
                """
                
                text_widget = tk.Text(error_dialog, height=15, width=60)
                text_widget.pack(pady=10, padx=10)
                text_widget.insert(tk.END, solution_text)
                text_widget.config(state=tk.DISABLED)
                
                # Save to Downloads as fallback
                save_path = os.path.join(os.path.expanduser("~"), "Downloads", "code.py")
                shutil.copy2(tmp_file_path, save_path)
                
                def try_again():
                    error_dialog.destroy()
                    # Try to get the path again (in case user reconnected)
                    new_keybow_path = get_keybow_path()
                    if new_keybow_path:
                        try:
                            shutil.copy2(tmp_file_path, os.path.join(new_keybow_path, 'code.py'))
                            messagebox.showinfo("Success", f"Firmware updated to commit {commit_hash}!\nPlease restart your Keybow2040.")
                        except PermissionError:
                            messagebox.showerror("Still Locked", "The Keybow2040 is still locked.\nPlease try the manual installation method.")
                    else:
                        messagebox.showinfo("Manual Installation", f"Firmware saved to: {save_path}\nPlease copy this file to your Keybow2040 manually.")
                
                def manual_install():
                    error_dialog.destroy()
                    messagebox.showinfo("Manual Installation", f"Firmware saved to: {save_path}\nPlease copy this file to your Keybow2040 manually.")
                
                button_frame = tk.Frame(error_dialog)
                button_frame.pack(pady=10)
                tk.Button(button_frame, text="Try Again", command=try_again, bg="green", fg="white").pack(side=tk.LEFT, padx=5)
                tk.Button(button_frame, text="Manual Install", command=manual_install, bg="blue", fg="white").pack(side=tk.LEFT, padx=5)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to install firmware: {e}")
        else:
            # If we can't find the Keybow path, save to a known location
            save_path = os.path.join(os.path.expanduser("~"), "Downloads", "code.py")
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
    
    # If not found, ask user to select manually
    result = messagebox.askyesno("Keybow2040 Not Found", 
                                "Could not automatically find your Keybow2040.\n\n"
                                "Would you like to select the drive manually?")
    if result:
        path = filedialog.askdirectory(title="Select Keybow2040 drive/folder")
        if path and os.path.exists(path):
            return path
    
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

def find_installed_apps():
    """Find installed applications on the system"""
    import subprocess
    import platform
    
    found_apps = {}
    
    if platform.system() == "Windows":
        # Common Windows app locations
        app_locations = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            r"C:\Users\%USERNAME%\AppData\Local\Programs",
            r"C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
        ]
        
        # Common Windows apps
        common_apps = {
            "chrome.exe": "Google Chrome",
            "msedge.exe": "Microsoft Edge",
            "firefox.exe": "Mozilla Firefox",
            "notepad.exe": "Notepad",
            "calc.exe": "Calculator",
            "mspaint.exe": "Paint",
            "wordpad.exe": "WordPad",
            "explorer.exe": "File Explorer",
            "cmd.exe": "Command Prompt",
            "powershell.exe": "PowerShell",
            "control.exe": "Control Panel",
            "taskmgr.exe": "Task Manager",
            "devmgmt.msc": "Device Manager",
            "services.msc": "Services",
            "ms-settings:": "Windows Settings",
            "winword.exe": "Microsoft Word",
            "excel.exe": "Microsoft Excel",
            "powerpnt.exe": "Microsoft PowerPoint",
            "outlook.exe": "Microsoft Outlook",
            "teams.exe": "Microsoft Teams",
            "discord.exe": "Discord",
            "spotify.exe": "Spotify",
            "vlc.exe": "VLC Media Player",
            "obs64.exe": "OBS Studio",
            "code.exe": "Visual Studio Code",
            "notepad++.exe": "Notepad++",
            "sublime_text.exe": "Sublime Text",
            "atom.exe": "Atom Editor",
            "git-bash.exe": "Git Bash",
            "putty.exe": "PuTTY",
            "winrar.exe": "WinRAR",
            "7zFM.exe": "7-Zip",
            "acrobat.exe": "Adobe Acrobat",
            "photoshop.exe": "Adobe Photoshop",
            "illustrator.exe": "Adobe Illustrator",
            "premiere.exe": "Adobe Premiere",
            "afterfx.exe": "Adobe After Effects",
            "blender.exe": "Blender",
            "unity.exe": "Unity",
            "unreal.exe": "Unreal Engine",
            "steam.exe": "Steam",
            "epicgameslauncher.exe": "Epic Games Launcher",
            "battle.net.exe": "Battle.net",
            "origin.exe": "Origin",
            "uplay.exe": "Ubisoft Connect"
        }
        
        # Try to find apps using where command
        for app_name, display_name in common_apps.items():
            try:
                result = subprocess.run(['where', app_name], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    found_apps[display_name] = app_name
            except:
                continue
    
    return found_apps

def browse_for_app():
    """Let user browse for an application file"""
    file_types = [
        ("Executable files", "*.exe"),
        ("All files", "*.*")
    ]
    
    if platform.system() == "Windows":
        file_types = [
            ("Executable files", "*.exe"),
            ("All files", "*.*")
        ]
    else:
        file_types = [
            ("All files", "*.*")
        ]
    
    filename = filedialog.askopenfilename(
        title="Select Application",
        filetypes=file_types,
        initialdir="/"
    )
    
    if filename:
        # Get just the filename without path
        app_name = os.path.basename(filename)
        return app_name, filename
    return None, None

def add_app_key():
    """Add a new app key with a dialog"""
    dialog = tk.Toplevel()
    dialog.title("Add App Key")
    dialog.geometry("500x500")
    
    # Key number
    tk.Label(dialog, text="Key Number (9-15):").pack()
    key_entry = tk.Entry(dialog)
    key_entry.pack()
    
    # App selection frame
    app_frame = tk.LabelFrame(dialog, text="App Selection")
    app_frame.pack(fill=tk.X, padx=10, pady=5)
    
    # Preset apps
    tk.Label(app_frame, text="Preset Apps:").pack(anchor=tk.W)
    preset_var = tk.StringVar()
    preset_combo = ttk.Combobox(app_frame, textvariable=preset_var, values=list(PRESET_APPS.keys()), state="readonly")
    preset_combo.pack(fill=tk.X, pady=2)
    
    # Installed apps
    tk.Label(app_frame, text="Installed Apps:").pack(anchor=tk.W, pady=(10,0))
    installed_var = tk.StringVar()
    installed_combo = ttk.Combobox(app_frame, textvariable=installed_var, state="readonly")
    installed_combo.pack(fill=tk.X, pady=2)
    
    # Browse button
    tk.Button(app_frame, text="Browse for App...", command=lambda: browse_and_fill()).pack(pady=5)
    
    # App details frame
    details_frame = tk.LabelFrame(dialog, text="App Details")
    details_frame.pack(fill=tk.X, padx=10, pady=5)
    
    tk.Label(details_frame, text="Shortcut (e.g., WIN+R):").pack(anchor=tk.W)
    shortcut_entry = tk.Entry(details_frame)
    shortcut_entry.pack(fill=tk.X, pady=2)
    
    tk.Label(details_frame, text="Command:").pack(anchor=tk.W)
    command_entry = tk.Entry(details_frame)
    command_entry.pack(fill=tk.X, pady=2)
    
    tk.Label(details_frame, text="Color (e.g., [255,0,0] or 'red') (optional):").pack(anchor=tk.W)
    color_entry = tk.Entry(details_frame)
    color_entry.pack(fill=tk.X, pady=2)
    
    # Color examples
    examples_frame = tk.Frame(details_frame)
    examples_frame.pack(pady=5)
    tk.Label(examples_frame, text="Examples: red, blue, [255,0,0], 255,0,0", fg="gray").pack()
    
    def load_installed_apps():
        """Load installed apps into the combo box"""
        try:
            found_apps = find_installed_apps()
            if found_apps:
                installed_combo['values'] = list(found_apps.keys())
                installed_combo.set("Select an installed app...")
            else:
                installed_combo['values'] = ["No apps found"]
        except Exception as e:
            installed_combo['values'] = [f"Error: {e}"]
    
    def on_preset_select(*args):
        if preset_var.get() in PRESET_APPS:
            app_config = PRESET_APPS[preset_var.get()]
            shortcut_entry.delete(0, tk.END)
            shortcut_entry.insert(0, app_config["shortcut"])
            command_entry.delete(0, tk.END)
            command_entry.insert(0, app_config["command"])
    
    def on_installed_select(*args):
        if installed_var.get() and installed_var.get() != "Select an installed app..." and installed_var.get() != "No apps found":
            found_apps = find_installed_apps()
            if installed_var.get() in found_apps:
                app_name = found_apps[installed_var.get()]
                shortcut_entry.delete(0, tk.END)
                shortcut_entry.insert(0, "WIN+R")
                command_entry.delete(0, tk.END)
                command_entry.insert(0, app_name)
    
    def browse_and_fill():
        app_name, full_path = browse_for_app()
        if app_name:
            shortcut_entry.delete(0, tk.END)
            shortcut_entry.insert(0, "WIN+R")
            command_entry.delete(0, tk.END)
            command_entry.insert(0, app_name)
    
    # Bind events
    preset_combo.bind('<<ComboboxSelected>>', on_preset_select)
    installed_combo.bind('<<ComboboxSelected>>', on_installed_select)
    
    # Load installed apps
    load_installed_apps()
    
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

# Visual tools
visual_frame = tk.LabelFrame(top_frame, text="Visual Tools")
visual_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

tk.Button(visual_frame, text="Key Map", command=create_key_map, bg="purple", fg="white").pack(side=tk.LEFT, padx=5)
tk.Button(visual_frame, text="Layer Status", command=create_layer_indicator, bg="green", fg="white").pack(side=tk.LEFT, padx=5)

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
6. Use "Key Map" to see the physical layout of your Keybow2040
7. Use "Layer Status" to see which layer is currently active
8. Edit keys directly in the text area or use the buttons above
9. Layer IDs must be 1-8, Key numbers must be 9-15 for content
"""
tk.Label(app, text=instructions, justify=tk.LEFT, fg="blue").pack(padx=10, pady=5)

app.mainloop()
