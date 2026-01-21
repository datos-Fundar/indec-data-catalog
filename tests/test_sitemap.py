"""Tests para el módulo sitemap."""

import xml.etree.ElementTree as ET
import pytest
from unittest.mock import patch, Mock
import requests

from indec_catalog.sitemap import extract_sitemap_urls, build_url
from indec_catalog.config import BASE_URL


class TestExtractSitemapUrls:
    """Tests para extract_sitemap_urls."""
    
    def test_extract_urls_with_matching_pattern(self):
        """Extrae URLs que coinciden con el patrón."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://www.indec.gob.ar/Nivel4/Tema-123</loc>
            </url>
            <url>
                <loc>https://www.indec.gob.ar/Nivel4/Tema-456</loc>
            </url>
            <url>
                <loc>https://www.indec.gob.ar/otra-pagina</loc>
            </url>
        </urlset>"""
        
        mock_response = Mock()
        mock_response.content = xml_content.encode()
        mock_response.raise_for_status = Mock()
        
        with patch("indec_catalog.sitemap.requests.get", return_value=mock_response):
            urls = extract_sitemap_urls(regex_pattern="Nivel4")
            
        assert len(urls) == 2
        assert "https://www.indec.gob.ar/Nivel4/Tema-123" in urls
        assert "https://www.indec.gob.ar/Nivel4/Tema-456" in urls
    
    def test_extract_urls_no_matches(self):
        """Retorna lista vacía si no hay coincidencias."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://www.indec.gob.ar/otra-pagina</loc>
            </url>
        </urlset>"""
        
        mock_response = Mock()
        mock_response.content = xml_content.encode()
        mock_response.raise_for_status = Mock()
        
        with patch("indec_catalog.sitemap.requests.get", return_value=mock_response):
            urls = extract_sitemap_urls(regex_pattern="Nivel4")
            
        assert len(urls) == 0
    
    def test_extract_urls_http_error(self):
        """Lanza excepción si falla la petición HTTP."""
        with patch("indec_catalog.sitemap.requests.get", side_effect=requests.RequestException()):
            with pytest.raises(requests.RequestException):
                extract_sitemap_urls()


class TestBuildUrl:
    """Tests para build_url."""
    
    def test_build_url_from_sitemap_link(self):
        """Construye correctamente la URL del tema."""
        link = "https://www.indec.gob.ar/Nivel4-Tema-123-Subtema-456"
        expected = f"{BASE_URL}/Nivel4/Tema/123/Subtema/456"
        
        result = build_url(link, BASE_URL)
        assert result == expected
    
    def test_build_url_simple(self):
        """Construye URL simple sin guiones."""
        link = "https://www.indec.gob.ar/Nivel4-Tema-123"
        expected = f"{BASE_URL}/Nivel4/Tema/123"
        
        result = build_url(link, BASE_URL)
        assert result == expected

