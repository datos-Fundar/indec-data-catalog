"""Funciones para extraer URLs del sitemap HTML del INDEC."""

import re
import requests
from typing import List
from bs4 import BeautifulSoup

from indec_catalog.config import SITEMAP_URL, DEFAULT_SITEMAP_REGEX, HTTP_TIMEOUT


def build_url(data_view: str, base_url: str) -> str:
    """
    Construye la URL del tema a partir del atributo data-view de un elemento <li> en la página del sitemap.
    
    Args:
        data_view: Valor del atributo data-view de un elemento <li> en la página del sitemap.
        base_url: URL base del sitio.
        
    Returns:
        URL completa del tema (ej: "https://www.indec.gob.ar/Nivel4/Tema/1/2/3")
    """
    
    url = f"{base_url}/{data_view}"
    return url


def extract_sitemap_urls(
    sitemap_url: str = SITEMAP_URL, regex_pattern: str = DEFAULT_SITEMAP_REGEX
) -> List[str]:
    """
    Extrae valores del atributo data-view de elementos <li> en la página del sitemap.
    Filtra los valores que comienzan o contienen el patrón regex.
    
    Args:
        sitemap_url: URL de la página del sitemap.
        regex_pattern: Patrón regex para filtrar valores de data-view.
        
    Returns:
        Lista de valores de data-view que coinciden con el patrón.
        
    Raises:
        requests.RequestException: Si falla la petición HTTP.
    """
    response = requests.get(sitemap_url, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    urls = []
    for li in soup.find_all('li', attrs={'data-view': True}):
        data_view = li.get('data-view')
        if data_view:
            data_view_str = str(data_view)
            if re.search(regex_pattern, data_view_str):
                urls.append(data_view_str)
    
    return urls

