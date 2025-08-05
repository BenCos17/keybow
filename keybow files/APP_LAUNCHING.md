# App Launching Feature

The Keybow2040 now supports launching applications directly using keyboard shortcuts!

## How to Use

1. **Hold the modifier key** (key 0, green LED)
2. **Press key 4** (red LED) to access the Apps layer
3. **Press any key** in the Apps layer to launch the corresponding application

## Available Apps (Layer 4)

- **Key 4**: Notepad
- **Key 5**: Calculator
- **Key 6**: Paint
- **Key 7**: WordPad
- **Key 8**: File Explorer
- **Key 9**: Command Prompt
- **Key 10**: PowerShell
- **Key 11**: Control Panel
- **Key 12**: Windows Settings
- **Key 13**: Task Manager
- **Key 14**: Device Manager
- **Key 15**: Services

## Adding Custom Apps

To add your own applications, edit the `config.json` file and add entries like this:

```json
{
  "type": "app",
  "shortcut": "WIN+R",
  "command": "your-app-name",
  "color": [255, 128, 0]
}
```

### Shortcut Options

- **WIN+R**: Opens Run dialog and types the command
- **CTRL+ALT+T**: Opens terminal (Linux)
- **WIN**: Just presses Windows key
- **CTRL+ALT+DELETE**: System shortcuts

### Command Examples

- `notepad` - Opens Notepad
- `calc` - Opens Calculator
- `mspaint` - Opens Paint
- `explorer` - Opens File Explorer
- `cmd` - Opens Command Prompt
- `powershell` - Opens PowerShell
- `control` - Opens Control Panel
- `taskmgr` - Opens Task Manager
- `devmgmt.msc` - Opens Device Manager
- `services.msc` - Opens Services
- `ms-settings:` - Opens Windows Settings

## How It Works

The app launching feature works by:
1. Pressing the specified keyboard shortcut (e.g., WIN+R)
2. Waiting for the dialog to open
3. Typing the command
4. Pressing Enter

This simulates exactly what you would do manually to launch applications. 