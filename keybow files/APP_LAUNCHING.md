# Keybow2040 Multi-Layer Configuration

The Keybow2040 now supports **8 layers** with app launching and extensive customization!

## Layer System

### Layer Selection
- **Modifier Key**: Key 0 (green LED when not held)
- **Layer Selectors**: Keys 1-8 (light up when modifier is held)
- **Layer Content**: Keys 9-15 (7 keys per layer)

### Available Layers

1. **Layer 1 - Numpad** (Purple)
   - Keys 9-15: Numpad keys (0-6)

2. **Layer 2 - Strings** (Cyan)  
   - Keys 9-15: Custom text strings

3. **Layer 3 - Media** (Yellow)
   - Keys 9-15: Media controls (volume, play/pause, etc.)

4. **Layer 4 - Apps** (Red)
   - Keys 9-15: Application launchers

5. **Layer 5 - Gaming** (Green)
   - Keys 9-15: Gaming controls (WASD, Space, etc.)

6. **Layer 6 - Programming** (Purple)
   - Keys 9-15: Programming shortcuts (Ctrl+C, Ctrl+V, etc.)

7. **Layer 7 - System** (Orange)
   - Keys 9-15: System controls (Alt+Tab, Windows key, etc.)

8. **Layer 8 - Custom** (White)
   - Keys 9-15: Function keys (F1-F7)

## How to Use

1. **Hold the modifier key** (key 0, green LED)
2. **Press any layer selector** (keys 1-8) to switch to that layer
3. **Release both keys** - you're now in the selected layer
4. **Press any content key** (keys 9-15) to activate that function

## App Launching Feature

### How to Use Apps Layer

1. **Hold the modifier key** (key 0)
2. **Press key 4** (red LED) to access the Apps layer
3. **Press any key** (9-15) to launch the corresponding application

### Available Apps (Layer 4)

- **Key 9**: Notepad
- **Key 10**: Calculator
- **Key 11**: Paint
- **Key 12**: File Explorer
- **Key 13**: Command Prompt
- **Key 14**: Control Panel
- **Key 15**: Task Manager

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

## Layer Customization

### Creating New Layers

You can create up to 8 layers total. Each layer can have:
- **7 content keys** (keys 9-15)
- **Custom colors** for the layer and individual keys
- **Different key types**: regular keys, app launchers, or text strings

### Key Types Supported

1. **Regular Keys**: Standard keyboard keys and shortcuts
2. **App Launchers**: Launch applications using shortcuts
3. **Text Strings**: Type custom text when pressed
4. **Media Controls**: Volume, playback controls
5. **System Controls**: Windows shortcuts, function keys

## How It Works

The multi-layer system works by:
1. Using the modifier key to access layer selection mode
2. Selecting a layer with keys 1-8
3. Using keys 9-15 for the actual functionality
4. Each layer can have completely different functions

This gives you **56 total functions** (8 layers × 7 keys) that you can access with just 16 physical keys! 