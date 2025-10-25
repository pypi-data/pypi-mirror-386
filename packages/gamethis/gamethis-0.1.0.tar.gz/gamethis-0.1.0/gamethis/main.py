import typer
import questionary
import sys
from rich.console import Console
from rich.panel import Panel

from gamethis.utils.conversion import convert_magnet_to_torrent_file
from gamethis.utils.run import start_torrent_download
from gamethis.utils.style import custom_style
from gamethis.scraper.fitgirl import search_fitgirl, get_magnet_uri


app = typer.Typer(help="The fitgirl CLI: Search and download game repacks.")
console = Console()

def search_game(
        console: Console,
        query: str,
        page: int = 1
    ):
    """Search for a game repack from fitgirl."""
    
    with console.status(f"[bold green]Searching for {query}...", spinner="dots"):
        data = search_fitgirl(console, query, page)
    
    if data:
        console.rule("[bold magenta]Search Results")
        
        choices = [result.title for result in data.results]
        if data.previos_page:
            choices.insert(0, "previous")
            
        if data.next_page:
            choices.append("next")
        
        selection = questionary.select(
            "Select a game to download:",
            choices=choices,
            style=custom_style,
            qmark="\n🎮",
            pointer="➤"
        ).ask()
        
        for result in data.results:
            
            if selection == "previous" and data.previos_page:
                search_game(console, query, page - 1)
                break
            
            if selection == "next" and data.next_page:
                search_game(console, query, page + 1)
                break
            
            if result.title == selection:
                try:
                    magnet_uri = get_magnet_uri(result.url)
                    torrent_path = convert_magnet_to_torrent_file(console, magnet_uri)
                
                    if torrent_path:
                        try:
                            start_torrent_download(console, torrent_path)
                            sys.exit()
                        
                        except FileNotFoundError:
                            console.print("[bold red]❌ Torrent client not found.[/bold red]")
                            break
                            
                        except Exception as e:
                            console.print(f"[bold red]❌ Cannot launch torrent client:[/bold red] {e}")
                            break
                        
                except Exception as e:
                    console.print(f"[bold red]❌ Magnet to torrent conversion failed:[/bold red] {e}")
                    break
                
    else:
        console.print("No results found.")

@app.command()
def gamethis(
        query: str = typer.Argument(..., help="The game you want to search for."),
    ):
    search_game(console, query)
        
        
def main():
    app()
    
if __name__ == "__main__":
    main()
    
