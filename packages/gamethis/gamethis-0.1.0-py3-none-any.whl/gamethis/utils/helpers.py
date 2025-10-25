from bs4 import BeautifulSoup
import httpx

def parse(url: str):
    html = httpx.get(url).text
    data = BeautifulSoup(html, 'html.parser')
    return data
