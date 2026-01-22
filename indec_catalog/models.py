from pydantic import BaseModel

class Archivo(BaseModel):
    nombre_archivo: str
    url: str

class Catalog(BaseModel):
    # ...
    archivos: list[Archivo]