"""Lista los endpoints de la aplicación.

El conteo sale del esquema OpenAPI, no de `app.routes`: Starlette guarda cada
sub-router incluido como una entrada única, así que `app.routes` solo muestra
los endpoints de primer nivel y no los 36 reales.
"""

import sys

from app.main import app

METODOS = ("get", "post", "put", "patch", "delete")

esquema = app.openapi()
filas = []
for ruta, operaciones in sorted(esquema["paths"].items()):
    if not ruta.startswith("/api"):
        continue
    for metodo in METODOS:
        if metodo in operaciones:
            filas.append((metodo.upper(), ruta))

print(f"versión de la API : {app.version}")
print(f"endpoints bajo /api: {len(filas)}")
print()
for metodo, ruta in filas:
    resumen = ""
    print(f"  {metodo:<7} {ruta}{resumen}")

if len(sys.argv) > 1 and sys.argv[1] == "--salir":
    raise SystemExit(1 if len(filas) != 36 else 0)
