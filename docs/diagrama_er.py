"""Diagrama entidad-relación del modelo de datos de RiTech.

    python -m docs.diagrama_er

Produce `docs/salida/diagrama_entidad_relacion.pdf` con dos páginas de
altura propia, ajustadas al contenido:

  · pág. 1  el diagrama, en disposición por capas según las dependencias
  · pág. 2  tabla de relaciones y detalle de las tablas de extensión
"""

from __future__ import annotations

import math
import pathlib

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as pdfcanvas

from docs import datos

SALIDA = pathlib.Path(__file__).parent / "salida"
SALIDA.mkdir(parents=True, exist_ok=True)

ESPRESSO = colors.HexColor("#2A1B13")
TINTA = colors.HexColor("#241A12")
SUAVE = colors.HexColor("#6B5D4F")
LINEA = colors.HexColor("#C9BBA0")
AZUL = colors.HexColor("#1F4E8C")
VERDE = colors.HexColor("#4B7B52")
ORO = colors.HexColor("#B9893B")
RUST = colors.HexColor("#A84B32")
GRIS = colors.HexColor("#6B5D4F")
CREMA = colors.HexColor("#FFFDF9")
BLANCO = colors.white

ANCHO = landscape(A3)[0]
ALTO_PAG_1 = 600   # el diagrama solo necesita esta altura
ALTO_PAG_2 = 420   # la tabla de relaciones, a dos columnas

ALTO_ENCABEZADO = 64
ALTO_CAB = 19
ALTO_FILA = 12.4
ANCHO_CAJA = 205
HUECO_CAMPO = 44   # espacio reservado a la nota de la derecha

COLOR = {
    "fincas": VERDE, "productos": VERDE,
    "lotes": ORO, "usuarios": GRIS, "clientes": AZUL, "envios": AZUL,
    "exportaciones": RUST, "detalle_exportacion": RUST,
    "documentos_exportacion": RUST,
}


# --------------------------------------------------------------------------- #
# Utilidades                                                                   #
# --------------------------------------------------------------------------- #
def _texto(c, x, y, txt, tam=7, negrita=False, color=TINTA, ancla="l"):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if negrita else "Helvetica", tam)
    {"m": c.drawCentredString, "r": c.drawRightString}.get(ancla, c.drawString)(x, y, txt)


def _recorta(txt, ancho, tam, negrita=False):
    fuente = "Helvetica-Bold" if negrita else "Helvetica"
    if stringWidth(txt, fuente, tam) <= ancho:
        return txt
    while txt and stringWidth(txt + "…", fuente, tam) > ancho:
        txt = txt[:-1]
    return txt + "…"


def _encabezado(c, titulo, subtitulo, alto_pag):
    c.setFillColor(ESPRESSO)
    c.rect(0, alto_pag - ALTO_ENCABEZADO, ANCHO, ALTO_ENCABEZADO, stroke=0, fill=1)
    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, alto_pag - 28, titulo)
    c.setFillColor(colors.HexColor("#C4B49C"))
    c.setFont("Helvetica", 8.5)
    c.drawString(40, alto_pag - 45, subtitulo)
    c.setFont("Helvetica", 7.5)
    c.drawRightString(ANCHO - 40, alto_pag - 45, f"{datos.EMPRESA}  ·  {datos.FECHA}")


def _alto(campos):
    # Los 4 puntos de más dejan el último campo por encima del borde inferior.
    return ALTO_CAB + len(campos) * ALTO_FILA + 10


def _tabla(c, x, y, titulo, campos):
    """Dibuja una tabla; devuelve su alto."""
    alto = _alto(campos)
    c.setFillColor(CREMA)
    c.setStrokeColor(LINEA)
    c.setLineWidth(0.9)
    c.rect(x, y, ANCHO_CAJA, alto, stroke=1, fill=1)
    c.setFillColor(COLOR.get(titulo, GRIS))
    c.rect(x, y + alto - ALTO_CAB, ANCHO_CAJA, ALTO_CAB, stroke=0, fill=1)
    _texto(c, x + ANCHO_CAJA / 2, y + alto - ALTO_CAB + 6, titulo, tam=7.8,
           negrita=True, color=BLANCO, ancla="m")

    yy = y + alto - ALTO_CAB - 4
    ancho_nota = ANCHO_CAJA * 0.44
    for nombre, tipo, nota in campos:
        yy -= ALTO_FILA
        fila = yy + ALTO_FILA - 4
        c.setFillColor(TINTA)
        c.setFont("Helvetica", 6.2)
        etiqueta = _recorta(f"{nombre}  {tipo}", ANCHO_CAJA - 12 - ancho_nota, 6.2)
        c.drawString(x + 6, fila, etiqueta)
        if nota:
            _texto(c, x + ANCHO_CAJA - 6, fila, _recorta(nota, ancho_nota - 6, 5.6),
                   tam=5.6, color=AZUL, ancla="r")
    return alto


def _flecha(c, x1, y1, x2, y2, color=SUAVE):
    """Línea ortogonal con punta, rotulada «1 : N»."""
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.0)
    if abs(x2 - x1) >= abs(y2 - y1):
        xm = x1 + (x2 - x1) / 2
        c.line(x1, y1, xm, y1)
        c.line(xm, y1, xm, y2)
        c.line(xm, y2, x2, y2)
        _texto(c, (x1 + xm) / 2, y1 + 3.5, "1 : N", tam=6, negrita=True,
               color=color, ancla="m")
    else:
        ym = y1 + (y2 - y1) / 2
        c.line(x1, y1, x1, ym)
        c.line(x1, ym, x2, ym)
        c.line(x2, ym, x2, y2)
        _texto(c, x1 + 5, ym + 3.5, "1 : N", tam=6, negrita=True, color=color)

    ang = math.atan2(y2 - y1, x2 - x1)
    largo = 8
    for delta in (0.42, -0.42):
        c.line(x2, y2,
               x2 - largo * math.cos(ang + delta),
               y2 - largo * math.sin(ang + delta))


# --------------------------------------------------------------------------- #
# Página 1: el diagrama                                                       #
# --------------------------------------------------------------------------- #
def _pagina_diagrama(c):
    c.setPageSize((ANCHO, ALTO_PAG_1))
    _encabezado(c, "Diagrama entidad-relación",
                "Nueve tablas del modelo de datos  ·  disposición en capas según "
                "las dependencias", ALTO_PAG_1)

    campos = {nombre: cols for nombre, cols, _ in datos.NUCLEO_TABLAS}

    capas = [
        [("fincas", 40), ("productos", 300), ("usuarios", 560), ("clientes", 820)],
        [("lotes", 170), ("exportaciones", 430)],
        [("detalle_exportacion", 170), ("documentos_exportacion", 430), ("envios", 690)],
    ]

    boxes = {}
    y = ALTO_PAG_1 - ALTO_ENCABEZADO - 24
    for capa in capas:
        max_alto = 0
        for nombre, x in capa:
            alto = _tabla(c, x, y - _alto(campos[nombre]), nombre, campos[nombre])
            boxes[nombre] = (x, y - alto, ANCHO_CAJA, alto)
            max_alto = max(max_alto, alto)
        y -= max_alto + 40

    def centro(n):
        x, yy, w, h = boxes[n]
        return x + w / 2

    def base(n):
        return boxes[n][1]

    def cima(n):
        return boxes[n][1] + boxes[n][3]

    def izquierda(n):
        x, yy, w, h = boxes[n]
        return x, yy + h / 2

    def derecha(n):
        x, yy, w, h = boxes[n]
        return x + w, yy + h / 2

    # capa 1 → capa 2
    _flecha(c, derecha("fincas")[0], derecha("fincas")[1],
            centro("lotes"), cima("lotes"))
    _flecha(c, centro("productos"), base("productos"), centro("lotes"), cima("lotes"))
    _flecha(c, centro("usuarios"), base("usuarios"),
            centro("exportaciones"), cima("exportaciones"))
    _flecha(c, centro("clientes"), base("clientes"),
            izquierda("exportaciones")[0], cima("exportaciones"))
    # capa 2 → capa 3
    _flecha(c, centro("exportaciones"), base("exportaciones"),
            centro("detalle_exportacion"), cima("detalle_exportacion"))
    _flecha(c, derecha("lotes")[0], derecha("lotes")[1],
            derecha("detalle_exportacion")[0], derecha("detalle_exportacion")[1])
    _flecha(c, derecha("exportaciones")[0], derecha("exportaciones")[1],
            centro("documentos_exportacion"), cima("documentos_exportacion"))
    _flecha(c, centro("exportaciones") + 46, base("exportaciones"),
            centro("envios"), cima("envios"))


# --------------------------------------------------------------------------- #
# Página 2: relaciones y extensiones, a dos columnas                         #
# --------------------------------------------------------------------------- #
def _pagina_relaciones(c):
    c.setPageSize((ANCHO, ALTO_PAG_2))
    _encabezado(c, "Relaciones y tablas de extensión",
                "Cardinalidad y regla de integridad de cada relación  ·  tablas "
                "añadidas por los módulos del Sprint 2", ALTO_PAG_2)

    ancho_col = (ANCHO - 80 - 24) / 2
    x_der = 40 + ancho_col + 24
    y_tope = ALTO_PAG_2 - ALTO_ENCABEZADO - 26

    # ---- Columna izquierda: relaciones ---------------------------------- #
    filas = datos.RELACIONES
    alto_izq = 34 + len(filas) * 18 + 12
    c.setFillColor(CREMA)
    c.setStrokeColor(LINEA)
    c.setLineWidth(0.9)
    c.rect(40, y_tope - alto_izq, ancho_col, alto_izq, stroke=1, fill=1)

    _texto(c, 56, y_tope - 22, "Relaciones entre tablas", tam=11, negrita=True)
    yy = y_tope - 42
    for origen, destino, card, regla in filas:
        _texto(c, 56, yy, f"{origen}  →  {destino}", tam=7.4, negrita=True, color=AZUL)
        _texto(c, 300, yy, card, tam=7.4, negrita=True, color=RUST, ancla="m")
        _texto(c, 330, yy, _recorta(regla, ancho_col - 300, 7), tam=7, color=SUAVE)
        yy -= 18

    # ---- Columna derecha: extensiones ------------------------------------ #
    ext = datos.EXTENSIONES_TABLAS
    alto_der = 46 + len(ext) * 42 + 10
    c.setFillColor(CREMA)
    c.setStrokeColor(LINEA)
    c.setLineWidth(0.9)
    c.rect(x_der, y_tope - alto_der, ancho_col, alto_der, stroke=1, fill=1)

    _texto(c, x_der + 16, y_tope - 22, "Tablas de extensión del Sprint 2",
           tam=11, negrita=True)
    _texto(c, x_der + 16, y_tope - 38,
           "Información que los módulos construidos necesitan y que no cabe en "
           "las nueve tablas originales.", tam=7, color=SUAVE)

    yy = y_tope - 58
    for tabla, desc in ext:
        c.setFillColor(colors.HexColor("#F3E8D2"))
        c.setStrokeColor(ORO)
        c.setLineWidth(0.8)
        c.rect(x_der + 16, yy - 6, ancho_col - 32, 34, stroke=1, fill=1)
        _texto(c, x_der + 28, yy + 15, tabla, tam=8.4, negrita=True,
               color=colors.HexColor("#6B4E1E"))
        _texto(c, x_der + 28, yy + 3, _recorta(desc, ancho_col - 60, 7),
               tam=7, color=TINTA)
        yy -= 42


# --------------------------------------------------------------------------- #
def construir(destino: pathlib.Path) -> None:
    c = pdfcanvas.Canvas(str(destino), pagesize=(ANCHO, ALTO_PAG_1))
    _pagina_diagrama(c)
    c.showPage()
    _pagina_relaciones(c)
    c.showPage()
    c.save()
    print(f"  diagrama_entidad_relacion.pdf  ({len(datos.NUCLEO_TABLAS)} tablas · "
          f"{len(datos.RELACIONES)} relaciones · "
          f"{len(datos.EXTENSIONES_TABLAS)} extensiones)")


def main() -> None:
    print("Diagrama entidad-relación")
    construir(SALIDA / "diagrama_entidad_relacion.pdf")
    print(f"  en {SALIDA}")


if __name__ == "__main__":
    main()
