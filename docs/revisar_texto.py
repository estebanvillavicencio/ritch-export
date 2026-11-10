"""Busca fragmentos corruptos en el texto de docs/datos.py.

Al escribir bloques largos de prosa a mano se cuelan trozos pegados o cortados
("qué le midsi la catación", "por qué-embarque va"). No se pueden ver en el
archivo porque se leen como español normal, así que se buscan con patrones:

  ·  palabras que mezclan vocabulario español con inglés en medio de la palabra;
  ·  un guion corto pegado a una palabra, tipo «CO-HUI-2026-0001x»;
  ·  palabras que empiezan por mayúscula en mitad de una frase sin ser nombre
     propio conocido;
  ·  caracteres de reemplazo (U+FFFD) que aparecen cuando algo se decodifica mal.
"""

import pathlib
import re
import sys

# Palabras inglesas que no deberían aparecer dentro de una palabra española.
INGLES = re.compile(
    r"\b\w*(?:ing|programming|shing|thing|some|ware|soft|code|test)\w*\b",
    re.IGNORECASE,
)

# Palabras que el patrón marca pero aquí sí son correctas: el nombre de la
# empresa, el de un integrante que se llama «Juanprogramming», y dos palabras
# castellanas que acaban en «ing» o «ar» y se confunden con inglés.
PERMITIDAS = {
    "ritch", "itech", "juanprogramming", "software", "contestar", "ninguna",
    "nadie", "camping", "shopping", "meeting", "testing", "string",
    "settings", "mapping", "warning", "building", "logging", "rendering",
    # Nombres de la propia herramienta, que el patrón marca como pegados.
    "rpoint", "yerror", "llayout", "lgrid", "rgrid", "qkey", "ror",
    # Inglés que sí va en un README de proyecto, y palabras castellanas que el
    # patrón confunde con inglés.
    "ascript", "escript", "pytest", "tests", "ningún", "algún",
    "test_portal_cliente", "check_js", "check_refs",
    # Nombres de herramientas y rutas, que el patrón ve como palabras pegadas.
    "code", "vscode", "nanywhere", "edrive", "nlocal", "yml", "pythonanywhere",
}

# Nombres propios que sí pueden estar en mayúscula dentro de una frase.
PROPIOS = re.compile(
    r"^(?:RiTech|Scrum|PostgreSQL|MySQL|SQLite|EUDR|Jira|Confluence|API|UML|"
    r"HTML|CSS|JavaScript|FastAPI|Andres|Juan|Dario|Camilo|Sebastian|Septiembre|"
    r"Antes|Ahora|Esta|Eso|Our|Aplicado|Terminada|Hecho)$"
)

SOSPECHOSO = re.compile(r"[a-záéíóúñ]-\s|\b(\w+)-\1\b|[a-z][A-Z][a-z]{3,}")


def revisar(ruta: pathlib.Path) -> int:
    texto = ruta.read_text(encoding="utf-8", newline="")
    lineas = texto.split("\n")
    hallazgos = 0

    for numero, linea in enumerate(lineas, 1):
        limpio = linea.strip()
        if limpio.startswith("#") or limpio.startswith('"') or limpio.startswith("'"):
            limpio = re.sub(r'^[\'"]|[\'"],?$', "", limpio)
        limpio = limpio.replace('\\"', " ").replace("f\"", " ")

        # 1. Caracteres de reemplazo: el texto se decodifico mal en algun punto.
        if "�" in linea:
            print(f"  L{numero}: caracter de reemplazo U+FFFD")
            print(f"      {limpio[:110]}")
            hallazgos += 1

        # 2. Ingles dentro de una palabra, o de una palabra que no es un nombre.
        for coincidencia in INGLES.findall(limpio):
            if coincidencia.lower() in PERMITIDAS:
                continue
            print(f"  L{numero}: posible ingles «{coincidencia}»")
            print(f"      {limpio[:110]}")
            hallazgos += 1
            break

        # 3. Palabras pegadas Rare: minuscula seguida de mayuscula en medio.
        for coincidencia in SOSPECHOSO.finditer(limpio):
            if coincidencia.group(1):
                continue
            palabra = coincidencia.group()
            if palabra.lower() in PERMITIDAS or "ritch" in palabra.lower():
                continue
            print(f"  L{numero}: palabra pegada «{palabra}»")
            print(f"      {limpio[:110]}")
            hallazgos += 1
            break

    print(f"  {hallazgos} fragmentos sospechosos en {ruta.name}")
    return hallazgos


if __name__ == "__main__":
    total = 0
    for nombre in sys.argv[1:] or ["docs/datos.py"]:
        total += revisar(pathlib.Path(nombre))
    sys.exit(1 if total else 0)
