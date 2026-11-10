"""Levanta la aplicación y, si se pide, el túnel público.

    python tools/levantar.py            # solo en tu computador
    python tools/levantar.py --tunel    # además, con enlace para compartir

Arranca dos procesos y se queda esperando a que respondan:

  1. la API, con los datos de ejemplo ya cargados;
  2. cloudflared, solo si se pasa `--tunel`, que da el enlace público.

Los dos quedan en segundo plano, sin ventanas, y sus registros se escriben en
`tools/logs/`. Los identificadores se guardan en `tools/logs/ritch.pids.json`
para que `python tools/bajar.py` los apague después.

Por qué este archivo: los procesos se caían cada vez que se cerraba la terminal
desde la que se habían lanzado, y eso hacía que la página dejara de abrir sin
que se viera por qué. Acá se lanzan desacoplados y queda registrado qué pasó.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
BACKEND = RAIZ / "backend"
LOGS = pathlib.Path(__file__).resolve().parent / "logs"
PIDS = LOGS / "ritch.pids.json"

#: Dónde puede estar el ejecutable de cloudflared.
CANDIDATOS = [
    pathlib.Path(__file__).resolve().parent / "bin" / "cloudflared.exe",
    pathlib.Path("C:/Users/esteb/AppData/Local/Temp/opencode/cloudflared.exe"),
    pathlib.Path("C:/Program Files/cloudflared/cloudflared.exe"),
]

#: De dónde se baja si no está en ninguno de los anteriores.
DESCARGA = ("https://github.com/cloudflare/cloudflared/releases/latest/download/"
            "cloudflared-windows-amd64.exe")

CUENTAS = [
    ("andres.villavicencio@ritch.com", "RiTech2026*", "Administrador"),
    ("juan.iguia@ritch.com", "RiTech2026*", "Administrador"),
    ("juan.araujo@ritch.com", "RiTech2026*", "Comercial"),
    ("dario.paz@ritch.com", "RiTech2026*", "Logística"),
    ("comprador@cafe-rotterdam.nl", "ClienteUE2026*", "Cliente europeo"),
]


# --------------------------------------------------------------------------- #
# Utilidades                                                                   #
# --------------------------------------------------------------------------- #
def log(*partes) -> None:
    print(*partes, flush=True)


def puerto_escuchando(puerto: int) -> int | None:
    """El identificador del proceso que escucha en ese puerto, o None."""
    if sys.platform == "win32":
        comando = ["netstat", "-ano", "-p", "TCP"]
        try:
            salida = subprocess.run(comando, capture_output=True, text=True,
                                    timeout=15).stdout
        except (OSError, subprocess.SubprocessError):
            return None
        for linea in salida.splitlines():
            if f":{puerto}" in linea and "LISTENING" in linea:
                partes = linea.split()
                if partes:
                    return int(partes[-1])
    return None


def esperar_http(url: str, segundos: int = 45) -> bool:
    """Espera a que la URL conteste."""
    limite = time.time() + segundos
    while time.time() < limite:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status < 500:
                    return True
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(1)
    return False


def opciones_sin_ventana() -> dict:
    """Creación de procesos sin ventana, solo en Windows."""
    if sys.platform != "win32":
        return {}
    return {"creationflags": subprocess.CREATE_NO_WINDOW}


def lanzar(comando: list[str], nombre_log: str, cwd: pathlib.Path) -> subprocess.Popen:
    """Arranca un proceso desacoplado, con su salida a un archivo."""
    LOGS.mkdir(exist_ok=True)
    salida = open(LOGS / nombre_log, "w", encoding="utf-8")
    proceso = subprocess.Popen(
        comando, cwd=str(cwd), stdout=salida, stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        **opciones_sin_ventana(),
    )
    return proceso


def leer_pids() -> dict:
    if not PIDS.exists():
        return {}
    try:
        return json.loads(PIDS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def guardar_pids(datos: dict) -> None:
    LOGS.mkdir(exist_ok=True)
    PIDS.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")


def buscar_cloudflared() -> pathlib.Path | None:
    for candidato in CANDIDATOS:
        if candidato.exists():
            return candidato
    en_el_path = shutil.which("cloudflared")
    return pathlib.Path(en_el_path) if en_el_path else None


def asegurar_cloudflared() -> pathlib.Path | None:
    """Devuelve el ejecutable, o lo baja si hace falta."""
    exe = buscar_cloudflared()
    if exe:
        return exe
    destino = CANDIDATOS[0]
    destino.parent.mkdir(parents=True, exist_ok=True)
    log(f"  no está cloudflared; se descarga ({destino.name})…")
    try:
        urllib.request.urlretrieve(DESCARGA, destino)
    except (urllib.error.URLError, OSError) as e:
        log(f"  [error] no se pudo descargar: {e}")
        return None
    return destino


# --------------------------------------------------------------------------- #
# Pasos                                                                        #
# --------------------------------------------------------------------------- #
def asegurar_datos() -> None:
    """Si la base está vacía, la siembra. No pisa datos que ya existan."""
    base = BACKEND / "ritch_dev.db"
    log("  Datos")
    if not base.exists():
        log("    no hay base de datos; se crea")
    subprocess.run([sys.executable, "-m", "app.seed", "--reset"], cwd=str(BACKEND),
                   env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                   **opciones_sin_ventana(), check=False)


def levantar_api(forzar: bool) -> int | None:
    existente = puerto_escuchando(8000)
    if existente and not forzar:
        log(f"  La API ya está corriendo (pid {existente}).")
        return existente

    log("  API")
    lanzar([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
          "api.log", BACKEND)
    if not esperar_http("http://localhost:8000/api/docs", 45):
        log("    [error] la API no respondió. Mira en tools/logs/api.log")
        return None
    pid = puerto_escuchando(8000)
    log(f"    arriba en http://localhost:8000 (pid {pid})")
    return pid


def levantar_tunel() -> str | None:
    exe = asegurar_cloudflared()
    if not exe:
        log("  [error] no hay cloudflared y no se pudo bajar. La API sigue viva,")
        log("          pero sin enlace público.")
        return None

    log("  Túnel")
    pids = leer_pids()
    anterior = pids.get("tunel_pid")

    proceso = lanzar(
        [str(exe), "tunnel", "--url", "http://localhost:8000", "--no-autoupdate"],
        "tunel.log", RAIZ,
    )

    # El enlace sale rápido, pero Cloudflare avisa que el dominio puede tardar
    # unos segundos en resolver. Con 30 de espera se llegaba a descartar un
    # enlace que sí funcionaba, así que se separa el hallazgo de la comprobación.
    limite = time.time() + 150
    enlace = None
    while time.time() < limite and not enlace:
        archivo = LOGS / "tunel.log"
        if archivo.exists():
            texto = archivo.read_text(encoding="utf-8", errors="ignore")
            encontrado = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", texto)
            if encontrado:
                enlace = encontrado.group(0)
                break
        time.sleep(2)

    if not enlace:
        log("    [error] el túnel no dio enlace. Mira en tools/logs/tunel.log")
        # Se borra el enlace viejo: si se deja, quien lo lea lo va a tomar por el
        # bueno cuando en realidad está caído. El túnel anterior se mantiene
        # hasta que haya uno nuevo que funcione.
        pids = leer_pids()
        if pids.get("enlace"):
            pids["enlace"] = None
            guardar_pids(pids)
        return None

    if not esperar_http(f"{enlace}/", 60):
        # Se muestra igual: el enlace es válido, solo que el dominio todavía no
        # resuelve. Tirarlo por no responder en un minuto sería engañoso.
        log(f"    {enlace}  (recién creado: si no abre, esperá unos segundos)")
    else:
        log(f"    {enlace}")

    # Recién con el túnel nuevo funcionando se cierra el anterior. Si se cerrara
    # antes, habría un rato sin ningún túnel, que es justo lo que pasaba.
    if anterior and anterior != proceso.pid:
        _terminar(anterior)

    pids = leer_pids()
    pids["tunel_pid"] = proceso.pid
    guardar_pids(pids)
    return enlace


def _terminar(pid: int) -> None:
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                       capture_output=True, timeout=30)
    else:
        try:
            os.kill(pid, 15)
        except OSError:
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tunel", action="store_true",
                    help="además levanta el túnel público")
    ap.add_argument("--reiniciar", action="store_true",
                    help="reinicia aunque ya esté corriendo")
    args = ap.parse_args()

    log("\n  Levantar RiTech")
    pids = leer_pids()
    if args.reiniciar:
        for nombre in ("tunel_pid", "api_pid"):
            if pids.get(nombre):
                log(f"  (reiniciando: {nombre} {pids[nombre]})")
                _terminar(pids[nombre])
        time.sleep(2)
        pids = {}

    asegurar_datos()
    api_pid = levantar_api(args.reiniciar)
    if not api_pid:
        return 1

    pids["api_pid"] = api_pid
    guardar_pids(pids)

    enlace = None
    if args.tunel:
        enlace = levantar_tunel()
        if enlace:
            pids = leer_pids()
            pids["enlace"] = enlace
            guardar_pids(pids)

    log("\n  Cuentas")
    for correo, clave, rol in CUENTAS:
        log(f"    {rol:16} {correo:34} {clave}")

    log("\n  Para entrar")
    log("    http://localhost:8000/#/login")
    if enlace:
        log(f"    {enlace}")
    log("\n  Para apagar:  python tools/bajar.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
