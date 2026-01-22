"""Módulo principal para generar el catálogo de datos del INDEC."""

from indec_catalog.config import BASE_URL
from indec_catalog.sitemap import extract_sitemap_urls, build_url
from indec_catalog.scraper import fetch_tema_data
from indec_catalog.models import Catalog
from typing import Any, List, Dict
from tqdm import tqdm


def generate_catalog_with_errors(
    show_progress: bool = True,
) -> tuple[List[Dict], List[str]]:
    """
    Genera el catálogo y retorna también las URLs que fallaron.
    
    Args:
        show_progress: Si mostrar barra de progreso (default: True).
        
    Returns:
        Tupla con (lista de diccionarios del catálogo, lista de URLs con errores).
    """
    links = extract_sitemap_urls()
    result: List[Dict] = []
    errors: List[str] = []
    
    iterable = tqdm(links, desc="Procesando links") if show_progress else links
    
    for link in iterable:
        url = build_url(link, BASE_URL)
        
        try:
            tema_data = fetch_tema_data(url)
            if tema_data is not None:
                result.append(tema_data)
            else:
                errors.append(url)
        except Exception:
            errors.append(url)
    
    return result, errors


def generate_catalog(
    show_progress: bool = True,
) -> List[Catalog]:
    """
    Genera un catálogo con todas las fuentes de datos del INDEC.
    
    Args:
        show_progress: Si mostrar barra de progreso (default: True).
        
    Returns:
        Lista de diccionarios con las claves: tema, subtema, agrupamiento, archivos.
        Cada archivo es un diccionario con 'nombre_archivo' y 'url'.
        
    Raises:
        requests.RequestException: Si falla la conexión con el sitemap.
    """
    result, _ = generate_catalog_with_errors(show_progress)

    return [
        Catalog.model_validate(x) 
        for x in result if x['archivos'] != []
    ]