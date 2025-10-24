# 2048 Text Environment

ASCII-based 2048 game as an MCP server for HUD SDK evaluation.

## Quick Start

### 1. Direct Python Module
```bash
uv run python -m hud_controller.server
```

### 2. MCP Inspector (Interactive UI)
```bash
npx @modelcontextprotocol/inspector uv run python -m hud_controller.server
```
Opens a browser UI to explore tools, resources, and test interactions.

### 3. Docker Debug Tool
```bash
# Build first
docker build -t hud-text-2048 .

# Validate all phases
hud debug hud-text-2048
```

### 4. Cursor Integration
Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "text-2048": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "hud-text-2048"]
    }
  }
}
```

### 5. HUD SDK Agent
See `examples/01_hello_2048.py` for a complete working example:
```bash
# Build the image first
docker build -t hud-text-2048 .

# Run the agent
python ../../examples/01_hello_2048.py
```

The agent will play 2048 and try to reach a target tile using the available tools.

## Available Tools

- **move** - Slide tiles: `move(direction="up|down|left|right")`
- **setup** - Initialize game: `setup(name="board", arguments={"board_size": 4})`
- **evaluate** - Check progress: `evaluate(name="max_number|efficiency")`

## Development Mode

### Option 1: Using `hud dev` (Recommended)

The easiest way to develop with hot-reload:

```bash
# Start development proxy
hud dev . --build

# This will:
# - Build/use hud-text-2048:dev image
# - Mount ./src for hot-reload
# - Provide HTTP endpoint for Cursor
# - Auto-restart on file changes
```

Add the URL from output to Cursor or click the deeplink.

### Option 2: Manual Setup

For manual control over the development environment:

1. Build dev image:
```bash
docker build -t hud-text-2048:dev
```

2. Add to `.cursor/mcp.json`:
```json
{
  "text-2048-dev": {
    "command": "npx",
    "args": [
      "reloaderoo", "--",
      "docker", "run", "-i", "--rm",
      "-v", "./src:/app/src:rw",
      "-e", "PYTHONPATH=/app/src",
      "hud-text-2048:dev"
    ]
  }
}
```

3. Edit code → Call `restart_server` → Changes apply instantly!