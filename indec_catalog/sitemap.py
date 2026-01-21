"""Funciones para extraer URLs del sitemap XML del INDEC."""

import re
import xml.etree.ElementTree as ET
import requests
from typing import List

from indec_catalog.config import SITEMAP_URL, DEFAULT_SITEMAP_REGEX, HTTP_TIMEOUT


def extract_sitemap_urls(
    sitemap_url: str = SITEMAP_URL, regex_pattern: str = DEFAULT_SITEMAP_REGEX
) -> List[str]:
    """
    Extrae URLs del sitemap XML que coinciden con el patrón regex.
    
    Args:
        sitemap_url: URL del sitemap XML a procesar.
        regex_pattern: Patrón regex para filtrar URLs.
        
    Returns:
        Lista de URLs que coinciden con el patrón.
        
    Raises:
        requests.RequestException: Si falla la petición HTTP.
        ET.ParseError: Si el XML no es válido.
    """
    response = requests.get(sitemap_url, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    
    root = ET.fromstring(response.content)
    
    urls = []
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    
    for url_elem in root.findall(f".//{namespace}loc"):
        url = url_elem.text
        if url and re.search(regex_pattern, url):
            urls.append(url)
    
    return urls


def build_url(link: str, base_url: str) -> str:
    """
    Construye la URL del tema a partir del link del sitemap.
    
    Args:
        link: URL del sitemap (ej: "https://www.indec.gob.ar/Nivel4-Tema-1-2-3")
        base_url: URL base del sitio.
        
    Returns:
        URL completa del tema (ej: "https://www.indec.gob.ar/Nivel4/Tema/1/2/3")
    """
    # Extrae la parte después de la base URL y reemplaza guiones por barras
    basename = link.split("/")[-1].replace("-","/")
    url = f"{base_url}/{basename}"
    return url

