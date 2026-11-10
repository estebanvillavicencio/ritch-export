"""Genera el guion de exposición de los Sprints 3 y 4.

    python -m docs.guion_sprint34

Produce, en `docs/salida/`:

    7_Guion_Sprint3_4_Exposicion.docx
    7_Guion_Sprint3_4_Exposicion.pdf

El contenido sale de `docs/datos_sprint34.py`, el mismo archivo que alimenta
los documentos de los dos sprints. Así el guion no puede contar algo distinto
de lo que dicen los documentos.
"""

from __future__ import annotations

import pathlib

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from docs import datos_sprint34 as d
from docs.nombres import EQUIPO
from docs.sprint34 import (
    ALTO_PAG,
    ANCHO_PAG,
    AZUL,
    AZUL_HEX,
    AZUL_RGB,
    BLANCO_RGB,
    CREMA,
    ESPRESSO,
    ESPRESSO_HEX,
    F_CUERPO,
    F_MONO,
    F_TITULO,
    LINEA,
    MARGEN,
    ORO,
    ORO_HEX,
    ORO_RGB,
    RUST,
    RUST_HEX,
    RUST_RGB,
    S_H1,
    S_H2,
    S_NOTA,
    S_P,
    S_SUBT,
    S_TD,
    S_TH,
    S_TITULO,
    SUAVE,
    SUAVE_RGB,
    TINTA,
    TINTA_RGB,
    UTIL,
    UTIL_MM,
    VERDE,
    VERDE_HEX,
    VERDE_RGB,
    _bordes,
    _campo,
    _escribir_celda,
    _h1,
    _h2,
    _margenes_celda,
    _no_partir_fila,
    _nota,
    _p,
    _par as _par_base,
    _pdf,
    _repetir_cabecera,
    _salto,
    _sombrear,
    _tabla_docx,
    _tabla_pdf,
)

SALIDA = pathlib.Path(__file__).parent / "salida"
SALIDA.mkdir(parents=True, exist_ok=True)
DESTINO_DOCX = SALIDA / "7_Guion_Sprint3_4_Exposicion.docx"
DESTINO_PDF = SALIDA / "7_Guion_Sprint3_4_Exposicion.pdf"

VERDE_OSCURO = colors.HexColor("#3C6343")
CREMA_HEX = "FFF7E8"
VERDE_CLARO = "EAF1EA"


def _limpio(txt: str) -> str:
    """Quita el marcado ligero que no tiene sentido en Word."""
    return str(txt).replace("`", "").replace("**", "")


def _caja_pdf(titulo: str, texto: str, fondo: str = "F3E8D2",
              borde=ORO) -> Paragraph:
    estilo = ParagraphStyle(
        "caja",
        parent=S_P,
        backColor=colors.HexColor(f"#{fondo}"),
        borderColor=borde,
        borderWidth=0.6,
        borderPadding=6,
        spaceBefore=3,
        spaceAfter=7,
        leading=13,
    )
    return _p(f"<b>{titulo}</b><br/>{texto}", estilo)


def _caja_docx(doc, titulo: str, texto: str, fondo: str = CREMA_HEX,
               color_titulo=ORO_RGB) -> None:
    tabla = doc.add_table(rows=1, cols=1)
    tabla.autofit = False
    _bordes(tabla, "DCD3C1", grosor=4)
    _margenes_celda(tabla, izq=140, der=140, arriba=90, abajo=90)
    celda = tabla.rows[0].cells[0]
    celda.width = Mm(UTIL_MM)
    _sombrear(celda, fondo)

    par = celda.paragraphs[0]
    par.paragraph_format.space_after = Pt(2)
    run = par.add_run(titulo)
    run.font.size = Pt(8)
    run.font.bold = True
    run.font.color.rgb = color_titulo
    run.font.name = F_CUERPO

    par = celda.add_paragraph()
    par.paragraph_format.space_after = Pt(0)
    par.paragraph_format.line_spacing = 1.13
    run = par.add_run(_limpio(texto))
    run.font.size = Pt(9.5)
    run.font.color.rgb = TINTA_RGB
    run.font.name = F_CUERPO
    _par(doc, "", despues=4)


# =========================================================================== #
# PDF                                                                         #
# =========================================================================== #
def _decorada(c, doc) -> None:
    c.saveState()
    c.setFillColor(ESPRESSO)
    c.rect(0, ALTO_PAG - 14 * mm, ANCHO_PAG, 14 * mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#C4B49C"))
    c.setFont("Helvetica", 7.5)
    c.drawString(
        MARGEN, ALTO_PAG - 9.5 * mm,
        f"{d.EMPRESA}  ·  Guion de exposición  ·  Sprints 3 y 4",
    )
    c.drawRightString(ANCHO_PAG - MARGEN, ALTO_PAG - 9.5 * mm, d.FECHA)
    c.setStrokeColor(LINEA)
    c.setLineWidth(0.5)
    c.line(MARGEN, 15 * mm, ANCHO_PAG - MARGEN, 15 * mm)
    c.setFillColor(SUAVE)
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGEN, 11 * mm, "Sistema de gestión de exportaciones de café y cacao")
    c.drawRightString(ANCHO_PAG - MARGEN, 11 * mm, f"Página {doc.page}")
    c.restoreState()


def _limpia(c, doc) -> None:
    c.saveState()
    c.setFillColor(ESPRESSO)
    c.rect(0, ALTO_PAG - 14 * mm, ANCHO_PAG, 14 * mm, stroke=0, fill=1)
    c.restoreState()


def _portada_pdf() -> list:
    g = d.GUION
    return [
        Spacer(1, 26 * mm),
        _p(d.EMPRESA, ParagraphStyle(
            "emp", parent=S_SUBT, fontSize=12, textColor=ORO,
            fontName="Helvetica-Bold",
        )),
        Spacer(1, 5 * mm),
        _p("Sistema de Gestión de Exportación<br/>de Café y Cacao a la Unión Europea",
           ParagraphStyle("tit", parent=S_TITULO, fontSize=23, leading=29,
                          alignment=TA_CENTER)),
        Spacer(1, 4 * mm),
        _p("Guion de exposición de los Sprints 3 y 4",
           ParagraphStyle("sub", parent=S_SUBT, fontSize=13)),
        Spacer(1, 2 * mm),
        _p(g["subtitulo"], ParagraphStyle(
            "lema", parent=S_SUBT, fontSize=10.5, textColor=AZUL,
            fontName="Helvetica-Oblique",
        )),
        Spacer(1, 12 * mm),
        _p("Reparto del tiempo", ParagraphStyle(
            "rep", parent=S_H2, alignment=TA_CENTER, fontSize=11.5,
        )),
        _tabla_reparto_pdf(),
        Spacer(1, 9 * mm),
        _p(
            "<b>Duración total:</b> 12 minutos, 3 minutos por persona.<br/>"
            "<b>Formato:</b> demostración en vivo con el sistema sembrado.<br/>"
            f"<b>Fecha:</b> {d.FECHA}.",
            ParagraphStyle("pie", parent=S_NOTA, alignment=TA_CENTER, fontSize=8.4),
        ),
        Spacer(1, 6 * mm),
        _p(
            "Este guion se apoya en los documentos 5 y 6. Si una cifra cambia en "
            "el código, se actualiza `docs/datos_sprint34.py` y se regeneran los "
            "tres entregables.",
            ParagraphStyle("nota", parent=S_NOTA, alignment=TA_CENTER, fontSize=8),
        ),
    ]


def _tabla_reparto_pdf() -> Table:
    filas = [
        [f"<b>{b['nombre']}</b>", b["bloque"],
         f"{b['inicio']} – {b['fin']}", _pdf(b["tema"])]
        for b in d.GUION["reparto"]
    ]
    return _tabla_pdf(
        ["Integrante", "Bloque", "Horario", "Qué cubre"],
        filas, [38 * mm, 42 * mm, 24 * mm, 70 * mm], color_cab=ESPRESSO,
    )


def _seccion_reparto_pdf() -> list:
    g = d.GUION
    e = [_p("1. Reparto y reglas de tiempo", S_H1)]
    e.append(_p(
        "Son doce minutos y cuatro personas. Cada bloque dura tres minutos y "
        "termina con una frase que entrega la palabra al siguiente. La "
        "demostración va dentro de esos tres minutos: no hay un bloque aparte "
        "para el computador."
    ))
    e.append(_p("1.1 Cómo usar este guion", S_H2))
    e.append(_p(
        "<b>No se lee palabra por palabra.</b> Cada persona encuentra su bloque, "
        "las ideas que debe dejar y las frases que conviene decir tal cual. Lo "
        "demás se explica con las palabras de cada uno."
    ))
    e.append(_vinetas_pdf([
        "Ensayar una vez con cronómetro y otra sin mirar el papel.",
        "Señalar la pantalla mientras se habla; el público sigue mejor una demostración.",
        "Si una demostración falla, seguir con el paso siguiente: la bitácora y las pruebas también sirven de evidencia.",
        "Respetar el cambio de persona: el puente ya está escrito al final de cada bloque.",
    ]))
    e.append(_p("1.2 Antes de empezar", S_H2))
    e.append(_vinetas_pdf(g["checklist"]))
    e.append(_p("1.3 Cuentas para la demostración", S_H2))
    e.append(_tabla_pdf(
        ["Rol", "Correo", "Contraseña"],
        [[r, f"`{c}`", f"`{p}`"] for r, c, p in g["credenciales"]],
        [34 * mm, 92 * mm, 48 * mm], color_cab=AZUL,
    ))
    e.append(_p(
        "La cuenta de administrador sirve para el financiero, la auditoría y el "
        "sistema. La cuenta de cliente europeo se abre en otra pestaña para "
        "demostrar el portal y el recorte de datos.",
        S_NOTA,
    ))
    e.append(_p("1.4 Consejos para la exposición", S_H2))
    e.append(_vinetas_pdf(g["consejos"]))
    return e


def _vinetas_pdf(items) -> Paragraph:
    return _p("<br/>".join(f"• {_pdf(x)}" for x in items))


def _seccion_personas_pdf() -> list:
    e = [_p("2. Guion por persona", S_H1)]
    e.append(_p(
        "Cada bloque tiene el mismo orden: qué hay en pantalla, lo que se dice, "
        "las frases que conviene memorizar y el puente para entregar la palabra."
    ))
    for i, b in enumerate(d.GUION["bloques"], start=1):
        e.append(PageBreak() if i > 1 else Spacer(1, 2 * mm))
        e.append(_p(f"2.{i} {b['nombre']}", S_H1))
        e.append(_p(
            f"<b>{b['bloque']}</b>  ·  {b['inicio']} – {b['fin']}  ·  "
            f"Pantalla: {_pdf(b['pantalla'])}",
            ParagraphStyle("meta", parent=S_P, textColor=SUAVE, fontSize=8.8,
                           spaceAfter=5),
        ))
        e.append(_caja_pdf("OBJETIVO DEL BLOQUE", _pdf(b["objetivo"])))
        e.append(_p("Lo que dices", S_H2))
        for frase in b["guion"]:
            e.append(_p(f"» {_pdf(frase)}", S_P))
        e.append(_p("Frases para recordar", S_H2))
        e.append(_vinetas_pdf(b["frases"]))
        e.append(_p("Cómo cerrar y pasar", S_H2))
        e.append(_caja_pdf("PUENTE", _pdf(b["puente"]), fondo=VERDE_CLARO,
                           borde=VERDE))
    return e


def _seccion_demo_pdf() -> list:
    g = d.GUION
    e = [_p("3. Demostración en vivo", S_H1)]
    e.append(_p(
        "El orden de los clics. Cada paso tiene un minuto objetivo; si se "
        "atrasa, se recorta la explicación, no la demostración."
    ))
    e.append(_tabla_pdf(
        ["Paso", "Minuto", "Pantalla", "Qué hacer", "Quién"],
        [[f"<b>{n}</b>", t, p, _pdf(a), q] for n, t, p, a, q in g["demo_orden"]],
        [12 * mm, 16 * mm, 25 * mm, 85 * mm, 26 * mm], color_cab=ORO,
    ))
    e.append(Spacer(1, 3 * mm))
    e.append(_p(
        "Si el sistema no responde durante la demostración, mostrar la salida "
        "de `python -m pytest -q`: noventa pruebas en verde. La evidencia no "
        "depende de la red."
    ))
    return e


def _seccion_preguntas_pdf() -> list:
    e = [_p("4. Preguntas frecuentes", S_H1)]
    e.append(_p(
        "Las respuestas están cortas a propósito: quien pregunta quiere una "
        "idea, no un párrafo. Si la pregunta pide detalle, se puede abrir el "
        "documento del sprint correspondiente."
    ))
    for pregunta, respuesta in d.GUION["preguntas"]:
        e.append(KeepTogether([
            _p(f"<b>{_pdf(pregunta)}</b>", ParagraphStyle(
                "q", parent=S_P, spaceBefore=4, spaceAfter=2,
            )),
            _p(_pdf(respuesta), ParagraphStyle(
                "a", parent=S_P, textColor=SUAVE, leftIndent=8,
            )),
        ]))
    return e


def _seccion_cierre_pdf() -> list:
    e = [_p("5. Cierre", S_H1)]
    e.append(_p(
        "El último minuto no se improvisa. El cierre resume lo que el público "
        "vio y deja el proyecto en su estado final."
    ))
    e.append(_caja_pdf(
        "TRES IDEAS PARA LLEVARSE",
        "El sistema no solo registra la operación: también la puede explicar.<br/>"
        "Habla el idioma y la moneda del cliente sin depender de internet.<br/>"
        "Deja una copia verificable de todo y noventa pruebas que lo respaldan.",
        fondo="F3E8D2",
    ))
    e.append(_p(
        "<b>Frase final:</b> «Con esto cerramos los dos sprints y el proyecto. "
        "Quedamos atentos a sus preguntas.»"
    ))
    e.append(Spacer(1, 8 * mm))
    estilo_fin = ParagraphStyle(
        "fin", parent=S_NOTA, alignment=TA_CENTER, fontSize=8.2,
    )
    e.append(_p(
        f"{d.EMPRESA}  ·  {d.PROYECTO}<br/>{d.FECHA}",
        estilo_fin,
    ))
    return e


def construir_pdf(destino: pathlib.Path) -> None:
    doc = BaseDocTemplate(
        str(destino), pagesize=A4,
        leftMargin=MARGEN, rightMargin=MARGEN,
        topMargin=22 * mm, bottomMargin=20 * mm,
        title=f"{d.PROYECTO} — Guion de exposición Sprints 3 y 4",
        author=d.EMPRESA,
        subject="Guion de exposición de los Sprints 3 y 4",
    )
    marco = Frame(MARGEN, 20 * mm, UTIL, ALTO_PAG - 42 * mm, id="marco")
    doc.addPageTemplates([
        PageTemplate(id="portada", frames=[marco], onPage=_limpia),
        PageTemplate(id="normal", frames=[marco], onPage=_decorada),
    ])

    historia = []
    historia += _portada_pdf()
    historia += [NextPageTemplate("normal"), PageBreak()]
    historia += _seccion_reparto_pdf()
    historia += [PageBreak()]
    historia += _seccion_personas_pdf()
    historia += [PageBreak()]
    historia += _seccion_demo_pdf()
    historia += [PageBreak()]
    historia += _seccion_preguntas_pdf()
    historia += [PageBreak()]
    historia += _seccion_cierre_pdf()
    doc.build(historia)


# =========================================================================== #
# Word                                                                        #
# =========================================================================== #
def _decorar_docx(seccion) -> None:
    cabecera = seccion.header
    par = cabecera.paragraphs[0]
    par.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = par.add_run(f"{d.EMPRESA}  ·  Guion de exposición  ·  Sprints 3 y 4")
    run.font.size = Pt(7.5)
    run.font.color.rgb = SUAVE_RGB
    run.font.name = F_CUERPO

    pie = seccion.footer
    par = pie.paragraphs[0]
    par.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = par.add_run("Página ")
    run.font.size = Pt(7.5)
    run.font.color.rgb = SUAVE_RGB
    run.font.name = F_CUERPO
    _campo(par, "PAGE")
    run = par.add_run(" de ")
    run.font.size = Pt(7.5)
    run.font.color.rgb = SUAVE_RGB
    run.font.name = F_CUERPO
    _campo(par, "NUMPAGES")
    for run in par.runs:
        run.font.size = Pt(7.5)
        run.font.color.rgb = SUAVE_RGB
        run.font.name = F_CUERPO


def _portada_docx(doc) -> None:
    g = d.GUION
    tabla = doc.add_table(rows=1, cols=1)
    tabla.autofit = False
    _margenes_celda(tabla, izq=200, der=200, arriba=240, abajo=240)
    celda = tabla.rows[0].cells[0]
    celda.width = Mm(UTIL_MM)
    _sombrear(celda, ESPRESSO_HEX)

    par = celda.paragraphs[0]
    par.paragraph_format.space_after = Pt(2)
    run = par.add_run(d.EMPRESA.upper())
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = ORO_RGB
    run.font.name = F_CUERPO

    par = celda.add_paragraph()
    par.paragraph_format.space_after = Pt(4)
    par.paragraph_format.line_spacing = 1.12
    run = par.add_run("Sistema de Gestión de Exportación\n"
                      "de Café y Cacao a la Unión Europea")
    run.font.size = Pt(20)
    run.font.bold = True
    run.font.color.rgb = BLANCO_RGB
    run.font.name = F_TITULO

    par = celda.add_paragraph()
    par.paragraph_format.space_after = Pt(0)
    run = par.add_run(f"Guion de exposición de los Sprints 3 y 4  ·  {g['subtitulo']}")
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(0xC4, 0xB4, 0x9C)
    run.font.name = F_CUERPO

    _par(doc, "", despues=8)
    _par(doc, "Reparto del tiempo", tam=10, negrita=True, despues=3)
    _tabla_docx(
        doc,
        ["Integrante", "Bloque", "Horario", "Qué cubre"],
        [[f"**{b['nombre']}**", b["bloque"], f"{b['inicio']} – {b['fin']}",
          b["tema"]] for b in g["reparto"]],
        [42, 44, 24, 64], color_cab=ESPRESSO_HEX, tam=8.6, cabecera_tam=8.4,
    )
    _par(doc, "", despues=6)
    _caja_docx(
        doc, "DURACIÓN TOTAL",
        "12 minutos, 3 minutos por persona. Demostración en vivo con el sistema "
        "sembrado. El guion se apoya en los documentos 5 y 6.",
    )
    _nota(doc, "Si una cifra cambia en el código, se actualiza "
               "docs/datos_sprint34.py y se regeneran los tres entregables.")
    _salto(doc)


def _seccion_reparto_docx(doc) -> None:
    g = d.GUION
    _h1(doc, "1. Reparto y reglas de tiempo")
    _par(doc, "Son doce minutos y cuatro personas. Cada bloque dura tres minutos "
              "y termina con una frase que entrega la palabra al siguiente. La "
              "demostración va dentro de esos tres minutos: no hay un bloque "
              "aparte para el computador.", tam=9.5)
    _h2(doc, "1.1 Cómo usar este guion")
    _par(doc, "No se lee palabra por palabra. Cada persona encuentra su "
              "bloque, las ideas que debe dejar y las frases que conviene decir "
              "tal cual. Lo demás se explica con las palabras de cada uno.",
         tam=9.5)
    _vinetas(doc, [
        "Ensayar una vez con cronómetro y otra sin mirar el papel.",
        "Señalar la pantalla mientras se habla; el público sigue mejor una demostración.",
        "Si una demostración falla, seguir con el paso siguiente: la bitácora y las pruebas también sirven de evidencia.",
        "Respetar el cambio de persona: el puente ya está escrito al final de cada bloque.",
    ])
    _h2(doc, "1.2 Antes de empezar")
    _vinetas(doc, g["checklist"])
    _h2(doc, "1.3 Cuentas para la demostración")
    _tabla_docx(
        doc, ["Rol", "Correo", "Contraseña"],
        [[r, f"`{c}`", f"`{p}`"] for r, c, p in g["credenciales"]],
        [34, 92, 48], color_cab=AZUL_HEX, tam=9,
    )
    _nota(doc, "La cuenta de administrador sirve para el financiero, la "
               "auditoría y el sistema. La cuenta de cliente europeo se abre en "
               "otra pestaña para demostrar el portal y el recorte de datos.")
    _h2(doc, "1.4 Consejos para la exposición")
    _vinetas(doc, g["consejos"])


def _seccion_personas_docx(doc) -> None:
    _salto(doc)
    _h1(doc, "2. Guion por persona")
    _par(doc, "Cada bloque tiene el mismo orden: qué hay en pantalla, lo que se "
              "dice, las frases que conviene memorizar y el puente para "
              "entregar la palabra.", tam=9.5)
    for i, b in enumerate(d.GUION["bloques"], start=1):
        if i > 1:
            _salto(doc)
        _h1(doc, f"2.{i} {b['nombre']}")
        _par(doc, f"{b['bloque']}  ·  {b['inicio']} – {b['fin']}  ·  "
                  f"Pantalla: {_limpio(b['pantalla'])}",
             tam=8.8, color=SUAVE_RGB, despues=5, interlineado=1.1)
        _caja_docx(doc, "OBJETIVO DEL BLOQUE", b["objetivo"])
        _h2(doc, "Lo que dices")
        for frase in b["guion"]:
            par = _par(doc, f"»  {frase}", tam=9.8, despues=4, interlineado=1.18)
            par.paragraph_format.left_indent = Mm(5)
        _h2(doc, "Frases para recordar")
        _vinetas(doc, b["frases"])
        _h2(doc, "Cómo cerrar y pasar", color=VERDE_RGB)
        _caja_docx(doc, "PUENTE", b["puente"], fondo=VERDE_CLARO,
                   color_titulo=VERDE_RGB)


def _seccion_demo_docx(doc) -> None:
    _salto(doc)
    _h1(doc, "3. Demostración en vivo")
    _par(doc, "El orden de los clics. Cada paso tiene un minuto objetivo; si se "
              "atrasa, se recorta la explicación, no la demostración.", tam=9.5)
    _tabla_docx(
        doc, ["Paso", "Minuto", "Pantalla", "Qué hacer", "Quién"],
        [[f"**{n}**", t, p, a, q] for n, t, p, a, q in d.GUION["demo_orden"]],
        [12, 16, 25, 88, 27], color_cab=ORO_HEX, tam=8.4,
    )
    _nota(doc, "Si el sistema no responde durante la demostración, mostrar la "
               "salida de python -m pytest -q: noventa pruebas en verde. La "
               "evidencia no depende de la red.")


def _seccion_preguntas_docx(doc) -> None:
    _salto(doc)
    _h1(doc, "4. Preguntas frecuentes")
    _par(doc, "Las respuestas están cortas a propósito: quien pregunta quiere "
              "una idea, no un párrafo. Si la pregunta pide detalle, se puede "
              "abrir el documento del sprint correspondiente.", tam=9.5)
    for pregunta, respuesta in d.GUION["preguntas"]:
        _par(doc, pregunta, tam=9.8, negrita=True, antes=5, despues=2)
        par = _par(doc, respuesta, tam=9.3, color=SUAVE_RGB, despues=5,
                   interlineado=1.12)
        par.paragraph_format.left_indent = Mm(7)


def _seccion_cierre_docx(doc) -> None:
    _salto(doc)
    _h1(doc, "5. Cierre")
    _par(doc, "El último minuto no se improvisa. El cierre resume lo que el "
              "público vio y deja el proyecto en su estado final.", tam=9.5)
    _caja_docx(
        doc, "TRES IDEAS PARA LLEVARSE",
        "El sistema no solo registra la operación: también la puede explicar.\n"
        "Habla el idioma y la moneda del cliente sin depender de internet.\n"
        "Deja una copia verificable de todo y noventa pruebas que lo respaldan.",
    )
    _par(doc, "Frase final: «Con esto cerramos los dos sprints y el "
              "proyecto. Quedamos atentos a sus preguntas.»", tam=9.8)
    _par(doc, "", despues=12)
    _par(doc, f"{d.EMPRESA}  ·  {d.PROYECTO}", tam=8, color=SUAVE_RGB,
         align=WD_ALIGN_PARAGRAPH.CENTER, despues=2)
    _par(doc, d.FECHA, tam=8, color=SUAVE_RGB,
         align=WD_ALIGN_PARAGRAPH.CENTER)


def construir_docx(destino: pathlib.Path) -> None:
    doc = Document()
    seccion = doc.sections[0]
    seccion.page_width = Mm(210)
    seccion.page_height = Mm(297)
    seccion.left_margin = Mm(18)
    seccion.right_margin = Mm(18)
    seccion.top_margin = Mm(22)
    seccion.bottom_margin = Mm(20)
    seccion.header_distance = Mm(12)
    seccion.footer_distance = Mm(12)
    _decorar_docx(seccion)

    normal = doc.styles["Normal"]
    normal.font.name = F_CUERPO
    normal.font.size = Pt(10)
    normal.font.color.rgb = TINTA_RGB
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.12

    _portada_docx(doc)
    _seccion_reparto_docx(doc)
    _seccion_personas_docx(doc)
    _seccion_demo_docx(doc)
    _seccion_preguntas_docx(doc)
    _seccion_cierre_docx(doc)

    props = doc.core_properties
    props.title = f"{d.PROYECTO} — Guion de exposición Sprints 3 y 4"
    props.author = d.EMPRESA
    props.subject = d.GUION["subtitulo"]
    props.comments = "Generado por docs/guion_sprint34.py desde docs/datos_sprint34.py"
    doc.save(str(destino))


# =========================================================================== #
# Entrada                                                                     #
# =========================================================================== #
def _paginas(destino: pathlib.Path) -> int:
    import pymupdf

    return len(pymupdf.open(destino))


def main() -> None:
    print("Guion de exposición · Sprints 3 y 4")
    construir_pdf(DESTINO_PDF)
    construir_docx(DESTINO_DOCX)
    print(f"  {DESTINO_PDF.name}  ({_paginas(DESTINO_PDF)} páginas)")
    print(f"  {DESTINO_DOCX.name}")
    print(f"  en {SALIDA}")


if __name__ == "__main__":
    main()
