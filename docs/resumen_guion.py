"""Resumen del estado del guion tras simplificarlo a nivel de segundo semestre.

Comprueba que están las cuatro personas, que los dos bloques suman diez minutos
exactos, que nadie se queda sin texto y que el reparto por personas sigue
casando con el backlog.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from docs import datos as d  # noqa: E402


def main() -> None:
    print("  Reparto de la exposicion")
    for bloque, ini, fin in d.bloques_con_tiempos():
        nombres = " + ".join(d.NOMBRE_CORTO[i] for i in bloque["integrantes"])
        print(f"    {ini // 60}:{ini % 60:02d} - {fin // 60}:{fin % 60:02d}   "
              f"{bloque['titulo']}  ({nombres})")
    total = d.bloques_con_tiempos()[-1][2]
    print(f"    total {total} s = {total / 60:.0f} min")

    print("\n  Tiempo asignado y texto hablado por persona")
    segundos = d.minutos_por_integrante()
    palabras = d.palabras_de_guion()
    for i in range(len(d.EQUIPO)):
        limite = segundos[i] * d.PALABRAS_POR_MINUTO / 60
        print(f"    {d.NOMBRE_CORTO[i].ljust(16)} {segundos[i]:3d} s "
              f"({segundos[i] / 60:.0f} min)   {palabras[i]:4d} palabras "
              f"({palabras[i] / limite * 100:.0f} % del cupo)")
    print(f"    {'suma':16} {sum(segundos.values()):3d} s "
          f"({sum(segundos.values()) / 60:.0f} min)   {sum(palabras.values()):4d} "
          f"palabras = {sum(palabras.values()) / d.PALABRAS_POR_MINUTO:.1f} min")

    print("\n  Diapositivas por persona")
    for i, entradas in sorted(d.guion_por_persona().items()):
        claves = [e["clave"] for e in entradas]
        print(f"    {d.NOMBRE_CORTO[i].ljust(16)} {len(claves)}  {claves}")

    print("\n  Tamano de los datos")
    print(f"    requisitos      {len(d.REQUISITOS_FUNCIONALES)} funcionales, "
          f"{len(d.REQUISITOS_NO_FUNCIONALES)} no funcionales, "
          f"{len(d.REQUISITOS_RESTRICCION)} de restriccion")
    print(f"    UML             {len(d.ACTORES)} actores, "
          f"{sum(len(v) for v in d.CASOS_DE_USO.values())} casos de uso")
    print(f"    backlog         {len(d.BACKLOG_SEPTIEMBRE)} tareas del sprint, "
          f"{len(d.TAREAS_SEPTIEMBRE)} tecnicas")
    print(f"    historias       {len(d.HISTORIAS)}")
    print(f"    base de datos   {len(d.NUCLEO_TABLAS)} tablas, "
          f"{len(d.EXTENSIONES_TABLAS)} extensiones, {len(d.KPIS)} indicadores")
    print("\n  El backlog casa con las claves de cada persona")
    for i in range(len(d.EQUIPO)):
        tareas = [t for t in d.BACKLOG_SEPTIEMBRE if t[3] == d.CLAVE[i]]
        print(f"    {d.NOMBRE_CORTO[i].ljust(16)} "
              f"{[t[0] for t in tareas]}")


if __name__ == "__main__":
    main()
