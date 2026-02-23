from mcp.server.fastmcp import FastMCP
import pynvml 
import psutil
import time

mcp = FastMCP(
    "sys_info",
    host="0.0.0.0",
    port=8000,
    json_response=True,
)
def _fmt_bytes(b):
    return f"{b / 1024**3:.2f} GB"

@mcp.tool()
async def system_summary() -> str:
    """Get system information."""
    cpu_count = psutil.cpu_count(logical=False)
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    uptime = time.time() - psutil.boot_time()
    root = "C:\\" if psutil.WINDOWS else "/"
    root_free = _fmt_bytes(psutil.disk_usage(root).free)
    root_total = _fmt_bytes(psutil.disk_usage(root).total)
    return f"""
    System Summary:
    - CPU: {cpu_count} cores, {cpu_percent}% usage
    - Memory: {_fmt_bytes(mem.used)} / {_fmt_bytes(mem.total)} ({mem.percent}%)
    - Uptime: {time.strftime("%H:%M:%S", time.gmtime(uptime))}
    - Disk: {root_free} / {root_total} free
    """
@mcp.tool()
async def get_memory_info() -> str:
    """Get memory information."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return f"""
    Memory Information:
    - Total: {_fmt_bytes(mem.total)}
    - Used: {_fmt_bytes(mem.used)}
    - Free: {_fmt_bytes(mem.free)}
    - Percent: {mem.percent}%
    - Swap Total: {_fmt_bytes(swap.total)}
    - Swap Used: {_fmt_bytes(swap.used)}
    - Swap Free: {_fmt_bytes(swap.free)}
    - Percent: {swap.percent}%
    """
@mcp.tool()
async def get_disk_info() -> str:
    """Get disk usage per drive/partition (e.g. C:, D:)."""
    lines = []
    for p in psutil.disk_partitions():
        if p.fstype == "cdrom" or not p.device:
            continue
        try:
            u = psutil.disk_usage(p.mountpoint)
            lines.append(
                f"{p.mountpoint}: total {_fmt_bytes(u.total)}, "
                f"used {u.percent}%, free {_fmt_bytes(u.free)}"
            )
        except (PermissionError, OSError):
            continue
    return "\n".join(lines) if lines else "No partitions found."

@mcp.tool()
async def get_top_processes(
    sort_by: str = "memory",
    limit: int = 15,) -> str:
    """Top N processes by memory or CPU. sort_by: 'memory' | 'cpu', limit: 1-30."""
    sort_by = (sort_by or "memory").lower()
    limit = max(1, min(30, limit or 15))
    key = "rss" if sort_by == "memory" else "cpu"
    rows = []
    for p in psutil.process_iter(attrs=["name", "pid", "memory_info", "cpu_percent", "status"]):
        try:
            i = p.info
            rss = (i.get("memory_info") or type("M", (), {"rss": 0})()).rss
            cpu = p.cpu_percent(interval=0) or 0
            name = (i.get("name") or "?")[:40]
            pid = i.get("pid", "?")
            st = (i.get("status") or "?")[:12]
            rows.append({"name": name, "pid": pid, "cpu": cpu, "rss_mb": rss / (1024 * 1024), "status": st})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if sort_by == "memory":
        rows.sort(key=lambda x: x["rss_mb"], reverse=True)
    else:
        rows.sort(key=lambda x: x["cpu"], reverse=True)
    lines = [f"{r['name']} (pid {r['pid']}): CPU {r['cpu']:.1f}%, RAM {r['rss_mb']:.1f} MB, {r['status']}" for r in rows[:limit]]
    return "\n".join(lines) if lines else "No processes."

@mcp.tool()
async def get_gpu_summary() -> str:
    """Per-GPU: name, utilization %, VRAM used/total, temperature (NVIDIA)."""
    try:
        pynvml.nvmlInit()
    except Exception as e:
        return f"NVIDIA GPU not available: {e}"
    lines = []
    try:
        n = pynvml.nvmlDeviceGetCount()
        for i in range(n):
            h = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(h)
            if isinstance(name, bytes):
                name = name.decode("utf-8", errors="replace")
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            used_gb = mem.used / (1024**3)
            total_gb = mem.total / (1024**3)
            try:
                temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
            except Exception:
                temp = "?"
            lines.append(f"GPU {i} ({name}): utilization {util.gpu}%, VRAM {used_gb:.2f}/{total_gb:.2f} GB, temp {temp}°C")
        return "\n".join(lines) if lines else "No GPUs."
    finally:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass

if __name__ == "__main__":
    mcp.run(transport="stdio")
    