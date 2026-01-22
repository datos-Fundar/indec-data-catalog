"""Script CLI para generar el catálogo de datos del INDEC."""

import argparse
import json
import sys
from pathlib import Path
from indec_catalog.catalog import generate_catalog, generate_catalog_with_errors
from indec_catalog.models import Catalog
from typing import List

def main():
    """Función principal del CLI."""
    parser = argparse.ArgumentParser(
        description="Genera un catálogo con todas las fuentes de datos del INDEC"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/catalogo_indec.json",
        help="Archivo de salida (default: data/catalogo_indec.json)",
    )
    parser.add_argument(
        "--errors",
        "-e",
        action="store_true",
        help="Incluir archivo con URLs que fallaron",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="No mostrar barra de progreso",
    )
    
    args = parser.parse_args()
    
    try:
        if args.errors:
            catalog : List[Catalog], errors : List[dict[str, str]] = generate_catalog_with_errors(
                show_progress=not args.no_progress,
            )
            
            output_path = Path(args.output)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump([x.model_dump() for x in catalog], f, indent=2, ensure_ascii=False)
            print(f"Catálogo guardado en: {output_path}")
            
            if errors:
                errors_path = output_path.with_suffix(".errors.txt")
                with open(errors_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(errors))
                print(f"Errores guardados en: {errors_path}")
                print(f"Total de errores: {len(errors)}")
        else:
            catalog : List[Catalog] = generate_catalog(
                show_progress=not args.no_progress,
            )
            
            Path("data").mkdir(parents=True, exist_ok=True)
            output_path = Path(args.output)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump([x.model_dump() for x in catalog], f, indent=2, ensure_ascii=False)
            print(f"Catálogo guardado en: {output_path}")
        
        print(f"Total de registros: {len(catalog)}")
        
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

