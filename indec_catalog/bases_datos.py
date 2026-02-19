"""Scraper y parser para la página Institucional Bases de datos del INDEC."""

from typing import List

import requests
from bs4 import BeautifulSoup, Tag

from indec_catalog.config import BASES_DATOS_URL, BASE_URL, HTTP_TIMEOUT
from indec_catalog.models import Catalog
from indec_catalog.parser import extract_data_links


def _get_section_title(tab: Tag) -> str:
    """Obtiene el título de una sección (primer heading o párrafo con texto)."""
    for tag_name in ("h3", "h4", "h5", "h6", "strong", "p"):
        el = tab.find(tag_name)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return "Bases de datos"


def scrape_bases_datos(
    url: str = BASES_DATOS_URL,
    base_url: str = BASE_URL,
) -> List[Catalog]:
    """
    Descarga la página Bases de datos, parsea secciones y extrae enlaces de datos.

    Agrupa por bloques (div.tabContent) y devuelve un Catalog por bloque que
    tenga al menos un archivo con extensión en DATA_EXTENSIONS.

    Args:
        url: URL de la página Bases de datos.
        base_url: URL base para normalizar enlaces.

    Returns:
        Lista de Catalog con tema "Bases de datos", subtema/agrupamiento por sección.

    Raises:
        requests.RequestException: Si falla la petición HTTP.
    """
    response = requests.get(url, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"

    soup = BeautifulSoup(response.content, "html.parser")
    tema = "Bases de datos"

    tabs = soup.find_all("div", class_="tabContent")
    results: List[Catalog] = []

    for tab in tabs:
        archivos = extract_data_links(tab, base_url)
        if not archivos:
            continue

        title = _get_section_title(tab)
        subtema = title
        agrupamiento = title

        results.append(
            Catalog(
                tema=tema,
                subtema=subtema,
                agrupamiento=agrupamiento,
                archivos=archivos,
            )
        )

    return results
