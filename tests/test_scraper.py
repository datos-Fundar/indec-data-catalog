"""Tests para el módulo scraper."""

import pytest
from unittest.mock import patch, Mock
from bs4 import BeautifulSoup
import requests

from indec_catalog.scraper import fetch_tema_data
from indec_catalog.config import BASE_URL


class TestFetchTemaData:
    """Tests para fetch_tema_data."""
    
    def test_fetch_tema_data_success(self):
        """Obtiene correctamente los datos de un tema."""
        html = """
        <html>
            <body>
                <div class="ruta-texto mb-3">Inicio> Tema> Subtema> Agrupamiento</div>
                <a href="/datos.csv">Datos CSV</a>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html.encode()
        mock_response.url = f"{BASE_URL}/Nivel4/Tema/123"
        mock_response.raise_for_status = Mock()
        
        with patch("indec_catalog.scraper.requests.get", return_value=mock_response):
            data = fetch_tema_data(f"{BASE_URL}/Nivel4/Tema/123")
        
        assert data is not None
        assert data["tema"] == "Tema"
        assert data["subtema"] == "Subtema"
        assert data["agrupamiento"] == "Agrupamiento"
        assert "archivos" in data
        assert isinstance(data["archivos"], list)
        assert len(data["archivos"]) == 1
        assert data["archivos"][0]["nombre_archivo"] == "Datos CSV"
    
    def test_fetch_tema_data_error_page(self):
        """Retorna None si la página es de error."""
        html = "<html><body>Error</body></html>"
        
        mock_response = Mock()
        mock_response.content = html.encode()
        mock_response.url = f"{BASE_URL}/Error-Default"
        mock_response.raise_for_status = Mock()
        
        with patch("indec_catalog.scraper.requests.get", return_value=mock_response):
            data = fetch_tema_data(f"{BASE_URL}/Nivel4/Tema/123")
        
        assert data is None
    
    def test_fetch_tema_data_no_ruta(self):
        """Retorna None si no encuentra la ruta."""
        html = """
        <html>
            <body>
                <div>Sin ruta</div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html.encode()
        mock_response.url = f"{BASE_URL}/Nivel4/Tema/123"
        mock_response.raise_for_status = Mock()
        
        with patch("indec_catalog.scraper.requests.get", return_value=mock_response):
            data = fetch_tema_data(f"{BASE_URL}/Nivel4/Tema/123")
        
        assert data is None
    
    def test_fetch_tema_data_http_error(self):
        """Lanza excepción si falla la petición HTTP."""
        with patch(
            "indec_catalog.scraper.requests.get",
            side_effect=requests.RequestException()
        ):
            with pytest.raises(requests.RequestException):
                fetch_tema_data(f"{BASE_URL}/Nivel4/Tema/123")

