"""Genera el documento del Sprint 2 con los cinco puntos del enunciado.

    python -m docs.documento

Produce:
    docs/salida/1_Documento_Sprint2_RiTech.pdf
"""

from __future__ import annotations

import pathlib

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from docs import datos
from docs import nombres

SALIDA = pathlib.Path(__file__).parent / "salida"
SALIDA.mkdir(parents=True, exist_ok=True)
DESTINO = SALIDA / "1_Documento_Sprint2_RiTech.pdf"
#: Ficheros intermedios: se limpian al terminar la construcción.
TEMPORAL = SALIDA / "_tmp"

# Paleta del proyecto
ESPRESSO = colors.HexColor("#2A1B13")
TINTA = colors.HexColor("#241A12")
SUAVE = colors.HexColor("#6B5D4F")
PAPER = colors.HexColor("#F1ECE2")
LINEA = colors.HexColor("#C9BBA0")
AZUL = colors.HexColor("#1F4E8C")
AZUL_SUAVE = colors.HexColor("#DCE7F4")
VERDE = colors.HexColor("#4B7B52")
VERDE_SUAVE = colors.HexColor("#DEEBDF")
ORO = colors.HexColor("#B9893B")
ORO_SUAVE = colors.HexColor("#F3E8D2")
RUST = colors.HexColor("#A84B32")
RUST_SUAVE = colors.HexColor("#F3DDD5")
CREMA = colors.HexColor("#FFFDF9")

ANCHO_PAG, ALTO_PAG = A4
MARGEN = 18 * mm
UTIL = ANCHO_PAG - 2 * MARGEN

# --------------------------------------------------------------------------- #
# Estilos                                                                     #
# --------------------------------------------------------------------------- #
base = getSampleStyleSheet()

S_TITULO = ParagraphStyle("titulo", parent=base["Title"], fontName="Helvetica-Bold",
                          fontSize=22, leading=26, textColor=ESPRESSO, spaceAfter=6)
S_SUBT = ParagraphStyle("subt", parent=base["Normal"], fontName="Helvetica",
                        fontSize=11, leading=15, textColor=SUAVE, alignment=TA_CENTER)
S_H1 = ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold",
                      fontSize=15, leading=19, textColor=ESPRESSO,
                      spaceBefore=6, spaceAfter=8)
S_H2 = ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold",
                      fontSize=11.5, leading=15, textColor=AZUL,
                      spaceBefore=10, spaceAfter=5)
S_H3 = ParagraphStyle("h3", parent=base["Heading3"], fontName="Helvetica-Bold",
                      fontSize=9.8, leading=13, textColor=TINTA,
                      spaceBefore=7, spaceAfter=3)
S_P = ParagraphStyle("p", parent=base["Normal"], fontName="Helvetica", fontSize=9,
                     leading=13, textColor=TINTA, alignment=TA_JUSTIFY, spaceAfter=5)
S_PC = ParagraphStyle("pc", parent=S_P, alignment=TA_CENTER)
S_NOTA = ParagraphStyle("nota", parent=base["Normal"], fontName="Helvetica-Oblique",
                        fontSize=7.8, leading=10.5, textColor=SUAVE, spaceAfter=4)
S_TH = ParagraphStyle("th", parent=base["Normal"], fontName="Helvetica-Bold",
                      fontSize=7.4, leading=9.5, textColor=colors.white)
S_TD = ParagraphStyle("td", parent=base["Normal"], fontName="Helvetica",
                      fontSize=7.4, leading=9.6, textColor=TINTA)
S_TDB = ParagraphStyle("tdb", parent=S_TD, fontName="Helvetica-Bold")
S_MONO = ParagraphStyle("mono", parent=base["Normal"], fontName="Courier",
                        fontSize=7, leading=9, textColor=TINTA)
S_CRIT = ParagraphStyle("crit", parent=base["Normal"], fontName="Helvetica",
                        fontSize=7.6, leading=10.2, textColor=TINTA, leftIndent=10)


def p(txt, estilo=S_P):
    return Paragraph(txt, estilo)


# --------------------------------------------------------------------------- #
# Plantilla con encabezado y numeración                                        #
# --------------------------------------------------------------------------- #
def _decorada(c, doc):
    c.saveState()
    # Franja superior
    c.setFillColor(ESPRESSO)
    c.rect(0, ALTO_PAG - 14 * mm, ANCHO_PAG, 14 * mm, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#C4B49C"))
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGEN, ALTO_PAG - 9.5 * mm,
                 f"{datos.EMPRESA}  ·  Sprint 2  ·  {datos.PROYECTO}")
    c.drawRightString(ANCHO_PAG - MARGEN, ALTO_PAG - 9.5 * mm, datos.FECHA)
    # Pie
    c.setStrokeColor(LINEA)
    c.setLineWidth(0.5)
    c.line(MARGEN, 15 * mm, ANCHO_PAG - MARGEN, 15 * mm)
    c.setFillColor(SUAVE)
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGEN, 11 * mm, "Sistema de gestión de exportaciones de café y cacao")
    c.drawRightString(ANCHO_PAG - MARGEN, 11 * mm, f"Página {doc.page}")
    c.restoreState()


def _limpia(c, doc):
    c.saveState()
    c.setFillColor(ESPRESSO)
    c.rect(0, ALTO_PAG - 14 * mm, ANCHO_PAG, 14 * mm, stroke=0, fill=1)
    c.restoreState()


# --------------------------------------------------------------------------- #
# Tablas                                                                      #
# --------------------------------------------------------------------------- #
def _tabla(cabeceras, filas, anchos, color_cab=ESPRESSO, zebra=True, tam=7.4):
    # Cada fila de Table es una lista de celdas: la cabecera va plana y
    # se envuelve una sola vez al concatenar con el cuerpo.
    cab = [Paragraph(t, S_TH) for t in cabeceras]
    cuerpo = [[Paragraph(str(c), S_TD) for c in fila] for fila in filas]
    t = Table([cab] + cuerpo, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), color_cab),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINEA),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    if zebra:
        for i in range(1, len(cuerpo) + 1):
            if i % 2 == 0:
                estilo.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FBF8F2")))
    t.setStyle(TableStyle(estilo))
    return t


# --------------------------------------------------------------------------- #
# Contenido                                                                    #
# --------------------------------------------------------------------------- #
def portada():
    return [
        Spacer(1, 34 * mm),
        p(datos.EMPRESA, ParagraphStyle("e", parent=S_SUBT, fontSize=12,
                                        textColor=ORO, fontName="Helvetica-Bold")),
        Spacer(1, 6 * mm),
        p("Sistema de Gestión de Exportación<br/>de Café y Cacao a la Unión Europea",
          ParagraphStyle("t", parent=S_TITULO, fontSize=25, leading=30, alignment=TA_CENTER)),
        Spacer(1, 4 * mm),
        p("Documento técnico del Sprint 2", ParagraphStyle("s", parent=S_SUBT, fontSize=12)),
        Spacer(1, 12 * mm),
        tabla_integrantes(),
        Spacer(1, 14 * mm),
        _tabla(
            ["Punto del enunciado", "Contenido", "Ubicación"],
            [
                ["1. Requisitos",
                 "Funcionales, no funcionales y de restricción",
                 "Sección 1"],
                ["2. Diagrama UML",
                 "Actores del sistema y casos de uso",
                 "Sección 2"],
                ["3. Product backlog de septiembre",
                 "Elementos trabajados y responsable de cada uno",
                 "Sección 3"],
                ["4. Épicas e historias de usuario",
                 "Con criterios de aceptación",
                 "Sección 4"],
                ["5. Base de datos",
                 "Tablas y relaciones entre tablas",
                 "Sección 5"],
            ],
            [58 * mm, 62 * mm, 28 * mm], color_cab=VERDE),
        Spacer(1, 12 * mm),
        p(f"<b>Metodología:</b> {datos.METODOLOGIA}<br/>"
          f"<b>Alcance:</b> módulos de productores y lotes, calidad, comercial y logística, "
          f"más el armazón de usuarios y roles.",
          ParagraphStyle("f", parent=S_NOTA, alignment=TA_CENTER, fontSize=8.2)),
    ]


def tabla_integrantes():
    filas = [[Paragraph(n, ParagraphStyle("n", parent=S_TD, fontName="Helvetica-Bold",
                                         fontSize=8.4, textColor=TINTA)),
              Paragraph(a, S_TD)] for n, a in zip(datos.EQUIPO, nombres.APELLIDOS)]
    t = Table([[Paragraph("Integrante", S_TH), Paragraph("Apellido", S_TH)]] + filas,
              colWidths=[80 * mm, 40 * mm], hAlign="CENTER")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ESPRESSO),
        ("GRID", (0, 0), (-1, -1), 0.4, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 1), (-1, -1), CREMA),
    ]))
    return t


def seccion_requisitos():
    e = [p("1. Requisitos del sistema", S_H1),
         p("Los sacamos del informe del proyecto y los separamos en tres tipos: "
           "lo que tiene que hacer el sistema, cómo se debe ver y con qué se "
           "puede trabajar. Son la base de las historias de usuario."),
         ]

    for titulo, filas, color in [
        ("1.1 Requisitos funcionales", datos.REQUISITOS_FUNCIONALES, AZUL),
        ("1.2 Requisitos no funcionales", datos.REQUISITOS_NO_FUNCIONALES, VERDE),
        ("1.3 Requisitos de restricción", datos.REQUISITOS_RESTRICCION, ORO),
    ]:
        e.append(p(titulo, S_H2))
        datos_t = [[f"<b>{rid}</b>", f"<b>{nombre}</b>", desc]
                   for rid, nombre, desc in filas]
        e.append(_tabla(["ID", "Nombre", "Qué tiene que hacer"],
                        datos_t, [18 * mm, 40 * mm, 116 * mm], color))
        e.append(Spacer(1, 3 * mm))

    return e


def seccion_uml():
    e = [p("2. Diagrama UML: actores y casos de uso", S_H1),
         p("El sistema tiene <b>cinco actores</b>. Cuatro son internos de RiTech SAS y "
           "se corresponden con los roles del requisito RR-003; el quinto es externo: "
           "el cliente europeo, que entra por un portal donde solo ve lo suyo."),
         p("2.1 Actores del sistema", S_H2),
         _tabla(["Actor", "Tipo", "Responsabilidad"],
                [[f"<b>{n}</b>",
                  "Interno" if n != "Cliente europeo" else "Externo",
                  d] for n, d in datos.ACTORES],
                [40 * mm, 20 * mm, 92 * mm], color_cab=VERDE),
         Spacer(1, 4 * mm),
         p("2.2 Casos de uso por módulo", S_H2),
         ]

    filas = []
    for modulo, casos in datos.CASOS_DE_USO.items():
        for i, (nombre, actor) in enumerate(casos):
            filas.append([f"<b>{modulo}</b>" if i == 0 else "",
                          f"<b>{nombre}</b>", actor])
    e.append(_tabla(["Módulo", "Caso de uso", "Actor principal"],
                    filas, [58 * mm, 58 * mm, 36 * mm], color_cab=AZUL))

    e.append(Spacer(1, 5 * mm))
    e.append(p("2.3 Diagrama de casos de uso", S_H2))
    img = _imagen("diagrama_casos_de_uso.pdf", ANCHO_PAG)
    if img:
        e.append(img)
        e.append(p("Figura 1. Diagrama de casos de uso del sistema.", S_NOTA))
    return e


def seccion_backlog():
    e = [p("3. Lo que hicimos en el sprint", S_H1),
         p("Estas son las siete tareas del sprint de septiembre. Cada una tiene una "
           "persona responsable, y las siete quedaron terminadas. Al lado de cada una "
           "estan las historias de usuario que se hicieron con ella."),
          p("3.1 Tareas del sprint", S_H2),
          ]
    filas = []
    for clave, que, hus, resp, estado in datos.BACKLOG_SEPTIEMBRE:
        color_estado = VERDE if estado == "Hecho" else ORO
        filas.append([
            f"<b>{clave}</b>", f"<b>{que}</b>", hus,
            resp, f'<font color="{color_estado.hexval()}"><b>{estado}</b></font>',
        ])
    e.append(_tabla(
        ["Tarea", "Qué se hizo", "Historias", "Quién lo hizo", "Estado"],
        filas, [16 * mm, 74 * mm, 22 * mm, 32 * mm, 30 * mm],
        color_cab=ESPRESSO))

    e.append(p("3.2 Tareas técnicas", S_H2))
    filas = [[f"<b>{c}</b>", d, r] for c, d, r in datos.TAREAS_SEPTIEMBRE]
    e.append(_tabla(["Tarea", "Descripción", "Quién lo hizo"], filas,
                    [16 * mm, 96 * mm, 62 * mm], color_cab=ORO))

    e.append(p("3.3 Distribución del trabajo por integrante", S_H2))
    filas = []
    for nombre in datos.EQUIPO:
        clave = datos.CLAVE[datos.EQUIPO.index(nombre)]
        epi = [b for b in datos.BACKLOG_SEPTIEMBRE if b[3] == clave]
        tar = [t for t in datos.TAREAS_SEPTIEMBRE if t[2] == clave]
        historias = sorted({h.strip() for b in epi for h in b[2].split(",")})
        filas.append([
            f"<b>{nombre}</b>",
            f"{len(epi)} tareas y {len(tar)} técnicas",
            ", ".join(historias) or "—",
        ])
    e.append(_tabla(["Integrante", "Qué hizo", "Historias a su cargo"],
                    filas, [52 * mm, 40 * mm, 82 * mm], color_cab=VERDE))
    return e


def seccion_historias():
    e = [p("4. Historias de usuario", S_H1),
         p(f"Del informe del proyecto sacamos <b>{len(datos.HISTORIAS)} historias de "
           "usuario</b>. Cada una dice quién la necesita, qué quiere hacer y para qué, "
           "y trae sus criterios de aceptación: las cosas que tiene que cumplir el "
           "sistema para que la cuenta como terminada."),
         p("4.1 Resumen de las historias", S_H2),
         ]
    filas = []
    for hid, epica, historia, rol, prio, _puntos, _c, estado in datos.HISTORIAS:
        filas.append([f"<b>{hid}</b>", f"<b>{epica}</b>", historia, rol, prio,
                      estado])
    e.append(_tabla(
        ["ID", "Módulo", "Historia de usuario", "Quién la necesita", "Prioridad",
         "Estado"],
        filas, [15 * mm, 28 * mm, 68 * mm, 24 * mm, 18 * mm, 21 * mm],
        color_cab=ESPRESSO))
    e.append(PageBreak())

    e.append(p("4.2 Historias con sus criterios de aceptación", S_H2))
    modulo_historia: dict[str, list] = {}
    for h in datos.HISTORIAS:
        modulo_historia.setdefault(h[1], []).append(h)

    for epica, historias in modulo_historia.items():
        bloque = [p(f"Módulo · {epica}", S_H3)]
        for hid, _e, historia, rol, prio, _puntos, criterios, estado in historias:
            filas = [
                ["Historia", f"<b>{historia}</b>"],
                ["Quién la necesita", rol],
                ["Prioridad", prio],
                ["Estado", estado],
                ["Criterios de aceptación", ""],
            ]
            # Los criterios de aceptación van como lista en la última fila.
            filas[-1][1] = "<br/>".join(f"• {c}" for c in criterios)
            t = _tabla(["Campo", "Valor"], filas,
                       [34 * mm, 118 * mm], color_cab=AZUL, zebra=False)
            bloque.append(t)
            bloque.append(Spacer(1, 3.5 * mm))
        e.append(KeepTogether(bloque))
    return e


def seccion_datos():
    e = [p("5. Estructura de la base de datos", S_H1),
         p("El modelo tiene <b>nueve tablas</b>, tal como se definió en el documento de "
           "base de datos del proyecto. A esas les añadimos <b>tres tablas más</b> para "
           "guardar la catación, los certificados y los contenedores, que son datos "
           "que el modelo original no tiene."),
         p("5.1 Tablas del modelo de datos", S_H2),
         ]

    for tabla, campos, desc in datos.NUCLEO_TABLAS:
        filas = [[f"<b>{n}</b>", f"<font face='Courier'>{t}</font>", nota or ""]
                 for n, t, nota in campos]
        t = Table(
            [[Paragraph(f"Tabla {tabla}", S_TH),
              Paragraph("PK = llave primaria · FK = llave foránea", S_TH)]] + filas,
            colWidths=[46 * mm, 56 * mm, 50 * mm], hAlign="LEFT", repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ESPRESSO),
            ("GRID", (0, 0), (-1, -1), 0.4, LINEA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        e.append(KeepTogether([
            t,
            p(desc, S_NOTA),
            Spacer(1, 3.5 * mm),
        ]))

    e.append(PageBreak())
    e.append(p("5.2 Relaciones entre tablas", S_H2))
    e.append(_tabla(
        ["Origen", "Destino", "Cardinalidad", "Regla de integridad"],
        [[f"<b>{o}</b>", f"<b>{d}</b>", c, r] for o, d, c, r in datos.RELACIONES],
        [32 * mm, 36 * mm, 22 * mm, 62 * mm], color_cab=VERDE))
    e.append(Spacer(1, 4 * mm))

    e.append(p("5.3 Tablas que añadimos", S_H2))
    e.append(p("Los cuatro módulos necesitan guardar tres cosas que no están en las "
               "nueve tablas del modelo. Van en tablas aparte, sin tocar el modelo "
               "que nos entregaron."))
    e.append(_tabla(["Tabla", "Propósito"],
                    [[f"<b>{t}</b>", d] for t, d in datos.EXTENSIONES_TABLAS],
                    [42 * mm, 110 * mm], color_cab=ORO))

    e.append(PageBreak())
    e.append(p("5.4 Diagrama entidad-relación", S_H2))
    img = _imagen("diagrama_entidad_relacion.pdf", ANCHO_PAG)
    if img:
        e.append(img)
        e.append(p("Figura 2. Diagrama entidad-relación y tabla de relaciones.", S_NOTA))

    e.append(p("5.5 Base de datos que usamos", S_H2))
    e.append(p("La información se guarda en PostgreSQL, que es lo que pide el "
               "requisito RR-002. El proyecto trae un archivo "
               "<font face='Courier'>sql/schema_postgres.sql</font> con la forma de "
               "crear las tablas, y la aplicación usa SQLite por defecto para que se "
               "pueda levantar sin instalar nada."))
    return e


def seccion_estado():
    e = [p("6. Qué quedó hecho y qué falta", S_H1),
         p("El sprint se dividió en cuatro módulos, y los cuatro quedaron "
           "terminados:"),
         ]
    filas = [[f"<b>{n}</b>", f"<b>{nombre}</b>", estado]
             for n, nombre, estado in datos.MODULOS]
    e.append(_tabla(["N.º", "Módulo", "Estado"], filas,
                    [16 * mm, 106 * mm, 40 * mm], color_cab=VERDE))
    e.append(Spacer(1, 5 * mm))

    e.append(p("6.1 Lo que falta para el siguiente sprint", S_H2))
    e.append(p("Quedan tres cosas, que ya están anotadas:"))
    e.append(_tabla(
        ["Qué falta", "Para qué sirve"],
        [["El módulo de pagos",
          " Registrar anticipos, saldos y cartas de crédito."],
         ["Avisos por correo",
          " Que llegue un correo cuando un certificado está por vencer."],
         ["Subida de documentos",
          " Poder adjuntar la factura y el certificado de embarque al envío."]],
        [56 * mm, 106 * mm], color_cab=ORO))
    e.append(Spacer(1, 5 * mm))

    e.append(p("6.2 Los datos que muestra el sistema", S_H2))
    e.append(p("En la pantalla principal se ven estos seis números:"))
    e.append(_tabla(["Dato", "Dato", "Dato"],
                    [datos.KPIS[i:i + 2] for i in (0, 2, 4)],
                    [54 * mm] * 3, color_cab=AZUL, zebra=False))
    e.append(Spacer(1, 5 * mm))

    e.append(p("6.3 Las etapas de un envío", S_H2))
    e.append(p("Cada envío pasa por estas seis etapas, y así se ve en la pantalla:"))
    e.append(_tabla(["Orden", "Etapa", "Orden", "Etapa"],
                    [[str(i + 1), e_, str(i + 3) if i + 3 < len(datos.CADENA_ESTADOS) else "",
                      datos.CADENA_ESTADOS[i + 3] if i + 3 < len(datos.CADENA_ESTADOS) else ""]
                     for i, e_ in enumerate(datos.CADENA_ESTADOS[:3])],
                    [20 * mm, 60 * mm, 20 * mm, 60 * mm], color_cab=RUST, zebra=False))
    e.append(p("El sistema deja mover el envío un paso a la vez, hacia adelante o "
               "hacia atrás, para que no se salte ninguna etapa.", S_NOTA))
    return e


# --------------------------------------------------------------------------- #
# Imagen de un PDF (primera página)                                            #
# --------------------------------------------------------------------------- #
def _imagen(nombre_pdf, ancho_max, dpi=150):
    """Incrusta la primera página de un PDF como imagen del documento.

    El PNG intermedio se escribe en `salida/_tmp` porque reportlab lo lee al
    maquetar, no al crear el flowable; se borra al terminar `construir()`.
    """
    import pymupdf

    ruta = SALIDA / nombre_pdf
    if not ruta.exists():
        return None
    doc = pymupdf.open(ruta)
    pix = doc[0].get_pixmap(dpi=dpi)
    doc.close()

    TEMPORAL.mkdir(parents=True, exist_ok=True)
    temporal = TEMPORAL / f"{nombre_pdf[:-4]}.png"
    pix.save(temporal)

    ancho_px, alto_px = pix.width, pix.height
    ancho = ancho_max
    alto = ancho * alto_px / ancho_px
    if alto > 195 * mm:
        alto = 195 * mm
        ancho = alto * ancho_px / alto_px
    return Image(str(temporal), width=ancho, height=alto)


def _limpiar_temporales() -> None:
    if TEMPORAL.exists():
        for f in TEMPORAL.iterdir():
            f.unlink(missing_ok=True)
        TEMPORAL.rmdir()


# --------------------------------------------------------------------------- #
# Construcción                                                                 #
# --------------------------------------------------------------------------- #
def construir() -> None:
    doc = BaseDocTemplate(
        str(DESTINO), pagesize=A4,
        leftMargin=MARGEN, rightMargin=MARGEN,
        topMargin=22 * mm, bottomMargin=20 * mm,
        title=f"{datos.PROYECTO} — Documento Sprint 2",
        author=datos.EMPRESA,
        subject="Requisitos, UML, backlog, historias de usuario y base de datos",
    )
    marco = Frame(MARGEN, 20 * mm, UTIL, ALTO_PAG - 42 * mm, id="marco")
    doc.addPageTemplates([
        PageTemplate(id="portada", frames=[marco], onPage=_limpia),
        PageTemplate(id="normal", frames=[marco], onPage=_decorada),
    ])

    historia = []
    historia += portada()
    historia += [NextPageTemplate("normal"), PageBreak()]
    historia += seccion_requisitos()
    historia += seccion_uml()
    historia += [PageBreak()]
    historia += seccion_backlog()
    historia += seccion_historias()
    historia += seccion_datos()
    historia += seccion_estado()

    try:
        doc.build(historia)
    finally:
        # Los PNG intermedios ya cumplieron su función.
        _limpiar_temporales()

    paginas = _cuenta_paginas()
    print(f"  1_Documento_Sprint2_RiTech.pdf  ({paginas} páginas)")


def _cuenta_paginas():
    import pymupdf

    return len(pymupdf.open(DESTINO))


def main() -> None:
    print("Documento del Sprint 2")
    # Los diagramas deben existir antes de incrustarlos.
    for f in ("diagrama_casos_de_uso.pdf", "diagrama_entidad_relacion.pdf"):
        if not (SALIDA / f).exists():
            import docs.diagramas as dg
            import docs.diagrama_er as er

            if f.startswith("diagrama_casos"):
                dg.diagrama_casos_de_uso(SALIDA / f)
            else:
                er.construir(SALIDA / f)
    construir()
    print(f"  en {DESTINO}")


if __name__ == "__main__":
    main()
