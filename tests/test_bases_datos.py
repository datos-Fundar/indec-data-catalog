"""Tests para el módulo bases_datos."""

import pytest
from unittest.mock import patch, Mock

from indec_catalog.bases_datos import scrape_bases_datos
from indec_catalog.models import Catalog, Archivo
from indec_catalog.config import BASE_URL, BASES_DATOS_URL


class TestScrapeBasesDatos:
    """Tests para scrape_bases_datos."""

    def test_tab1_eph_with_strong(self):
        """Patrón tab1: L1 (p font-color-violeta), L2 (sub_enc_salud_tit), L3 (strong). Agrupamiento incluye strong."""
        html = """
        <html>
            <body>
                <div class="tabContent">
                    <p class="font-color-violeta">Encuesta Permanente de Hogares (EPH)</p>
                    <div class="sub_enc_salud_tit">Bases de microdatos</div>
                    <div class="sub_enc_salud_cont">
                        <strong>Base individual y hogar. Total aglomerados EPH.</strong>
                        <strong>Tercer trimestre 2025.</strong>
                        <a href="/ftp/eph/EPH_usu_3_Trim_2025_txt.zip">Formato txt</a>
                        <a href="/ftp/eph/EPH_usu_3_Trim_2025_xls.zip">Formato xls</a>
                    </div>
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
        assert result[0].tema == "Bases de datos"
        assert result[0].subtema == "Encuesta Permanente de Hogares (EPH)"
        assert "Tercer trimestre 2025." in result[0].agrupamiento
        assert "Bases de microdatos" in result[0].agrupamiento
        assert result[0].agrupamiento == "Bases de microdatos | Tercer trimestre 2025."
        assert len(result[0].archivos) == 2
        assert result[0].archivos[0].url == f"{BASE_URL}/ftp/eph/EPH_usu_3_Trim_2025_txt.zip"

    def test_tab2_encuestas_salud(self):
        """Patrón tab2: un L1 (Encuestas de salud) y varios L2 (Documentos, Base de datos, 2018)."""
        html = """
        <html>
            <body>
                <div class="tabContent">
                    <p class="font-color-violeta">Encuestas de salud</p>
                    <div class="sub_enc_salud_tit">Documentos metodológicos</div>
                    <div><a href="/ftp/encoprac/cuestionario.txt">Cuestionario</a></div>
                    <div class="sub_enc_salud_tit">Base de datos</div>
                    <ul><li><a href="/ftp/encoprac/base.txt">Base txt</a></li></ul>
                    <div class="sub_enc_salud_tit">2018</div>
                    <ul><li><a href="/ftp/enfr/enfr2018.rar">ENFR 2018</a></li></ul>
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

        assert len(result) == 3
        by_agrup = {c.agrupamiento: c for c in result}
        assert "Documentos metodológicos" in by_agrup
        assert "Base de datos" in by_agrup
        assert "2018" in by_agrup
        assert all(c.subtema == "Encuestas de salud" for c in result)
        assert by_agrup["Base de datos"].archivos[0].nombre_archivo == "Base txt"
        assert by_agrup["2018"].archivos[0].url.endswith("enfr2018.rar")

    def test_tab4_gastos_multi_encuesta(self):
        """Patrón tab4: dos L1 (p fontsize20 por encuesta), cada uno con L2 Bases de datos y enlaces."""
        html = """
        <html>
            <body>
                <div class="tabContent">
                    <p class="fontsize20 font-color-violeta">Encuesta Nacional de Gastos de los Hogares 2017 / 2018</p>
                    <div class="sub_enc_salud_tit">Bases de datos</div>
                    <ul><li><a href="/ftp/engho/engho2018_gastos.zip">Base de gastos</a></li></ul>
                    <p class="fontsize20 font-color-violeta">Encuesta Nacional de Gastos de los Hogares 2012 / 2013</p>
                    <div class="sub_enc_salud_tit">Bases de microdatos</div>
                    <ul><li><a href="/ftp/engho/bases_datos_engho2012.rar">Bases de datos</a></li></ul>
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

        assert len(result) == 2
        r1 = next(c for c in result if "2017" in c.subtema)
        r2 = next(c for c in result if "2012" in c.subtema)
        assert r1.subtema == "Encuesta Nacional de Gastos de los Hogares 2017 / 2018"
        assert r1.agrupamiento == "Bases de datos"
        assert len(r1.archivos) == 1 and r1.archivos[0].nombre_archivo == "Base de gastos"
        assert r2.subtema == "Encuesta Nacional de Gastos de los Hogares 2012 / 2013"
        assert r2.agrupamiento == "Bases de microdatos"
        assert r2.archivos[0].url.endswith("bases_datos_engho2012.rar")

    def test_strong_without_level2(self):
        """Caso borde: solo L1 y strong antes del enlace; agrupamiento usa el strong."""
        html = """
        <html>
            <body>
                <div class="tabContent">
                    <p class="font-color-violeta">Sección única</p>
                    <strong>Período 2024.</strong>
                    <a href="/ftp/datos.xlsx">Datos</a>
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
        assert result[0].subtema == "Sección única"
        assert result[0].agrupamiento == "Período 2024."
        assert len(result[0].archivos) == 1

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
