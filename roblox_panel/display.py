from datetime import datetime
from typing import List, Optional
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.console import Group

from roblox_panel.models import Universe, ServerInstance, LogEntry, MetricSnapshot


def make_universe_summary(universe: Universe, latest_metric: Optional[MetricSnapshot] = None) -> Panel:
    txt = Text()
    txt.append(f"{universe.name}\n", style="bold white")
    txt.append(f"Universe ID: {universe.universe_id} | Root Place: {universe.root_place_id}\n", style="dim")
    txt.append(f"Creator: {universe.creator_name}\n", style="dim")
    txt.append("Active CCU: ", style="bold cyan")
    txt.append(f"{universe.active_players:,}", style="bold yellow")
    
    if latest_metric:
        txt.append(f"  |  Servers: {latest_metric.server_count}", style="dim")
        txt.append(f"  |  Avg FPS: {latest_metric.avg_fps:.1f}", style="dim")
    
    return Panel(txt, title="[bold green]Universe Info[/bold green]", border_style="green")


def make_servers_table(servers: List[ServerInstance]) -> Table:
    table = Table(title="Live Game Instances", expand=True, box=None)
    table.add_column("Server ID", style="dim", no_wrap=True)
    table.add_column("Place ID", justify="right")
    table.add_column("Players", justify="center")
    table.add_column("FPS", justify="right")
    table.add_column("Ping", justify="right")
    table.add_column("Uptime", justify="right")

    if not servers:
        table.add_row("No active servers found", "-", "0/0", "0.0", "0ms", "0m")
        return table

    for s in servers:
        # highlight instances with struggling frame rate
        fps_style = "green" if s.fps >= 55.0 else "yellow" if s.fps >= 35.0 else "bold red"
        ping_style = "green" if s.ping_ms < 100 else "yellow" if s.ping_ms < 200 else "red"

        uptime_min = s.uptime_seconds // 60
        uptime_str = f"{uptime_min}m" if uptime_min < 60 else f"{uptime_min // 60}h {uptime_min % 60}m"

        table.add_row(
            s.server_id[:12] + "...",
            str(s.place_id),
            f"{s.player_count}/{s.max_players}",
            f"[{fps_style}]{s.fps:.1f}[/{fps_style}]",
            f"[{ping_style}]{s.ping_ms:.0f}ms[/{ping_style}]",
            uptime_str,
        )
    return table


def make_logs_panel(logs: List[LogEntry], max_entries: int = 14) -> Panel:
    table = Table(box=None, expand=True, show_header=False)
    table.add_column("Time", style="dim", width=9)
    table.add_column("Level", width=8)
    table.add_column("Server", style="cyan", width=10)
    table.add_column("Message", ratio=1)

    # take the latest events
    slice_logs = logs[-max_entries:] if len(logs) > max_entries else logs

    if not slice_logs:
        return Panel(Text("No incoming log stream events.", style="dim"), title="Server Logs", border_style="blue")

    for entry in slice_logs:
        lvl = entry.severity.upper()
        if lvl in ("ERROR", "CRITICAL"):
            lvl_style = "bold red"
        elif lvl in ("WARN", "WARNING"):
            lvl_style = "bold yellow"
        else:
            lvl_style = "green"

        time_str = entry.timestamp.strftime("%H:%M:%S")
        srv = entry.server_id[:8] if entry.server_id else "-"
        
        # truncate extra noisy lua error stack traces for the panel
        cleaned_msg = entry.message.split("\n")[0][:120]
        table.add_row(time_str, f"[{lvl_style}]{lvl:<5}[/{lvl_style}]", srv, cleaned_msg)

    return Panel(table, title="[bold blue]Recent Logs[/bold blue]", border_style="blue")


def build_dashboard_layout(
    universe: Universe,
    servers: List[ServerInstance],
    logs: List[LogEntry],
    latest_metric: Optional[MetricSnapshot] = None
) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="body", ratio=1)
    )
    layout["body"].split_row(
        Layout(name="servers", ratio=3),
        Layout(name="logs", ratio=2)
    )

    layout["header"].update(make_universe_summary(universe, latest_metric))
    layout["servers"].update(Panel(make_servers_table(servers), border_style="dim"))
    layout["logs"].update(make_logs_panel(logs))
    return layout
