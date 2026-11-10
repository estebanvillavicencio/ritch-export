"""Genera todos los entregables escritos del Sprint 2.

    python -m docs.generar_todo

Produce, en `docs/salida/`:

    diagrama_casos_de_uso.pdf
    diagrama_entidad_relacion.pdf
    1_Documento_Sprint2_RiTech.pdf
    1_Documento_Sprint2_RiTech.docx
    3_Guion_de_Exposicion.docx
    4_Guion_de_Exposicion.pptx
    2_Presentacion_Sprint2_RiTech.pptx
    5_Codigo_para_Exponer.docx

Lo primero que hace es rehacer `GUION_DETALLADO` a partir de `EXPOSICION`, para
que el guion de Word y el de PowerPoint digan exactamente lo mismo que la
presentación. Esa reescritura cambia `docs/datos.py` en disco, así que después
hay que recargar el módulo para que el resto de generadores vea el texto nuevo.
"""

from __future__ import annotations

import importlib
import time

from docs import (
    codigo,
    datos,
    diagrama_er,
    diagramas,
    documento,
    generar_guion_detallado,
    guion,
    guion_pptx,
    presentacion,
    word,
)


def main() -> None:
    inicio = time.perf_counter()

    print("Guion detallado")
    generar_guion_detallado.main()
    importlib.reload(datos)

    print("Diagramas")
    diagramas.diagrama_casos_de_uso(diagramas.SALIDA / "diagrama_casos_de_uso.pdf")
    diagrama_er.construir(diagrama_er.SALIDA / "diagrama_entidad_relacion.pdf")

    print("Documento (PDF)")
    documento.construir()

    print("Documento (Word)")
    word.construir()

    print("Guion de exposición (Word)")
    importlib.reload(guion)
    guion.construir()

    print("Guion de exposición (PowerPoint)")
    importlib.reload(guion_pptx)
    guion_pptx.construir()

    print("Presentación")
    importlib.reload(presentacion)
    presentacion.construir()

    print("Código para exponer")
    importlib.reload(codigo)
    codigo.main()

    print(f"\nListo en {time.perf_counter() - inicio:.1f} s. "
          f"Archivos en {documento.SALIDA}")


if __name__ == "__main__":
    main()
