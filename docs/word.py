"""Genera el documento del Sprint 2 en Word.

    python -m docs.word

Produce:
    docs/salida/1_Documento_Sprint2_RiTech.docx

Mismo contenido que `documento.py` (el PDF), con la ventaja de que se puede
editar: es el formato útil cuando hay que corregir el reparto de responsables o
los criterios de aceptación antes de entregar.
"""

from __future__ import annotations

import pathlib

import pymupdf
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

from docs import datos, nombres

SALIDA = pathlib.Path(__file__).parent / "salida"
SALIDA.mkdir(parents=True, exist_ok=True)
DESTINO = SALIDA / "1_Documento_Sprint2_RiTech.docx"
TEMPORAL = SALIDA / "_tmp"

# --------------------------------------------------------------------------- #
# Paleta (idéntica al PDF y al mockup del proyecto)                           #
# --------------------------------------------------------------------------- #
ESPRESSO = "2A1B13"
TINTA = RGBColor(0x24, 0x1A, 0x12)
SUAVE = RGBColor(0x6B, 0x5D, 0x4F)
CREMA = RGBColor(0xFF, 0xFD, 0xF9)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
AZUL = RGBColor(0x1F, 0x4E, 0x8C)
VERDE = RGBColor(0x4B, 0x7B, 0x52)
RUST = RGBColor(0xA8, 0x4B, 0x32)
ORO = RGBColor(0xB9, 0x89, 0x3B)

F_TITULO = "Georgia"
F_CUERPO = "Calibri"
F_MONO = "Consolas"

MARGEN = Mm(18)
UTIL_MM = 174  # A4 menos los dos márgenes


# --------------------------------------------------------------------------- #
# Utilidades de bajo nivel (python-docx no expone sombreado ni campos)        #
# --------------------------------------------------------------------------- #
def _sombrear(celda, color_hex: str) -> None:
    tc_pr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def _sombrear_parrafo(parrafo, color_hex: str) -> None:
    p_pr = parrafo._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    p_pr.append(shd)


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


def _repetir_cabecera(fila) -> None:
    """Marca la fila como encabezado, para que se repita al saltar de página."""
    tr_pr = fila._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


def _no_partir_fila(fila) -> None:
    tr_pr = fila._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    tr_pr.append(el)


def _margenes_celda(tabla, izq=80, der=80, arriba=40, abajo=40) -> None:
    margins = OxmlElement("w:tblCellMar")
    for lado, valor in (("top", arriba), ("left", izq),
                        ("bottom", abajo), ("right", der)):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:w"), str(valor))
        el.set(qn("w:type"), "dxa")
        margins.append(el)
    tabla._tbl.tblPr.append(margins)


def _campo(parrafo, instruccion: str) -> None:
    """Inserta un campo de Word, por ejemplo PAGE o NUMPAGES."""
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


def _espaciador(parrafo, puntos: float) -> None:
    """Espaciado antes y después del párrafo, en puntos."""
    parrafo.paragraph_format.space_before = Pt(puntos)
    parrafo.paragraph_format.space_after = Pt(puntos)


# --------------------------------------------------------------------------- #
# Párrafos y tablas                                                            #
# --------------------------------------------------------------------------- #
def _p(doc, texto="", tam=10, color=TINTA, negrita=False, fuente=F_CUERPO,
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


def _rico(doc, partes, tam=10, align=WD_ALIGN_PARAGRAPH.LEFT, antes=0,
          despues=5, interlineado=1.12):
    """Párrafo con varios tramos de formato: [(texto, negrita, fuente), …]."""
    par = doc.add_paragraph()
    par.alignment = align
    par.paragraph_format.space_before = Pt(antes)
    par.paragraph_format.space_after = Pt(despues)
    par.paragraph_format.line_spacing = interlineado
    for texto, negrita, fuente in partes:
        run = par.add_run(texto)
        run.font.size = Pt(tam)
        run.font.color.rgb = TINTA
        run.font.bold = negrita
        run.font.name = fuente
    return par


def _h1(doc, texto):
    par = _p(doc, texto, tam=15, color=RGBColor(0x2A, 0x1B, 0x13), negrita=True,
             fuente=F_TITULO, antes=14, despues=7, interlineado=1.0)
    # El borde inferior separa las secciones sin necesidad de una tabla.
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


def _h2(doc, texto, color=AZUL):
    return _p(doc, texto, tam=11.5, color=color, negrita=True, fuente=F_TITULO,
              antes=11, despues=4, interlineado=1.0)


def _h3(doc, texto, color=TINTA):
    return _p(doc, texto, tam=10, color=color, negrita=True, antes=8, despues=3,
              interlineado=1.0)


def _tabla(doc, cabeceras, filas, anchos_mm, color_cab=ESPRESSO, banda=True,
           tam=8, cabecera_tam=None):
    tabla = doc.add_table(rows=0, cols=len(cabeceras))
    tabla.alignment = WD_TABLE_ALIGNMENT.LEFT
    tabla.autofit = False
    _bordes(tabla)
    _margenes_celda(tabla)

    cab_tam = cabecera_tam if cabecera_tam is not None else tam

    # Cabecera
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
        run.font.color.rgb = BLANCO
        run.font.name = F_CUERPO

    # Cuerpo
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
            _escribir_celda(par, str(valor), tam)
    return tabla


def _escribir_celda(par, valor: str, tam: float) -> None:
    """Escribe en la celda respetando **negrita** y `mono` dentro del texto."""
    import re

    partes = re.split(r"(\*\*.+?\*\*|`[^`]+`)", valor)
    for parte in partes:
        if not parte:
            continue
        if parte.startswith("**") and parte.endswith("**"):
            run = par.add_run(parte[2:-2])
            run.font.bold = True
        elif parte.startswith("`") and parte.endswith("`"):
            run = par.add_run(parte[1:-1])
            run.font.name = F_MONO
        else:
            run = par.add_run(parte)
        run.font.size = Pt(tam)
        run.font.color.rgb = TINTA
        run.font.name = F_MONO if (parte.startswith("`") and parte.endswith("`")) \
            else F_CUERPO
        if run.font.name is None:
            run.font.name = F_CUERPO


def _nota(doc, texto):
    return _p(doc, texto, tam=8, color=SUAVE, cursiva=True, despues=6,
              interlineado=1.1)


def _aviso(doc, titulo, texto):
    """Recuadro destacado para las advertencias de la sección 3."""
    tabla = doc.add_table(rows=1, cols=1)
    tabla.autofit = False
    _bordes(tabla, "E0CBA0", grosor=8)
    _margenes_celda(tabla, izq=120, der=120, arriba=80, abajo=80)
    celda = tabla.rows[0].cells[0]
    celda.width = Mm(UTIL_MM)
    _sombrear(celda, "F3E8D2")

    par = celda.paragraphs[0]
    par.paragraph_format.space_after = Pt(2)
    run = par.add_run(titulo)
    run.font.size = Pt(9)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x6B, 0x4E, 0x1E)
    run.font.name = F_CUERPO

    par2 = celda.add_paragraph()
    par2.paragraph_format.space_after = Pt(0)
    par2.paragraph_format.line_spacing = 1.12
    run = par2.add_run(texto)
    run.font.size = Pt(8.5)
    run.font.color.rgb = TINTA
    run.font.name = F_CUERPO
    _p(doc, "", despues=4)
    return tabla


def _imagen(doc, nombre_pdf, ancho_mm=UTIL_MM, pagina=0):
    """Incrusta una página de un PDF, adjusting el alto a la caja disponible."""
    ruta = SALIDA / nombre_pdf
    if not ruta.exists():
        _p(doc, f"[falta {nombre_pdf}]", tam=9, color=RUST)
        return None

    doc_pdf = pymupdf.open(ruta)
    pix = doc_pdf[min(pagina, len(doc_pdf) - 1)].get_pixmap(dpi=200)
    doc_pdf.close()

    TEMPORAL.mkdir(parents=True, exist_ok=True)
    temporal = TEMPORAL / f"word_{nombre_pdf[:-4]}_{pagina}.png"
    pix.save(temporal)

    proporcion = pix.width / pix.height
    ancho = ancho_mm
    alto = ancho / proporcion
    max_alto = 232  # mm: el alto útil de la página con márgenes
    if alto > max_alto:
        alto = max_alto
        ancho = alto * proporcion

    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(4)
    par.paragraph_format.space_after = Pt(2)
    par.add_run().add_picture(str(temporal), width=Mm(ancho))
    return temporal


def _limpiar_temporales() -> None:
    if TEMPORAL.exists():
        for f in TEMPORAL.glob("word_*.png"):
            f.unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# Encabezado y pie de página                                                   #
# --------------------------------------------------------------------------- #
def _decorar(seccion, con_pagina: bool = True) -> None:
    cabecera = seccion.header
    par = cabecera.paragraphs[0]
    par.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = par.add_run(f"{datos.EMPRESA}  ·  Sprint 2  ·  {datos.PROYECTO}")
    run.font.size = Pt(7.5)
    run.font.color.rgb = SUAVE
    run.font.name = F_CUERPO

    pie = seccion.footer
    par = pie.paragraphs[0]
    par.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if con_pagina:
        run = par.add_run("Página ")
        run.font.size = Pt(7.5)
        run.font.color.rgb = SUAVE
        run.font.name = F_CUERPO
        _campo(par, "PAGE")
        run = par.add_run(" de ")
        run.font.size = Pt(7.5)
        run.font.color.rgb = SUAVE
        _campo(par, "NUMPAGES")
    for run in par.runs:
        run.font.size = Pt(7.5)
        run.font.color.rgb = SUAVE
        run.font.name = F_CUERPO


# --------------------------------------------------------------------------- #
# Secciones del documento                                                      #
# --------------------------------------------------------------------------- #
def portada(doc):
    # Bloque de título
    tabla = doc.add_table(rows=1, cols=1)
    tabla.autofit = False
    _margenes_celda(tabla, izq=200, der=200, arriba=260, abajo=260)
    celda = tabla.rows[0].cells[0]
    celda.width = Mm(UTIL_MM)
    _sombrear(celda, ESPRESSO)

    par = celda.paragraphs[0]
    par.paragraph_format.space_after = Pt(2)
    run = par.add_run(datos.EMPRESA.upper())
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0xB9, 0x89, 0x3B)
    run.font.name = F_CUERPO

    par = celda.add_paragraph()
    par.paragraph_format.space_after = Pt(4)
    par.paragraph_format.line_spacing = 1.12
    run = par.add_run("Sistema de Gestión de Exportación\n"
                      "de Café y Cacao a la Unión Europea")
    run.font.size = Pt(20)
    run.font.bold = True
    run.font.color.rgb = BLANCO
    run.font.name = F_TITULO

    par = celda.add_paragraph()
    par.paragraph_format.space_after = Pt(0)
    run = par.add_run(f"Documento técnico del Sprint 2  ·  {datos.METODOLOGIA}")
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(0xC4, 0xB4, 0x9C)
    run.font.name = F_CUERPO

    _p(doc, "", despues=8)

    _p(doc, "Equipo de trabajo", tam=10, negrita=True, despues=3)
    filas = [[f"**{nombre}**", apellido]
             for nombre, apellido in zip(datos.EQUIPO, nombres.APELLIDOS)]
    _tabla(doc, ["Integrante", "Apellido"], filas, [100, 74], color_cab=ESPRESSO,
           tam=9, cabecera_tam=8.5)

    _p(doc, "", despues=6)
    _p(doc, "Contenido del documento", tam=10, negrita=True, despues=3)
    _tabla(
        doc,
        ["Punto del enunciado", "Contenido", "Sección"],
        [
            ["1. Requisitos", "Funcionales, no funcionales y de restricción", "1"],
            ["2. Diagrama UML", "Actores del sistema y casos de uso", "2"],
            ["3. Product backlog de septiembre",
             "Elementos trabajados y responsable de cada uno", "3"],
            ["4. Épicas e historias de usuario",
             "Con criterios de aceptación", "4"],
            ["5. Base de datos", "Tablas y relaciones entre tablas", "5"],
        ],
        [70, 76, 28], color_cab="4B7B52", tam=9, cabecera_tam=8.5)

    _p(doc, "", despues=6)
    _nota(doc, f"Fecha: {datos.FECHA}.  Metodología: {datos.METODOLOGIA}.  "
               f"Alcance: módulos de productores y lotes, calidad, comercial y "
               f"logística, más el armazón de usuarios y roles.")

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def seccion_requisitos(doc):
    _h1(doc, "1. Requisitos del sistema")
    _p(doc, "Los sacamos del informe del proyecto y los separamos en tres tipos: lo "
            "que tiene que hacer el sistema, cómo se debe ver y con qué se puede "
            "trabajar. Son la base de las historias de usuario.")

    for titulo, filas, color_hex, color_rgb in [
        ("1.1 Requisitos funcionales", datos.REQUISITOS_FUNCIONALES, "1F4E8C", AZUL),
        ("1.2 Requisitos no funcionales", datos.REQUISITOS_NO_FUNCIONALES,
         "4B7B52", VERDE),
        ("1.3 Requisitos de restricción", datos.REQUISITOS_RESTRICCION,
         "B9893B", ORO),
    ]:
        _h2(doc, titulo, color=color_rgb)
        _tabla(
            doc, ["ID", "Nombre", "Qué tiene que hacer"],
            [[f"**{rid}**", f"**{nombre}**", desc] for rid, nombre, desc in filas],
            [18, 42, 114], color_cab=color_hex, tam=8.5)
        _p(doc, "", despues=4)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def seccion_uml(doc):
    _h1(doc, "2. Diagrama UML: actores y casos de uso")
    _rico(doc, [
        ("El sistema tiene ", False, F_CUERPO),
        ("cinco actores", True, F_CUERPO),
        (". Cuatro son internos de RiTech SAS y se corresponden con los roles del "
         "requisito RR-003; el quinto es externo: el cliente europeo, que entra por "
         "un portal donde solo ve lo suyo.", False, F_CUERPO),
    ])

    _h2(doc, "2.1 Actores del sistema", color=VERDE)
    _tabla(
        doc, ["Actor", "Tipo", "Responsabilidad"],
        [[f"**{n}**", "Externo" if n == "Cliente europeo" else "Interno", d]
         for n, d in datos.ACTORES],
        [42, 20, 112], color_cab="4B7B52", tam=8.5)

    _h2(doc, "2.2 Casos de uso por módulo")
    filas = []
    for modulo, casos in datos.CASOS_DE_USO.items():
        for i, (nombre, actor) in enumerate(casos):
            filas.append([f"**{modulo}**" if i == 0 else "", f"**{nombre}**", actor])
    _tabla(doc, ["Módulo", "Caso de uso", "Actor principal"], filas,
           [58, 58, 58], color_cab="1F4E8C", tam=8.5)

    _h2(doc, "2.3 Diagrama de casos de uso")
    _imagen(doc, "diagrama_casos_de_uso.pdf")
    _nota(doc, "Figura 1. Diagrama de casos de uso del sistema. Los óvalos son "
               "casos de uso y la figura bajo cada columna es su actor principal.")

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def seccion_backlog(doc):
    _h1(doc, "3. Lo que hicimos en el sprint")
    _p(doc, "Estas son las siete tareas del sprint de septiembre. Cada una tiene una "
            "persona responsable, y las siete quedaron terminadas. Al lado de cada una "
            "estan las historias de usuario que se hicieron con ella.")

    _h2(doc, "3.1 Tareas del sprint")
    _tabla(
        doc, ["Tarea", "Qué se hizo", "Historias", "Quién lo hizo", "Estado"],
        [[f"**{clave}**", f"**{que}**", hus, f"**{resp}**", estado]
         for clave, que, hus, resp, estado in datos.BACKLOG_SEPTIEMBRE],
        [16, 76, 22, 32, 28], color_cab=ESPRESSO, tam=8.5)

    _h2(doc, "3.2 Tareas técnicas", color=ORO)
    _tabla(
        doc, ["Tarea", "Descripción", "Quién lo hizo"],
        [[f"**{clave}**", desc, resp]
         for clave, desc, resp in datos.TAREAS_SEPTIEMBRE],
        [16, 96, 62], color_cab="B9893B", tam=8.5)

    _h2(doc, "3.3 Distribución del trabajo por integrante", color=VERDE)
    filas = []
    for nombre in datos.EQUIPO:
        clave = datos.CLAVE[datos.EQUIPO.index(nombre)]
        epi = [b for b in datos.BACKLOG_SEPTIEMBRE if b[3] == clave]
        tar = [t for t in datos.TAREAS_SEPTIEMBRE if t[2] == clave]
        historias = sorted({h.strip() for b in epi for h in b[2].split(",")})
        filas.append([
            f"**{nombre}**",
            f"{len(epi)} tareas y {len(tar)} técnicas",
            ", ".join(historias) or "—",
        ])
    _tabla(doc, ["Integrante", "Qué hizo", "Historias a su cargo"], filas,
           [54, 40, 80], color_cab="4B7B52", tam=8.5)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def seccion_historias(doc):
    _h1(doc, "4. Historias de usuario")
    _rico(doc, [
        ("Del informe del proyecto sacamos ", False, F_CUERPO),
        (f"{len(datos.HISTORIAS)} historias de usuario", True, F_CUERPO),
        (". Cada una dice quién la necesita, qué quiere hacer y para qué, y trae sus "
         "criterios de aceptación: las cosas que tiene que cumplir el sistema para "
         "que la cuenta como terminada.", False, F_CUERPO),
    ])

    _h2(doc, "4.1 Resumen de las historias")
    _tabla(
        doc, ["ID", "Módulo", "Historia de usuario", "Quién la necesita",
              "Prioridad", "Estado"],
        [[f"**{hid}**", f"**{modulo}**", historia, rol, prio, estado]
         for hid, modulo, historia, rol, prio, _p, _c, estado in datos.HISTORIAS],
        [16, 28, 66, 24, 18, 20], color_cab=ESPRESSO, tam=8.5)

    _h2(doc, "4.2 Historias con sus criterios de aceptación")
    modulo_historia: dict[str, list] = {}
    for h in datos.HISTORIAS:
        modulo_historia.setdefault(h[1], []).append(h)

    for epica, historias in modulo_historia.items():
        titulo_epica = _h3(doc, f"Módulo · {epica}",
                           color=RGBColor(0x6B, 0x4E, 0x1E))
        # El encabezado del módulo no puede quedar solo al pie de la página.
        titulo_epica.paragraph_format.keep_with_next = True

        for hid, _e, historia, rol, prio, _puntos, criterios, estado in historias:
            tabla = doc.add_table(rows=0, cols=2)
            tabla.autofit = False
            _bordes(tabla)
            _margenes_celda(tabla)

            campos = [
                ("Historia", f"**{hid} · {historia}**"),
                ("Quién la necesita", rol),
                ("Prioridad", prio),
                ("Estado", estado),
            ]
            for etiqueta, valor in campos:
                fila = tabla.add_row()
                _no_partir_fila(fila)
                izq, der = fila.cells
                izq.width = Mm(34)
                der.width = Mm(140)
                _sombrear(izq, "1F4E8C")
                par = izq.paragraphs[0]
                par.paragraph_format.space_before = Pt(1)
                par.paragraph_format.space_after = Pt(1)
                # Encadena las filas para que la ficha no se parta.
                par.paragraph_format.keep_with_next = True
                run = par.add_run(etiqueta)
                run.font.size = Pt(8)
                run.font.bold = True
                run.font.color.rgb = BLANCO
                run.font.name = F_CUERPO
                par = der.paragraphs[0]
                par.paragraph_format.space_before = Pt(1)
                par.paragraph_format.space_after = Pt(1)
                par.paragraph_format.keep_with_next = True
                _escribir_celda(par, valor, 8.5)

            # Los criterios van como lista con viñeta dentro de la última fila.
            fila = tabla.add_row()
            _no_partir_fila(fila)
            izq, der = fila.cells
            izq.width = Mm(34)
            der.width = Mm(140)
            _sombrear(izq, "1F4E8C")
            par = izq.paragraphs[0]
            par.paragraph_format.space_before = Pt(1)
            par.paragraph_format.space_after = Pt(1)
            run = par.add_run("Criterios\nde aceptación")
            run.font.size = Pt(8)
            run.font.bold = True
            run.font.color.rgb = BLANCO
            run.font.name = F_CUERPO

            for i, criterio in enumerate(criterios):
                par = der.paragraphs[0] if i == 0 else der.add_paragraph()
                par.paragraph_format.space_before = Pt(0)
                par.paragraph_format.space_after = Pt(2)
                par.paragraph_format.line_spacing = 1.08
                par.paragraph_format.left_indent = Mm(3)
                run = par.add_run(f"•  {criterio}")
                run.font.size = Pt(8.5)
                run.font.color.rgb = TINTA
                run.font.name = F_CUERPO
            _p(doc, "", despues=5)


def seccion_datos(doc):
    _h1(doc, "5. Estructura de la base de datos")
    _rico(doc, [
        ("El modelo tiene ", False, F_CUERPO),
        ("nueve tablas", True, F_CUERPO),
        (", tal como se definió en el documento de base de datos del proyecto. A esas "
         "les añadimos ", False, F_CUERPO),
        ("tres tablas más", True, F_CUERPO),
        (" para guardar la catación, los certificados y los contenedores, que son "
         "datos que el modelo original no tiene.", False, F_CUERPO),
    ])

    _h2(doc, "5.1 Tablas del modelo de datos")
    for tabla_nombre, campos, desc in datos.NUCLEO_TABLAS:
        _h3(doc, f"Tabla {tabla_nombre}")
        filas = [[f"**{n}**", f"`{t}`", nota] for n, t, nota in campos]
        t = _tabla(doc, ["Campo", "Tipo", "Notas"], filas, [52, 52, 70],
                   color_cab=ESPRESSO, tam=8, cabecera_tam=8)
        _nota(doc, desc)

    _h2(doc, "5.2 Relaciones entre tablas", color=VERDE)
    _tabla(
        doc, ["Origen", "Destino", "Card.", "Regla de integridad"],
        [[f"**{o}**", f"**{d}**", card, regla]
         for o, d, card, regla in datos.RELACIONES],
        [34, 38, 16, 86], color_cab="4B7B52", tam=8.5)

    _h2(doc, "5.3 Tablas que añadimos", color=ORO)
    _p(doc, "Los cuatro módulos necesitan guardar tres cosas que no están en las "
            "nueve tablas del modelo. Van en tablas aparte, sin tocar el modelo que "
            "nos entregaron.")
    _tabla(
        doc, ["Tabla", "Propósito"],
        [[f"**{t}**", d] for t, d in datos.EXTENSIONES_TABLAS],
        [44, 130], color_cab="B9893B", tam=8.5)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    _h2(doc, "5.4 Diagrama entidad-relación")
    _imagen(doc, "diagrama_entidad_relacion.pdf")
    _nota(doc, "Figura 2. Diagrama entidad-relación de las nueve tablas del modelo, "
               "en disposición por capas según las dependencias.")

    _h2(doc, "5.5 Base de datos que usamos")
    _rico(doc, [
        ("La información se guarda en ", False, F_CUERPO),
        ("PostgreSQL", False, F_MONO),
        (", que es lo que pide el requisito RR-002. El proyecto trae un archivo "
         "sql/schema_postgres.sql con la forma de crear las tablas. Para poder "
         "levantar el sistema sin instalar nada, la aplicación usa SQLite por "
         "defecto.", False, F_CUERPO),
    ])


def seccion_estado(doc):
    _h1(doc, "6. Qué quedó hecho y qué falta")
    _p(doc, "El sprint se dividió en cuatro módulos, y los cuatro quedaron "
            "terminados:")
    _tabla(
        doc, ["N.º", "Módulo", "Estado"],
        [[n, f"**{m}**", e] for n, m, e in datos.MODULOS],
        [14, 108, 52], color_cab="4B7B52", tam=8.5)

    _h2(doc, "6.1 Lo que falta para el siguiente sprint", color=ORO)
    _p(doc, "Quedan tres cosas, que ya están anotadas:")
    _tabla(
        doc, ["Qué falta", "Para qué sirve"],
        [["El módulo de pagos",
          "Registrar anticipos, saldos y cartas de crédito."],
         ["Avisos por correo",
          "Que llegue un correo cuando un certificado está por vencer."],
         ["Subida de documentos",
          "Poder adjuntar la factura y el certificado de embarque al envío."]],
        [56, 118], color_cab="B9893B", banda=False, tam=8.5)

    _h2(doc, "6.2 Los datos que muestra el sistema")
    _p(doc, "En la pantalla principal se ven estos seis números:")
    _tabla(doc, ["Dato", "Dato", "Dato"],
           [datos.KPIS[i:i + 2] for i in (0, 2, 4)],
           [58, 58, 58], color_cab="1F4E8C", banda=False, tam=8.5)

    _h2(doc, "6.3 Las etapas de un envío", color=RUST)
    _p(doc, "Cada envío pasa por estas seis etapas, y así se ve en la pantalla:")
    # La cadena se parte en dos mitades para que la tabla quede angosta.
    cadena = datos.CADENA_ESTADOS
    mitad = (len(cadena) + 1) // 2
    filas = []
    for i in range(mitad):
        derecho = cadena[i + mitad] if i + mitad < len(cadena) else ""
        filas.append([
            str(i + 1), cadena[i],
            str(i + mitad + 1) if derecho else "", derecho,
        ])
    _tabla(doc, ["Orden", "Etapa", "Orden", "Etapa"], filas,
           [18, 68, 18, 70], color_cab="A84B32", banda=False, tam=8.5)
    _nota(doc, "El sistema deja mover el envío un paso a la vez, hacia adelante o "
               "hacia atrás, para que no se salte ninguna etapa.")


# --------------------------------------------------------------------------- #
# Construcción                                                                 #
# --------------------------------------------------------------------------- #
def construir() -> None:
    doc = Document()

    # Página A4 con los márgenes del PDF
    seccion = doc.sections[0]
    seccion.page_width = Mm(210)
    seccion.page_height = Mm(297)
    seccion.left_margin = MARGEN
    seccion.right_margin = MARGEN
    seccion.top_margin = Mm(22)
    seccion.bottom_margin = Mm(20)
    seccion.header_distance = Mm(12)
    seccion.footer_distance = Mm(12)
    _decorar(seccion)

    # Estilo base
    normal = doc.styles["Normal"]
    normal.font.name = F_CUERPO
    normal.font.size = Pt(10)
    normal.font.color.rgb = TINTA
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.12

    portada(doc)
    seccion_requisitos(doc)
    seccion_uml(doc)
    seccion_backlog(doc)
    seccion_historias(doc)
    seccion_datos(doc)
    seccion_estado(doc)

    propiedades = doc.core_properties
    propiedades.title = f"{datos.PROYECTO} — Documento Sprint 2"
    propiedades.author = datos.EMPRESA
    propiedades.subject = ("Requisitos, UML, backlog, historias de usuario y "
                           "base de datos")
    propiedades.comments = (f"Generado por docs/word.py. Integrantes: "
                            + ", ".join(datos.EQUIPO))

    try:
        doc.save(str(DESTINO))
    finally:
        _limpiar_temporales()

    print(f"  1_Documento_Sprint2_RiTech.docx")
    print(f"  en {DESTINO}")


def main() -> None:
    print("Documento del Sprint 2 (Word)")
    for f in ("diagrama_casos_de_uso.pdf", "diagrama_entidad_relacion.pdf"):
        if not (SALIDA / f).exists():
            if f.startswith("diagrama_casos"):
                from docs import diagramas
                diagramas.diagrama_casos_de_uso(SALIDA / f)
            else:
                from docs import diagrama_er
                diagrama_er.construir(SALIDA / f)
    construir()


if __name__ == "__main__":
    main()
