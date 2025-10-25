from gamethis.utils.helpers import parse
from dataclasses import dataclass
from typing import List, Optional
from rich.console import Console

BASE_URL = "https://fitgirl-repacks.site"

@dataclass
class SearchResult:
    title: str
    url: str

@dataclass
class SearchResults:
    results: List[SearchResult]
    previos_page: Optional[bool]
    next_page: Optional[bool]

def get_magnet_uri(uri: str) -> str | None:
    data = parse(uri)
    urls = data.select(".entry-content ul li a")
    
    for url in urls:
        if "magnet" in url.get("href"):
            magnet_url = url.get("href")
            # print(magnet_url)
            return magnet_url
    
    return None

def search_fitgirl(console: Console, query: str, page_number: int = 1) -> SearchResults | None:
    query = query.replace(" ", "+").strip().lower()
    
    url = f"{BASE_URL}/page/{page_number}/?s={query}"
    data = parse(url)
    articles = data.select("article")
    
    pages = data.select(".page-numbers")
    
    next_page: bool = False
    previos_page: bool = False
    
    for page in pages:
        if "next" in page.text.lower():
            next_page = True
            
        if "previous" in page.text.lower():
            previos_page = True

    results = []

    if not articles:
        return []
        
    for result in articles:
        try:
            title = result.select_one("h1.entry-title a").text
            
            if title:
                url = result.select_one("h1.entry-title a").get("href")
                
                results.append(
                    SearchResult(
                        title=title,
                        url=url
                    )
                )
                
        except Exception as e:
            console.log(f"Error scraping a result from fitgirl: {e}", style="bold red")
    
    return SearchResults(results, previos_page, next_page)
