import json
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# Global configuration object
config = {}

def load_config():
    path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if not path:
        return
    try:
        with open(path, "r") as f:
            global config
            config = json.load(f)
        layer_select['values'] = list(config['layers'].keys())
        layer_select.current(0)
        show_keys()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load config: {e}")

def show_keys(*_):
    layer_id = layer_select.get()
    keys_text.delete("1.0", tk.END)
    if layer_id in config["layers"]:
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
                    # Parse app configuration
                    app_part = value_part.split("APP -", 1)[1].strip()
                    if "->" in app_part:
                        shortcut_part, command_part = app_part.split("->", 1)
                        shortcut = shortcut_part.strip()
                        command = command_part.strip()
                        
                        # Extract color if present
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
                        # Simple app without command
                        keys[key] = {
                            "type": "app",
                            "shortcut": app_part
                        }
                else:
                    # Handle regular keys
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
    if layer_id in config["layers"]:
        config["layers"][layer_id]["keys"] = keys

def add_app_key():
    """Add a new app key with a dialog"""
    dialog = tk.Toplevel()
    dialog.title("Add App Key")
    dialog.geometry("400x300")
    
    tk.Label(dialog, text="Key Number:").pack()
    key_entry = tk.Entry(dialog)
    key_entry.pack()
    
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
    
    def save_app():
        try:
            key = key_entry.get().strip()
            shortcut = shortcut_entry.get().strip()
            command = command_entry.get().strip()
            color_text = color_entry.get().strip()
            
            if not key or not shortcut:
                messagebox.showerror("Error", "Key number and shortcut are required!")
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
            if layer_id in config["layers"]:
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
    
    tk.Label(dialog, text="Layer ID:").pack()
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
            layer_select['values'] = list(config['layers'].keys())
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
app.title("Keybow Configurator - App Launcher Support")
app.geometry("600x500")

# Top frame for controls
top_frame = tk.Frame(app)
top_frame.pack(fill=tk.X, padx=10, pady=5)

tk.Button(top_frame, text="Load Config", command=load_config).pack(side=tk.LEFT, padx=5)
tk.Button(top_frame, text="Save Config", command=save_config).pack(side=tk.LEFT, padx=5)
tk.Button(top_frame, text="Add Layer", command=add_layer).pack(side=tk.LEFT, padx=5)
tk.Button(top_frame, text="Add App Key", command=add_app_key).pack(side=tk.LEFT, padx=5)

# Layer selection
layer_frame = tk.Frame(app)
layer_frame.pack(fill=tk.X, padx=10, pady=5)
tk.Label(layer_frame, text="Layer:").pack(side=tk.LEFT)
layer_select = ttk.Combobox(layer_frame, state="readonly")
layer_select.pack(side=tk.LEFT, padx=5)
layer_select.bind('<<ComboboxSelected>>', show_keys)

# Keys display
keys_frame = tk.Frame(app)
keys_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

tk.Label(keys_frame, text="Keys Configuration (Format: Key X: CODE or Key X: APP - SHORTCUT -> COMMAND)").pack()

keys_text = tk.Text(keys_frame, width=70, height=20)
keys_text.pack(fill=tk.BOTH, expand=True)

# Instructions
instructions = """
Instructions:
- Regular keys: Key X: CODE [R, G, B]
- App keys: Key X: APP - WIN+R -> notepad [255, 128, 0]
- Use "Add App Key" button for easy app key creation
- Use "Add Layer" button to create new layers
"""
tk.Label(app, text=instructions, justify=tk.LEFT, fg="blue").pack(padx=10, pady=5)

app.mainloop()
