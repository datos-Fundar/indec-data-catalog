"""Funciones para hacer scraping de páginas web."""

from typing import Dict
import requests
from bs4 import BeautifulSoup

from indec_catalog.config import BASE_URL, HTTP_TIMEOUT
from indec_catalog.parser import extract_data_links, parse_tema_info


def fetch_tema_data(url: str) -> Dict | None:
    """
    Obtiene los datos de un tema desde su URL.

    Args:
        url: URL del tema a procesar.
        
    Returns:
        Diccionario con 'tema', 'subtema', 'agrupamiento' y 'archivos', o None si hay error.
        
    Raises:
        requests.RequestException: Si falla la petición HTTP.
    """
    response = requests.get(url, allow_redirects=True, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    
    if "Error-Default" in response.url:
        return None
    
    soup = BeautifulSoup(response.content, "html.parser")
    tema_info = parse_tema_info(soup)
    if tema_info is None:
        return None
    
    archivos = extract_data_links(soup, BASE_URL)
    tema_info["archivos"]  = archivos
    return tema_info

