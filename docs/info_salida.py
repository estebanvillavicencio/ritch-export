"""Cuenta las páginas de los PDF de `docs/salida` y muestra su primer título.

    python -m docs.info_salida

Sirve para confirmar que los diagramas se generaron bien y para saber de un
vistazo qué hay en la carpeta de entregables, sin tener que abrir los archivos.
"""

import pathlib

import pymupdf

SALIDA = pathlib.Path(__file__).resolve().parent / "salida"

PDF = [
    "1_Documento_Sprint2_RiTech.pdf",
    "diagrama_casos_de_uso.pdf",
    "diagrama_entidad_relacion.pdf",
]

OTROS = [
    "1_Documento_Sprint2_RiTech.docx",
    "2_Presentacion_Sprint2_RiTech.pptx",
    "3_Guion_de_Exposicion.docx",
    "4_Guion_de_Exposicion.pptx",
]


def main() -> None:
    print("  PDF")
    for nombre in PDF:
        ruta = SALIDA / nombre
        if not ruta.exists():
            print(f"    {nombre:36} no está")
            continue
        with pymupdf.open(ruta) as doc:
            lineas = [x.strip() for x in doc[0].get_text().split("\n") if x.strip()]
            titulo = lineas[0] if lineas else ""
            print(f"    {nombre:36} {len(doc):2d} pág  "
                  f"{ruta.stat().st_size // 1024:4d} KB   {titulo[:50]}")

    print("  Word y PowerPoint")
    for nombre in OTROS:
        ruta = SALIDA / nombre
        if not ruta.exists():
            print(f"    {nombre:36} no está")
            continue
        print(f"    {nombre:36}     {ruta.stat().st_size // 1024:4d} KB")

    print("  Imágenes")
    for ruta in sorted(SALIDA.glob("*.png")):
        print(f"    {ruta.name:36}     {ruta.stat().st_size // 1024:4d} KB")


if __name__ == "__main__":
    main()
