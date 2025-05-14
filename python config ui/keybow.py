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

                # Split value and optional color
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
app.title("Keybow Configurator")

tk.Button(app, text="Load Config", command=load_config).pack()
layer_select = ttk.Combobox(app, state="readonly")
layer_select.pack()
tk.Button(app, text="Show Keys", command=show_keys).pack()
keys_text = tk.Text(app, width=50, height=15)
keys_text.pack()
tk.Button(app, text="Save Config", command=save_config).pack()

app.mainloop()
