"""Quita los escapes `\\uXXXX` que quedaron literales en el texto.

Al editar una línea con acentos a través de la herramienta, a veces el acento se
escribe como `\\u00f3` en vez de `ó`. En Python eso dentro de una cadena
normal no es un escape (las cadenas no interpretan `\\u`), así que el archivo
compila pero el entregable sale con `\\u00f3` impreso en medio de la frase.

Este script convierte esos cuatro caracteres a su carácter real.
"""

import pathlib
import re

p = pathlib.Path(
    r"C:\Users\esteb\OneDrive\Documentos\Proyecto predeterminado\ritch-export"
    r"\docs\datos.py"
)
s = p.read_text(encoding="utf-8", newline="")

patron = re.compile(r"\\u([0-9a-fA-F]{4})")
encontrados = patron.findall(s)
s = patron.sub(lambda m: chr(int(m.group(1), 16)), s)
p.write_text(s, encoding="utf-8", newline="")

print(f"  {len(encontrados)} escapes literales convertidos: "
      f"{sorted({chr(int(x, 16)) for x in encontrados})}")
