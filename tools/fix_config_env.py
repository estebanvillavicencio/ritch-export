"""Arregla dónde se busca el archivo `.env`.

`SettingsConfigDict(env_file=".env")` es una ruta **relativa**, que se resuelve
desde el directorio de trabajo. En tu computadora da igual porque siempre se
arranca desde `backend/`. En un hosting, en cambio, el directorio de trabajo es
la carpeta del usuario, así que el `.env` del proyecto no se leería: la
aplicación arrancaría con los valores por defecto sin avisar, entre ellos la
clave de las sesiones.

La solución es buscar el archivo en los sitios donde realmente puede estar, en
orden: la variable de entorno `RITECH_ENV_FILE` si se puso, la carpeta del
proyecto, y por último la carpeta de trabajo. El orden no importa mientras
encuentre uno; lo que importa es que encuentre el correcto.
"""

import pathlib

RUTA = pathlib.Path(
    r"C:\Users\esteb\OneDrive\Documentos\Proyecto predeterminado"
    r"\ritch-export\backend\app\config.py"
)

s = RUTA.read_text(encoding="utf-8", newline="")

viejo = '''"""Configuración de la aplicación (carga desde .env o variables de entorno)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="RITECH_", extra="ignore"
    )'''

nuevo = '''"""Configuración de la aplicación (carga desde .env o variables de entorno)."""

import os
import pathlib
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

#: Dónde puede estar el archivo `.env`. Se listan en orden de prioridad:
#:  · `RITECH_ENV_FILE`, si alguien lo indica explícitamente;
#:  · la carpeta del proyecto, que es donde está cuando se trabaja en local y
#    también cuando se despliega el proyecto entero en un hosting;
#:  · `backend/`, que es el directorio de trabajo cuando se arranca con uvicorn;
#:  · la carpeta de trabajo, que en un hosting es la del usuario.
_CARPETAS = [
    pathlib.Path(__file__).resolve().parent.parent.parent,   # raíz del proyecto
    pathlib.Path(__file__).resolve().parent.parent,          # backend/
    pathlib.Path.cwd(),
]


def _buscar_env() -> str:
    """El primer `.env` que exista, o una cadena vacía si no hay ninguno.

    Se usa el primero que se encuentre: si hay dos, gana el de mayor prioridad,
    que es el de la raíz del proyecto.
    """
    indicado = os.environ.get("RITECH_ENV_FILE")
    if indicado:
        return indicado
    vistos: list[str] = []
    for carpeta in _CARPETAS:
        candidato = carpeta / ".env"
        vistos.append(str(candidato))
        if candidato.is_file():
            return str(candidato)
    # Ninguno existe: se devuelve una ruta imposible en vez de "" porque
    # pydantic-settings trata "" como un archivo de nombre inválido.
    return os.path.join(vistos[0], ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_buscar_env(), env_prefix="RITECH_", extra="ignore"
    )'''

assert viejo in s, "no se encontró la clase Settings"
s = s.replace(viejo, nuevo, 1)
RUTA.write_text(s, encoding="utf-8", newline="")
print("  ok  config.py: el .env se busca en el proyecto, no en la carpeta de trabajo")
