"""Genera docs/nombres.py con los integrantes del equipo, tomados del documento
«RiTech_Base_datos_relaciones_equipo_APIs.pdf» y de la presentación del proyecto.

Se hace por script para no transcribir los nombres a mano.
"""

import pathlib
import re

ORIGEN = pathlib.Path(
    r"C:\Users\esteb\AppData\Local\Temp\opencode\text\RiTech_Base_datos_relaciones_equipo_APIs.txt"
)
DESTINO = pathlib.Path(
    r"C:\Users\esteb\OneDrive\Documentos\Proyecto predeterminado\ritch-export\docs\nombres.py"
)

texto = ORIGEN.read_text(encoding="utf-8")

# El texto extraído separa cada palabra por saltos de línea; se aplana.
plano = re.sub(r"\s+", " ", texto.replace(" \n", " ").replace("\n ", " "))

# Los cuatro nombres aparecen justo antes de su descripción de aporte.
patron = re.compile(
    r"(Andres Esteban Villavicencio Ojeda|Juan Sebastian [\wÁÉÍÓÚáéíóúñÑ]+ [\wÁÉÍÓÚáéíóúñÑ]+"
    r"|Juan Camilo Araujo Portilla|Dario Sebastian Paz Cabrera)"
)
encontrados = []
for m in patron.finditer(plano):
    nombre = m.group(1)
    if nombre not in encontrados:
        encontrados.append(nombre)

if len(encontrados) < 4:
    raise SystemExit(f"Se esperaban 4 integrantes; se hallaron {len(encontrados)}: {encontrados}")

integrantes = encontrados[:4]

# Apellido familiar: la última palabra del nombre.
apellidos = [n.split()[-1] for n in integrantes]

contenido = '''"""Integrantes del equipo de trabajo.

Generado a partir de «RiTech_Base_datos_relaciones_equipo_APIs.pdf» y de la
presentación del proyecto. No editar a mano: la fuente es
`docs/generar_nombres.py`.
"""

EQUIPO = [
'''
for nombre in integrantes:
    contenido += f'    "{nombre}",\n'
contenido += ''']

APELLIDOS = [
'''
for apellido in apellidos:
    contenido += f'    "{apellido}",\n'
contenido += ''']
'''

DESTINO.write_text(contenido, encoding="utf-8", newline="\n")
print(f"docs/nombres.py generado con {len(integrantes)} integrantes")
for nombre in integrantes:
    print(f"  - {nombre}")
