"""Vigila que la aplicación y el enlace público sigan arriba.

    python tools/vigilante.py            # corre en primer plano
    python tools/vigilante.py --instalar # además, se arranca al iniciar sesión

Qué hace, cada 20 segundos:

  · comprueba que la API responda en el puerto 8000; si no, la vuelve a
    levantar y vuelve a sembrar los datos si la base está vacía;
  · comprueba que el túnel esté vivo y que su enlace conteste; si no, crea uno
    nuevo;
  · guarda el enlace actual en `tools/logs/enlace.txt`, que es el archivo que hay
    que mirar para saber a dónde entrar después de un reinicio.

Por qué existe: el túnel de Cloudflare es temporal, se cae cuando el equipo se
suspende, cuando se reinicia o cuando se cae la red. Levantarlo a mano cada vez
es lo que venía pasando, y es fácil que en medio de la demostración la página
deje de abrir. Con esto, se vuelve a levantar sola.

Un aviso honesto: el enlace público **cambia cada vez que se crea un túnel
nuevo**, porque es un enlace temporal. Para que fuera fijo hace falta una cuenta
de Cloudflare con un dominio propio; ver el final de este archivo.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parent
LOGS = AQUI / "logs"
PIDS = LOGS / "ritch.pids.json"
ENLACE = LOGS / "enlace.txt"

#: Cada cuánto se revisa. Veinte segundos es suficiente para que nadie note la
#: interrupción, y no es tanto tráfico.
INTERVALO = 20

#: Si el túnel se cae más de esta cantidad de veces seguidas, se deja de
#: reintentarlo: casi siempre es que no hay internet, y un bucle infinito
#: llenaría el registro y no arreglaría nada.
MAX_FALLOS_SEGUIDOS = 8

#: Segundos mínimos entre dos intentos de crear un túnel. Cloudflare
#: demora —o rechaza— los túneles pedidos en ráfaga, y antes se caía y se
#: volvía a pedir cada 20 segundos. Con un minuto de margen alcanza para
#: que uno nuevo esté de pie, y no se abusa del servicio.
ESPERA_ENTRE_TUNELES = 60

#: Hora del último intento de túnel, para respetar la espera.
_ultimo_tunel: float = 0.0

PATRON_ENLACE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


# --------------------------------------------------------------------------- #
# Utilidades                                                                   #
# --------------------------------------------------------------------------- #
def log(mensaje: str) -> None:
    """Escribe con la hora, y también en un archivo."""
    hora = time.strftime("%H:%M:%S")
    linea = f"[{hora}] {mensaje}"
    print(linea, flush=True)
    try:
        LOGS.mkdir(exist_ok=True)
        with open(LOGS / "vigilante.log", "a", encoding="utf-8") as archivo:
            archivo.write(linea + "\n")
    except OSError:
        pass


def responde(url: str, segundos: int = 8) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=segundos) as r:
            return r.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except (urllib.error.URLError, OSError):
        return False


def opciones_sin_ventana() -> dict:
    if sys.platform != "win32":
        return {}
    return {"creationflags": subprocess.CREATE_NO_WINDOW}


# --------------------------------------------------------------------------- #
# Levantar cosas (delega en levantar.py, para no duplicar la lógica)          #
# --------------------------------------------------------------------------- #
def lanzar_levantar(con_args: list[str]) -> None:
    subprocess.run([sys.executable, str(AQUI / "levantar.py"), *con_args],
                   cwd=str(RAIZ), capture_output=True, timeout=300,
                   env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                   **opciones_sin_ventana())


def leer_enlace_guardado() -> str | None:
    """El enlace vigente, o None si no hay ninguno.

    La fuente es `ritch.pids.json`. `enlace.txt` existe para que el humano lo
    abra y sepa a dónde entrar, y puede contener un aviso como
    «(recreando el enlace...)»; por eso se lo lee al final y solo si parece una
    dirección de verdad.
    """
    if PIDS.exists():
        try:
            valor = json.loads(PIDS.read_text(encoding="utf-8")).get("enlace")
            if valor and PATRON_ENLACE.fullmatch(valor):
                return valor
        except json.JSONDecodeError:
            pass

    # Respaldo: el archivo de texto, siempre que tenga una dirección y no un
    # aviso.
    if ENLACE.exists():
        for linea in ENLACE.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if PATRON_ENLACE.fullmatch(linea):
                return linea
    return None


def guardar_enlace(enlace: str) -> None:
    LOGS.mkdir(exist_ok=True)
    ENLACE.write_text(enlace + "\n", encoding="utf-8")
    try:
        datos = json.loads(PIDS.read_text(encoding="utf-8")) if PIDS.exists() else {}
    except json.JSONDecodeError:
        datos = {}
    datos["enlace"] = enlace
    PIDS.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"enlace: {enlace}")


# --------------------------------------------------------------------------- #
# Revisiones                                                                   #
# --------------------------------------------------------------------------- #
def revisar_api() -> bool:
    if responde("http://localhost:8000/api/docs"):
        return True
    log("la API no responde; se vuelve a levantar")
    lanzar_levantar([])
    return responde("http://localhost:8000/api/docs")


def revisar_tunel() -> bool:
    """Devuelve True si hay un enlace vivo."""
    global _ultimo_tunel
    ahora = time.time()
    if ahora - _ultimo_tunel < ESPERA_ENTRE_TUNELES:
        return False  # todavía no toca volver a pedir uno
    _ultimo_tunel = ahora
    guardado = leer_enlace_guardado()
    if guardado and responde(f"{guardado}/", 10):
        # Se escribe igual: es el archivo que uno mira cuando la página no
        # abre, y tiene que estar al día aunque el túnel no se haya recreado.
        guardar_enlace(guardado)
        return True

    if guardado:
        log("el enlace guardado no responde; se crea uno nuevo")
    else:
        log("no hay enlace; se crea uno")
    # Se avisa en el archivo de texto, para que si alguien lo está mirando sepa
    # que espere en vez de recargar una dirección muerta.
    try:
        LOGS.mkdir(exist_ok=True)
        ENLACE.write_text("(recreando el enlace...)\n", encoding="utf-8")
    except OSError:
        pass

    lanzar_levantar(["--tunel"])
    recien = leer_enlace_guardado()
    if not recien:
        return False
    guardar_enlace(recien)
    return responde(f"{recien}/", 45)


# --------------------------------------------------------------------------- #
# Arranque automático                                                          #
# --------------------------------------------------------------------------- #
TAREA = "RiTech vigilante"


def carpeta_inicio() -> pathlib.Path:
    """La carpeta de Inicio del usuario, que Windows ejecuta al iniciar sesion."""
    return (pathlib.Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows"
            / "Start Menu" / "Programs" / "Startup")


def instalar_autoinicio() -> int:
    """Pone un acceso en la carpeta de Inicio para que el vigilante arranque solo.

    Se usa esa carpeta y no el Programador de tareas porque este ultimo pide
    permisos de administrador. La carpeta de Inicio funciona con cualquier
    usuario y hace lo mismo: correr el vigilante al iniciar sesion.
    """
    destino = carpeta_inicio()
    if not destino.is_dir():
        log(f"[error] no se encontro la carpeta de Inicio: {destino}")
        return 1

    acceso = destino / "RiTech.cmd"
    acceso.write_text(
        "@echo off\r\n"
        "REM Generado por tools/vigilante.py --instalar.\r\n"
        "REM Mantiene la aplicacion de RiTech SAS y su enlace publico encendidos.\r\n"
        f'cd /d "{RAIZ}"\r\n'
        f'"{sys.executable}" "{AQUI / "vigilante.py"}"\r\n',
        encoding="cp1252", errors="replace",
    )
    log(f"acceso creado: {acceso}")
    log("el vigilante arrancara solo la proxima vez que inicies sesion")
    log("para quitarlo, se borra ese archivo")
    return 0


def arrancar_ya() -> int:
    """Arranca el vigilante ahora, desacoplado de esta terminal.

    Es lo que hace que siga vivo: lanzado como proceso normal se cae junto con
    la ventana desde la que se llamo, que es justo lo que pasaba antes.
    """
    if sys.platform == "win32":
        # DETACHED_PROCESS (0x8) + CREATE_NEW_PROCESS_GROUP (0x200)
        banderas = 0x00000008 | 0x00000200
    else:
        banderas = 0

    proceso = subprocess.Popen(
        [sys.executable, str(AQUI / "vigilante.py")], cwd=str(RAIZ),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, creationflags=banderas,
        start_new_session=(sys.platform != "win32"),
    )
    time.sleep(4)
    if proceso.poll() is None:
        log(f"vigilante arrancado (pid {proceso.pid})")
        return 0
    log("[error] el vigilante no se quedo corriendo")
    return 1



# --------------------------------------------------------------------------- #
# Bucle                                                                        #
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--instalar", action="store_true",
                    help="deja el acceso en la carpeta de Inicio y sale")
    ap.add_argument("--arrancar", action="store_true",
                    help="arranca el vigilante desacoplado y sale")
    ap.add_argument("--una-vez", action="store_true",
                    help="revisa una sola vez y sale, sin quedarse esperando")
    args = ap.parse_args()

    if args.instalar:
        return instalar_autoinicio()
    if args.arrancar:
        return arrancar_ya()

    log("vigilante encendido")
    fallos = 0
    while True:
        try:
            if revisar_api():
                log("API bien")
                fallos = 0
            else:
                fallos += 1
        except Exception as e:  # noqa: BLE001  (el vigilante no debe morir)
            fallos += 1
            log(f"[aviso] la revisión de la API falló: {e}")

        if fallos >= MAX_FALLOS_SEGUIDOS:
            log(f"{fallos} revisiones seguidas sin que la API responda. "
                "Parece un problema de red o de la base de datos; se deja de "
                "reintentar para no llenar el registro.")
            return 1

        try:
            revisar_tunel()
        except Exception as e:  # noqa: BLE001
            log(f"[aviso] la revisión del túnel falló: {e}")

        if args.una_vez:
            return 0
        time.sleep(INTERVALO)


if __name__ == "__main__":
    sys.exit(main())
