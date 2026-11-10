"""Comprueba que los entregables nodigan cosas que ya no son ciertas.

    python -m docs.verificar_entregables

El resumen Simplificamos el Sprint 2 para un nivel de segundo semestre, pero los
generadores tienen textos escritos a mano, y en varios de ellos seguían cifras
que ya no aplican: «58 endpoints», «51 pruebas», «trece elementos», «seis
actores», «cinco tablas de extensión», «once módulos». Este script abre los
archivos ya generados y busca esas phrases, para que no vuelva a colarse una.

No abre Word ni PowerPoint con la aplicación: los .docx y .pptx son archivos zip,
así que se leen con `zipfile` y se buscan en el XML.
"""

import pathlib
import re
import sys
import zipfile

SALIDA = pathlib.Path(__file__).resolve().parent / "salida"

#: Frases que no pueden aparecer en ningún entregable, con el motivo.
PROHIBIDAS = {
    "58 operaciones": "contaba las operaciones de la API, ya no se dice",
    "58 endpoints": "contaba las rutas de la API, ya no se dice",
    "51 pruebas": "contaba las pruebas automáticas, ya no se dice",
    "treinta y siete casos": "el diagrama tiene 11 casos, no 37",
    "trece elementos": "el backlog tiene 7 tareas, no 13",
    "once épicas": "el backlog tiene 7 tareas, no 11",
    "seis actores": "el UML tiene 5 actores, no 6",
    "cinco tablas de extensión": "añadimos 3 tablas, no 5",
    "once módulos": "el sprint tiene 4 módulos, no 11",
    "puntos de historia": "el backlog ya no usa puntos de historia",
    "Dado / Cuando / Entonces": "los criterios se escriben en frases, no en Given-When-Then",
    "georreferenciación": "decimos «ubicación de la finca»",
    "EUDR": "decimos «certificación europea»",
    "Sprint 3": "decimos «el siguiente sprint»",
    "Jira": "no usamos tablero en el documento del sprint",
    "Trazabilidad de los requisitos": "esa tabla se quitó por avanzada",
    "5.5 Motor de base de datos": "se redujo a una línea sobre PostgreSQL",
    "tipos portables": "la comparación entre motores ya no está",
    "cuentas de prueba para cada rol":
        "quedan 4 cuentas, una por persona del equipo, no una por rol",
    "maria.peralta": "se quitaron las cuentas de relleno del seed",
    "camila.ortiz": "se quitaron las cuentas de relleno del seed",
    "andres.quintero": "se quitaron las cuentas de relleno del seed",
}

#: Formatos que se leen como zip (los que produce Office).
ZIP = {".docx", ".pptx"}


def texto_de(ruta: pathlib.Path) -> str:
    """Devuelve el texto del archivo, sea PDF, Word o PowerPoint."""
    if ruta.suffix == ".pdf":
        import pymupdf
        with pymupdf.open(ruta) as doc:
            return "\n".join(pagina.get_text() for pagina in doc)

    if ruta.suffix in ZIP:
        partes = []
        with zipfile.ZipFile(ruta) as z:
            for nombre in z.namelist():
                if nombre.endswith(".xml") and (
                        "document" in nombre or "slide" in nombre
                        or "notesSlide" in nombre or "header" in nombre):
                    crudo = z.read(nombre).decode("utf-8", "ignore")
                    # Se quitan las etiquetas: solo interesan las palabras.
                    partes.append(re.sub(r"<[^>]+>", " ", crudo))
        return " ".join(partes)

    return ruta.read_text(encoding="utf-8", errors="ignore")


def normalizar(texto: str) -> str:
    """Colapsa espacios y pasa a minúsculas, para comparar frases partidas."""
    return re.sub(r"\s+", " ", texto.replace("\xa0", " ")).lower()


def main() -> int:
    archivos = sorted(p for p in SALIDA.iterdir() if p.is_file())
    if not archivos:
        print("  no hay archivos en salida/")
        return 1

    hallazgos = 0
    for ruta in archivos:
        if ruta.name.startswith("_") or ruta.suffix not in {".pdf", ".docx", ".pptx"}:
            continue
        texto = normalizar(texto_de(ruta))
        malos = [(frase, motivo) for frase, motivo in PROHIBIDAS.items()
                 if frase.lower() in texto]
        if malos:
            print(f"  {ruta.name}")
            for frase, motivo in malos:
                print(f"      «{frase}»  -> {motivo}")
                hallazgos += 1
        else:
            print(f"  {ruta.name}  limpio")

    print()
    if hallazgos:
        print(f"  {hallazgos} frases que ya no aplican. Revísalas en los generadores.")
        return 1
    print("  Ningún entregable menciona datos que ya no son ciertos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
