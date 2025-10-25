import asyncio
import os
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)
from magnet2torrent import Magnet2Torrent, FailedToFetchException


def convert_magnet_to_torrent_file(
    console: Console,
    magnet_uri: str,
    output_dir: str = "./torrent_cache",
) -> str | None:
    """
    Fetch torrent metadata from a magnet link and save as .torrent file,
    with a Rich progress bar for visual feedback.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    async def _retrieve_metadata_task():
        m2t = Magnet2Torrent(magnet_uri)

        console.print(f"[bold yellow]🔍 Searching swarm for torrent metadata...[/bold yellow]")

        with Progress(
            SpinnerColumn(),
            BarColumn(bar_width=30),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("[bold cyan]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Connecting to peers...", total=100)

            try:
                # Start metadata retrieval
                retrieve_task = asyncio.create_task(m2t.retrieve_torrent())
                pct = 0

                while not retrieve_task.done():
                    # Simulate progress for visual feedback
                    await asyncio.sleep(0.2)
                    if pct < 90:
                        pct += 1
                        progress.update(task, completed=pct)

                filename, torrent_data = await retrieve_task
                

                # When finished — instantly fill the bar
                progress.update(task, completed=100, description="Metadata retrieved!")
                
                console.print("[bold green]We are almost there...[/bold green]")
                console.print(f"[bold magenta]Finishing up ![/bold magenta]")

                safe_filename = filename if filename else m2t.info_hash
                final_output_path = os.path.join(output_dir, f"{safe_filename}.torrent")

                with open(final_output_path, "wb") as f:
                    f.write(torrent_data)

                return final_output_path

            except FailedToFetchException:
                progress.stop()
                console.print("\n[bold red]❌ Failed to retrieve metadata.[/bold red] Peer discovery timed out or failed.")
                return None

            except Exception as e:
                progress.stop()
                console.print(f"\n[bold red]❌ An unexpected error occurred:[/bold red] {e}")
                return None

    # Run the async task synchronously
    final_path = asyncio.run(_retrieve_metadata_task())

    if final_path:
        console.print(f"\n[bold green]Conversion Complete![/bold green]")
        console.print(f"File saved to: [yellow]{final_path}[/yellow]")

    return final_path
