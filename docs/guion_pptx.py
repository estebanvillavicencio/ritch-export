"""Genera el guion de exposición en PowerPoint, para leerlo desde la sala.

    python -m docs.guion_pptx

Produce:
    docs/salida/4_Guion_de_Exposicion.pptx

Es el mismo guion de `docs/guion.py`, pero como mazo de PowerPoint: una
diapositiva por persona, con el texto en grande sobre fondo oscuro para que se
lea desde el atril. Sirve para ensayar y para tener abierto en el portátil
mientras se expone, que es cuando se acaba el agobio de no saber qué toca.
"""

from __future__ import annotations

import pathlib

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from docs import datos

SALIDA = pathlib.Path(__file__).parent / "salida"
SALIDA.mkdir(parents=True, exist_ok=True)
DESTINO = SALIDA / "4_Guion_de_Exposicion.pptx"

ESPRESSO = RGBColor(0x2A, 0x1B, 0x13)
PAPEL = RGBColor(0x1A, 0x11, 0x0C)
TINTA = RGBColor(0xF4, 0xEF, 0xE6)
SUAVE = RGBColor(0xB0, 0xA1, 0x8D)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
ORO = RGBColor(0xB9, 0x89, 0x3B)

TITULO_F = "Georgia"
CUERPO_F = "Segoe UI"

ANCHO_P, ALTO_P = Inches(13.333), Inches(7.5)

COLOR_INTEGRANTE = {
    0: RGBColor(0x6E, 0xA1, 0x76),
    1: RGBColor(0x4B, 0x7B, 0x52),
    2: RGBColor(0xC4, 0x6A, 0x4B),
    3: RGBColor(0xA8, 0x4B, 0x32),
}


def _rgb(color):
    return RGBColor.from_string(color) if isinstance(color, str) else color


def _texto(slide, x, y, w, h, txt, tam=18, color=TINTA, negrita=False,
           fuente=CUERPO_F, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
           interlineado=1.0):
    marco = slide.shapes.add_textbox(x, y, w, h)
    tf = marco.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    for i, linea in enumerate(txt.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = interlineado
        r = p.add_run()
        r.text = linea
        r.font.size = Pt(tam)
        r.font.bold = negrita
        r.font.name = fuente
        r.font.color.rgb = _rgb(color)
    return marco


def _rect(slide, x, y, w, h, relleno):
    from pptx.enum.shapes import MSO_SHAPE

    f = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    f.fill.solid()
    f.fill.fore_color.rgb = _rgb(relleno)
    f.line.fill.background()
    f.shadow.inherit = False
    return f


def _fondo(slide):
    _rect(slide, Emu(0), Emu(0), ANCHO_P, ALTO_P, PAPEL)


def _barra(slide, color, alto=Inches(0.12)):
    _rect(slide, Emu(0), Emu(0), ANCHO_P, alto, color)


# --------------------------------------------------------------------------- #
# Diapositivas                                                                 #
# --------------------------------------------------------------------------- #
def portada(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _barra(s, ORO, Inches(0.18))

    _texto(s, Inches(1.0), Inches(1.5), Inches(11), Inches(0.4),
           datos.EMPRESA.upper(), tam=13, color=ORO, negrita=True)
    _texto(s, Inches(1.0), Inches(2.0), Inches(11.3), Inches(1.6),
           "Guion de exposición", tam=42, color=BLANCO, negrita=True,
           fuente=TITULO_F, interlineado=1.1)
    _texto(s, Inches(1.0), Inches(3.05), Inches(11.3), Inches(0.5),
           "Diez minutos, cuatro personas, dos parejas", tam=17, color=SUAVE)

    _rect(s, Inches(1.0), Inches(3.95), Inches(11.3), Inches(0.02),
          RGBColor(0x4A, 0x33, 0x22))

    minutos = datos.minutos_por_integrante()
    x = Inches(1.0)
    for i, nombre in enumerate(datos.EQUIPO):
        color = COLOR_INTEGRANTE[i]
        _rect(s, x, Inches(4.3), Inches(0.07), Inches(1.15), color)
        _texto(s, x + Inches(0.22), Inches(4.3), Inches(2.6), Inches(0.6),
               nombre, tam=12.5, color=BLANCO, negrita=True, interlineado=1.15)
        _texto(s, x + Inches(0.22), Inches(5.05), Inches(2.6), Inches(0.3),
               f"{minutos[i] // 60} min {minutos[i] % 60} s", tam=13, color=ORO,
               negrita=True)
        x += Inches(2.9)

    _texto(s, Inches(1.0), Inches(6.3), Inches(11.3), Inches(0.3),
           datos.FECHA, tam=11, color=RGBColor(0x7A, 0x6B, 0x58))
    return s


def agenda(prs, n):
    """Quién habla y cuándo, diapositiva por diapositiva."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _barra(s, ORO)

    _texto(s, Inches(0.7), Inches(0.45), Inches(9), Inches(0.5),
           "Quién habla y cuándo", tam=24, color=BLANCO, negrita=True,
           fuente=TITULO_F)
    _texto(s, Inches(9.6), Inches(0.55), Inches(3.0), Inches(0.35),
           "orden de la exposición", tam=11, color=SUAVE, align=PP_ALIGN.RIGHT)

    y = 1.18
    for indice, (bloque, inicio, fin_bloque) in enumerate(
            datos.bloques_con_tiempos(), start=1):
        _texto(s, Inches(0.7), Inches(y), Inches(8.6), Inches(0.4),
               f"Bloque {indice} · {bloque['titulo']}", tam=15, color=ORO,
               negrita=True, fuente=TITULO_F)
        _texto(s, Inches(9.4), Inches(y + 0.05), Inches(3.2), Inches(0.3),
               f"{_mm2s(inicio)} – {_mm2s(fin_bloque)}", tam=12, color=SUAVE,
               align=PP_ALIGN.RIGHT)
        y += 0.36

        for clave, dueno, titulo, segundos, guion in bloque["diapositivas"]:
            autores = datos.autores_de(guion)
            compartido = len(autores) > 1
            color = (COLOR_INTEGRANTE[dueno] if dueno is not None
                     else bloque["color"])
            _rect(s, Inches(0.7), Inches(y), Inches(0.05), Inches(0.34),
                  color)
            _texto(s, Inches(0.92), Inches(y + 0.04), Inches(6.2), Inches(0.3),
                   titulo, tam=12, color=TINTA)
            quien = (" + ".join(datos.NOMBRE_CORTO[a] for a in autores)
                     if compartido else datos.NOMBRE_CORTO[dueno])
            _texto(s, Inches(7.3), Inches(y + 0.05), Inches(3.5), Inches(0.3),
                   quien, tam=10, color=color, align=PP_ALIGN.RIGHT)
            _texto(s, Inches(10.9), Inches(y + 0.05), Inches(1.7), Inches(0.3),
                   f"{segundos} s", tam=10, color=SUAVE, align=PP_ALIGN.RIGHT)
            y += 0.36
        y += 0.14

    _texto(s, Inches(0.7), Inches(7.1), Inches(12.0), Inches(0.3),
           f"Total: {_mm2s(600)} de tiempo  ·  una diapositiva compartida por "
           f"pareja al final de cada bloque",
           tam=8.5, color=RGBColor(0x6A, 0x5C, 0x4B))
    return s


#: Espacio útil del guion en la diapositiva de persona, en pulgadas.
ALTO_UTIL = 5.62
Y_INICIO = 1.32
#: Tamaños candidatos, de mayor a menor.
TAMANOS = (13.5, 12.5, 11.5, 10.5, 9.5, 8.5)
#: Ancho útil del texto, en pulgadas.
ANCHO_UTIL = 11.8


def _lineas_de(frase: str, tam: float) -> int:
    """Cuántas líneas ocupa una frase a un tamaño dado.

    Se estima con un ancho medio de carácter de media caja: para Segoe UI es
    una aproximación suficiente, y si falla es por una línea, que el ajuste
    automático de la derecha ya absorbe.
    """
    ancho_pt = ANCHO_UTIL * 72
    por_linea = max(20, int(ancho_pt / (tam * 0.48)))
    return max(1, -(-len(frase) // por_linea))


def _alto_del_guion(frases_por_diapositiva, tam: float) -> float:
    """Altura total, en pulgadas, que ocuparía el guion a ese tamaño."""
    alto_linea = tam * 1.16 / 72
    total = 0.0
    for frases in frases_por_diapositiva:
        total += 0.28 + 0.10          # cabecera de diapositiva y separacion
        for frase in frases:
            total += 0.07 + _lineas_de(frase, tam) * alto_linea
    return total


def _tamano_que_cabe(frases_por_diapositiva) -> float:
    """El mayor tamaño de TAMANOS con el que el guion entra en la diapositiva."""
    for tam in TAMANOS:
        if _alto_del_guion(frases_por_diapositiva, tam) <= ALTO_UTIL:
            return tam
    return TAMANOS[-1]


def persona(prs, i, numero, total):
    """La diapositiva de una persona: su guion, en grande y sin adornos."""
    nombre = datos.EQUIPO[i]
    color = COLOR_INTEGRANTE[i]

    suyas = []
    num = 1
    for bloque in datos.EXPOSICION:
        for clave, dueno, titulo, segundos, guion in bloque["diapositivas"]:
            if dueno == i:
                suyas.append((num, titulo, segundos, list(guion), False))
            elif dueno is None:
                autores = datos.autores_de(guion)
                mias = [f for a, f in datos.guion_normalizado(guion) if a == i]
                if mias:
                    suyas.append((num, titulo, segundos // len(autores),
                                  mias, True))
            num += 1

    minutos = datos.minutos_por_integrante()

    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _barra(s, color, Inches(0.14))

    # --- cabecera ---------------------------------------------------------- #
    _texto(s, Inches(0.7), Inches(0.36), Inches(9.6), Inches(0.5),
           nombre, tam=21, color=BLANCO, negrita=True, fuente=TITULO_F)
    _texto(s, Inches(0.7), Inches(0.86), Inches(9.6), Inches(0.3),
           f"{len(suyas)} diapositivas  ·  {minutos[i] // 60} min "
           f"{minutos[i] % 60} s en total  ·  texto para leer, no para memorizar",
           tam=10.5, color=SUAVE)
    _texto(s, Inches(0.7), Inches(1.12), Inches(11.9), Inches(0.3),
           f"Tu idea: {datos.IDEA[i]}", tam=10, color=_rgb(color),
           negrita=True)
    _rect(s, Inches(10.7), Inches(0.36), Inches(2.0), Inches(0.52), color)
    _texto(s, Inches(10.7), Inches(0.47), Inches(2.0), Inches(0.35),
           f"{i + 1}.º de 4", tam=13, color=PAPEL, negrita=True,
           align=PP_ALIGN.CENTER)

    # --- guion ------------------------------------------------------------- #
    # y se lleva en pulgadas y se convierte en cada uso: las cajas de texto
    # de python-pptx miden en EMU y una pulgada desnuda las manda al origen.
    # El tamaño se elige una vez para toda la diapositiva: si se ajustase frase
    # por frase, el guion quedaría con letras de tamaños distintos.
    tam = _tamano_que_cabe([f for _n, _t, _s, f, _c in suyas])
    alto_linea = tam * 1.16 / 72

    y = Y_INICIO + 0.16
    for num, titulo, segundos, frases, compartida in suyas:
        marca = ("  ·  la compartís con tu compañero" if compartida else "")
        _texto(s, Inches(0.7), Inches(y), Inches(7.0), Inches(0.24),
               f"Diapositiva {num}  ·  {segundos} s{marca}", tam=9,
               color=color, negrita=True)
        _texto(s, Inches(7.8), Inches(y), Inches(4.9), Inches(0.24),
               titulo, tam=9, color=SUAVE, align=PP_ALIGN.RIGHT)
        y += 0.28

        for frase in frases:
            alto = 0.06 + _lineas_de(frase, tam) * alto_linea
            _rect(s, Inches(0.7), Inches(y), Inches(0.04), Inches(alto), color)
            _texto(s, Inches(0.9), Inches(y), Inches(ANCHO_UTIL), Inches(alto),
                   frase, tam=tam, color=TINTA, interlineado=1.16)
            y += alto
        y += 0.10

    _texto(s, Inches(0.7), Inches(7.05), Inches(12.0), Inches(0.3),
           f"Guion de exposición  ·  {datos.EMPRESA}  ·  persona {i + 1} de {total}"
           f"  ·  los números «Diapositiva N» son los de la presentación",
           tam=8.5, color=RGBColor(0x6A, 0x5C, 0x4B))
    return s


def preguntas(prs):
    """El turno de preguntas, con las respuestas de una frase.

    Mismo problema que en las diapositivas de persona: seis pares de pregunta y
    respuesta no caben si el salto es fijo. Aquí el salto y el tamaño se
    calculan a partir de la altura disponible.
    """
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _barra(s, ORO)

    _texto(s, Inches(0.7), Inches(0.42), Inches(9), Inches(0.5),
           "Preguntas que seguro llegan", tam=24, color=BLANCO, negrita=True,
           fuente=TITULO_F)
    _texto(s, Inches(9.6), Inches(0.55), Inches(3.0), Inches(0.35),
           "para el turno de preguntas", tam=11, color=SUAVE,
           align=PP_ALIGN.RIGHT)

    parejas = datos.PREGUNTAS_FRECUENTES
    # 5,3 pulgadas útiles para las seis filas, con margen arriba y abajo.
    paso = min(0.94, 5.30 / len(parejas))
    tam_p = 11.5 if paso > 0.82 else 10.5
    tam_r = 10.5 if paso > 0.82 else 9.5

    y = 1.32
    for pregunta, respuesta in parejas:
        _texto(s, Inches(0.7), Inches(y), Inches(5.1), Inches(paso - 0.06),
               pregunta, tam=tam_p, color=ORO, negrita=True, interlineado=1.12)
        _texto(s, Inches(6.0), Inches(y), Inches(6.6), Inches(paso - 0.06),
               respuesta, tam=tam_r, color=TINTA, interlineado=1.14)
        _rect(s, Inches(0.7), Inches(y + paso - 0.1), Inches(11.9),
              Inches(0.01), RGBColor(0x3A, 0x29, 0x1C))
        y += paso

    _texto(s, Inches(0.7), Inches(7.05), Inches(12.0), Inches(0.3),
           f"Cualquiera de los cuatro puede contestarlas; si es técnica, "
           f"derivarla a quien la hizo  ·  {datos.EMPRESA}",
           tam=8.5, color=RGBColor(0x6A, 0x5C, 0x4B))
    return s


def _mm2s(segundos: int) -> str:
    return f"{segundos // 60}:{segundos % 60:02d}"


# --------------------------------------------------------------------------- #
def construir() -> None:
    prs = Presentation()
    prs.slide_width = ANCHO_P
    prs.slide_height = ALTO_P

    portada(prs)
    agenda(prs, len(datos.EQUIPO))

    for i in range(len(datos.EQUIPO)):
        persona(prs, i, 2 + i, 4)

    preguntas(prs)
    prs.save(str(DESTINO))
    total = sum(x[3] for b in datos.EXPOSICION for x in b["diapositivas"])
    print(f"  4_Guion_de_Exposicion.pptx  ({len(prs.slides._sldIdLst)} diapositivas, "
          f"guion de {_mm2s(total)})")


def main() -> None:
    print("Guion de exposición en PowerPoint")
    construir()
    print(f"  en {DESTINO}")


if __name__ == "__main__":
    main()
