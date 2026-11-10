"""Genera el guion de exposición: qué dice cada persona y en qué minuto.

    python -m docs.guion

Produce:
    docs/salida/3_Guion_de_Exposicion.docx
    docs/salida/3_Guion_de_Exposicion.pdf

El guion sale de `datos.EXPOSICION`, que es la misma tabla que usa la
presentación, así que el texto y las diapositivas no pueden desincronizarse.
"""

from __future__ import annotations

import pathlib

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

from docs import datos

SALIDA = pathlib.Path(__file__).parent / "salida"
SALIDA.mkdir(parents=True, exist_ok=True)
DESTINO = SALIDA / "3_Guion_de_Exposicion.docx"

ESPRESSO = "2A1B13"
TINTA = RGBColor(0x24, 0x1A, 0x12)
SUAVE = RGBColor(0x6B, 0x5D, 0x4F)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
ORO = RGBColor(0xB9, 0x89, 0x3B)
RUST = RGBColor(0xA8, 0x4B, 0x32)
VERDE = RGBColor(0x4B, 0x7B, 0x52)

F_TITULO = "Georgia"
F_CUERPO = "Calibri"

MARGEN = Mm(16)
UTIL_MM = 178
COLOR_INTEGRANTE = {0: "4B7B52", 1: "4B7B52", 2: "A84B32", 3: "A84B32"}


# --------------------------------------------------------------------------- #
# Utilidades                                                                   #
# --------------------------------------------------------------------------- #
def _sombrear(celda, color_hex: str) -> None:
    tc_pr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def _bordes(tabla, color_hex="DCD3C1", grosor=4) -> None:
    borders = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(grosor))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color_hex)
        borders.append(el)
    tabla._tbl.tblPr.append(borders)


def _margenes(tabla, izq=90, der=90, arriba=50, abajo=50) -> None:
    margins = OxmlElement("w:tblCellMar")
    for lado, valor in (("top", arriba), ("left", izq),
                        ("bottom", abajo), ("right", der)):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:w"), str(valor))
        el.set(qn("w:type"), "dxa")
        margins.append(el)
    tabla._tbl.tblPr.append(margins)


def _ancho_fijo(tabla, anchos) -> None:
    """Fija el ancho de las columnas.

    Necesario porque el layout de la tabla es fijo: Word usa el `tblGrid`, y
    solo se escribe al asignar `columns[j].width`. Asignar el ancho de la celda
    no basta, se queda con el reparto por defecto y la tabla se desborda.
    """
    tabla.autofit = False
    for j, ancho in enumerate(anchos):
        tabla.columns[j].width = ancho
        for fila in tabla.rows:
            fila.cells[j].width = ancho
    # Ancho total explícito, para que Word no lo recalcule.
    tbl_pr = tabla._tbl.tblPr
    for viejo in tbl_pr.findall(qn("w:tblW")):
        tbl_pr.remove(viejo)
    w = OxmlElement("w:tblW")
    w.set(qn("w:type"), "dxa")
    w.set(qn("w:w"), str(sum(int(a.emu / 635) for a in anchos)))
    tbl_pr.append(w)


def _no_partir(fila) -> None:
    tr_pr = fila._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))


def _p(doc, texto="", tam=10, color=TINTA, negrita=False, fuente=F_CUERPO,
       align=WD_ALIGN_PARAGRAPH.LEFT, antes=0, despues=5, interlineado=1.15,
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


def _h2(doc, texto, color=RGBColor(0x1F, 0x4E, 0x8C)):
    return _p(doc, texto, tam=11.5, color=color, negrita=True,
             fuente=F_TITULO, antes=10, despues=4, interlineado=1.0)


def _h1(doc, texto):
    par = _p(doc, texto, tam=15, color=RGBColor(0x2A, 0x1B, 0x13), negrita=True,
             fuente=F_TITULO, antes=14, despues=7, interlineado=1.0)
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


def _mm2s(segundos: int) -> str:
    return f"{segundos // 60}:{segundos % 60:02d}"


def _reloj(acumulado: int) -> str:
    return f"{_mm2s(acumulado)} – {_mm2s(acumulado + 0)}"


# --------------------------------------------------------------------------- #
# Contenido                                                                    #
# --------------------------------------------------------------------------- #
def portada(doc):
    tabla = doc.add_table(rows=1, cols=1)
    _ancho_fijo(tabla, (Mm(UTIL_MM),))
    _margenes(tabla, izq=200, der=200, arriba=240, abajo=240)
    celda = tabla.rows[0].cells[0]
    celda.width = Mm(UTIL_MM)
    _sombrear(celda, ESPRESSO)

    par = celda.paragraphs[0]
    par.paragraph_format.space_after = Pt(2)
    run = par.add_run(datos.EMPRESA.upper())
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = ORO
    run.font.name = F_CUERPO

    par = celda.add_paragraph()
    par.paragraph_format.space_after = Pt(4)
    par.paragraph_format.line_spacing = 1.12
    run = par.add_run("Guion de exposición")
    run.font.size = Pt(22)
    run.font.bold = True
    run.font.color.rgb = BLANCO
    run.font.name = F_TITULO

    par = celda.add_paragraph()
    par.paragraph_format.space_after = Pt(0)
    run = par.add_run("Diez minutos, cuatro personas, dos bloques")
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0xC4, 0xB4, 0x9C)
    run.font.name = F_CUERPO

    _p(doc, "", despues=8)

    # ---- Cómo se reparte el tiempo ---------------------------------------- #
    _p(doc, "Reparto del tiempo", tam=10, negrita=True, despues=3)

    minutos = datos.minutos_por_integrante()
    compartidos = {}
    for bloque in datos.EXPOSICION:
        for _clave, dueno, _titulo, segundos, guion in bloque["diapositivas"]:
            if dueno is None:
                for i in datos.autores_de(guion):
                    compartidos[i] = (segundos // len(datos.autores_de(guion)),
                                      bloque["integrantes"])

    filas = []
    for i, nombre in enumerate(datos.EQUIPO):
        segundos = minutos[i]
        bloque_indice = 0 if i in (0, 1) else 1
        bloque = datos.EXPOSICION[bloque_indice]
        orden = list(bloque["integrantes"]).index(i) + 1
        orden_texto = "1.º" if orden == 1 else "2.º"

        if i in compartidos:
            propios, dupla = compartidos[i]
            otro = [j for j in dupla if j != i][0]
            nota = f"{propios} s con {datos.NOMBRE_CORTO[otro]}"
        else:
            nota = "sin diapositiva compartida"

        filas.append([
            nombre,
            COLOR_INTEGRANTE[i],
            f"{bloque_indice + 1}. {bloque['titulo']}",
            orden_texto,
            f"{segundos // 60} min {segundos % 60} s",
            nota,
        ])

    anchos = [Mm(50), Mm(5), Mm(43), Mm(14), Mm(26), Mm(40)]
    tabla = doc.add_table(rows=0, cols=6)
    _ancho_fijo(tabla, anchos)
    _bordes(tabla)
    _margenes(tabla)

    cab = ["Integrante", "", "Bloque", "Orden", "Duración", "Compartida"]
    fila = tabla.add_row()
    _no_partir(fila)
    for j, texto in enumerate(cab):
        celda = fila.cells[j]
        _sombrear(celda, ESPRESSO)
        par = celda.paragraphs[0]
        par.paragraph_format.space_before = Pt(1)
        par.paragraph_format.space_after = Pt(1)
        if j == 1:
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = par.add_run("")
        else:
            run = par.add_run(texto)
        run.font.size = Pt(8.5)
        run.font.bold = True
        run.font.color.rgb = BLANCO
        run.font.name = F_CUERPO

    for j, valores in enumerate(filas):
        fila = tabla.add_row()
        _no_partir(fila)
        for k, valor in enumerate(valores):
            celda = fila.cells[k]
            if k == 1:
                _sombrear(celda, valor)
                par = celda.paragraphs[0]
                par.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = par.add_run("")
                run.font.size = Pt(8.5)
                continue
            if j % 2 == 1:
                _sombrear(celda, "FBF8F2")
            par = celda.paragraphs[0]
            par.paragraph_format.space_before = Pt(1)
            par.paragraph_format.space_after = Pt(1)
            run = par.add_run(str(valor))
            run.font.size = Pt(8.5)
            run.font.bold = (k == 0)
            run.font.color.rgb = TINTA if k != 5 else SUAVE
            run.font.name = F_CUERPO

    _p(doc, "", despues=6)
    _p(doc, "", despues=4)

    # ---- Los dos bloques -------------------------------------------------- #
    _p(doc, "Los dos bloques", tam=10, negrita=True, despues=3)
    for bloque, inicio, fin in datos.bloques_con_tiempos():
        epi = [b for b in datos.BACKLOG_SEPTIEMBRE
               if b[3] in {datos.CLAVE[i] for i in bloque["integrantes"]}]
        segundos = fin - inicio
        tabla = doc.add_table(rows=1, cols=2)
        _ancho_fijo(tabla, (Mm(34), Mm(UTIL_MM - 34)))
        _bordes(tabla)
        _margenes(tabla, izq=120, der=120, arriba=90, abajo=90)
        izq, der = tabla.rows[0].cells
        _sombrear(izq, bloque["color"])

        par = izq.paragraphs[0]
        par.paragraph_format.space_before = Pt(2)
        par.paragraph_format.space_after = Pt(2)
        run = par.add_run(f"{_mm2s(inicio)}\n{_mm2s(fin)}")
        run.font.size = Pt(9)
        run.font.bold = True
        run.font.color.rgb = BLANCO
        run.font.name = F_CUERPO

        par = der.paragraphs[0]
        par.paragraph_format.space_after = Pt(1)
        run = par.add_run(f"«{bloque['titulo']}» — {bloque['lema']}")
        run.font.size = Pt(10.5)
        run.font.bold = True
        run.font.color.rgb = TINTA
        run.font.name = F_CUERPO

        par = der.add_paragraph()
        par.paragraph_format.space_after = Pt(0)
        gente = " y ".join(datos.NOMBRE[i] for i in bloque["integrantes"])
        run = par.add_run(f"{gente}  ·  {len(bloque['diapositivas'])} diapositivas "
                          f"·  {len(epi)} elementos del backlog")
        run.font.size = Pt(8.5)
        run.font.color.rgb = SUAVE
        run.font.name = F_CUERPO
        _p(doc, "", despues=3)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def cronometro(doc):
    """La línea de tiempo completa, diapositiva por diapositiva."""
    _h1(doc, "1. Línea de tiempo")
    _p(doc, "Lo que va diciendo cada persona y en qué momento del cronómetro. "
            "Los segundos son la duración estimada: si alguien se pasa, se recorta "
            "por el principio, nunca reduciendo el bloque entero.")

    color_izq = Mm(26)
    color_der = Mm(UTIL_MM - 26)
    acumulado = 0
    numero = 1

    for bloque, _inicio, _fin in datos.bloques_con_tiempos():
        par = _p(doc, "", antes=6, despues=3)
        run = par.add_run(f"Bloque «{bloque['titulo']}»  ·  "
                          f"{_mm2s(acumulado)} – {_mm2s(_fin)}")
        run.font.size = Pt(10.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x2A, 0x1B, 0x13)
        run.font.name = F_CUERPO

        for clave, dueno, titulo, segundos, guion in bloque["diapositivas"]:
            inicio = acumulado
            acumulado += segundos
            color = (COLOR_INTEGRANTE[dueno] if dueno is not None
                     else bloque["color"])
            parrafo_guion = " ".join(f for _a, f in datos.guion_normalizado(guion))
            palabras = len(parrafo_guion.split())

            autores = datos.autores_de(guion)
            compartido = dueno is None and len(autores) > 1
            color_izq_efectiva = color

            tabla = doc.add_table(rows=1, cols=2)
            _ancho_fijo(tabla, (color_izq, color_der))
            _bordes(tabla)
            _margenes(tabla, arriba=80, abajo=80)
            fila = tabla.rows[0]
            _no_partir(fila)

            # --- izquierda: número, reloj y duración --------------------- #
            izq = fila.cells[0]
            izq.width = color_izq
            _sombrear(izq, color)
            par = izq.paragraphs[0]
            par.paragraph_format.space_after = Pt(0)
            par.paragraph_format.line_spacing = 1.12
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for k, linea in enumerate((f"#{numero}",
                                       f"{_mm2s(inicio)} – {_mm2s(acumulado)}",
                                       f"{segundos} s")):
                run = par.add_run(linea + ("\n" if k < 2 else ""))
                run.font.size = Pt(9 if k == 1 else 8.5)
                run.font.bold = (k != 1)
                run.font.color.rgb = BLANCO
                run.font.name = F_CUERPO

            # --- derecha: título, hablante y texto ----------------------- #
            der = fila.cells[1]
            der.width = color_der

            par = der.paragraphs[0]
            par.paragraph_format.space_after = Pt(1)
            run = par.add_run(titulo)
            run.font.size = Pt(10)
            run.font.bold = True
            run.font.color.rgb = TINTA
            run.font.name = F_CUERPO

            par = der.add_paragraph()
            par.paragraph_format.space_after = Pt(3)
            if compartido:
                quien = " + ".join(datos.NOMBRE[i] for i in autores)
            elif dueno is not None:
                quien = datos.NOMBRE[dueno]
            else:
                quien = "el bloque"
            run = par.add_run(f"{quien}  ·  {palabras} palabras")
            run.font.size = Pt(8)
            run.font.color.rgb = ORO
            run.font.name = F_CUERPO

            for autor, frase in datos.guion_normalizado(guion):
                par = der.add_paragraph()
                par.paragraph_format.space_after = Pt(2)
                par.paragraph_format.line_spacing = 1.15
                par.paragraph_format.left_indent = Mm(4)
                prefijo = (f"{datos.NOMBRE[autor].split()[0]}:  "
                           if compartido and autor is not None else "»  ")
                run = par.add_run(prefijo + frase)
                run.font.size = Pt(9)
                run.font.color.rgb = TINTA
                run.font.name = F_CUERPO

            _p(doc, "", despues=3)
            numero += 1

    par = _p(doc, f"Total: {_mm2s(acumulado)} de guion para {_mm2s(600)} de tiempo. "
                  f"Margen: {600 - acumulado} segundos.",
             tam=9, color=SUAVE, cursiva=True, antes=6)


def _recuadro(doc, titulo, texto, color_fondo, color_texto, tam=9,
              ancho=UTIL_MM):
    """Una celda de una tabla usada como recuadro de texto."""
    tabla = doc.add_table(rows=1, cols=1)
    _ancho_fijo(tabla, (Mm(ancho),))
    _bordes(tabla, "DCD3C1", grosor=4)
    _margenes(tabla, izq=120, der=120, arriba=80, abajo=80)
    celda = tabla.rows[0].cells[0]
    _sombrear(celda, color_fondo)

    par = celda.paragraphs[0]
    par.paragraph_format.space_after = Pt(1)
    run = par.add_run(titulo)
    run.font.size = Pt(tam - 1)
    run.font.bold = True
    run.font.color.rgb = color_texto
    run.font.name = F_CUERPO

    par = celda.add_paragraph()
    par.paragraph_format.space_after = Pt(0)
    par.paragraph_format.line_spacing = 1.14
    run = par.add_run(texto)
    run.font.size = Pt(tam)
    run.font.color.rgb = TINTA
    run.font.name = F_CUERPO
    _p(doc, "", despues=3)
    return tabla


def por_persona(doc):
    """Una sección por persona, con el guion explicado paso a paso."""
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    _h1(doc, "2. Guion por persona")
    _p(doc, "Una sección por integrante, en el orden en que suben al escenario. "
            "Cada quien solo tiene que leer lo suyo: lo anterior ya lo dijo otro.")
    _p(doc, "Cada diapositiva trae cinco cosas: qué hay en pantalla, lo que "
            "tienes que decir, la ampliación por si sobra tiempo, cómo decirlo y "
            "la frase con la que pasas a la siguiente. El bloque de ampliación no "
            "es obligatorio: está para quien tenga más confianza, para ensayar y "
            "para responder preguntas.")

    guion = datos.guion_por_persona()
    palabras = datos.palabras_de_guion()
    seg = 60.0 / datos.PALABRAS_POR_MINUTO

    for i, nombre in enumerate(datos.EQUIPO):
        entradas = guion[i]
        if not entradas:
            continue

        par = _p(doc, "", antes=12, despues=3)
        run = par.add_run(nombre)
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x2A, 0x1B, 0x1B if False else 0x12)
        run.font.name = F_TITULO

        epi = [b for b in datos.BACKLOG_SEPTIEMBRE
                       if b[3] == datos.CLAVE[i]]
        historias = sorted({h.strip() for b in epi for h in b[2].split(",")})
        _p(doc, f"{palabras[i] * seg / 60:.1f} min hablados  ·  "
                f"{len(entradas)} diapositivas  ·  {len(epi)} elementos del "
                f"backlog  ·  historias: {', '.join(historias)}",
            tam=8.5, color=SUAVE, despues=5)

        _recuadro(doc, "LA IDEA QUE TIENES QUE DEJAR",
                  datos.IDEA[i], "F3E8D2", RGBColor(0x6B, 0x4E, 0x1E))

        for e in entradas:
            marca = "  ·  la compartís con tu compañero" if e["compartida"] else ""
            par = _p(doc, "", despues=1)
            run = par.add_run(f"Diapositiva {e['numero']}  ·  {e['segundos']} s"
                              f"{marca}")
            run.font.size = Pt(8)
            run.font.bold = True
            run.font.color.rgb = ORO
            run.font.name = F_CUERPO
            _p(doc, e["titulo"], tam=11, negrita=True, despues=3)

            _p(doc, f"EN PANTALLA:  {e['pantalla']}",
                tam=8.5, color=SUAVE, cursiva=True, despues=4)

            _p(doc, "LO QUE DICES", tam=8, color=RGBColor(0x4B, 0x7B, 0x52),
                negrita=True, despues=1)
            for frase in e["decir"]:
                par = _p(doc, f"»  {frase}", tam=10, despues=3, interlineado=1.2)
                par.paragraph_format.left_indent = Mm(6)

            if e["ampliacion"]:
                _p(doc, "SI SOBRA TIEMPO", tam=8, color=SUAVE, negrita=True,
                    antes=3, despues=1)
                for frase in e["ampliacion"]:
                    par = _p(doc, f"»  {frase}", tam=9, color=SUAVE,
                             despues=3, interlineado=1.2)
                    par.paragraph_format.left_indent = Mm(6)

            _p(doc, f"CÓMO DECIRLO:  {e['como']}",
                tam=8.5, color=RGBColor(0xA8, 0x4B, 0x32), despues=2)
            par = _p(doc, f"PUENTE:  «{e['puente']}»",
                     tam=8.5, color=RGBColor(0x1F, 0x4E, 0x8C), despues=8)
            par.paragraph_format.left_indent = Mm(6)


def consejos(doc):
    """Qué no hacer y qué recortar si se va con retraso."""
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    _h1(doc, "3. Para la defensa")
    _p(doc, "Lo que decide cómo va la presentación no es el contenido, que ya "
            "está, sino estos dos detalles.")

    _h2(doc, "3.1 Si se va con retraso", color=RUST)
    _p(doc, "En orden: lo primero que se cae es lo que menos duele. Con esto "
            "el guion sigue cabiendo en diez minutos aunque se pierda un minuto "
            "por el camino.")
    tabla = doc.add_table(rows=0, cols=2)
    anchos = [Mm(18), Mm(UTIL_MM - 18)]
    _ancho_fijo(tabla, anchos)
    _bordes(tabla)
    _margenes(tabla)
    fila = tabla.add_row()
    _no_partir(fila)
    for j, texto in enumerate(["#", "Qué recortar"]):
        celda = fila.cells[j]
        _sombrear(celda, "A84B32")
        par = celda.paragraphs[0]
        par.paragraph_format.space_before = Pt(1)
        par.paragraph_format.space_after = Pt(1)
        if j == 0:
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = par.add_run(texto)
        run.font.size = Pt(8.5)
        run.font.bold = True
        run.font.color.rgb = BLANCO
        run.font.name = F_CUERPO
    for k, consejo in enumerate(datos.PLAN_B, start=1):
        fila = tabla.add_row()
        _no_partir(fila)
        for j, valor in enumerate((str(k), consejo)):
            celda = fila.cells[j]
            if k % 2 == 0:
                _sombrear(celda, "FBF8F2")
            par = celda.paragraphs[0]
            par.paragraph_format.space_before = Pt(1)
            par.paragraph_format.space_after = Pt(1)
            par.paragraph_format.line_spacing = 1.12
            if j == 0:
                par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = par.add_run(valor)
            run.font.size = Pt(9)
            run.font.bold = (j == 0)
            run.font.color.rgb = RUST if j == 0 else TINTA
            run.font.name = F_CUERPO

    _h2(doc, "3.2 Lo que conviene no hacer", color=RUST)
    for consejo in datos.PRECAUCIONES:
        par = _p(doc, f"×  {consejo}", tam=9.5, despues=4, interlineado=1.18)
        par.paragraph_format.left_indent = Mm(4)

    _h2(doc, "3.3 Reparto del turno", color=VERDE)
    _p(doc, "Las parejas comparten la última diapositiva de su bloque. Los "
            "turnos están marcados en la pantalla, pero hay que acordarlos de "
            "antemano para que no haya silencios:")
    for bloque, _inicio, _fin in datos.bloques_con_tiempos():
        _p(doc, f"{datos.NOMBRE_CORTO[bloque['integrantes'][0]]} habla primero, "
                f"después {datos.NOMBRE_CORTO[bloque['integrantes'][1]]}. "
                f"El que cierra el bloque da las gracias.",
            tam=9.5, despues=3)
        par = _p(doc, "", despues=6)
        par.paragraph_format.left_indent = Mm(4)


def preguntas(doc):
    """Lo que seguro preguntan, con la respuesta corta."""
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    _h1(doc, "4. Preguntas que seguro llegan")
    _p(doc, "Respuestas de una o dos frases. Cualquiera de los cuatro la puede "
            "contestar, pero conviene saber quién la tiene. Si la respuesta es "
            "técnica, derivarla a la persona que hizo esa parte.")

    preguntas = datos.PREGUNTAS_FRECUENTES

    anchos = [Mm(66), Mm(UTIL_MM - 66)]
    tabla = doc.add_table(rows=0, cols=2)
    _ancho_fijo(tabla, anchos)
    _bordes(tabla)
    _margenes(tabla, arriba=70, abajo=70)

    fila = tabla.add_row()
    _no_partir(fila)
    for j, texto in enumerate(["Pregunta", "Respuesta corta"]):
        celda = fila.cells[j]
        _sombrear(celda, ESPRESSO)
        par = celda.paragraphs[0]
        run = par.add_run(texto)
        run.font.size = Pt(9)
        run.font.bold = True
        run.font.color.rgb = BLANCO
        run.font.name = F_CUERPO

    for j, (pregunta, respuesta) in enumerate(preguntas):
        fila = tabla.add_row()
        _no_partir(fila)
        for k, valor in enumerate((pregunta, respuesta)):
            celda = fila.cells[k]
            celda.width = Mm(anchos[k])
            if j % 2 == 1:
                _sombrear(celda, "FBF8F2")
            par = celda.paragraphs[0]
            par.paragraph_format.line_spacing = 1.15
            run = par.add_run(valor)
            run.font.size = Pt(9)
            run.font.bold = (k == 0)
            run.font.color.rgb = TINTA
            run.font.name = F_CUERPO


# --------------------------------------------------------------------------- #
def construir() -> None:
    doc = Document()
    seccion = doc.sections[0]
    seccion.page_width = Mm(210)
    seccion.page_height = Mm(297)
    seccion.left_margin = MARGEN
    seccion.right_margin = MARGEN
    seccion.top_margin = Mm(18)
    seccion.bottom_margin = Mm(18)

    normal = doc.styles["Normal"]
    normal.font.name = F_CUERPO
    normal.font.size = Pt(10)
    normal.font.color.rgb = TINTA
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.15

    portada(doc)
    cronometro(doc)
    por_persona(doc)
    consejos(doc)
    preguntas(doc)

    propiedades = doc.core_properties
    propiedades.title = "Guion de exposición — Sprint 2"
    propiedades.author = datos.EMPRESA
    propiedades.subject = "Reparto de los 10 minutos entre los cuatro integrantes"

    doc.save(str(DESTINO))
    total = sum(x[3] for b in datos.EXPOSICION for x in b["diapositivas"])
    print(f"  3_Guion_de_Exposicion.docx  "
          f"(guion de {_mm2s(total)}, margen {_mm2s(600 - total)})")


def main() -> None:
    print("Guion de exposición")
    construir()
    print(f"  en {DESTINO}")


if __name__ == "__main__":
    main()
