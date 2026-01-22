"""Configuración y constantes del paquete."""

BASE_URL = "https://www.indec.gob.ar"
SITEMAP_URL = "https://www.indec.gob.ar/Institucional/Indec/MapaSitio"
DEFAULT_SITEMAP_REGEX = "Nivel4"
HTTP_TIMEOUT = 30  # Timeout en segundos para peticiones HTTP

DATA_EXTENSIONS = (
    ".csv",
    ".xlsx",
    ".xls",
    ".xml",
    ".txt",
    ".json",
    ".parquet",
    ".zip",
    ".rar",
    ".dta",
    ".dbf",
    ".sav",
)

