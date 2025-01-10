# 🔄 Hot Reload

A lightweight Python module reloader that watches for file changes and automatically reloads modules during development.

## Features

- 🔍 Automatically detects and reloads Python modules when changes are saved
- 📁 Supports modules in both current directory and Utils/ subdirectory 
- 🎨 Clean console UI with colored output
- 🔄 Clear console option on each reload
- 🎯 Callback support for custom reload actions
- ⚡ Fast and lightweight

## Requirements

- Python 3.8 or higher

## Installation

No installation required - just copy `hot_reload.py` to your project directory.

Required dependencies:
- watchdog


# Usage

```bash
Arguments:
- `module_name`: Name of the module to watch (without .py extension)
- `-c, --clear`: Clear console on each reload
- `-noUI`: Disable UI elements
- `-v, --version`: Show version information

```

# Warning

This module was not tested with complex applications, but it should work with simple scripts.
# License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
