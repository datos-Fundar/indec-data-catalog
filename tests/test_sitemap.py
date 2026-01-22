"""Tests para el módulo sitemap."""

import pytest
from unittest.mock import patch, Mock
import requests

from indec_catalog.sitemap import extract_sitemap_urls, build_url
from indec_catalog.config import BASE_URL


class TestExtractSitemapUrls:
    """Tests para extract_sitemap_urls."""
    
    def test_extract_urls_with_matching_pattern(self):
        """Extrae valores de data-view que coinciden con el patrón."""
        html_content = """
        <html>
            <body>
                <ul>
                    <li data-view="Nivel4/Tema/2/41/170">Censo 1970</li>
                    <li data-view="Nivel4/Tema/2/41/164">Censo 1980</li>
                    <li data-view="Otro/Tema/1/2/3">Otra página</li>
                </ul>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html_content.encode()
        mock_response.raise_for_status = Mock()
        
        with patch("indec_catalog.sitemap.requests.get", return_value=mock_response):
            urls = extract_sitemap_urls(regex_pattern="Nivel4")
            
        assert len(urls) == 2
        assert "Nivel4/Tema/2/41/170" in urls
        assert "Nivel4/Tema/2/41/164" in urls
    
    def test_extract_urls_no_matches(self):
        """Retorna lista vacía si no hay coincidencias."""
        html_content = """
        <html>
            <body>
                <ul>
                    <li data-view="Otro/Tema/1/2/3">Otra página</li>
                </ul>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html_content.encode()
        mock_response.raise_for_status = Mock()
        
        with patch("indec_catalog.sitemap.requests.get", return_value=mock_response):
            urls = extract_sitemap_urls(regex_pattern="Nivel4")
            
        assert len(urls) == 0
    
    def test_extract_urls_no_li_with_data_view(self):
        """Retorna lista vacía si no hay elementos li con data-view."""
        html_content = """
        <html>
            <body>
                <ul>
                    <li>Sin data-view</li>
                    <li class="test">Otro sin data-view</li>
                </ul>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html_content.encode()
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
    
    def test_build_url_from_data_view(self):
        """Construye correctamente la URL del tema desde data-view."""
        data_view = "Nivel4/Tema/2/41/170"
        expected = f"{BASE_URL}/Nivel4/Tema/2/41/170"
        
        result = build_url(data_view, BASE_URL)
        assert result == expected
    
    def test_build_url_simple(self):
        """Construye URL simple desde data-view."""
        data_view = "Nivel4/Tema/1/2/3"
        expected = f"{BASE_URL}/Nivel4/Tema/1/2/3"
        
        result = build_url(data_view, BASE_URL)
        assert result == expected

