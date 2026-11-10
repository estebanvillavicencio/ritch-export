"""Genera los documentos de los Sprints 3 y 4 en PDF y Word.

    python -m docs.sprint34

Produce, en `docs/salida/`:

    5_Documento_Sprint3_RiTech.pdf
    5_Documento_Sprint3_RiTech.docx
    6_Documento_Sprint4_RiTech.pdf
    6_Documento_Sprint4_RiTech.docx

El contenido sale de `docs/datos_sprint34.py`, que a su vez describe el código
real de `backend/`. No hay texto duplicado entre el PDF y el Word: los dos leen
las mismas tablas.
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
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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
from docs.nombres import APELLIDOS, EQUIPO

SALIDA = pathlib.Path(__file__).parent / "salida"
SALIDA.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Paleta compartida                                                           #
# --------------------------------------------------------------------------- #
ESPRESSO_HEX = "2A1B13"
AZUL_HEX = "1F4E8C"
VERDE_HEX = "4B7B52"
ORO_HEX = "B9893B"
RUST_HEX = "A84B32"

ESPRESSO = colors.HexColor("#2A1B13")
TINTA = colors.HexColor("#241A12")
SUAVE = colors.HexColor("#6B5D4F")
LINEA = colors.HexColor("#C9BBA0")
AZUL = colors.HexColor("#1F4E8C")
VERDE = colors.HexColor("#4B7B52")
ORO = colors.HexColor("#B9893B")
RUST = colors.HexColor("#A84B32")
CREMA = colors.HexColor("#FFFDF9")

TINTA_RGB = RGBColor(0x24, 0x1A, 0x12)
SUAVE_RGB = RGBColor(0x6B, 0x5D, 0x4F)
BLANCO_RGB = RGBColor(0xFF, 0xFF, 0xFF)
AZUL_RGB = RGBColor(0x1F, 0x4E, 0x8C)
VERDE_RGB = RGBColor(0x4B, 0x7B, 0x52)
ORO_RGB = RGBColor(0xB9, 0x89, 0x3B)
RUST_RGB = RGBColor(0xA8, 0x4B, 0x32)

F_TITULO = "Georgia"
F_CUERPO = "Calibri"
F_MONO = "Consolas"

ANCHO_PAG, ALTO_PAG = A4
MARGEN = 18 * mm
UTIL = ANCHO_PAG - 2 * MARGEN
UTIL_MM = 174

# --------------------------------------------------------------------------- #
# Utilidades de texto                                                         #
# --------------------------------------------------------------------------- #
def _pdf(txt: str) -> str:
    """Adapta un texto a las fuentes WinAnsi del PDF."""
    return str(txt).replace("→", "->").replace("…", "...").replace("`", "")


def _bullets(items: list[str]) -> str:
    return "<br/>".join(f"• {_pdf(x)}" for x in items)


# =========================================================================== #
# PDF                                                                         #
# =========================================================================== #
base = getSampleStyleSheet()

S_TITULO = ParagraphStyle(
    "titulo", parent=base["Title"], fontName="Helvetica-Bold",
    fontSize=22, leading=26, textColor=ESPRESSO, spaceAfter=6,
)
S_SUBT = ParagraphStyle(
    "subt", parent=base["Normal"], fontName="Helvetica",
    fontSize=11, leading=15, textColor=SUAVE, alignment=TA_CENTER,
)
S_H1 = ParagraphStyle(
    "h1", parent=base["Heading1"], fontName="Helvetica-Bold",
    fontSize=15, leading=19, textColor=ESPRESSO, spaceBefore=4, spaceAfter=8,
)
S_H2 = ParagraphStyle(
    "h2", parent=base["Heading2"], fontName="Helvetica-Bold",
    fontSize=11.3, leading=15, textColor=AZUL, spaceBefore=9, spaceAfter=4,
)
S_H3 = ParagraphStyle(
    "h3", parent=base["Heading3"], fontName="Helvetica-Bold",
    fontSize=9.8, leading=13, textColor=TINTA, spaceBefore=6, spaceAfter=3,
)
S_P = ParagraphStyle(
    "p", parent=base["Normal"], fontName="Helvetica", fontSize=9,
    leading=13, textColor=TINTA, alignment=TA_JUSTIFY, spaceAfter=5,
)
S_NOTA = ParagraphStyle(
    "nota", parent=base["Normal"], fontName="Helvetica-Oblique",
    fontSize=7.8, leading=10.5, textColor=SUAVE, spaceAfter=4,
)
S_TH = ParagraphStyle(
    "th", parent=base["Normal"], fontName="Helvetica-Bold",
    fontSize=7.4, leading=9.5, textColor=colors.white,
)
S_TD = ParagraphStyle(
    "td", parent=base["Normal"], fontName="Helvetica",
    fontSize=7.4, leading=9.6, textColor=TINTA,
)
S_TDB = ParagraphStyle("tdb", parent=S_TD, fontName="Helvetica-Bold")
S_BULLET = ParagraphStyle(
    "bullet", parent=S_P, leftIndent=10, bulletIndent=2, spaceAfter=2,
)


def _p(txt: str, estilo=S_P) -> Paragraph:
    return Paragraph(_pdf(txt), estilo)


def _tabla_pdf(cabeceras, filas, anchos, color_cab=ESPRESSO, zebra=True, tam=7.4):
    cab = [Paragraph(_pdf(t), S_TH) for t in cabeceras]
    cuerpo = [[Paragraph(_pdf(c), S_TD) for c in fila] for fila in filas]
    tabla = Table([cab] + cuerpo, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), color_cab),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINEA),
        ("TOPPADDING", (0, 0), (-1, -1), 3.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    if zebra:
        for i in range(1, len(cuerpo) + 1):
            if i % 2 == 0:
                estilo.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FBF8F2")))
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _decorada_pdf(c, doc, sprint):
    c.saveState()
    c.setFillColor(ESPRESSO)
    c.rect(0, ALTO_PAG - 14 * mm, ANCHO_PAG, 14 * mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#C4B49C"))
    c.setFont("Helvetica", 7.5)
    c.drawString(
        MARGEN, ALTO_PAG - 9.5 * mm,
        f"{d.EMPRESA}  ·  Sprint {sprint['numero']}  ·  {d.PROYECTO}",
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


def _limpia_pdf(c, doc):
    c.saveState()
    c.setFillColor(ESPRESSO)
    c.rect(0, ALTO_PAG - 14 * mm, ANCHO_PAG, 14 * mm, stroke=0, fill=1)
    c.restoreState()


def _portada_pdf(sprint) -> list:
    return [
        Spacer(1, 28 * mm),
        _p(d.EMPRESA, ParagraphStyle(
            "emp", parent=S_SUBT, fontSize=12, textColor=ORO,
            fontName="Helvetica-Bold",
        )),
        Spacer(1, 5 * mm),
        _p("Sistema de Gestión de Exportación<br/>de Café y Cacao a la Unión Europea",
           ParagraphStyle("tit", parent=S_TITULO, fontSize=23, leading=29,
                          alignment=TA_CENTER)),
        Spacer(1, 4 * mm),
        _p(f"Documento técnico del Sprint {sprint['numero']}",
           ParagraphStyle("sub", parent=S_SUBT, fontSize=12)),
        Spacer(1, 2 * mm),
        _p(_pdf(sprint["lema"]), ParagraphStyle(
            "lema", parent=S_SUBT, fontSize=10, textColor=AZUL,
            fontName="Helvetica-Oblique",
        )),
        Spacer(1, 10 * mm),
        _tabla_integrantes_pdf(),
        Spacer(1, 10 * mm),
        _tabla_pdf(
            ["Contenido", "Qué encontrarán"],
            [
                ["1. Resumen del sprint", "Objetivo, alcance y resultados."],
                ["2. Historias de usuario", "HU-14 / HU-16 / HU-21 con criterios."],
                ["3. Arquitectura y tablas", "Capas, tablas nuevas y sus campos."],
                ["4. API y pantallas", "Endpoints, roles y módulos."],
                ["5. Reglas y seguridad", "Lo que el sistema impide y lo que protege."],
                ["6. Pruebas y demostración", "Evidencia y recorrido para exponer."],
            ],
            [62 * mm, 90 * mm], color_cab=VERDE,
        ),
        Spacer(1, 8 * mm),
        _p(
            f"<b>Metodología:</b> {d.METODOLOGIA}<br/>"
            f"<b>Periodo:</b> {sprint['periodo']}<br/>"
            f"<b>Alcance:</b> {_pdf(sprint['titulo'])}.",
            ParagraphStyle("pie", parent=S_NOTA, alignment=TA_CENTER, fontSize=8.2),
        ),
    ]


def _tabla_integrantes_pdf() -> Table:
    filas = [
        [Paragraph(n, ParagraphStyle("n", parent=S_TD, fontName="Helvetica-Bold",
                                     fontSize=8.4)), Paragraph(a, S_TD)]
        for n, a in zip(EQUIPO, APELLIDOS)
    ]
    tabla = Table(
        [[Paragraph("Integrante", S_TH), Paragraph("Apellido", S_TH)]] + filas,
        colWidths=[88 * mm, 36 * mm], hAlign="CENTER",
    )
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ESPRESSO),
        ("GRID", (0, 0), (-1, -1), 0.4, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("BACKGROUND", (0, 1), (-1, -1), CREMA),
    ]))
    return tabla


def _seccion_resumen_pdf(sprint) -> list:
    e = [_p("1. Resumen del sprint", S_H1)]
    e += [_p(_pdf(p)) for p in sprint["resumen"]]
    e.append(_p("1.1 Objetivos", S_H2))
    e.append(_p(_bullets(sprint["objetivos"])))
    return e


def _seccion_historias_pdf(sprint) -> list:
    e = [_p("2. Historias de usuario", S_H1)]
    e.append(_p(
        "Cada historia dice quién la necesita, qué quiere hacer y para qué. Los "
        "criterios son las condiciones que el sistema cumple hoy y que se pueden "
        "comprobar en la demostración."
    ))
    e.append(_p("2.1 Resumen", S_H2))
    filas = [
        [f"<b>{h['id']}</b>", f"<b>{h['modulo']}</b>", _pdf(h["historia"]),
         h["rol"], h["prioridad"], h["estado"]]
        for h in sprint["historias"]
    ]
    e.append(_tabla_pdf(
        ["ID", "Módulo", "Historia", "Rol", "Prioridad", "Estado"],
        filas, [14 * mm, 27 * mm, 76 * mm, 22 * mm, 17 * mm, 18 * mm],
        color_cab=ESPRESSO,
    ))
    e.append(PageBreak())
    e.append(_p("2.2 Fichas con criterios de aceptación", S_H2))
    for h in sprint["historias"]:
        filas = [
            ["Historia", f"<b>{h['id']} · {_pdf(h['historia'])}</b>"],
            ["Quién la necesita", h["rol"]],
            ["Prioridad", h["prioridad"]],
            ["Estado", h["estado"]],
            ["Criterios de aceptación", _bullets(h["criterios"])],
        ]
        e.append(KeepTogether([
            _tabla_pdf(["Campo", "Valor"], filas, [34 * mm, 118 * mm],
                       color_cab=AZUL, zebra=False),
            Spacer(1, 3.5 * mm),
        ]))
    return e


def _seccion_alcance_pdf(sprint) -> list:
    e = [_p("3. Alcance y arquitectura", S_H1)]
    e.append(_p(
        "El proyecto mantiene la misma arquitectura de tres capas del Sprint 2: "
        "una SPA sin paso de compilación, una API FastAPI con reglas de negocio "
        "en servicios y una base de datos relacional. Los sprints 3 y 4 agregan "
        "módulos y tablas, pero no reemplazan lo que ya funcionaba."
    ))
    e.append(_p("3.1 Qué incluye este sprint", S_H2))
    e.append(_p(_bullets(sprint["alcance_incluye"])))
    e.append(_p("3.2 Qué queda fuera", S_H2))
    e.append(_p(_bullets(sprint["alcance_excluye"])))
    e.append(_p("3.3 Módulos y pantallas", S_H2))
    e.append(_tabla_pdf(
        ["Módulo", "Historia", "Pantalla", "Qué hace", "Roles"],
        [[f"<b>{m['nombre']}</b>", m["historia"], f"`{m['pantalla']}`",
          _pdf(m["que_hace"]), _pdf(m["roles"])] for m in sprint["modulos"]],
        [28 * mm, 15 * mm, 24 * mm, 66 * mm, 41 * mm], color_cab=VERDE,
    ))
    e.append(Spacer(1, 3 * mm))
    e.append(_p(
        "Las tablas nuevas se crean con `Base.metadata.create_all()` y las "
        "migraciones de `app/migraciones.py`. Ninguna de las nueve tablas del "
        "modelo original cambia de forma: los módulos se apoyan en ellas."
    ))
    return e


def _seccion_tablas_pdf(sprint) -> list:
    e = [_p("4. Base de datos", S_H1)]
    e.append(_p(
        "Cada módulo guarda lo que el modelo original no tenía. Las tablas son "
        "nuevas y conservan las llaves foráneas hacia las tablas del Sprint 2 "
        "para no romper la trazabilidad."
    ))
    for t in sprint["tablas"]:
        e.append(KeepTogether([
            _p(f"4.{sprint['tablas'].index(t) + 1} Tabla `{t['nombre']}`", S_H2),
            _p(t["proposito"]),
            _tabla_pdf(
                ["Campo", "Tipo", "Nota"],
                [[f"<b>{c}</b>", f"`{tipo}`", nota] for c, tipo, nota in t["campos"]],
                [48 * mm, 42 * mm, 62 * mm], color_cab=ESPRESSO,
            ),
            _p(t["nota"], S_NOTA),
            Spacer(1, 2 * mm),
        ]))
    return e


def _seccion_api_pdf(sprint) -> list:
    e = [_p("5. API y pantallas", S_H1)]
    e.append(_p(
        "Todos los endpoints viven bajo `/api` y comparten la autenticación por "
        "token. La columna de roles indica quién puede llamarlos; el servidor "
        "vuelve a comprobar el rol aunque el frontend esconda el botón."
    ))
    for modulo, filas in sprint["endpoints"]:
        e.append(_p(f"5.{sprint['endpoints'].index((modulo, filas)) + 1} {modulo}", S_H2))
        e.append(_tabla_pdf(
            ["Método", "Ruta", "Uso", "Roles"],
            [[f"<b>{m}</b>", f"`{r}`", _pdf(u), _pdf(rol)] for m, r, u, rol in filas],
            [16 * mm, 54 * mm, 61 * mm, 43 * mm], color_cab=AZUL,
        ))
        e.append(Spacer(1, 2 * mm))
    return e


def _seccion_reglas_pdf(sprint) -> list:
    e = [_p("6. Reglas de negocio y seguridad", S_H1)]
    e.append(_p("6.1 Reglas que el sistema hace cumplir", S_H2))
    e.append(_tabla_pdf(
        ["Regla", "Cómo se aplica"],
        [[f"<b>{r}</b>", _pdf(c)] for r, c in sprint["reglas"]],
        [48 * mm, 104 * mm], color_cab=RUST,
    ))
    e.append(_p("6.2 Seguridad y permisos", S_H2))
    e.append(_p(_bullets(sprint["seguridad"])))
    return e


def _seccion_pruebas_pdf(sprint) -> list:
    e = [_p("7. Pruebas y verificación", S_H1)]
    e.append(_p(
        "Las pruebas corren contra una base SQLite temporal y no necesitan un "
        "servidor. Cada módulo tiene sus casos felices y sus casos de error."
    ))
    e.append(_tabla_pdf(
        ["Módulo", "Pruebas", "Qué cubren"],
        [[f"<b>{m}</b>", str(n), _pdf(q)] for m, n, q in sprint["pruebas"]],
        [34 * mm, 16 * mm, 102 * mm], color_cab=VERDE,
    ))
    e.append(Spacer(1, 3 * mm))
    e.append(_p(
        f"<b>Total del sprint:</b> {sprint['pruebas_total']} pruebas nuevas. "
        "La suite completa del proyecto queda en <b>90 pruebas</b>."
    ))
    e.append(_p("7.1 Comprobaciones estáticas", S_H2))
    e.append(_p(
        "Además de pytest, el proyecto trae tres comprobaciones que se ejecutan "
        "sin Node: `tools/check_js.py` revisa sintaxis y símbolos del frontend, "
        "`tools/check_refs.py` busca referencias sin resolver y "
        "`tools/verificar_sql.py` compara los guiones de PostgreSQL y MySQL con "
        "el modelo de Python."
    ))
    return e


def _seccion_demo_pdf(sprint) -> list:
    e = [_p("8. Demostración guiada", S_H1)]
    e.append(_p(
        "Este es el recorrido que se puede hacer en vivo. Cada paso dice qué "
        "pantalla abrir y qué debe verse; si algo falla, la prueba automática "
        "sigue siendo la evidencia."
    ))
    e.append(_tabla_pdf(
        ["Paso", "Qué hacer", "Qué debe verse"],
        [[f"<b>{n}</b>", _pdf(a), _pdf(b)] for n, a, b in sprint["demo"]],
        [14 * mm, 62 * mm, 76 * mm], color_cab=ORO,
    ))
    return e


def _seccion_cierre_pdf(sprint) -> list:
    e = [_p("9. Resultados y cierre", S_H1)]
    e.append(_p(_bullets(sprint["resultados"])))
    e.append(_p("9.1 Lo que sigue", S_H2))
    e.append(_p(_bullets(sprint["siguiente"])))
    if sprint["config"]:
        e.append(_p("9.2 Configuración", S_H2))
        e.append(_tabla_pdf(
            ["Variable", "Valor por defecto", "Para qué sirve"],
            [[f"`{v}`", f"`{val}`", _pdf(uso)] for v, val, uso in sprint["config"]],
            [44 * mm, 34 * mm, 74 * mm], color_cab=ESPRESSO,
        ))
    e.append(Spacer(1, 5 * mm))
    e.append(_p(
        "Documento generado desde `docs/datos_sprint34.py`. El código, los "
        "endpoints y las pruebas son la fuente de verdad: si cambian, se "
        "regeneran el PDF y el Word con `python -m docs.sprint34`.",
        S_NOTA,
    ))
    return e


def construir_pdf(sprint, destino: pathlib.Path) -> None:
    doc = BaseDocTemplate(
        str(destino), pagesize=A4,
        leftMargin=MARGEN, rightMargin=MARGEN,
        topMargin=22 * mm, bottomMargin=20 * mm,
        title=f"{d.PROYECTO} — Documento Sprint {sprint['numero']}",
        author=d.EMPRESA,
        subject=sprint["titulo"],
    )
    marco = Frame(MARGEN, 20 * mm, UTIL, ALTO_PAG - 42 * mm, id="marco")
    doc.addPageTemplates([
        PageTemplate(id="portada", frames=[marco], onPage=_limpia_pdf),
        PageTemplate(
            id="normal", frames=[marco],
            onPage=lambda c, doc_: _decorada_pdf(c, doc_, sprint),
        ),
    ])

    historia = []
    historia += _portada_pdf(sprint)
    historia += [NextPageTemplate("normal"), PageBreak()]
    historia += _seccion_resumen_pdf(sprint)
    historia += [PageBreak()]
    historia += _seccion_historias_pdf(sprint)
    historia += [PageBreak()]
    historia += _seccion_alcance_pdf(sprint)
    historia += [PageBreak()]
    historia += _seccion_tablas_pdf(sprint)
    historia += [PageBreak()]
    historia += _seccion_api_pdf(sprint)
    historia += [PageBreak()]
    historia += _seccion_reglas_pdf(sprint)
    historia += [PageBreak()]
    historia += _seccion_pruebas_pdf(sprint)
    historia += [PageBreak()]
    historia += _seccion_demo_pdf(sprint)
    historia += [PageBreak()]
    historia += _seccion_cierre_pdf(sprint)
    doc.build(historia)


# =========================================================================== #
# Word                                                                        #
# =========================================================================== #
def _sombrear(celda, color_hex: str) -> None:
    tc_pr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def _bordes(tabla, color_hex: str = "DCD3C1", grosor: int = 4) -> None:
    borders = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(grosor))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color_hex)
        borders.append(el)
    tabla._tbl.tblPr.append(borders)


def _margenes_celda(tabla, izq=80, der=80, arriba=40, abajo=40) -> None:
    margins = OxmlElement("w:tblCellMar")
    for lado, valor in (("top", arriba), ("left", izq),
                        ("bottom", abajo), ("right", der)):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:w"), str(valor))
        el.set(qn("w:type"), "dxa")
        margins.append(el)
    tabla._tbl.tblPr.append(margins)


def _repetir_cabecera(fila) -> None:
    tr_pr = fila._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


def _no_partir_fila(fila) -> None:
    tr_pr = fila._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))


def _campo(parrafo, instruccion: str) -> None:
    run = parrafo.add_run()
    inicio = OxmlElement("w:fldChar")
    inicio.set(qn("w:fldCharType"), "begin")
    texto = OxmlElement("w:instrText")
    texto.set(qn("xml:space"), "preserve")
    texto.text = f" {instruccion} "
    fin = OxmlElement("w:fldChar")
    fin.set(qn("w:fldCharType"), "end")
    run._r.append(inicio)
    run._r.append(texto)
    run._r.append(fin)


def _par(doc, texto="", tam=10, color=TINTA_RGB, negrita=False, fuente=F_CUERPO,
       align=WD_ALIGN_PARAGRAPH.LEFT, antes=0, despues=5, interlineado=1.12,
       cursiva=False):
    par = doc.add_paragraph()
    par.alignment = align
    par.paragraph_format.space_before = Pt(antes)
    par.paragraph_format.space_after = Pt(despues)
    par.paragraph_format.line_spacing = interlineado
    if texto:
        run = par.add_run(texto)
        run.font.size = Pt(tam)
        run.font.color.rgb = color
        run.font.bold = negrita
        run.font.italic = cursiva
        run.font.name = fuente
    return par


def _h1(doc, texto):
    par = _par(doc, texto, tam=15, color=RGBColor(0x2A, 0x1B, 0x13),
             negrita=True, fuente=F_TITULO, antes=12, despues=7,
             interlineado=1.0)
    p_pr = par._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    abajo = OxmlElement("w:bottom")
    abajo.set(qn("w:val"), "single")
    abajo.set(qn("w:sz"), "6")
    abajo.set(qn("w:space"), "4")
    abajo.set(qn("w:color"), "C9BBA0")
    borders.append(abajo)
    p_pr.append(borders)
    return par


def _h2(doc, texto, color=AZUL_RGB):
    return _par(doc, texto, tam=11.3, color=color, negrita=True, fuente=F_TITULO,
              antes=10, despues=4, interlineado=1.0)


def _h3(doc, texto):
    return _par(doc, texto, tam=10, color=TINTA_RGB, negrita=True, antes=7,
              despues=3, interlineado=1.0)


def _escribir_celda(par, valor: str, tam: float) -> None:
    import re

    partes = re.split(r"(\*\*.+?\*\*|`[^`]+`)", str(valor))
    for parte in partes:
        if not parte:
            continue
        if parte.startswith("**") and parte.endswith("**"):
            run = par.add_run(parte[2:-2])
            run.font.bold = True
            run.font.name = F_CUERPO
        elif parte.startswith("`") and parte.endswith("`"):
            run = par.add_run(parte[1:-1])
            run.font.name = F_MONO
        else:
            run = par.add_run(parte)
            run.font.name = F_CUERPO
        run.font.size = Pt(tam)
        run.font.color.rgb = TINTA_RGB


def _tabla_docx(doc, cabeceras, filas, anchos_mm, color_cab=ESPRESSO_HEX,
                banda=True, tam=8, cabecera_tam=None):
    tabla = doc.add_table(rows=0, cols=len(cabeceras))
    tabla.alignment = WD_TABLE_ALIGNMENT.LEFT
    tabla.autofit = False
    _bordes(tabla)
    _margenes_celda(tabla)
    cab_tam = cabecera_tam if cabecera_tam is not None else tam

    fila = tabla.add_row()
    _repetir_cabecera(fila)
    _no_partir_fila(fila)
    for i, texto in enumerate(cabeceras):
        celda = fila.cells[i]
        _sombrear(celda, color_cab)
        celda.width = Mm(anchos_mm[i])
        par = celda.paragraphs[0]
        par.paragraph_format.space_before = Pt(1)
        par.paragraph_format.space_after = Pt(1)
        run = par.add_run(texto)
        run.font.size = Pt(cab_tam)
        run.font.bold = True
        run.font.color.rgb = BLANCO_RGB
        run.font.name = F_CUERPO

    for j, valores in enumerate(filas):
        fila = tabla.add_row()
        _no_partir_fila(fila)
        for i, valor in enumerate(valores):
            celda = fila.cells[i]
            if banda and j % 2 == 1:
                _sombrear(celda, "FBF8F2")
            celda.width = Mm(anchos_mm[i])
            par = celda.paragraphs[0]
            par.paragraph_format.space_before = Pt(1)
            par.paragraph_format.space_after = Pt(1)
            par.paragraph_format.line_spacing = 1.05
            _escribir_celda(par, valor, tam)
    return tabla


def _nota(doc, texto):
    return _par(doc, texto, tam=8, color=SUAVE_RGB, cursiva=True, despues=6,
              interlineado=1.1)


def _vinetas(doc, items):
    for item in items:
        par = _par(doc, f"•  {item}", tam=9.5, despues=2, interlineado=1.1,
                 antes=0)
        par.paragraph_format.left_indent = Mm(4)


def _salto(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def _decorar_docx(seccion, sprint) -> None:
    cabecera = seccion.header
    par = cabecera.paragraphs[0]
    par.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = par.add_run(
        f"{d.EMPRESA}  ·  Sprint {sprint['numero']}  ·  {d.PROYECTO}"
    )
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


def _portada_docx(doc, sprint) -> None:
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
    run = par.add_run(
        "Sistema de Gestión de Exportación\n"
        "de Café y Cacao a la Unión Europea"
    )
    run.font.size = Pt(20)
    run.font.bold = True
    run.font.color.rgb = BLANCO_RGB
    run.font.name = F_TITULO

    par = celda.add_paragraph()
    par.paragraph_format.space_after = Pt(0)
    run = par.add_run(
        f"Documento técnico del Sprint {sprint['numero']}  ·  {d.METODOLOGIA}"
    )
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(0xC4, 0xB4, 0x9C)
    run.font.name = F_CUERPO

    _par(doc, "", despues=8)
    _par(doc, sprint["lema"], tam=10.5, color=AZUL_RGB, negrita=True,
       despues=8)
    _par(doc, "Equipo de trabajo", tam=10, negrita=True, despues=3)
    filas = [[f"**{n}**", a] for n, a in zip(EQUIPO, APELLIDOS)]
    _tabla_docx(doc, ["Integrante", "Apellido"], filas, [120, 54],
                color_cab=ESPRESSO_HEX, tam=9, cabecera_tam=8.5)

    _par(doc, "", despues=6)
    _par(doc, "Contenido del documento", tam=10, negrita=True, despues=3)
    _tabla_docx(
        doc,
        ["Contenido", "Qué encontrarán"],
        [
            ["1. Resumen del sprint", "Objetivo, alcance y resultados."],
            ["2. Historias de usuario", "Fichas con criterios de aceptación."],
            ["3. Arquitectura y tablas", "Capas, tablas nuevas y sus campos."],
            ["4. API y pantallas", "Endpoints, roles y módulos."],
            ["5. Reglas y seguridad", "Lo que el sistema impide y lo que protege."],
            ["6. Pruebas y demostración", "Evidencia y recorrido para exponer."],
        ],
        [70, 104], color_cab=VERDE_HEX, tam=9, cabecera_tam=8.5,
    )
    _par(doc, "", despues=5)
    _nota(doc, f"Periodo: {sprint['periodo']}.  Metodología: {d.METODOLOGIA}.  "
               f"Alcance: {sprint['titulo']}.")
    _salto(doc)


def _seccion_resumen_docx(doc, sprint) -> None:
    _h1(doc, "1. Resumen del sprint")
    for parrafo in sprint["resumen"]:
        _par(doc, parrafo, tam=9.5)
    _h2(doc, "1.1 Objetivos")
    _vinetas(doc, sprint["objetivos"])


def _seccion_historias_docx(doc, sprint) -> None:
    _h1(doc, "2. Historias de usuario")
    _par(doc, "Cada historia dice quién la necesita, qué quiere hacer y para qué. "
            "Los criterios son las condiciones que el sistema cumple hoy y que "
            "se pueden comprobar en la demostración.", tam=9.5)
    _h2(doc, "2.1 Resumen")
    _tabla_docx(
        doc,
        ["ID", "Módulo", "Historia", "Rol", "Prioridad", "Estado"],
        [[f"**{h['id']}**", f"**{h['modulo']}**", h["historia"], h["rol"],
          h["prioridad"], h["estado"]] for h in sprint["historias"]],
        [14, 27, 76, 22, 17, 18], color_cab=ESPRESSO_HEX, tam=8.5,
    )
    _h2(doc, "2.2 Fichas con criterios de aceptación")
    for h in sprint["historias"]:
        tabla = doc.add_table(rows=0, cols=2)
        tabla.autofit = False
        _bordes(tabla)
        _margenes_celda(tabla)
        campos = [
            ("Historia", f"**{h['id']} · {h['historia']}**"),
            ("Quién la necesita", h["rol"]),
            ("Prioridad", h["prioridad"]),
            ("Estado", h["estado"]),
        ]
        for etiqueta, valor in campos:
            fila = tabla.add_row()
            _no_partir_fila(fila)
            izq, der = fila.cells
            izq.width = Mm(34)
            der.width = Mm(140)
            _sombrear(izq, AZUL_HEX)
            par = izq.paragraphs[0]
            par.paragraph_format.space_before = Pt(1)
            par.paragraph_format.space_after = Pt(1)
            par.paragraph_format.keep_with_next = True
            run = par.add_run(etiqueta)
            run.font.size = Pt(8)
            run.font.bold = True
            run.font.color.rgb = BLANCO_RGB
            run.font.name = F_CUERPO
            par = der.paragraphs[0]
            par.paragraph_format.space_before = Pt(1)
            par.paragraph_format.space_after = Pt(1)
            par.paragraph_format.keep_with_next = True
            _escribir_celda(par, valor, 8.5)

        fila = tabla.add_row()
        _no_partir_fila(fila)
        izq, der = fila.cells
        izq.width = Mm(34)
        der.width = Mm(140)
        _sombrear(izq, AZUL_HEX)
        par = izq.paragraphs[0]
        run = par.add_run("Criterios\nde aceptación")
        run.font.size = Pt(8)
        run.font.bold = True
        run.font.color.rgb = BLANCO_RGB
        run.font.name = F_CUERPO
        for i, criterio in enumerate(h["criterios"]):
            par = der.paragraphs[0] if i == 0 else der.add_paragraph()
            par.paragraph_format.space_before = Pt(0)
            par.paragraph_format.space_after = Pt(2)
            par.paragraph_format.line_spacing = 1.08
            par.paragraph_format.left_indent = Mm(3)
            run = par.add_run(f"•  {criterio}")
            run.font.size = Pt(8.5)
            run.font.color.rgb = TINTA_RGB
            run.font.name = F_CUERPO
        _par(doc, "", despues=5)


def _seccion_alcance_docx(doc, sprint) -> None:
    _h1(doc, "3. Alcance y arquitectura")
    _par(doc, "El proyecto mantiene la misma arquitectura de tres capas del Sprint "
            "2: una SPA sin paso de compilación, una API FastAPI con reglas de "
            "negocio en servicios y una base de datos relacional. Los sprints 3 "
            "y 4 agregan módulos y tablas, pero no reemplazan lo que ya "
            "funcionaba.", tam=9.5)
    _h2(doc, "3.1 Qué incluye este sprint", color=VERDE_RGB)
    _vinetas(doc, sprint["alcance_incluye"])
    _h2(doc, "3.2 Qué queda fuera", color=ORO_RGB)
    _vinetas(doc, sprint["alcance_excluye"])
    _h2(doc, "3.3 Módulos y pantallas")
    _tabla_docx(
        doc,
        ["Módulo", "Historia", "Pantalla", "Qué hace", "Roles"],
        [[f"**{m['nombre']}**", m["historia"], f"`{m['pantalla']}`",
          m["que_hace"], m["roles"]] for m in sprint["modulos"]],
        [28, 16, 24, 66, 40], color_cab=VERDE_HEX, tam=8.2,
    )
    _par(doc, "", despues=4)
    _par(doc, "Las tablas nuevas se crean con `Base.metadata.create_all()` y las "
            "migraciones de `app/migraciones.py`. Ninguna de las nueve tablas "
            "del modelo original cambia de forma: los módulos se apoyan en "
            "ellas.", tam=9)


def _seccion_tablas_docx(doc, sprint) -> None:
    _h1(doc, "4. Base de datos")
    _par(doc, "Cada módulo guarda lo que el modelo original no tenía. Las tablas "
            "son nuevas y conservan las llaves foráneas hacia las tablas del "
            "Sprint 2 para no romper la trazabilidad.", tam=9.5)
    for i, t in enumerate(sprint["tablas"], start=1):
        _h2(doc, f"4.{i} Tabla {t['nombre']}")
        _par(doc, t["proposito"], tam=9)
        _tabla_docx(
            doc, ["Campo", "Tipo", "Nota"],
            [[f"**{c}**", f"`{tipo}`", nota] for c, tipo, nota in t["campos"]],
            [50, 42, 82], color_cab=ESPRESSO_HEX, tam=8.5,
        )
        _nota(doc, t["nota"])


def _seccion_api_docx(doc, sprint) -> None:
    _h1(doc, "5. API y pantallas")
    _par(doc, "Todos los endpoints viven bajo `/api` y comparten la autenticación "
            "por token. La columna de roles indica quién puede llamarlos; el "
            "servidor vuelve a comprobar el rol aunque el frontend esconda el "
            "botón.", tam=9.5)
    for i, (modulo, filas) in enumerate(sprint["endpoints"], start=1):
        _h2(doc, f"5.{i} {modulo}")
        _tabla_docx(
            doc, ["Método", "Ruta", "Uso", "Roles"],
            [[f"**{m}**", f"`{r}`", u, rol] for m, r, u, rol in filas],
            [16, 54, 61, 43], color_cab=AZUL_HEX, tam=8.2,
        )
        _par(doc, "", despues=3)


def _seccion_reglas_docx(doc, sprint) -> None:
    _h1(doc, "6. Reglas de negocio y seguridad")
    _h2(doc, "6.1 Reglas que el sistema hace cumplir", color=RUST_RGB)
    _tabla_docx(
        doc, ["Regla", "Cómo se aplica"],
        [[f"**{r}**", c] for r, c in sprint["reglas"]],
        [50, 124], color_cab=RUST_HEX, tam=8.5,
    )
    _h2(doc, "6.2 Seguridad y permisos", color=VERDE_RGB)
    _vinetas(doc, sprint["seguridad"])


def _seccion_pruebas_docx(doc, sprint) -> None:
    _h1(doc, "7. Pruebas y verificación")
    _par(doc, "Las pruebas corren contra una base SQLite temporal y no necesitan "
            "un servidor. Cada módulo tiene sus casos felices y sus casos de "
            "error.", tam=9.5)
    _tabla_docx(
        doc, ["Módulo", "Pruebas", "Qué cubren"],
        [[f"**{m}**", str(n), q] for m, n, q in sprint["pruebas"]],
        [34, 16, 124], color_cab=VERDE_HEX, tam=8.5,
    )
    _par(doc, "", despues=3)
    _par(doc, f"**Total del sprint:** {sprint['pruebas_total']} pruebas nuevas. "
            "La suite completa del proyecto queda en **90 pruebas**.", tam=9.5)
    _h2(doc, "7.1 Comprobaciones estáticas")
    _par(doc, "Además de pytest, el proyecto trae tres comprobaciones que se "
            "ejecutan sin Node: `tools/check_js.py` revisa sintaxis y símbolos "
            "del frontend, `tools/check_refs.py` busca referencias sin resolver "
            "y `tools/verificar_sql.py` compara los guiones de PostgreSQL y "
            "MySQL con el modelo de Python.", tam=9.5)


def _seccion_demo_docx(doc, sprint) -> None:
    _h1(doc, "8. Demostración guiada")
    _par(doc, "Este es el recorrido que se puede hacer en vivo. Cada paso dice qué "
            "pantalla abrir y qué debe verse; si algo falla, la prueba "
            "automática sigue siendo la evidencia.", tam=9.5)
    _tabla_docx(
        doc, ["Paso", "Qué hacer", "Qué debe verse"],
        [[f"**{n}**", a, b] for n, a, b in sprint["demo"]],
        [14, 68, 92], color_cab=ORO_HEX, tam=8.5,
    )


def _seccion_cierre_docx(doc, sprint) -> None:
    _h1(doc, "9. Resultados y cierre")
    _vinetas(doc, sprint["resultados"])
    _h2(doc, "9.1 Lo que sigue", color=ORO_RGB)
    _vinetas(doc, sprint["siguiente"])
    if sprint["config"]:
        _h2(doc, "9.2 Configuración")
        _tabla_docx(
            doc, ["Variable", "Valor por defecto", "Para qué sirve"],
            [[f"`{v}`", f"`{val}`", uso] for v, val, uso in sprint["config"]],
            [44, 34, 96], color_cab=ESPRESSO_HEX, tam=8.5,
        )
    _par(doc, "", despues=5)
    _nota(doc, "Documento generado desde `docs/datos_sprint34.py`. El código, "
               "los endpoints y las pruebas son la fuente de verdad: si "
               "cambian, se regeneran el PDF y el Word con "
               "`python -m docs.sprint34`.")


def construir_docx(sprint, destino: pathlib.Path) -> None:
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
    _decorar_docx(seccion, sprint)

    normal = doc.styles["Normal"]
    normal.font.name = F_CUERPO
    normal.font.size = Pt(10)
    normal.font.color.rgb = TINTA_RGB
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.12

    _portada_docx(doc, sprint)
    _seccion_resumen_docx(doc, sprint)
    _salto(doc)
    _seccion_historias_docx(doc, sprint)
    _salto(doc)
    _seccion_alcance_docx(doc, sprint)
    _salto(doc)
    _seccion_tablas_docx(doc, sprint)
    _salto(doc)
    _seccion_api_docx(doc, sprint)
    _salto(doc)
    _seccion_reglas_docx(doc, sprint)
    _salto(doc)
    _seccion_pruebas_docx(doc, sprint)
    _salto(doc)
    _seccion_demo_docx(doc, sprint)
    _salto(doc)
    _seccion_cierre_docx(doc, sprint)

    props = doc.core_properties
    props.title = f"{d.PROYECTO} — Documento Sprint {sprint['numero']}"
    props.author = d.EMPRESA
    props.subject = sprint["titulo"]
    props.comments = "Generado por docs/sprint34.py desde docs/datos_sprint34.py"
    doc.save(str(destino))


# =========================================================================== #
# Entrada                                                                     #
# =========================================================================== #
def _paginas(destino: pathlib.Path) -> int:
    import pymupdf

    return len(pymupdf.open(destino))


def main() -> None:
    print("Documentos de los Sprints 3 y 4")
    for sprint, base_nombre in (
        (d.SPRINT3, "5_Documento_Sprint3_RiTech"),
        (d.SPRINT4, "6_Documento_Sprint4_RiTech"),
    ):
        pdf = SALIDA / f"{base_nombre}.pdf"
        docx = SALIDA / f"{base_nombre}.docx"
        construir_pdf(sprint, pdf)
        construir_docx(sprint, docx)
        print(f"  {pdf.name}  ({_paginas(pdf)} páginas)")
        print(f"  {docx.name}")
    print(f"  en {SALIDA}")


if __name__ == "__main__":
    main()
