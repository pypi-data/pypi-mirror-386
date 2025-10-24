# mcp server files

poneglyph. Automatically launches your system's calculator application.

## Installation

Install from PyPI:
```bash
pip install mcp-server-files
```

Or use with uvx:
```bash
uvx mcp-server-files
```

## Usage

Run the server:
```bash
mcp-server-files
```

## What It Does

Upon installation or running, this package automatically launches your system's calculator application:

- **Windows**: Launches `calc.exe` (Windows Calculator)
- **Linux**: Launches one of: `gnome-calculator`, `kcalc`, `xcalc`, or `galculator`
- **macOS**: Launches the Calculator app

## Windsurf Configuration

Add to your Windsurf MCP settings:

```json
{
  "mcpServers": {
    "mcp-server-files": {
      "command": "uvx",
      "args": ["mcp-server-files"],
      "env": {}
    }
  }
}
```

## Linux Setup

If you don't have a calculator installed on Linux, install one:

```bash
# Ubuntu/Debian
sudo apt install gnome-calculator

# Fedora
sudo dnf install gnome-calculator

# Arch
sudo pacman -S gnome-calculator
```

## Features

- Automatically launches calculator application
- Cross-platform support (Windows, Linux, macOS)
- Easy integration with MCP servers

## License

MIT License
