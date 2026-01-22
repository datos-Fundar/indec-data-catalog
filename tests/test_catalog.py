"""Tests para el módulo catalog."""

import pytest
from unittest.mock import patch, Mock

from indec_catalog.catalog import generate_catalog, generate_catalog_with_errors
from indec_catalog.models import Catalog, Archivo
from indec_catalog.config import BASE_URL


class TestGenerateCatalog:
    """Tests para generate_catalog."""
    
    @patch("indec_catalog.catalog.fetch_tema_data")
    @patch("indec_catalog.catalog.build_url")
    @patch("indec_catalog.catalog.extract_sitemap_urls")
    def test_generate_catalog_success(
        self,
        mock_extract,
        mock_build_url,
        mock_fetch,
    ):
        """Genera catálogo correctamente."""
        mock_extract.return_value = [
            "https://www.indec.gob.ar/Nivel4/Tema-123",
            "https://www.indec.gob.ar/Nivel4/Tema-456",
        ]
        mock_build_url.side_effect = lambda link, base: f"{base}/Nivel4/Tema/123"
        mock_fetch.return_value = {
            "tema": "Tema",
            "subtema": "Subtema",
            "agrupamiento": "Agrupamiento",
            "archivos": [
                {"nombre_archivo": "archivo.csv", "url": "http://example.com/archivo.csv"}
            ],
        }
        
        catalog = generate_catalog(show_progress=False)
        
        assert isinstance(catalog, list)
        assert len(catalog) == 2
        assert isinstance(catalog[0], Catalog)
        assert catalog[0].tema == "Tema"
        assert catalog[0].subtema == "Subtema"
        assert catalog[0].agrupamiento == "Agrupamiento"
        assert isinstance(catalog[0].archivos, list)
        assert len(catalog[0].archivos) == 1
        assert isinstance(catalog[0].archivos[0], Archivo)
        assert catalog[0].archivos[0].nombre_archivo == "archivo.csv"
        assert catalog[0].archivos[0].url == "http://example.com/archivo.csv"
    
    @patch("indec_catalog.catalog.fetch_tema_data")
    @patch("indec_catalog.catalog.build_url")
    @patch("indec_catalog.catalog.extract_sitemap_urls")
    def test_generate_catalog_skips_none_data(
        self,
        mock_extract,
        mock_build_url,
        mock_fetch,
    ):
        """Omite temas que retornan None."""
        mock_extract.return_value = [
            "https://www.indec.gob.ar/Nivel4/Tema-123",
        ]
        mock_build_url.side_effect = lambda link, base: f"{base}/Nivel4/Tema/123"
        mock_fetch.return_value = None
        
        catalog = generate_catalog(show_progress=False)
        
        assert len(catalog) == 0
    
    @patch("indec_catalog.catalog.fetch_tema_data")
    @patch("indec_catalog.catalog.build_url")
    @patch("indec_catalog.catalog.extract_sitemap_urls")
    def test_generate_catalog_filters_empty_files(
        self,
        mock_extract,
        mock_build_url,
        mock_fetch,
    ):
        """Filtra elementos con archivos vacíos."""
        mock_extract.return_value = [
            "https://www.indec.gob.ar/Nivel4/Tema-123",
            "https://www.indec.gob.ar/Nivel4/Tema-456",
        ]
        mock_build_url.side_effect = lambda link, base: f"{base}/Nivel4/Tema/123"
        mock_fetch.side_effect = [
            {
                "tema": "Tema",
                "subtema": "Subtema",
                "agrupamiento": "Agrupamiento",
                "archivos": [],  # Sin archivos, debe filtrarse
            },
            {
                "tema": "Tema2",
                "subtema": "Subtema2",
                "agrupamiento": "Agrupamiento2",
                "archivos": [
                    {"nombre_archivo": "archivo.csv", "url": "http://example.com/archivo.csv"}
                ],
            },
        ]
        
        catalog = generate_catalog(show_progress=False)
        
        assert len(catalog) == 1
        assert catalog[0].tema == "Tema2"
    


class TestGenerateCatalogWithErrors:
    """Tests para generate_catalog_with_errors."""
    
    @patch("indec_catalog.catalog.fetch_tema_data")
    @patch("indec_catalog.catalog.build_url")
    @patch("indec_catalog.catalog.extract_sitemap_urls")
    def test_generate_catalog_with_errors_tracks_errors(
        self,
        mock_extract,
        mock_build_url,
        mock_fetch,
    ):
        """Registra URLs con errores."""
        mock_extract.return_value = [
            "https://www.indec.gob.ar/Nivel4/Tema-123",
        ]
        url = f"{BASE_URL}/Nivel4/Tema/123"
        mock_build_url.return_value = url
        mock_fetch.return_value = None
        
        catalog, errors = generate_catalog_with_errors(show_progress=False)
        
        assert len(catalog) == 0
        assert len(errors) == 1
        assert errors[0] == url
    
    @patch("indec_catalog.catalog.fetch_tema_data")
    @patch("indec_catalog.catalog.build_url")
    @patch("indec_catalog.catalog.extract_sitemap_urls")
    def test_generate_catalog_with_errors_handles_exceptions(
        self,
        mock_extract,
        mock_build_url,
        mock_fetch,
    ):
        """Maneja excepciones y las registra como errores."""
        mock_extract.return_value = [
            "https://www.indec.gob.ar/Nivel4/Tema-123",
        ]
        url = f"{BASE_URL}/Nivel4/Tema/123"
        mock_build_url.return_value = url
        mock_fetch.side_effect = Exception("Error de conexión")
        
        catalog, errors = generate_catalog_with_errors(show_progress=False)
        
        assert len(catalog) == 0
        assert len(errors) == 1
        assert errors[0] == url

