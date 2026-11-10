"""Revisa el documento «Código para exponer» antes de entregarlo.

    python -m docs.verificar_codigo

Tres cosas que hay que mirar y que es fácil que salgan mal:

  1. que las tres funciones existan todavía en `reglas.py` y sigan siendo cortas;
  2. que la explicación cubra el código real: si alguien añadió una instrucción,
     la tabla por líneas quedaría corta y el documento mentiría;
  3. que el documento generado tenga el tamaño esperado, que es como se nota
     que una tabla se desbordó y quedó vacía.

Las instrucciones se cuentan con `ast` y no contando líneas: un `raise` de
cinco líneas es una sola instrucción, y el texto de un comentario de tres líneas
no es ninguna.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import sys
import textwrap

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(RAIZ))

from app.services import reglas  # noqa: E402
from docs.codigo import EXPLICACIONES, PIEZAS, PREGUNTAS, QUE_DECIR  # noqa: E402

SALIDA = RAIZ / "docs" / "salida" / "5_Codigo_para_Exponer.docx"

#: Una función con más instrucciones que esto ya no sirve para explicar en voz alta.
MAX_INSTRUCCIONES = 12

#: Nodos de `ast` que cuentan como instrucción. Los `Return` que cuelgan de un
#: `if` de una sola línea van incluidos; los `Expr` son los comentarios y las
#: constantes, que no hacen nada.
CUENTAN = (ast.Assign, ast.AnnAssign, ast.If, ast.For, ast.While, ast.Raise,
           ast.Return, ast.Try, ast.AugAssign, ast.Expr, ast.Match)


def instrucciones(nombre: str) -> list:
    """Las instrucciones de una función, en orden y sin contar los comentarios."""
    arbol = ast.parse(textwrap.dedent(inspect.getsource(getattr(reglas, nombre))))
    func = arbol.body[0]
    salida = []

    def visitar(nodos, sangria: str) -> None:
        for nodo in nodos:
            if not isinstance(nodo, CUENTAN):
                continue
            # Un `Expr` que es un texto es el comentario del bloque.
            if isinstance(nodo, ast.Expr) and isinstance(nodo.value, ast.Constant):
                continue
            if isinstance(nodo, (ast.If, ast.For, ast.While)):
                etiqueta = f"{sangria}{type(nodo).__name__.lower()}"
                fuente = ast.unparse(nodo.test if isinstance(nodo, ast.If) else nodo)
                salida.append((etiqueta, f"{etiqueta} {fuente}"))
                visitar(nodo.body, sangria + "  ")
                visitar(nodo.orelse, sangria + "  ")
                continue
            if isinstance(nodo, (ast.Try,)):
                etiqueta = f"{sangria}try"
                salida.append((etiqueta, "try"))
                visitar(nodo.body, sangria + "  ")
                for manejador in nodo.handlers:
                    salida.append((f"{sangria}except",
                                   f"except {ast.unparse(manejador.type)}"))
                    visitar(manejador.body, sangria + "  ")
                continue
            if isinstance(nodo, ast.Expr):
                # Una llamada suelta (como `.all()` al final de una cadena).
                salida.append((f"{sangria}llamada", ast.unparse(nodo)[:60]))
                continue
            etiqueta = f"{sangria}{type(nodo).__name__.lower()}"
            salida.append((etiqueta, f"{etiqueta} {ast.unparse(nodo)[:60]}"))

    visitar(func.body, "")
    return salida


def main() -> int:
    falla = 0

    print("  Las funciones existen y son cortas")
    for nombre, _titulo, _ in PIEZAS:
        if not hasattr(reglas, nombre):
            print(f"    !!  {nombre}: ya no está en reglas.py")
            falla += 1
            continue
        pasos = instrucciones(nombre)
        # El `def` no es una instrucción del cuerpo, pero sí ocupa una línea de
        # explicación, así que se cuenta aparte.
        total = len(pasos)
        marca = "ok  " if total <= MAX_INSTRUCCIONES else "!!  "
        if total > MAX_INSTRUCCIONES:
            falla += 1
        print(f"    {marca} {nombre}(): {total} instrucciones")

    print("\n  La explicación cubre el código real")
    for nombre, _t, _s in PIEZAS:
        if not hasattr(reglas, nombre):
            continue
        pasos = instrucciones(nombre)
        explicadas = len(EXPLICACIONES.get(nombre, []))
        diferencia = len(pasos) - explicadas
        marca = "ok  " if diferencia <= 1 else "!!  "
        if diferencia > 1:
            falla += 1
        print(f"    {marca} {nombre}(): {len(pasos)} instrucciones, "
              f"{explicadas} explicadas"
              + ("" if diferencia <= 1 else f"  → faltan {diferencia - 1}"))

    print("\n  Hay qué decir y qué contestar")
    for nombre, _t, _s in PIEZAS:
        decir = len(QUE_DECIR.get(nombre, []))
        preguntar = len(PREGUNTAS.get(nombre, []))
        marca = "ok  " if decir >= 3 else "!!  "
        if decir < 3:
            falla += 1
        print(f"    {marca} {nombre}(): {decir} frases, {preguntar} preguntas")

    print("\n  El archivo generado")
    if not SALIDA.exists():
        print(f"    !!  no existe {SALIDA.name}; corrél con python -m docs.codigo")
        return 1
    kb = SALIDA.stat().st_size / 1024
    marca = "ok  " if kb > 20 else "!!  "
    if kb <= 20:
        falla += 1
    print(f"    {marca} {SALIDA.name}  {kb:.0f} KB")
    if kb <= 20:
        print("       un documento tan chico suele significar que una tabla "
              "se desbordó y quedó vacía")

    print()
    if falla:
        print(f"  {falla} cosa(s) por revisar.")
        return 1
    print("  El documento está al día con el código.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
