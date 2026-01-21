"""
Script legacy para generar catálogo de datos del INDEC.

NOTA: Este script requiere pandas y está mantenido solo por compatibilidad.
El código actualizado está en el paquete indec_catalog que genera JSON en lugar de DataFrames.
"""

import requests
import xml.etree.ElementTree as ET
from typing import List
import re
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd

BASE_URL = "https://www.indec.gob.ar"

def links_sitemap(sitemap_url: str = "https://www.indec.gob.ar/sitemap.xml", regex_search:str = "Nivel4") -> List[str]:
    """
    Obtiene los links del sitemap XML que contienen la substring regex_search.
    
    Args:
        sitemap_url: URL del sitemap XML a procesar.
        
    Returns:
        Lista de URLs que contienen "Nivel" en su ruta.
    """
    response = requests.get(sitemap_url)
    response.raise_for_status()
    
    root = ET.fromstring(response.content)
    
    links_nivel = []
    for url_elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        url = url_elem.text
        if url and re.search(regex_search, url):
            links_nivel.append(url)
    
    return links_nivel


def get_nivel_url(link: str) -> str:
    """
    Con el link obtengo la URL a la que hace la request
    """
    nivel = link.split("/")[-1].replace("-","/")
    url = f"{BASE_URL}/{nivel}"
    return url

def find_data_links(soup: BeautifulSoup, base_url: str = BASE_URL) -> dict[str, str]:
    """
    Encuentra los links de datos en la página que apuntan a archivos de datos.
    
    Args:
        soup: Objeto BeautifulSoup con el contenido HTML parseado.
        base_url: URL base para convertir URLs relativas a absolutas.
        
    Returns:
        Diccionario con el texto del link como clave y la URL completa como valor.
    """
    a_tags = soup.find_all('a', href=True)
    data_extensions = (
        '.csv', '.xlsx', '.xls', 
        '.xml', '.txt', '.json', 
        '.parquet', '.zip', '.rar',
        '.dta', '.dbf', '.sav'
        )
    
    links_dict = {}
    
    for tag in a_tags:
        href = tag.get('href', '').strip()
        if not href:
            continue
        
        href_lower = href.lower()
        if not any(href_lower.endswith(ext) for ext in data_extensions):
            continue
        
        link_text = tag.get_text(strip=True)
        if not link_text:
            pass
        
        if href.startswith('http://') or href.startswith('https://'):
            url = href
        elif href.startswith('/'):
            url = f"{base_url}{href}"
        elif href.startswith('/../../'):
            url = f"{base_url}{re.sub('/../../', '/', href)}"
        else:
            url = f"{base_url}/{href}"
        
        links_dict[link_text] = url
    
    return links_dict

def get_nivel_data(url: str) -> dict | None:
    """
    Con la URL a la que hace la request, obtengo el nombre del nivel, 
    que se encuentra en la ruta de la página (div class="ruta-texto mb-3").
    """
    response = requests.get(url, allow_redirects=True)
    response.raise_for_status()
    
    if "Error-Default" in response.url:
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    ruta_texto = soup.find('div', class_='ruta-texto mb-3')
    if not ruta_texto:
        return None
    
    data_nivel = {}
    texto = ruta_texto.get_text(strip=True)
    nivel_name = re.sub(r'Inicio> ', '', texto)
    nivel_name = re.sub(r' >|>', ', ', nivel_name)
    data_nivel["nivel"] = nivel_name.split(', ')[0]
    data_nivel["tema"] = nivel_name.split(', ')[1]
    data_nivel["subtema"] = nivel_name.split(', ')[2]
    data_nivel['archivos'] = find_data_links(soup)
    return data_nivel

def filter_nivel(url:str, base_url: str = BASE_URL, desagregacion: int = 3) -> bool:
    """
    Filtra los niveles que tienen determinada desagregación.
    
    Args:
        url: URL del nivel a filtrar.
        desagregacion: Desagregación a filtrar.
                
    Returns:
        True si el nivel tiene determinada desagregación, False en caso contrario.
    """
    url_ =re.sub(base_url+'/'+'Nivel\\d{1}/Tema/', '', url)
    url_parts = url_.split('/')
    return True if len(url_parts) == desagregacion else False

def get_links_report() -> List[dict]:
    """
    Devuelve un DataFrame reportando los links de manera organizada para facilitar la búsqueda
    """
    links = links_sitemap()
    nivel = 3
    result = []
    for link in tqdm(links, desc="Procesando links"):
        url = get_nivel_url(link)
        if filter_nivel(url, BASE_URL, nivel):
            nivel_data = get_nivel_data(url)
            if nivel_data is not None:
                result.append(nivel_data)
            else:
                print(f"No se encontró datos para la URL: {url}")
    return pd.DataFrame(result)


if __name__ == "__main__":
    df = get_links_report()