"""Comprobaciones estáticas del frontend (sin Node).

    python tools/check_js.py     sintaxis, símbolos importados, métodos de la API
    python tools/check_refs.py   referencias sin resolver

Salida: 0 si todo está bien, 1 si hay errores.
"""

import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
JS = RAIZ / "frontend" / "js"

GLOBALS_NAVEGADOR = {
    "Object", "Array", "String", "Number", "Boolean", "Symbol", "BigInt", "Math",
    "JSON", "Date", "Map", "Set", "WeakMap", "WeakSet", "Promise", "RegExp",
    "Error", "TypeError", "RangeError", "SyntaxError", "Proxy", "Reflect",
    "Infinity", "NaN", "undefined", "globalThis", "console", "window",
    "document", "localStorage", "sessionStorage", "location", "history",
    "navigator", "fetch", "URL", "URLSearchParams", "FormData", "Headers",
    "Event", "CustomEvent", "Node", "Element", "HTMLElement", "Intl",
    "setTimeout", "clearTimeout", "setInterval", "clearInterval",
    "requestAnimationFrame", "structuredClone", "Blob", "File", "FileReader",
    "alert", "parseInt", "parseFloat", "isNaN", "encodeURIComponent",
    "decodeURIComponent", "queueMicrotask",
}

PALABRAS_CLAVE = {
    "return", "const", "let", "var", "function", "async", "await", "if", "else",
    "for", "of", "in", "new", "try", "catch", "finally", "throw", "typeof",
    "instanceof", "this", "null", "true", "false", "delete", "void", "yield",
    "export", "default", "class", "extends", "super", "switch", "case", "break",
    "continue", "do", "while", "import", "from", "as", "static", "get", "set",
}


def sin_cadenas(src: str) -> str:
    """Sustituye por espacios comentarios y cadenas, conservando los saltos."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            fin = n if j < 0 else j + 2
            out.append("\n" * src.count("\n", i, fin))
            i = fin
            continue
        if c in "\"'`":
            comilla = c
            out.append(" ")
            i += 1
            while i < n and src[i] != comilla:
                if src[i] == "\\":
                    i += 1
                elif src[i] == "\n":
                    out.append("\n")
                i += 1
            i += 1
            out.append(" ")
            continue
        out.append(c)
        i += 1
    return "".join(out)


def balance(ruta: pathlib.Path, codigo: str, fallos: list[str]) -> None:
    pares = {")": "(", "}": "{", "]": "["}
    stack: list[tuple[str, int]] = []
    linea = 1
    for ch in codigo:
        if ch == "\n":
            linea += 1
        elif ch in "({[":
            stack.append((ch, linea))
        elif ch in ")}]":
            if not stack or stack[-1][0] != pares[ch]:
                fallos.append(f"{ruta.name}:{linea} delimitador desbalanceado '{ch}'")
                return
            stack.pop()
    for ch, ln in stack:
        fallos.append(f"{ruta.name}:{ln} '{ch}' sin cerrar")


def main() -> int:
    fallos: list[str] = []
    avisos: list[str] = []
    archivos = sorted(JS.rglob("*.js"))
    print(f"Analizando {len(archivos)} módulos JavaScript\n")

    for ruta in archivos:
        src = ruta.read_text(encoding="utf-8")
        codigo = sin_cadenas(src)
        balance(ruta, codigo, fallos)

        cuerpo = re.sub(r"^import[^;]+;\s*$", "", src, flags=re.M)
        for bloque, origen in re.findall(
            r"^import\s*\{([^}]+)\}\s*from\s*'([^']+)'", src, flags=re.M
        ):
            destino = (ruta.parent / origen).resolve()
            if not destino.exists():
                fallos.append(f"{ruta.name}: importa de un módulo inexistente: {origen}")
                continue
            defns = destino.read_text(encoding="utf-8")
            for simbolo in (s.strip() for s in bloque.split(",")):
                if not simbolo:
                    continue
                if not re.search(rf"\b{re.escape(simbolo)}\b", cuerpo):
                    avisos.append(f"{ruta.name}: import sin usar «{simbolo}»")
                patron = (
                    rf"export\s+(?:async\s+)?(?:function|class|const|let|var)\s+{re.escape(simbolo)}\b"
                )
                if not (
                    re.search(patron, defns)
                    or re.search(rf"export\s*\{{[^}}]*\b{re.escape(simbolo)}\b", defns)
                ):
                    fallos.append(f"{ruta.name}: importa «{simbolo}» pero {origen} no lo exporta")

    # Los métodos api.<ns>.<m>() deben existir en api.js
    api_src = (JS / "api.js").read_text(encoding="utf-8")
    grupos = dict(re.findall(r"^  (\w+): \{(.*?)^\  \},", api_src, flags=re.M | re.S))
    for ruta in archivos:
        if ruta.name == "api.js":
            continue
        codigo = sin_cadenas(ruta.read_text(encoding="utf-8"))
        for ns, metodo in re.findall(r"\bapi\.(\w+)\.(\w+)\s*\(", codigo):
            if ns not in grupos:
                fallos.append(f"{ruta.name}: api.{ns} no existe en api.js")
            elif not re.search(rf"^\s+{re.escape(metodo)}\s*:", grupos[ns], flags=re.M):
                fallos.append(f"{ruta.name}: api.{ns}.{metodo}() no existe en api.js")

    for a in avisos:
        print(f"  AVISO {a}")
    print()
    for f in fallos:
        print(f"  FALLA {f}")

    print()
    print("=" * 62)
    if fallos:
        print(f"{len(fallos)} error(es), {len(avisos)} aviso(s)")
    else:
        print(f"Correcto. {len(avisos)} aviso(s).")
    print("=" * 62)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
