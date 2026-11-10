"""Apaga la aplicación y el túnel público.

    python tools/bajar.py

Lee `tools/logs/ritch.pids.json`, que es lo que escribe `tools/levantar.py`, y
termina esos procesos. También revisa el puerto 8000 por si quedó algo escuchando
sin que esté registrado, que es lo que pasa si la API se levantó a mano.

Dejar la API corriendo tiene un efecto secundario molesto: ocupa el puerto 8000
y la siguiente vez que se levante algo ahí falla sin avisar.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

LOGS = pathlib.Path(__file__).resolve().parent / "logs"
PIDS = LOGS / "ritch.pids.json"


def vivo(pid: int) -> bool:
    try:
        subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                       capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return False
    salida = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                            capture_output=True, text=True, timeout=20).stdout
    return str(pid) in salida


def puerto_escuchando(puerto: int) -> int | None:
    salida = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True,
                            text=True, timeout=20).stdout
    for linea in salida.splitlines():
        if f":{puerto}" in linea and "LISTENING" in linea:
            partes = linea.split()
            if partes:
                return int(partes[-1])
    return None


def terminar(pid: int, etiqueta: str) -> bool:
    if not vivo(pid):
        print(f"  --  {etiqueta} (pid {pid}) ya no estaba")
        return False
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                   capture_output=True, timeout=30)
    print(f"  ok  {etiqueta} (pid {pid}) apagado")
    return True


def main() -> int:
    print("\n  Apagar RiTech")

    datos = {}
    if PIDS.exists():
        try:
            datos = json.loads(PIDS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            datos = {}

    for clave, etiqueta in (("tunel_pid", "túnel"), ("api_pid", "API")):
        if datos.get(clave):
            terminar(int(datos[clave]), etiqueta)
        time.sleep(1)

    # Por si la API quedó levantada a mano, sin pasar por este script.
    huerfano = puerto_escuchando(8000)
    if huerfano and huerfano != datos.get("api_pid"):
        print("  (había otra cosa en el puerto 8000, se apaga también)")
        terminar(huerfano, "proceso en el 8000")

    if PIDS.exists():
        PIDS.unlink()

    if puerto_escuchando(8000) is None:
        print("  el puerto 8000 quedó libre")
    return 0


if __name__ == "__main__":
    sys.exit(main())
