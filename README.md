# MCP Sys Info

MCP server that exposes system info (CPU, RAM, disk, GPU, processes) as tools for Cursor or any MCP client.

## Tools

- **system_summary** — CPU cores & usage, RAM, disk free, uptime
- **get_memory_info** — RAM and swap (total, used, free, %)
- **get_disk_info** — Per-drive usage (e.g. C:, D:)
- **get_top_processes** — Top N processes by memory or CPU (`sort_by`, `limit`)
- **get_gpu_summary** — NVIDIA GPU(s): utilization %, VRAM, temperature

## Install

```bash
cd server
pip install -r requirements.txt
```

## Run (stdio)

```bash
cd server
python server.py
```

## Cursor

In MCP settings, add a server that runs the above (e.g. command: `python`, args: path to `server.py`). Use stdio transport.

## Requirements

- Python 3.10+
- NVIDIA GPU optional: GPU tools work only with NVIDIA drivers and `nvidia-ml-py`; otherwise they return a friendly “not available” message.
