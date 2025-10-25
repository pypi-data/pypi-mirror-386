import os
import subprocess
import platform
import sys
from rich.console import Console
from rich.panel import Panel

def start_torrent_download(console: Console, torrent_path: str):
    system = platform.system()
    
    console.print(f"[bold cyan]Attempting to launch client on {system}...[/bold cyan]")
    
    if system == "Windows":
        os.startfile(torrent_path)
        
    elif system == "Darwin":
        subprocess.run(["open", torrent_path], check=True)
        
    elif system == "Linux":
        subprocess.run(["xdg-open", torrent_path], check=True)
        
    else:
        console.print("[bold red]Unsupported operating system.[/bold red]")
        return
        
    console.print(
        Panel(
            f"[bold green]Download Initiated![/bold green]\n"
            f"File: [dim]{os.path.basename(torrent_path)}[/dim]\n\n"
            f"Check your default torrent client (qBittorrent, etc.) to view the progress.",
            border_style="green"
        )
    )
    
    sys.exit()
    