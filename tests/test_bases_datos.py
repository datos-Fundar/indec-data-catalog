"""Tests para el módulo bases_datos."""

import pytest
from unittest.mock import patch, Mock

from indec_catalog.bases_datos import scrape_bases_datos
from indec_catalog.models import Catalog, Archivo
from indec_catalog.config import BASE_URL, BASES_DATOS_URL


class TestScrapeBasesDatos:
    """Tests para scrape_bases_datos."""

    def test_returns_list_of_catalog(self):
        """Retorna lista de Catalog con tema, subtema, agrupamiento y archivos."""
        html = """
        <html>
            <body>
                <div class="tabContent">
                    <h3>Encuesta Permanente de Hogares</h3>
                    <a href="/ftp/cuadros/eph/datos.txt">Formato txt</a>
                    <a href="/ftp/otro/archivo.xlsx">Formato xls</a>
                </div>
                <div class="tabContent">
                    <h4>Encuestas de salud</h4>
                    <a href="/ftp/salud/base.csv">Base CSV</a>
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = html.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_response.encoding = "utf-8"

        with patch("indec_catalog.bases_datos.requests.get", return_value=mock_response):
            result = scrape_bases_datos()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(c, Catalog) for c in result)

        assert result[0].tema == "Bases de datos"
        assert result[0].subtema == "Encuesta Permanente de Hogares"
        assert result[0].agrupamiento == "Encuesta Permanente de Hogares"
        assert len(result[0].archivos) == 2
        assert all(isinstance(a, Archivo) for a in result[0].archivos)
        assert result[0].archivos[0].nombre_archivo == "Formato txt"
        assert result[0].archivos[0].url == f"{BASE_URL}/ftp/cuadros/eph/datos.txt"
        assert result[0].archivos[1].url == f"{BASE_URL}/ftp/otro/archivo.xlsx"

        assert result[1].tema == "Bases de datos"
        assert result[1].subtema == "Encuestas de salud"
        assert len(result[1].archivos) == 1
        assert result[1].archivos[0].url == f"{BASE_URL}/ftp/salud/base.csv"

    def test_skips_tab_with_no_data_links(self):
        """Omite bloques tabContent sin enlaces de datos."""
        html = """
        <html>
            <body>
                <div class="tabContent">
                    <h3>Sección con datos</h3>
                    <a href="/ftp/datos.txt">Datos</a>
                </div>
                <div class="tabContent">
                    <h3>Solo texto</h3>
                    <p>Sin enlaces a archivos.</p>
                    <a href="/pagina.html">Ir a página</a>
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = html.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_response.encoding = "utf-8"

        with patch("indec_catalog.bases_datos.requests.get", return_value=mock_response):
            result = scrape_bases_datos()

        assert len(result) == 1
        assert result[0].subtema == "Sección con datos"
        assert len(result[0].archivos) == 1

    def test_uses_fallback_title_when_no_heading(self):
        """Usa 'Bases de datos' como título si no hay heading en el bloque."""
        html = """
        <html>
            <body>
                <div class="tabContent">
                    <a href="/ftp/datos.csv">Datos CSV</a>
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = html.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_response.encoding = "utf-8"

        with patch("indec_catalog.bases_datos.requests.get", return_value=mock_response):
            result = scrape_bases_datos()

        assert len(result) == 1
        assert result[0].subtema == "Bases de datos"
        assert result[0].agrupamiento == "Bases de datos"

    def test_http_error_raises(self):
        """Lanza si falla la petición HTTP."""
        import requests

        with patch("indec_catalog.bases_datos.requests.get", side_effect=requests.RequestException()):
            with pytest.raises(requests.RequestException):
                scrape_bases_datos()

    def test_normalizes_relative_urls(self):
        """Normaliza URLs relativas con la base_url."""
        html = """
        <html>
            <body>
                <div class="tabContent">
                    <h3>Test</h3>
                    <a href="relativo/archivo.zip">ZIP</a>
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = html.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_response.encoding = "utf-8"

        with patch("indec_catalog.bases_datos.requests.get", return_value=mock_response):
            result = scrape_bases_datos(base_url=BASE_URL)

        assert len(result) == 1
        assert result[0].archivos[0].url == f"{BASE_URL}/relativo/archivo.zip"
