# indec-data-catalog

Catálogo automatizado de todas las fuentes de datos públicas del INDEC.

## Descripción

Este paquete extrae y organiza información sobre todas las fuentes de datos disponibles en el sitio web del INDEC, generando un catálogo estructurado en formato JSON.

## Instalación

El proyecto usa `uv` como gestor de paquetes. Para instalar:

```bash
uv sync
```

Para instalar también las dependencias de desarrollo (tests):

```bash
uv sync --group dev
```

## Uso

### Desde la línea de comandos

```bash
# Generar catálogo con configuración por defecto
uv run python -m indec_catalog.cli

# Especificar archivo de salida
uv run python -m indec_catalog.cli --output mi_catalogo.json

# Incluir archivo con URLs que fallaron
uv run python -m indec_catalog.cli --errors

```

### Desde Python

```python
import json
from indec_catalog import generate_catalog

# Generar el catálogo
catalog = generate_catalog(show_progress=True)

# Guardar en JSON
with open("catalogo_indec.json", "w", encoding="utf-8") as f:
    json.dump(catalog, f, indent=2, ensure_ascii=False)
```

## Estructura del Proyecto

```
indec_catalog/
├── __init__.py      # Exportaciones principales
├── config.py        # Configuración y constantes
├── sitemap.py       # Extracción de URLs del sitemap
├── scraper.py       # Scraping de páginas web
├── parser.py        # Parsing HTML y extracción de datos
├── catalog.py       # Orquestación principal
└── cli.py           # Interfaz de línea de comandos

tests/
├── test_sitemap.py
├── test_scraper.py
├── test_parser.py
└── test_catalog.py
```

## Tests

Ejecutar los tests:

```bash
uv run --group dev pytest
```

Con cobertura:

```bash
uv run --group dev pytest --cov=indec_catalog --cov-report=term-missing
```

## Automatización con GitHub Actions

El proyecto incluye un workflow de GitHub Actions (`.github/workflows/generate_catalog.yml`) que:

- Se ejecuta automáticamente cada domingo a medianoche
- Puede ejecutarse manualmente desde la pestaña Actions
- Ejecuta los tests antes de generar el catálogo
- Guarda el catálogo en formato JSON en el repositorio

## Desarrollo

El código está organizado en módulos independientes y testeables:

- **sitemap**: Extracción de URLs del sitemap XML
- **scraper**: Scraping HTTP de páginas
- **parser**: Parsing HTML y normalización de datos
- **catalog**: Lógica de orquestación y generación del catálogo
- **config**: Constantes y configuración centralizada 
