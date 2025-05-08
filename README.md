# Keybow Configurator

Keybow Configurator is a simple graphical interface built with Python and Tkinter, allowing users to manage and edit configurations for Keybow devices.

## Features

- Load and edit JSON configuration files for Keybow keymaps.
- Switch between different layers using a dropdown menu.
- View and update key assignments for each layer.
- Save the modified configuration back to a JSON file.

## Requirements

- Python 3.x
- Tkinter (comes pre-installed with Python)
- JSON file for configuration (structure as defined in your Keybow setup)

## Example Config

An example `config.json` is available in the `keybow` folder to help you get started with the proper format.

## Usage

 running from the exe:
 1. download the files from the latest release and copy the files in the keybow folder to the keybow itself
 2.run the exe to create the config.json and edit (there's an example one in the keybow files folder so import that to it

 
running from source:
1. Run the Python script to open the Keybow Configurator.
2. Click "Load Config" to load an existing JSON configuration file.
3. Select a layer from the dropdown to view its key assignments.
4. Modify the key assignments in the displayed text area.
5. Click "Save Config" to save the changes to a new JSON file.


the files in the keybow folder need to be copied to the drive the keybow shows as in the os
