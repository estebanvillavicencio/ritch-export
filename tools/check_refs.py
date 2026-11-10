"""Detecta referencias a identificadores que no existen en el módulo.

    python tools/check_refs.py

Se centra en la forma en que se rompe una pantalla: una llamada a la raíz de algo
no importado (`aOpciones(...)`) o el acceso a un objeto que no se importó
(`sesion.puede(...)`), que en el navegador aparecen como *«X is not defined»*.

Salida: 0 si todo está bien, 1 si hay referencias sin resolver.
"""

import builtins
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


def declarados_en(codigo: str, fuente: str) -> set[str]:
    """Símbolos visibles dentro del módulo."""
    nombres: set[str] = set()
    for bloque in re.findall(r"^import\s*\{([^}]+)\}", fuente, flags=re.M):
        nombres |= {s.strip() for s in bloque.split(",") if s.strip()}
    nombres |= set(re.findall(r"^import\s+(\w+)", fuente, flags=re.M))
    for patron in (
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)",
        r"\b(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)",
        r"\bclass\s+([A-Za-z_$][\w$]*)",
    ):
        nombres |= set(re.findall(patron, codigo))
    # Parámetros de funciones y flechas.
    for params in re.findall(r"\(([^()]*)\)\s*(?:=>|\{)", codigo):
        for p in params.split(","):
            p = p.strip().strip("{}[]").split("=")[0].strip().lstrip(".").strip()
            if re.fullmatch(r"[A-Za-z_$][\w$]*", p or ""):
                nombres.add(p)
    nombres |= set(re.findall(r"\b([A-Za-z_$][\w$]*)\s*=>", codigo))
    # Desestructuración de objeto y de array.
    for bloque in re.findall(r"\{([^{}]*)\}\s*=\s*[^=]", codigo):
        for nombre in bloque.split(","):
            nombre = nombre.split(":")[0].strip().strip("{}[]").lstrip(".")
            if re.fullmatch(r"[A-Za-z_$][\w$]*", nombre or ""):
                nombres.add(nombre)
    for bloque in re.findall(r"\[([^\[\]]*)\]\s*=\s*[^=]", codigo):
        for nombre in bloque.split(","):
            nombre = nombre.split(":")[0].strip().strip("{}[]").lstrip(".")
            if re.fullmatch(r"[A-Za-z_$][\w$]*", nombre or ""):
                nombres.add(nombre)
    for bloque in re.findall(r"\bfor\s*\(([\s\S]{0,120}?)\bof\b", codigo):
        bloque = re.sub(r"^[^{}\[\]]*[\[{]", "", bloque)
        for nombre in bloque.split(","):
            nombre = nombre.strip().strip("{}[]")
            if re.fullmatch(r"[A-Za-z_$][\w$]*", nombre or ""):
                nombres.add(nombre)
    return nombres


def main() -> int:
    fallos: list[str] = []
    modulos = [p for p in sorted(JS.rglob("*.js")) if p.name != "api.js"]
    print(f"Revisados {len(modulos)} módulos.\n")

    known = set(dir(builtins)) | GLOBALS_NAVEGADOR | PALABRAS_CLAVE

    for ruta in modulos:
        fuente = ruta.read_text(encoding="utf-8", newline="")
        codigo = re.sub(r"^\s*import[^;]*;", "", sin_cadenas(fuente), flags=re.M)
        declarados = declarados_en(codigo, fuente) | known

        # Raíces de llamadas: identificador no precedido por «.» y seguido de «(» o «.»
        for m in re.finditer(r"(?<![\w$.])([a-zA-Z_$][\w$]*)\s*(?=[(.])", codigo):
            nombre = m.group(1)
            if nombre in declarados:
                continue
            previo = codigo[max(0, m.start() - 30) : m.start()]
            if previo.rstrip().endswith(":"):
                continue  # valor de objeto: { clave: valor }
            if previo.rstrip().endswith(","):
                continue  # elemento de una lista o clave
            if re.search(r"(?:const|let|var|function|return|case)\s*$", previo):
                continue  # declaración, no referencia
            ln = codigo[: m.start()].count("\n") + 1
            fallos.append(
                f"{ruta.name}:{ln}  «{nombre}» no está definido ni importado"
                f"   …{previo[-25:].strip()} {nombre}"
            )

    print(f"{len(set(fallos))} referencia(s) sin resolver\n")
    for f in sorted(set(fallos)):
        print(f"  {f}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
