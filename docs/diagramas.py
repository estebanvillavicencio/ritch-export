"""Generadores de diagramas UML y entidad-relación en PDF (reportlab).

    python -m docs.diagramas

Produce:
    docs/salida/diagrama_casos_de_uso.pdf

El diagrama entidad-relación lo genera `python -m docs.diagrama_er`.
"""

from __future__ import annotations

import pathlib

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as pdfcanvas

from docs import datos

SALIDA = pathlib.Path(__file__).parent / "salida"
SALIDA.mkdir(parents=True, exist_ok=True)

# Paleta del proyecto (mockup RiTech)
ESPRESSO = colors.HexColor("#2A1B13")
TINTA = colors.HexColor("#241A12")
SUAVE = colors.HexColor("#6B5D4F")
PAPER = colors.HexColor("#F1ECE2")
LINEA = colors.HexColor("#C9BBA0")
AZUL = colors.HexColor("#1F4E8C")
AZUL_SUAVE = colors.HexColor("#DCE7F4")
VERDE = colors.HexColor("#4B7B52")
ORO = colors.HexColor("#B9893B")
ORO_SUAVE = colors.HexColor("#F3E8D2")
RUST = colors.HexColor("#A84B32")
GRIS = colors.HexColor("#6B5D4F")
CREMA = colors.HexColor("#FFFDF9")
BLANCO = colors.white

ANCHO, ALTO = landscape(A3)  # 1190.55 x 841.89
MARGEN = 40
ALTO_ENCABEZADO = 64


# --------------------------------------------------------------------------- #
# Utilidades                                                                   #
# --------------------------------------------------------------------------- #
def _cabeza(c: pdfcanvas.Canvas, titulo: str, subtitulo: str, alto: float) -> None:
    """Banda oscura de encabezado con título y subtítulo."""
    c.setFillColor(ESPRESSO)
    c.rect(0, alto - ALTO_ENCABEZADO, ANCHO, ALTO_ENCABEZADO, stroke=0, fill=1)
    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(MARGEN, alto - 28, titulo)
    c.setFillColor(colors.HexColor("#C4B49C"))
    c.setFont("Helvetica", 8.5)
    c.drawString(MARGEN, alto - 45, subtitulo)
    c.setFont("Helvetica", 7.5)
    c.drawRightString(ANCHO - MARGEN, alto - 45,
                      f"{datos.EMPRESA}  ·  {datos.FECHA}")


def _texto(c, x, y, txt, tam=7, negrita=False, color=TINTA, ancla="l"):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if negrita else "Helvetica", tam)
    if ancla == "m":
        c.drawCentredString(x, y, txt)
    elif ancla == "r":
        c.drawRightString(x, y, txt)
    else:
        c.drawString(x, y, txt)


def _recorta(txt: str, ancho: float, tam: float, negrita: bool = False) -> str:
    """Recorta el texto para que quepa en el ancho dado."""
    fuente = "Helvetica-Bold" if negrita else "Helvetica"
    if stringWidth(txt, fuente, tam) <= ancho:
        return txt
    while txt and stringWidth(txt + "…", fuente, tam) > ancho:
        txt = txt[:-1]
    return txt + "…"


def _actor(c, x, y, nombre, escala=1.0) -> None:
    """Figura de actor de UML."""
    s = escala
    c.setStrokeColor(TINTA)
    c.setLineWidth(1.1)
    # Piernas
    c.line(x - 6 * s, y, x - 10 * s, y - 18 * s)
    c.line(x + 6 * s, y, x + 10 * s, y - 18 * s)
    # Cuerpo
    c.line(x, y - 18 * s, x, y - 27 * s)
    # Brazos
    c.line(x - 12 * s, y - 12 * s, x + 12 * s, y - 12 * s)
    # Cabeza
    c.setFillColor(BLANCO)
    c.circle(x, y + 5.5 * s, 6.4 * s, stroke=1, fill=1)
    _texto(c, x, y - 30 * s, nombre, tam=7.2, negrita=True, ancla="m")


def _envolver(txt: str, max_car: int) -> list[str]:
    palabras, lineas, actual = txt.split(), [], ""
    for p in palabras:
        tentativa = (actual + " " + p).strip()
        if len(tentativa) <= max_car:
            actual = tentativa
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


# --------------------------------------------------------------------------- #
# 1. Diagrama de casos de uso                                                  #
# --------------------------------------------------------------------------- #
def diagrama_casos_de_uso(destino: pathlib.Path) -> None:
    # La página se recorta a la altura que necesita el contenido, para que la
    # vista incrustada en la presentación no quede con medio cuerpo de blanco.
    alto = 760
    c = pdfcanvas.Canvas(str(destino), pagesize=(ANCHO, alto))
    _cabeza(c, "Diagrama de casos de uso",
            f"{datos.PROYECTO}  · actors internos de RiTech SAS y actor externo "
            "de la Unión Europea", alto)

    # Límite del sistema
    bx, by = MARGEN, 118
    bw, bh = ANCHO - 2 * MARGEN, alto - ALTO_ENCABEZADO - by - 22
    c.setStrokeColor(LINEA)
    c.setLineWidth(1.2)
    c.setFillColor(colors.HexColor("#FDFBF6"))
    c.rect(bx, by, bw, bh, stroke=1, fill=1)
    _texto(c, bx + 12, by + bh - 18, "Sistema de gestión de exportaciones de café y cacao",
           tam=10, negrita=True)
    _texto(c, bx + 12, by + bh - 30,
           "Límite del sistema · los casos de uso se agrupan por módulo funcional",
           tam=7, color=SUAVE)

    modulos = list(datos.CASOS_DE_USO.items())
    n = len(modulos)
    ancho_col = (bw - 24) / n
    y_tope = by + bh - 44

    paso = 50
    alto_ovale = 34
    ancho_ovale = ancho_col - 24
    y_ini = y_tope - 26 - 34
    suelo = by + 24

    for i, (modulo, casos) in enumerate(modulos):
        x0 = bx + 12 + i * ancho_col
        x_centro = x0 + ancho_col / 2

        # Cuántos casos caben antes de chocar con el suelo del sistema.
        caben = int((y_ini - alto_ovale / 2 - suelo) / paso) + 1
        visibles = casos[:max(caben, 1)]

        # El actor va justo debajo de su último caso, para no dejar hueco.
        y_actor = y_ini - paso * len(visibles) - 16

        # Banda del módulo
        c.setFillColor(colors.HexColor("#FBF8F2"))
        c.setStrokeColor(colors.HexColor("#EDE6D8"))
        c.setLineWidth(0.6)
        c.rect(x0 + 4, y_actor - 38, ancho_col - 8,
               y_tope - (y_actor - 38), stroke=1, fill=1)

        c.setFillColor(ORO_SUAVE)
        c.rect(x0 + 4, y_tope - 26, ancho_col - 8, 26, stroke=0, fill=1)
        lineas = _envolver(modulo, 22)
        for k, linea in enumerate(lineas[:2]):
            _texto(c, x_centro, y_tope - 10 - k * 8, linea, tam=7, negrita=True,
                   color=colors.HexColor("#6B4E1E"), ancla="m")

        # Actor representativo: el que interviene en más casos del módulo.
        cuenta = {}
        for _caso, rol in casos:
            if rol != "Todos":
                cuenta[rol] = cuenta.get(rol, 0) + 1
        actor_nombre = max(cuenta, key=cuenta.get) if cuenta else "Todos"
        _actor(c, x_centro, y_actor, actor_nombre, escala=0.85)

        # Casos de uso apilados
        y = y_ini
        for nombre_caso, _rol in visibles:
            # Línea de asociación
            c.setStrokeColor(colors.HexColor("#D8CEBA"))
            c.setLineWidth(0.5)
            c.line(x_centro, y_actor + 12, x_centro, y - alto_ovale / 2)
            # Óvalo. Ojo: Canvas.ellipse recibe las esquinas de la caja
            # delimitadora, no ancho y alto como Canvas.rect.
            c.setStrokeColor(AZUL)
            c.setLineWidth(1)
            c.setFillColor(CREMA)
            c.ellipse(x_centro - ancho_ovale / 2, y - alto_ovale / 2,
                      x_centro + ancho_ovale / 2, y + alto_ovale / 2,
                      stroke=1, fill=1)
            lineas = _envolver(nombre_caso, 24)
            for k, linea in enumerate(lineas):
                _texto(c, x_centro, y + (len(lineas) - 1) * 4.2 - k * 8.4 + 1.4,
                       linea, tam=7, ancla="m")
            y -= 33

    # Leyenda de actores
    c.setFillColor(CREMA)
    c.setStrokeColor(LINEA)
    c.setLineWidth(0.8)
    c.rect(MARGEN, 24, 250, 84, stroke=1, fill=1)
    _texto(c, MARGEN + 12, 94, "Actores del sistema", tam=8.5, negrita=True)
    y = 80
    for nombre, desc in datos.ACTORES:
        _texto(c, MARGEN + 12, y, f"•  {nombre}", tam=6.8, color=TINTA)
        y -= 9.5
    _texto(c, MARGEN + 258, 94, "Notación", tam=8.5, negrita=True)
    _texto(c, MARGEN + 258, 80, "Los óvalos son casos de uso; el actor situado bajo", tam=6.8)
    _texto(c, MARGEN + 258, 70, "cada columna es su actor principal. Un mismo caso puede", tam=6.8)
    _texto(c, MARGEN + 258, 60, "involucrar a más de un rol.", tam=6.8)

    c.showPage()
    c.save()
    total = sum(len(casos) for _, casos in modulos)
    print(f"  diagrama_casos_de_uso.pdf  ({len(modulos)} módulos · {total} casos)")


def main() -> None:
    print("Diagramas UML")
    diagrama_casos_de_uso(SALIDA / "diagrama_casos_de_uso.pdf")
    print(f"  en {SALIDA}")


if __name__ == "__main__":
    main()
