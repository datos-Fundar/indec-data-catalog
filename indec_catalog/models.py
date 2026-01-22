from pydantic import BaseModel

class Archivo(BaseModel):
    nombre_archivo: str
    url: str

class Catalog(BaseModel):
    tema: str
    subtema: str
    agrupamiento: str
    archivos: list[Archivo]