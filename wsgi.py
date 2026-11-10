"""Punto de entrada WSGI, para subir la aplicación a un hosting.

Los servicios que alojan una aplicación web en Python (PythonAnywhere, y en
general cualquier servidor con WSGI) no ejecutan `uvicorn` como lo hacemos en
local:·e theyeglobal WSGI application, una variable llamada `application` en un archivo que ellos mismos indican.

Este archivo es ese `application`. Es el mismo `app` de la API de siempre, sin
cambiar una línea: la aplicación no sabe si está en tu computadora o en un
servidor, y por eso el resto del proyecto no tiene que enterarse.

En PythonAnywhere: se crea el dominio, en «Configuración» se pone la ruta a este
archivo y el nombre de la variable `application`.
"""

import os
import pathlib
import sys

# El hosting arranca desde su carpeta de usuario, no desde el proyecto, así que
# hay que Tell el archivo dónde está `backend` para que lo encuentre. En local
# esto no hace nada porque ya estamos en la raíz.
RAIZ = pathlib.Path(__file__).resolve().parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
if str(RAIZ / "backend") not in sys.path:
    sys.path.insert(0, str(RAIZ / "backend"))

# En el hosting no se sirven los archivos estáticos con un servidor aparte, así
# que los que devuelve la API no pueden pedir `.env`. Las variables se leen de
# verdad y por eso se avisa de las dos que importan.
if not os.environ.get("RITECH_JWT_SECRET"):
    print("[aviso] RITECH_JWT_SECRET no está definida: las sesiones se firmarán "
          "con la clave de ejemplo y no serán seguras para nadie más.")

from app.main import app  # noqa: E402  (después de arreglar sys.path)

#: El nombre que el hosting busca.
application = app

#: Alias en minúsculas, que es como lo pide gunicorn y algunos paneles.
wsgi_app = app
