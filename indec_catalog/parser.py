"""Funciones para parsear HTML y extraer información de las páginas."""

import re
from typing import Dict, List
from bs4 import BeautifulSoup

from indec_catalog.config import BASE_URL, DATA_EXTENSIONS


def extract_data_links(soup: BeautifulSoup, base_url: str = BASE_URL) -> List[Dict[str, str]]:
    """
    Extrae los links de archivos de datos de una página HTML.
    
    Args:
        soup: Objeto BeautifulSoup con el contenido HTML parseado.
        base_url: URL base para convertir URLs relativas a absolutas.
        
    Returns:
        Lista de diccionarios con 'nombre_archivo' y 'url'.
    """
    a_tags = soup.find_all("a", href=True)
    links_list = []
    
    for tag in a_tags:
        href = tag.get("href", "").strip()
        if not href:
            continue
        
        href_lower = href.lower()
        if not any(href_lower.endswith(ext) for ext in DATA_EXTENSIONS):
            continue
        
        link_text = tag.get_text(strip=True)
        
        url = _normalize_url(href, base_url)
        links_list.append({
            "nombre_archivo": link_text,
            "url": url
        })
    
    return links_list


def _normalize_url(href: str, base_url: str) -> str:
    """
    Normaliza una URL relativa a una URL absoluta.
    
    Args:
        href: URL relativa o absoluta.
        base_url: URL base del sitio.
        
    Returns:
        URL absoluta normalizada.
    """
    if href.startswith(("http://", "https://")):
        return href
    elif href.startswith("/../../"):
        return f"{base_url}{re.sub('/../../', '/', href)}"
    elif href.startswith("../../"):
        return f"{base_url}{re.sub('../../', '/', href)}"
    elif href.startswith("/"):
        return f"{base_url}{href}"
    else:
        return f"{base_url}/{href}"


def parse_tema_info(soup: BeautifulSoup) -> Dict[str, str] | None:
    """
    Extrae la información del nivel desde el HTML parseado.
    
    Args:
        soup: Objeto BeautifulSoup con el contenido HTML.
        
    Returns:
        Diccionario con 'tema', 'subtema', 'agrupamiento' o None si no se encuentra.
    """
    ruta_texto = soup.find("div", class_="ruta-texto mb-3")
    if not ruta_texto:
        return None
    
    texto = ruta_texto.get_text(strip=True)
    nivel_name = re.sub(r"Inicio> ", "", texto)
    nivel_name = re.sub(r" >|>", ", ", nivel_name)
    
    parts = [part.strip() for part in nivel_name.split(", ")]
    
    if len(parts) < 3:
        return None
    
    return {
        "tema": parts[0],
        "subtema": parts[1],
        "agrupamiento": parts[2],
    }

