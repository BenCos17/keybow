import json
import tkinter as tk
from tkinter import filedialog, ttk

def load_config():
    path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if not path:
        return
    with open(path, "r") as f:
        global config
        config = json.load(f)
    layer_select['values'] = list(config['layers'].keys())
    layer_select.current(0)
    show_keys()

def show_keys(*_):
    layer_id = layer_select.get()
    keys_text.delete("1.0", tk.END)
    if layer_id in config["layers"]:
        keys = config["layers"][layer_id]["keys"]
        for k, v in keys.items():
            keys_text.insert(tk.END, f"Key {k}: {v}\n")

def save_config():
    path = filedialog.asksaveasfilename(defaultextension=".json")
    if not path:
        return
    with open(path, "w") as f:
        json.dump(config, f, indent=2)

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
