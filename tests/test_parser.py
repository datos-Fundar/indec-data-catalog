"""Tests para el módulo parser."""

import pytest
from bs4 import BeautifulSoup

from indec_catalog.parser import (
    extract_data_links,
    parse_tema_info,
)
from indec_catalog.config import BASE_URL


class TestExtractDataLinks:
    """Tests para extract_data_links."""
    
    def test_extract_csv_link(self):
        """Extrae links de archivos CSV."""
        html = """
        <html>
            <body>
                <a href="/datos.csv">Datos CSV</a>
                <a href="https://example.com/external.xlsx">Excel externo</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        
        links = extract_data_links(soup, BASE_URL)
        
        assert len(links) == 2
        assert links[0]["nombre_archivo"] == "Datos CSV"
        assert links[0]["url"] == f"{BASE_URL}/datos.csv"
        assert links[1]["nombre_archivo"] == "Excel externo"
        assert links[1]["url"] == "https://example.com/external.xlsx"
    
    def test_extract_only_data_files(self):
        """Solo extrae archivos con extensiones de datos."""
        html = """
        <html>
            <body>
                <a href="/datos.csv">CSV</a>
                <a href="/pagina.html">HTML</a>
                <a href="/archivo.xlsx">Excel</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        
        links = extract_data_links(soup, BASE_URL)
        
        assert len(links) == 2
        nombres = [link["nombre_archivo"] for link in links]
        assert "CSV" in nombres
        assert "Excel" in nombres
        assert "HTML" not in nombres
    
    def test_normalize_relative_urls(self):
        """Normaliza URLs relativas correctamente."""
        html = """
        <html>
            <body>
                <a href="/datos.csv">Absoluta</a>
                <a href="datos.xlsx">Relativa</a>
                <a href="/../../datos.txt">Con ../..</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        
        links = extract_data_links(soup, BASE_URL)
        
        links_dict = {link["nombre_archivo"]: link["url"] for link in links}
        assert links_dict["Absoluta"] == f"{BASE_URL}/datos.csv"
        assert links_dict["Relativa"] == f"{BASE_URL}/datos.xlsx"
        assert links_dict["Con ../.."] == f"{BASE_URL}/datos.txt"


class TestParseTemaInfo:
    """Tests para parse_tema_info."""
    
    def test_parse_tema_info_success(self):
        """Extrae correctamente la información del tema."""
        html = """
        <html>
            <body>
                <div class="ruta-texto mb-3">Inicio> Tema> Subtema> Agrupamiento</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        
        info = parse_tema_info(soup)
        
        assert info is not None
        assert info["tema"] == "Tema"
        assert info["subtema"] == "Subtema"
        assert info["agrupamiento"] == "Agrupamiento"
    
    def test_parse_tema_info_not_found(self):
        """Retorna None si no encuentra la ruta."""
        html = """
        <html>
            <body>
                <div>Sin ruta</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        
        info = parse_tema_info(soup)
        
        assert info is None
    
    def test_parse_tema_info_insufficient_parts(self):
        """Retorna None si no hay suficientes partes."""
        html = """
        <html>
            <body>
                <div class="ruta-texto mb-3">Inicio> Tema> Subtema</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        
        info = parse_tema_info(soup)
        
        assert info is None

