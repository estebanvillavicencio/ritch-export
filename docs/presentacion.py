"""Genera la presentación del Sprint 2 en PowerPoint.

    python -m docs.presentacion

Produce:
    docs/salida/2_Presentacion_Sprint2_RiTech.pptx

Diseñada para 10 minutos: una diapositiva por idea, con las intervene-
ciones individualizadas al final.
"""

from __future__ import annotations

import pathlib

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from docs import datos, nombres

SALIDA = pathlib.Path(__file__).parent / "salida"
SALIDA.mkdir(parents=True, exist_ok=True)
DESTINO = SALIDA / "2_Presentacion_Sprint2_RiTech.pptx"
#: Ficheros intermedios: se limpian al terminar la construcción.
TEMPORAL = SALIDA / "_tmp"

# --------------------------------------------------------------------------- #
# Paleta y tipografías (idénticas al mockup del proyecto)                      #
# --------------------------------------------------------------------------- #
ESPRESSO = RGBColor(0x2A, 0x1B, 0x13)
PAPER = RGBColor(0xF1, 0xEC, 0xE2)
PAPER_2 = RGBColor(0xE7, 0xE0, 0xD2)
CREMA = RGBColor(0xFF, 0xFD, 0xF9)
TINTA = RGBColor(0x24, 0x1A, 0x12)
SUAVE = RGBColor(0x6B, 0x5D, 0x4F)
LINEA = RGBColor(0xDC, 0xD3, 0xC1)
ORO = RGBColor(0xB9, 0x89, 0x3B)
ORO_SUAVE = RGBColor(0xF3, 0xE8, 0xD2)
AZUL = RGBColor(0x1F, 0x4E, 0x8C)
AZUL_SUAVE = RGBColor(0xDC, 0xE7, 0xF4)
VERDE = RGBColor(0x4B, 0x7B, 0x52)
VERDE_SUAVE = RGBColor(0xDE, 0xEB, 0xDF)
RUST = RGBColor(0xA8, 0x4B, 0x32)
RUST_SUAVE = RGBColor(0xF3, 0xDD, 0xD5)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)

TITULO_F = "Georgia"
CUERPO_F = "Segoe UI"

ANCHO_P, ALTO_P = Inches(13.333), Inches(7.5)

#: Quién tiene la palabra ahora. `construir()` lo fija antes de cada
#: diapositiva y `_encabezado()` lo lee, para no pasar el dato por veinte firmas.
_DESTACADO: dict = {"dueno": None, "color": "B9893B"}

#: Color por integrante: el mismo para los dos de cada bloque, de modo que se
#: vea de un vistazo dónde termina una pareja y empieza la otra.
COLOR_INTEGRANTE = {
    0: "4B7B52",  # Andres  - bloque 1
    1: "4B7B52",  # Juanprogramming - bloque 1
    2: "A84B32",  # Juanprogramming - bloque 2
    3: "A84B32",  # Dario    - bloque 2
}


# --------------------------------------------------------------------------- #
# Utilidades                                                                   #
# --------------------------------------------------------------------------- #
def _texto(slide, x, y, w, h, txt, tam=18, color=TINTA, negrita=False,
           fuente=CUERPO_F, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
           interlineado=1.0):
    marco = slide.shapes.add_textbox(x, y, w, h)
    tf = marco.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    lineas = txt.split("\n")
    for i, linea in enumerate(lineas):
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


def _rgb(color):
    """Acepta tanto un RGBColor como una cadena «RRGGBB»."""
    if isinstance(color, str):
        return RGBColor.from_string(color)
    return color


def _rect(slide, x, y, w, h, relleno, linea=None, grosor=1.0):
    from pptx.enum.shapes import MSO_SHAPE

    relleno = _rgb(relleno)
    if linea is not None:
        linea = _rgb(linea)
    f = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    f.fill.solid()
    f.fill.fore_color.rgb = relleno
    if linea is None:
        f.line.fill.background()
    else:
        f.line.color.rgb = linea
        f.line.width = Pt(grosor)
    f.shadow.inherit = False
    return f


def _fondo(slide, color=CREMA):
    _rect(slide, Emu(0), Emu(0), ANCHO_P, ALTO_P, color)


def _encabezado(slide, titulo, bajada=None, dueno="auto", color_dueno=None):
    """Franja superior con el título y, si toca, quién explica la diapositiva.

    `dueno="auto"` toma el hablante que `construir()` dejó fijado.
    """
    if dueno == "auto":
        dueno = _DESTACADO["dueno"]
        if color_dueno is None:
            color_dueno = _DESTACADO["color"]
    if color_dueno is None:
        color_dueno = "B9893B"

    _rect(slide, Emu(0), Emu(0), ANCHO_P, Inches(1.02), ESPRESSO)
    ancho_titulo = Inches(9.4) if dueno else Inches(11.5)
    _texto(slide, Inches(0.55), Inches(0.20), ancho_titulo, Inches(0.45),
           titulo, tam=24, color=BLANCO, negrita=True, fuente=TITULO_F)
    if bajada:
        _texto(slide, Inches(0.55), Inches(0.66), ancho_titulo, Inches(0.3),
               bajada, tam=11, color=RGBColor(0xC4, 0xB4, 0x9C))
    if dueno:
        # Distintivo de quién tiene la palabra: es lo que hace la defensa
        # navegable sin que nadie tenga que leer la agenda.
        ancho = Inches(3.05)
        x = Inches(12.78) - ancho
        _rect(slide, x, Inches(0.20), ancho, Inches(0.34),
              RGBColor.from_string(color_dueno))
        _texto(slide, x, Inches(0.265), ancho, Inches(0.25),
               dueno, tam=9.5, color=ESPRESSO, negrita=True,
               align=PP_ALIGN.CENTER)



def _numero(slide, n):
    _texto(slide, Inches(12.5), Inches(7.0), Inches(0.6), Inches(0.3),
           str(n), tam=10, color=SUAVE, align=PP_ALIGN.RIGHT)


def _tarjetas(slide, items, y, alto=Inches(1.15), columnas=None, x0=Inches(0.55),
              ancho_total=None):
    """Fila de tarjetas con número, título y texto."""
    ancho_total = ancho_total or (ANCHO_P - Inches(1.1))
    columnas = columnas or len(items)
    gap = Inches(0.18)
    ancho = int((ancho_total - gap * (columnas - 1)) / columnas)
    for i, (titulo, texto, color, suave) in enumerate(items):
        col = i % columnas
        fila = i // columnas
        x = x0 + col * (ancho + gap)
        yy = y + fila * (alto + gap)
        _rect(slide, x, yy, ancho, alto, CREMA, LINEA, 0.75)
        _rect(slide, x, yy, Inches(0.07), alto, color)
        _texto(slide, x + Inches(0.22), yy + Inches(0.12), ancho - Inches(0.4),
               Inches(0.3), titulo, tam=13, color=color, negrita=True)
        _texto(slide, x + Inches(0.22), yy + Inches(0.44), ancho - Inches(0.4),
               alto - Inches(0.5), texto, tam=10, color=SUAVE, interlineado=1.12)


def _tabla(slide, x, y, w, cabeceras, filas, anchos_rel, alto_fila=Inches(0.32),
           color_cab=ESPRESSO, tam=10):
    from pptx.util import Inches as In

    n_col = len(cabeceras)
    alturas = [In(0.34)] + [alto_fila] * len(filas)
    tabla = slide.shapes.add_table(len(filas) + 1, n_col, x, y, w,
                                   In(0.34) + alto_fila * len(filas)).table
    for j, anc in enumerate(anchos_rel):
        tabla.columns[j].width = Emu(int(w * anc))
    for i, h in enumerate(alturas):
        tabla.rows[i].height = h

    for j, txt in enumerate(cabeceras):
        celda = tabla.cell(0, j)
        celda.fill.solid()
        celda.fill.fore_color.rgb = color_cab
        celda.text = txt
        p = celda.text_frame.paragraphs[0]
        p.runs[0].font.size = Pt(tam - 1)
        p.runs[0].font.bold = True
        p.runs[0].font.name = CUERPO_F
        p.runs[0].font.color.rgb = BLANCO
        celda.vertical_anchor = MSO_ANCHOR.MIDDLE

    for i, fila in enumerate(filas, start=1):
        for j, txt in enumerate(fila):
            celda = tabla.cell(i, j)
            celda.fill.solid()
            celda.fill.fore_color.rgb = CREMA if i % 2 else PAPER
            celda.text = str(txt)
            p = celda.text_frame.paragraphs[0]
            p.runs[0].font.size = Pt(tam - 1)
            p.runs[0].font.name = CUERPO_F
            p.runs[0].font.color.rgb = TINTA
            celda.vertical_anchor = MSO_ANCHOR.MIDDLE
    return tabla


def _imagen(slide, ruta, x, y, w=None, h=None, max_w=None, max_h=None):
    """Inserta una imagen ajustada a la caja disponible sin deformarla.

    Si se pasan ``max_w`` y ``max_h``, la imagen se escala para caber dentro,
    conservando la proporción, y se centra horizontalmente en la caja.
    """
    ruta = pathlib.Path(ruta)
    if not ruta.exists():
        _texto(slide, x, y, Inches(4), Inches(0.4),
               f"[falta {ruta.name}]", tam=11, color=RUST)
        return None

    if max_w is not None and max_h is not None:
        import struct

        with open(ruta, "rb") as fh:
            cab = fh.read(26)
        ancho_px, alto_px = struct.unpack(">II", cab[16:24])
        prop = ancho_px / alto_px
        ancho = max_w
        alto = int(ancho / prop)
        if alto > max_h:
            alto = max_h
            ancho = int(alto * prop)
        x = x + int((max_w - ancho) / 2)
        return slide.shapes.add_picture(str(ruta), x, y, width=ancho, height=alto)

    if w is not None:
        return slide.shapes.add_picture(str(ruta), x, y, width=w)
    return slide.shapes.add_picture(str(ruta), x, y, height=h)


def _png_de_pdf(nombre_pdf, dpi=170):
    """Convierte la primera página de un PDF a PNG para incrustarla.

    El PNG es un fichero intermedio: python-pptx lo lee al insertarlo, así que
    se puede borrar en cuanto la diapositiva está montada.
    """
    import pymupdf

    origen = SALIDA / nombre_pdf
    if not origen.exists():
        return None
    TEMPORAL.mkdir(parents=True, exist_ok=True)
    destino = TEMPORAL / f"{nombre_pdf[:-4]}.png"
    doc = pymupdf.open(origen)
    doc[0].get_pixmap(dpi=dpi).save(destino)
    doc.close()
    return destino


def _limpiar_temporales() -> None:
    if TEMPORAL.exists():
        for f in TEMPORAL.iterdir():
            f.unlink(missing_ok=True)
        TEMPORAL.rmdir()


# --------------------------------------------------------------------------- #
# Diapositivas                                                                 #
# --------------------------------------------------------------------------- #
def diapositiva_portada(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s, ESPRESSO)
    _rect(s, Inches(0), Inches(0), Inches(0.32), ALTO_P, ORO)

    _texto(s, Inches(1.0), Inches(1.5), Inches(11), Inches(0.4),
           datos.EMPRESA.upper(), tam=14, color=ORO, negrita=True)
    _texto(s, Inches(1.0), Inches(2.05), Inches(11.2), Inches(1.7),
           "Sistema de Gestión de Exportación\nde Café y Cacao a la Unión Europea",
           tam=38, color=BLANCO, negrita=True, fuente=TITULO_F, interlineado=1.14)
    _texto(s, Inches(1.0), Inches(3.75), Inches(11), Inches(0.4),
           "Presentación del Sprint 2  ·  Metodología Scrum", tam=16,
           color=RGBColor(0xC4, 0xB4, 0x9C))

    _rect(s, Inches(1.0), Inches(4.5), Inches(11.2), Inches(0.02), RGBColor(0x5C, 0x40, 0x28))

    x = Inches(1.0)
    for i, nombre in enumerate(datos.EQUIPO):
        _texto(s, x, Inches(4.85), Inches(2.75), Inches(0.3),
               nombre.split()[0] + " " + (nombre.split()[1] if len(nombre.split()) > 1 else ""),
               tam=13, color=BLANCO, negrita=True)
        _texto(s, x, Inches(5.18), Inches(2.75), Inches(0.3),
               nombres.APELLIDOS[i], tam=10, color=ORO)
        x += Inches(2.85)

    _texto(s, Inches(1.0), Inches(6.3), Inches(11), Inches(0.3),
           datos.FECHA, tam=11, color=RGBColor(0x8A, 0x7A, 0x65))
    return s


def diapositiva_problema(prs, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _encabezado(s, "El problema y nuestra propuesta",
                "Qué hace el sistema y por qué se construyó así")

    _texto(s, Inches(0.55), Inches(1.3), Inches(6.0), Inches(0.9),
           "Antes", tam=15, color=RUST, negrita=True, fuente=TITULO_F)
    _texto(s, Inches(0.55), Inches(1.72), Inches(5.9), Inches(1.5),
           "De qué finca viene un lote de café y si se puede vender en Europa estaba "
           "anotado en planillas de cálculo y cuadernos. Nadie podía responder las dos "
           "preguntas a la vez, y todo dependía de que alguien se acordara.",
           tam=12, color=TINTA, interlineado=1.2)

    _texto(s, Inches(6.9), Inches(1.3), Inches(6.0), Inches(0.9),
           "Ahora", tam=15, color=VERDE, negrita=True, fuente=TITULO_F)
    _texto(s, Inches(6.9), Inches(1.72), Inches(5.9), Inches(1.5),
           "Un solo sistema que registra el origen del producto, su calidad, sus "
           "certificados y su envío. El personal de RiTech SAS lo usa desde su panel, y "
           "el cliente europeo ve lo suyo desde su portal.",
           tam=12, color=TINTA, interlineado=1.2)

    _tarjetas(s, [
        ("Origen", "Finca, productor, asociación y ubicación de cada lote.", VERDE, None),
        ("Calidad", "Catación y laboratorio. El estado del lote sale solo del puntaje.", ORO, None),
        ("Certificados", "Orgánico, Fairtrade y europeo, con aviso de vencimiento.", AZUL, None),
        ("Trazabilidad", "Seis etapas: finca, beneficio, puerto, tránsito, aduana y cliente.", RUST, None),
    ], Inches(3.5), Inches(1.2))
    _numero(s, n)
    return s


def diapositiva_estado(prs, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _encabezado(s, "Estado actual de la aplicación",
                "Prototipo funcional: cuatro módulos terminados y operando")

    _imagen(s, SALIDA / "app_resumen.png", Inches(0.5), Inches(1.22),
            max_w=Inches(5.55), max_h=Inches(5.35))
    _texto(s, Inches(0.5), Inches(6.72), Inches(5.55), Inches(0.3),
           "Panel general: indicadores y línea de tiempo del envío.", tam=9.5,
           color=SUAVE, align=PP_ALIGN.CENTER)

    x = Inches(6.55)
    _texto(s, x, Inches(1.3), Inches(6.3), Inches(0.4),
           "Lo que funciona hoy", tam=16, color=ESPRESSO, negrita=True, fuente=TITULO_F)
    lineas = [
        ("Panel general", "Los datos más importantes arriba y el recorrido del envío "
                          "abajo."),
        ("Productores y lotes", "Alta de fincas y lotes, y control de cuánto café hay "
                                "disponible para vender."),
        ("Calidad", "Registro de la catación; el estado del lote sale del resultado."),
        ("Comercial", "Clientes europeos, pedidos y conversión del pedido en contrato."),
        ("Logística", "Contenedores, envíos y las fechas de salida y de llegada."),
        ("Portal del cliente", "Pedidos y envíos del cliente europeo, sin salir del "
                               "sistema."),
    ]
    y = 1.82
    for titulo, texto in lineas:
        _rect(s, x, Inches(y), Inches(0.05), Inches(0.62), ORO)
        _texto(s, x + Inches(0.18), Inches(y), Inches(6.1), Inches(0.25),
               titulo, tam=12, color=TINTA, negrita=True)
        _texto(s, x + Inches(0.18), Inches(y + 0.24), Inches(6.1), Inches(0.42),
               texto, tam=9.5, color=SUAVE, interlineado=1.1)
        y += 0.83
    _numero(s, n)
    return s


def diapositiva_arquitectura(prs, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _encabezado(s, "Cómo está hecho",
                "Tres partes: la pantalla, las reglas de negocio y la base de datos")

    capas = [
        ("Pantalla", "Lo que ve el usuario. Panel interno y portal del cliente.",
         AZUL, AZUL_SUAVE),
        ("Reglas", "Las condiciones que tiene que cumplir todo. Van aparte, en un "
                   "solo archivo, para poder cambiarlas sin tocar la pantalla.",
         ORO, ORO_SUAVE),
        ("Base de datos", "PostgreSQL, con las nueve tablas del modelo y tres más "
                          "que añadimos.", VERDE, VERDE_SUAVE),
    ]
    y = Inches(1.45)
    for nombre, texto, color, suave in capas:
        _rect(s, Inches(0.55), y, Inches(7.4), Inches(1.15), CREMA, LINEA, 0.75)
        _rect(s, Inches(0.55), y, Inches(2.1), Inches(1.15), color)
        _texto(s, Inches(0.7), y + Inches(0.4), Inches(1.8), Inches(0.4),
               nombre, tam=12, color=BLANCO, negrita=True, align=PP_ALIGN.CENTER)
        _texto(s, Inches(2.85), y + Inches(0.32), Inches(4.95), Inches(0.6),
               texto, tam=11, color=TINTA, interlineado=1.15)
        y += Inches(1.32)

    _texto(s, Inches(8.35), Inches(1.35), Inches(4.5), Inches(0.4),
           "Con qué lo hicimos", tam=15, color=ESPRESSO, negrita=True, fuente=TITULO_F)
    tags = ["Python", "FastAPI", "PostgreSQL", "SQLAlchemy", "HTML y CSS",
            "JavaScript", "UML", "Scrum"]
    y = Inches(1.9)
    for i, t in enumerate(tags):
        w = Inches(2.15)
        x = Inches(8.35) + (i % 2) * (w + Inches(0.2))
        yy = y + (i // 2) * Inches(0.62)
        _rect(s, x, yy, w, Inches(0.5), PAPER_2, None)
        _texto(s, x + Inches(0.12), yy + Inches(0.14), w - Inches(0.2), Inches(0.25),
               t, tam=10, color=TINTA)
    _numero(s, n)
    return s


def diapositiva_uml(prs, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _encabezado(s, "Diagrama UML: actores y casos de uso",
                "Quién usa el sistema y qué hace cada uno")
    img = _png_de_pdf("diagrama_casos_de_uso.pdf")
    _imagen(s, img, Inches(0.4), Inches(1.2),
            max_w=Inches(12.5), max_h=Inches(6.05))
    _numero(s, n)
    return s


def diagrama_er_slide(prs, n, titulo, bajada):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _encabezado(s, titulo, bajada)
    img = _png_de_pdf("diagrama_entidad_relacion.pdf")
    _imagen(s, img, Inches(0.5), Inches(1.2),
            max_w=Inches(12.3), max_h=Inches(6.1))
    _numero(s, n)
    return s


def diapositiva_modulos(prs, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _encabezado(s, "Los cuatro módulos del Sprint 2",
                "Alcance comprometido y su estado")

    _tarjetas(s, [
        ("Productores, fincas y lotes",
         "Alta de fincas y productores, registro de lotes con código, y saber cuánto "
         "café hay disponible para vender.\n\n"
         "HU-04 · HU-05", VERDE, None),
        ("Calidad y certificaciones",
         "Catación, humedad y laboratorio. El estado del lote sale del puntaje. Los "
         "certificados tienen fecha de vencimiento y el sistema avisa.\n\n"
         "HU-06 · HU-07", ORO, None),
        ("Clientes y pedidos",
         "Clientes europeos con su puerto, los pedidos y la conversión del pedido en "
         "contrato. Al vender, los kilos se descuentan del lote.\n\n"
         "HU-03 · HU-08", AZUL, None),
        ("Envíos y portal del cliente",
         "Contenedores, navieras y las fechas de salida y de llegada. El cliente "
         "europeo ve sus pedidos y sus envíos en su portal.\n\n"
         "HU-09 · HU-10", RUST, None),
    ], Inches(1.35), Inches(2.4), columnas=2)

    _texto(s, Inches(0.55), Inches(6.55), Inches(12.2), Inches(0.5),
           "Queda para el siguiente sprint: el módulo de pagos, los avisos por correo "
           "y la subida de documentos.",
           tam=11, color=SUAVE)
    _numero(s, n)
    return s


def diapositiva_items(prs, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _encabezado(s, "Lo que hicimos en el sprint",
                "Las siete tareas de septiembre, y quién hizo cada una")

    filas = []
    for clave, que, hus, resp, _estado in datos.BACKLOG_SEPTIEMBRE:
        filas.append([clave, que, hus, resp])
    _tabla(s, Inches(0.6), Inches(1.35), Inches(12.1),
           ["Tarea", "Qué se hizo", "Historias", "Quién lo hizo"],
           filas, [0.10, 0.50, 0.16, 0.24], alto_fila=Inches(0.44), tam=11)

    _texto(s, Inches(0.5), Inches(6.4), Inches(12.3), Inches(0.5),
           "Las siete quedaron terminadas. El detalle, con las historias de usuario de "
           "cada una, está en el documento entregado, sección 3.",
           tam=11, color=SUAVE)
    _numero(s, n)
    return s


def diapositiva_bloque(prs, n, titulo, lema, integrantes, color):
    """Separadora: anuncia el bloque y señala quién lo explica."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s, ESPRESSO)
    _rect(s, Inches(0), Inches(0), Inches(0.32), ALTO_P,
          RGBColor.from_string(color))

    _texto(s, Inches(1.0), Inches(2.5), Inches(2.4), Inches(0.35),
           "BLOQUE", tam=12, color=ORO, negrita=True)
    _texto(s, Inches(1.0), Inches(2.95), Inches(11.2), Inches(0.9),
           titulo, tam=40, color=BLANCO, negrita=True, fuente=TITULO_F)
    _texto(s, Inches(1.0), Inches(3.95), Inches(11.2), Inches(0.5),
           lema, tam=17, color=RGBColor(0xC4, 0xB4, 0x9C))

    _rect(s, Inches(1.0), Inches(4.85), Inches(11.2), Inches(0.02),
          RGBColor(0x5C, 0x40, 0x28))

    x = Inches(1.0)
    for i in integrantes:
        _rect(s, x, Inches(5.25), Inches(0.05), Inches(0.85),
              RGBColor.from_string(color))
        _texto(s, x + Inches(0.22), Inches(5.28), Inches(5.0), Inches(0.5),
               datos.NOMBRE[i], tam=15, color=BLANCO, negrita=True,
               interlineado=1.15)
        x += Inches(5.7)
    _numero(s, n)
    return s


def diapositiva_pareja(prs, n, titulo, integrantes, color, historias, guion,
                       segundos):
    """La diapositiva del bloque: qué hizo la pareja y qué va a decir.

    `guion` es una lista de (índice de integrante, frase): la atribución es lo
    que hace la diapositiva útil, porque los dos comparten turnada.
    """
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    gente = " + ".join(datos.NOMBRE[i] for i in integrantes)
    _encabezado(s, titulo, f"{gente}  ·  lo que va a decir cada uno",
                dueno="los dos", color_dueno=color)

    # --- izquierda: las dos tarjetas de integrante ------------------------- #
    x = Inches(0.55)
    for k, i in enumerate(integrantes):
        color_ind = COLOR_INTEGRANTE[i]
        _rect(s, x, Inches(1.3), Inches(2.05), Inches(2.5), color_ind)
        _texto(s, x + Inches(0.18), Inches(1.46), Inches(1.7), Inches(0.28),
               "Integrante", tam=8, color=RGBColor(0xE0, 0xD5, 0xC4), negrita=True)
        _texto(s, x + Inches(0.18), Inches(1.72), Inches(1.72), Inches(1.1),
               datos.NOMBRE[i], tam=11, color=BLANCO, negrita=True,
               fuente=TITULO_F, interlineado=1.14)
        _texto(s, x + Inches(0.18), Inches(2.92), Inches(1.72), Inches(0.28),
               "A su cargo", tam=8, color=RGBColor(0xE0, 0xD5, 0xC4), negrita=True)
        _texto(s, x + Inches(0.18), Inches(3.14), Inches(1.72), Inches(0.6),
               ", ".join(historias[i]) or "—", tam=9, color=BLANCO,
               interlineado=1.16)
        x += Inches(2.18)

    # --- izquierda abajo: el reparto de la diapositiva --------------------- #
    _rect(s, Inches(0.55), Inches(3.95), Inches(4.23), Inches(2.85), CREMA,
          LINEA, 0.75)
    _texto(s, Inches(0.75), Inches(4.1), Inches(3.85), Inches(0.28),
           "Cómo se reparten la palabra", tam=11, color=ESPRESSO, negrita=True,
           fuente=TITULO_F)

    y = 4.45
    for i in integrantes:
        lineas = [f for autor, f in datos.guion_normalizado(guion) if autor == i]
        palabras = sum(len(f.split()) for f in lineas)
        _rect(s, Inches(0.75), Inches(y), Inches(0.05), Inches(0.95),
              COLOR_INTEGRANTE[i])
        _texto(s, Inches(0.95), Inches(y), Inches(3.6), Inches(0.28),
               datos.NOMBRE[i], tam=10, color=TINTA, negrita=True)
        _texto(s, Inches(0.95), Inches(y + 0.26), Inches(3.6), Inches(0.7),
               f"{len(lineas)} frases  ·  {palabras} palabras  ·  "
               f"unos {segundos // 2} s",
               tam=9, color=SUAVE, interlineado=1.14)
        y += 1.1

    # --- derecha: el guion, atribuido --------------------------------------- #
    _texto(s, Inches(5.05), Inches(1.32), Inches(7.75), Inches(0.3),
           "Lo que va a decir, y quién lo dice", tam=12, color=ESPRESSO,
           negrita=True, fuente=TITULO_F)

    y = 1.72
    for autor, frase in datos.guion_normalizado(guion):
        color = COLOR_INTEGRANTE[autor] if autor is not None else color
        lineas = max(1, int(len(frase) / 74) + 1)
        alto = 0.26 + 0.19 * lineas
        _rect(s, Inches(5.05), Inches(y), Inches(7.75), Inches(alto), CREMA,
              LINEA, 0.75)
        _rect(s, Inches(5.05), Inches(y), Inches(0.05), Inches(alto), color)
        if autor is not None:
            _texto(s, Inches(5.25), Inches(y + 0.05), Inches(2.4), Inches(0.25),
                   datos.NOMBRE[autor].split()[0], tam=8.5, color=color,
                   negrita=True)
        _texto(s, Inches(5.25), Inches(y + (0.22 if autor is not None else 0.05)),
               Inches(7.4), Inches(alto - 0.1), frase, tam=10, color=TINTA,
               interlineado=1.15)
        y += alto + 0.09
    _numero(s, n)
    return s


def diapositiva_demo(prs, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _encabezado(s, "Demostración",
                "El sistema funcionando, en tres pasos")

    _texto(s, Inches(0.55), Inches(1.3), Inches(6.1), Inches(0.35),
           "Cómo se levanta", tam=15, color=ESPRESSO, negrita=True, fuente=TITULO_F)
    _rect(s, Inches(0.55), Inches(1.75), Inches(6.1), Inches(2.1), ESPRESSO)
    _texto(s, Inches(0.8), Inches(1.95), Inches(5.6), Inches(1.7),
           "cd backend\n"
           "pip install -r requirements.txt\n"
           "python -m app.seed --reset\n"
           "uvicorn app.main:app --port 8000",
           tam=12, color=BLANCO, fuente="Consolas", interlineado=1.35)
    _texto(s, Inches(0.55), Inches(4.0), Inches(6.1), Inches(0.35),
           "Cada persona del equipo tiene su cuenta, así que se puede entrar como "
           "cualquiera sin preguntar nada.",
           tam=10, color=SUAVE, interlineado=1.2)

    _texto(s, Inches(7.05), Inches(1.3), Inches(5.8), Inches(0.35),
           "Los tres pasos que voy a hacer", tam=15, color=ESPRESSO, negrita=True,
           fuente=TITULO_F)
    pasos = [
        "Crear una finca nueva, con su productor y su ubicación.",
        "Registrar una catación de 86 puntos y ver cómo el lote queda aprobado solo.",
        "Abrir el recorrido de un envío y ver en qué etapa está.",
    ]
    y = Inches(1.9)
    for i, paso in enumerate(pasos, start=1):
        _rect(s, Inches(7.05), y, Inches(0.4), Inches(0.4), ORO)
        _texto(s, Inches(7.05), y + Inches(0.09), Inches(0.4), Inches(0.25),
               str(i), tam=12, color=ESPRESSO, negrita=True, align=PP_ALIGN.CENTER)
        _texto(s, Inches(7.65), y + Inches(0.04), Inches(5.2), Inches(0.7),
               paso, tam=11, color=TINTA, interlineado=1.2)
        y += Inches(1.05)
    _texto(s, Inches(7.05), Inches(5.3), Inches(5.8), Inches(0.6),
           "Si algo falla, digo «el sistema responde» y sigo: la idea es que se vea "
           "que está funcionando, no hacerlo perfecto.",
           tam=10, color=SUAVE, interlineado=1.2)
    _numero(s, n)
    return s


def diapositiva_calidad(prs, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _encabezado(s, "Las reglas que pusimos",
                "Cosas que el sistema no deja hacer, para que los datos queden bien")

    _tarjetas(s, [
        ("No se vende más de lo que hay",
         "Si alguien intenta comprometer más kilos de los disponibles en un lote, el "
         "sistema avisa y no lo deja pasar.", VERDE, None),
        ("El estado sale del resultado",
         "El lote no se aprueba a mano: queda aprobado, con reserva o rechazado según "
         "el puntaje de la catación.", AZUL, None),
        ("Las fechas tienen orden",
         "Un envío no puede llegar antes de salir, y no se salta ninguna de las seis "
         "etapas.", ORO, None),
    ], Inches(1.3), Inches(1.45), columnas=3)

    _texto(s, Inches(0.55), Inches(3.15), Inches(12.2), Inches(0.35),
           "Otras reglas que hay", tam=15, color=ESPRESSO,
           negrita=True, fuente=TITULO_F)
    reglas = [
        "No se pueden registrar dos lotes con el mismo código.",
        "La humedad de la catación tiene que estar entre 8 y 14.",
        "Un contenedor no se asigna si el envío pesa más que su capacidad.",
        "La certificación europea solo cuenta si el lote tiene su ubicación.",
        "Solo las personas con permiso pueden ver o cambiar la información.",
        "El correo de una persona no se puede repetir entre usuarios.",
    ]
    y = Inches(3.7)
    for i, r in enumerate(reglas):
        col, fila = i % 2, i // 2
        x = Inches(0.55) + col * Inches(6.3)
        yy = y + fila * Inches(0.95)
        _rect(s, x, yy, Inches(0.04), Inches(0.62), ORO)
        _texto(s, x + Inches(0.2), yy + Inches(0.08), Inches(5.9), Inches(0.62),
               r, tam=11, color=TINTA, interlineado=1.2)
    _numero(s, n)
    return s


def diapositiva_siguiente(prs, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _fondo(s)
    _encabezado(s, "Lo que sigue",
                "Lo que falta, y para el siguiente sprint")

    _texto(s, Inches(0.55), Inches(1.3), Inches(6.1), Inches(0.35),
           "Queda pendiente", tam=15, color=ESPRESSO, negrita=True,
           fuente=TITULO_F)
    pendientes = [
        "El módulo de pagos: anticipos, saldos y cartas de crédito.",
        "Avisos por correo cuando un certificado está por vencer.",
        "Poder subir documentos al envío: la factura y el certificado de embarque.",
    ]
    y = Inches(1.9)
    for p in pendientes:
        _rect(s, Inches(0.55), y, Inches(0.05), Inches(0.6), RUST)
        _texto(s, Inches(0.78), y + Inches(0.06), Inches(5.8), Inches(0.6),
               p, tam=11, color=TINTA, interlineado=1.15)
        y += Inches(0.92)

    _texto(s, Inches(7.05), Inches(1.3), Inches(5.8), Inches(0.35),
           "Para cerrar", tam=15, color=ESPRESSO, negrita=True, fuente=TITULO_F)
    _rect(s, Inches(7.05), Inches(1.75), Inches(5.8), Inches(4.1), CREMA, LINEA, 0.75)
    _texto(s, Inches(7.3), Inches(1.95), Inches(5.3), Inches(3.8),
           "El sistema junta en un solo lugar el origen del café y del cacao, su "
           "calidad y su envío.\n\n"
           "Lo que más nos costó no fue la pantalla, sino las reglas: que no se pueda "
           "vender más café del que hay, y que el estado de un lote salga del "
           "resultado de la catación y no de quien lo registre.\n\n"
           "Aprendimos que un sistema de este sirve si las reglas están en un solo "
           "sitio, y no repartidas por las pantallas.",
           tam=12, color=TINTA, interlineado=1.25)
    _numero(s, n)
    return s


# --------------------------------------------------------------------------- #
# Reparto de la exposición                                                     #
# --------------------------------------------------------------------------- #
#: Cada clave de `datos.EXPOSICION` apunta a la función que la dibuja.
DIBUJANTES = {
    "portada": lambda prs, n, d: diapositiva_portada(prs),
    "problema": lambda prs, n, d: diapositiva_problema(prs, n),
    "arquitectura": lambda prs, n, d: diapositiva_arquitectura(prs, n),
    "diagrama_er": lambda prs, n, d: diagrama_er_slide(
        prs, n, "Diagrama entidad-relación",
        "Las nueve tablas del modelo de datos y sus relaciones"),
    "diagrama_uml": lambda prs, n, d: diapositiva_uml(prs, n),
    "modulos": lambda prs, n, d: diapositiva_modulos(prs, n),
    "items": lambda prs, n, d: diapositiva_items(prs, n),
    "estado": lambda prs, n, d: diapositiva_estado(prs, n),
    "calidad": lambda prs, n, d: diapositiva_calidad(prs, n),
    "demo": lambda prs, n, d: diapositiva_demo(prs, n),
    "siguiente": lambda prs, n, d: diapositiva_siguiente(prs, n),
}


def construir() -> None:
    prs = Presentation()
    prs.slide_width = ANCHO_P
    prs.slide_height = ALTO_P

    n = 0
    faltan = set()

    for indice, bloque in enumerate(datos.EXPOSICION):
        n += 1
        diapositiva_bloque(prs, n, bloque["titulo"], bloque["lema"],
                           bloque["integrantes"], bloque["color"])

        for clave, dueno, titulo, segundos, guion in bloque["diapositivas"]:
            n += 1
            _DESTACADO["dueno"] = (
                None if dueno is None else datos.NOMBRE[dueno]
            )
            _DESTACADO["color"] = (
                bloque["color"] if dueno is None else COLOR_INTEGRANTE[dueno]
            )

            if clave == "pareja":
                historias = {}
                for i in bloque["integrantes"]:
                    epi = [b for b in datos.BACKLOG_SEPTIEMBRE
                           if b[3] == datos.CLAVE[i]]
                    historias[i] = sorted({h.strip() for b in epi
                                           for h in b[2].split(",")})
                diapositiva_pareja(prs, n, titulo, bloque["integrantes"],
                                   bloque["color"], historias, guion, segundos)
                continue

            dibujar = DIBUJANTES.get(clave)
            if dibujar is None:
                faltan.add(clave)
                continue
            dibujar(prs, n, bloque)

    if faltan:
        raise KeyError(f"claves sin dibujante en EXPOSICION: {sorted(faltan)}")

    _DESTACADO["dueno"] = None
    try:
        prs.save(str(DESTINO))
    finally:
        _limpiar_temporales()

    total = sum(x[3] for b in datos.EXPOSICION for x in b["diapositivas"])
    print(f"  2_Presentacion_Sprint2_RiTech.pptx  "
          f"({len(prs.slides._sldIdLst)} diapositivas, "
          f"{total // 60} min {total % 60} s de guion)")


def main() -> None:
    print("Presentación del Sprint 2")
    for f, gen in (
        ("diagrama_casos_de_uso.pdf", lambda: __import__("docs.diagramas", fromlist=["x"]).diagrama_casos_de_uso(SALIDA / "diagrama_casos_de_uso.pdf")),
        ("diagrama_entidad_relacion.pdf", lambda: __import__("docs.diagrama_er", fromlist=["x"]).construir(SALIDA / "diagrama_entidad_relacion.pdf")),
    ):
        if not (SALIDA / f).exists():
            gen()
    construir()
    print(f"  en {DESTINO}")


if __name__ == "__main__":
    main()
