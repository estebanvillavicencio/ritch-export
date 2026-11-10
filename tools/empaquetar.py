"""Empaqueta el proyecto en `ritch-export-codigo.zip`, sin basura.

    python tools/empaquetar.py

`Compress-Archive` no sirve para esto por dos motivos:

  · no deja excluir archivos, y el proyecto tiene que ir sin la base de datos
    de desarrollo (`backend/ritch_dev.db`, que además está bloqueada mientras
    el servidor está corriendo) y sin los `__pycache__`;
  · si falla a mitad, deja un zip corrupto.

Este script arma el zip en una sola pasada, guardando solo lo que interesa y
avanzando la barra cada cien archivos para que no parezca colgado.

Qué entra: el código fuente, los archivos de SQL, el frontend, los generadores
de los entregables y los entregables ya generados en `docs/salida/`.

Qué no entra: la base de datos de desarrollo (se regenera con
`python -m app.seed --reset`), los `__pycache__`, los `.pyc`, las copias `.bak`
y los archivos temporales de los generadores.
"""

import pathlib
import sys
import zipfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DESTINO = RAIZ.parent / "ritch-export-codigo.zip"

#: Sufijos y carpetas que no van al zip.
EXCLUIR_SUFIJOS = (".pyc", ".db", ".sqlite", ".sqlite3", ".bak", ".tmp",
                   ".antes", ".old", ".log")
#: `uploads` va fuera porque se llena con los documentos que se suben al
#: arrancar el sistema. `.vscode` sí entra a propósito: trae la configuración
#: de depuración, y con ella F5 levanta el proyecto en cualquier máquina.
EXCLUIR_CARPETAS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".git",
                    ".idea", "uploads", "logs"}


def incluir(ruta: pathlib.Path) -> bool:
    """¿Este archivo va dentro del zip?"""
    if any(parte in EXCLUIR_CARPETAS for parte in ruta.parts):
        return False
    if ruta.suffix.lower() in EXCLUIR_SUFIJOS:
        return False
    # El .db de desarrollo cambia con cada semilla; que lo arme quien lo clone.
    if ruta.name.endswith(".db"):
        return False
    # El ejecutable de cloudflared pesa 54 MB y solo sirve para armar el enlace
    # público. `tools/levantar.py` lo vuelve a bajar si no lo encuentra.
    if ruta.suffix.lower() == ".exe":
        return False
    return True


def main() -> int:
    archivos = [p for p in RAIZ.rglob("*") if p.is_file() and incluir(p)]
    archivos.sort()

    if DESTINO.exists():
        DESTINO.unlink()

    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        for n, ruta in enumerate(archivos, 1):
            z.write(ruta, ruta.relative_to(RAIZ.parent))
            if n % 100 == 0:
                print(f"    {n}/{len(archivos)}", flush=True)

    tam = DESTINO.stat().st_size
    print(f"  {DESTINO.name}  {tam // 1024} KB  ·  {len(archivos)} archivos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
