"""El documento «5_Codigo_para_Exponer»: tres funciones y cómo contarlas.

    python -m docs.codigo

Genera `docs/salida/5_Codigo_para_Exponer.docx`.

Por qué este documento: en la defensa lo difícil no es que el código exista, sino
poder decir en treinta segundos qué hace y por qué está hecho así. Se eligieron
las tres funciones más cortas de `backend/app/services/reglas.py` porque:

  * no dependen de nada raro: se leen de arriba abajo sin saber FastAPI;
  * cada una contiene una regla de negocio que se puede razonar en voz alta;
  · juntas explican el proyecto entero: un dato que no se puede inventar, un
    código que se arma solo y un estado que no se puede saltar.

El código que sale impreso **se lee del archivo real con `inspect.getsource`**, no
se copia a mano. Si alguien edita `reglas.py`, el documento queda viejo en el
código pero la explicación sigue diciendo lo que dice, porque va por separado.
"""

from __future__ import annotations

import inspect
import pathlib
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "backend"))

from app.services import reglas  # noqa: E402  (lee el código real)

SALIDA = pathlib.Path(__file__).resolve().parent / "salida"

ESPRESSO = RGBColor(0x2A, 0x1B, 0x13)
VERDE = RGBColor(0x3F, 0x6B, 0x47)
RUST = RGBColor(0xA8, 0x4B, 0x32)
GRIS = RGBColor(0x6B, 0x5E, 0x52)
TINTA = RGBColor(0x2B, 0x2B, 0x2B)

F_CUERPO = "IBM Plex Sans"
F_MONO = "IBM Plex Mono"

#: Fondo del bloque de código y de los recuadros de «qué decir».
FONDO_CODIGO = "F4F1EA"
FONDO_AVISO = "EEF3EC"


# --------------------------------------------------------------------------- #
# Explicación, línea por línea                                                #
# --------------------------------------------------------------------------- #
# Cada entrada es (qué hace esa línea, en una frase corta). La clave es la
# primera palabra o el identificador de la línea, para no depender de que el
# código no cambie de comentarios.

EXPLICACIONES: dict[str, list[tuple[str, str]]] = {
    "verificar_disponibilidad": [
        ('"""Lanza ValueError…"""',
         "El texto entre comillas triple es el comentario del propio código. "
         "Python lo ignora al ejecutar; sirve para que quien lo lea sepa qué hace."),
        ("def …",
         "La definición de la función. Recibe la conexión a la base, el número "
         "del lote y la cantidad que se quiere vender. No devuelve nada: o "
         "termina bien, o avisa."),
        ("lote = db.get(Lote, id_lote)",
         "Busca el lote en la base de datos por su número. Es el equivalente a "
         "abrir una ficha."),
        ("if lote is None:",
         "Si no lo encontró, la siguiente línea lanza el error. `is None` se "
         "escribe así, con dos iguales, para preguntar «¿es None?» sin "
         "comparar de más."),
        ("raise ValueError(…)",
         "Frena todo aquí. `raise` lanza un error que la capa de arriba "
         "convierte en un mensaje para el usuario."),
        ("disponible = lote.disponible_kg",
         "Lee cuánto café queda libre en ese lote."),
        ("if disponible is None:",
         "A veces ese campo está vacío, porque todavía no se ha calculado."),
        ("lote.cantidad_kg - lote.consumo_kg",
         "Si está vacío, se calcula: lo que entró menos lo que ya se vendió. "
         "Eso es todo el cálculo de la regla, en una resta."),
        ("if cantidad > disponible:",
         "La comparación que decide todo. Es la pregunta que se le hace al "
         "pedido: ¿pedís más de lo que hay?"),
        ("f\"El lote {lote.codigo_lote}…\"",
         "Si sí, se arma el mensaje. La `f` adelante significa que el texto "
         "entre comillas es una plantilla: lo que va entre llaves se reemplaza "
         "por su valor."),
    ],
    "_siguiente_correlativo": [
        ('"""Genera el siguiente código…"""',
         "El comentario explica el formato: PREFIJO-AÑO-NÚMERO. Ejemplo: "
         "CO-HUI-2026-0001."),
        ("anio = date.today().year",
         "El año de hoy. Con eso el código cambia solo cada enero."),
        ("patron = f\"{prefijo}-{anio}-\"",
         "Se arma el pedazo que todos los códigos del año van a compartir."),
        ("existentes = db.scalars(…)",
         "Pide a la base todos los códigos que empiezan por ese pedazo. "
         "`select` arma la consulta y `.all()` la ejecuta."),
        ("consecutivo = 1",
         "Se supone que el primer código es el 0001."),
        ("for codigo in existentes:",
         "Un `for` recorre la lista, código por código."),
        ("int(str(codigo).rsplit(\"-\", 1)[1])",
         "Parte la cadena por el guion y se queda con el último pedazo, que es "
         "el número. Con «CO-HUI-2026-0004» devuelve 4."),
        ("consecutivo = max(…)",
         "Si ese código es más alto que el que veníamos llevando, se queda con "
         "el más alto. Se usa `max` y no un `if` para no tener que comparar a "
         "mano."),
        ("except (IndexError, ValueError):",
         "Si un código viene raro y no se puede convertir en número, no se "
         "detiene todo: lo salta y sigue. Sin esto, un solo dato raro tumbaría "
         "el sistema."),
        ("return f\"{patron}{consecutivo:04d}\"",
         "Devuelve el código nuevo. El `:04d` significa «rellena con ceros "
         "hasta cuatro dígitos», y por eso sale 0001 y no 1."),
    ],
    "puede_transicionar": [
        ('"""Indica si el cambio…"""',
         "El comentario dice qué se permite: avanzar, retroceder un paso, o "
         "anular si todavía no se entregó."),
        ("if actual == nuevo:",
         "Si el estado es el mismo, no hay cambio, y se permite. También "
         "absorbe el caso de guardar dos veces el mismo formulario."),
        ("return True",
         "El `return` termina la función ahí mismo y devuelve sí. Es lo que "
         "hace el primer `if`: si no hay cambio, no hay nada más que mirar."),
        ("if nuevo == EstadoExportacion.ANULADO:",
         "Pregunta si lo que quieren es anular. Si sí, entra al caso especial."),
        ("return actual in (…)",
         "Solo se puede anular si el pedido está en una de estas tres etapas, "
         "es decir, antes de salir. Un pedido que ya va en el mar no se anula: "
         "el café ya está cargado."),
        ("if actual == EstadoExportacion.ANULADO:",
         "Y un pedido ya anulado se queda anulado: no vuelve atrás. Anular es "
         "el final de la historia, no un estado más."),
        ("if actual not in ORDEN_EXPORTACION or nuevo not in ORDEN_EXPORTACION:",
         "Pregunta si alguno de los dos estados está en la lista de las siete "
         "etapas. Si alguno no está, es un estado que esta función no conoce, y "
         "por seguridad lo deja pasar en vez de inventarse una regla."),
        ("return True",
         "Sí, pasa. Cuando la función no sabe de qué estado se trata, "
         "prefiere no frenar a nadie."),
        ("distancia = abs(…)",
         "Se mide cuántas etapas hay de diferencia entre el estado actual y el "
         "nuevo. `abs` da el valor positivo, para que atrás y adelante valgan "
         "lo mismo."),
        ("return distancia <= 1",
         "La regla completa: la diferencia tiene que ser de un paso, o menos. "
         "Un envío no puede saltar de «en puerto» a «entregado»."),
    ],
}


#: Qué decir, con las palabras exactas. Es lo que se estudia la noche anterior.
QUE_DECIR: dict[str, list[str]] = {
    "verificar_disponibilidad": [
        "Esta función es la razón de que el sistema sirva para algo. Sin ella, "
        "el inventario es una lista de números que alguien actualiza a mano.",
        "La idea es simple: uno pide una cantidad, y la función contesta sí o "
        "no según cuánto café quede en el lote.",
        "Si no alcanza, lanza un error con un mensaje claro. Eso es todo: leer, "
        "restar, comparar y avisar.",
        "La regla no depende de la pantalla. Da igual desde dónde se llame, "
        "siempre sale igual.",
    ],
    "_siguiente_correlativo": [
        "El código del lote no lo escribe nadie. Lo arma el sistema.",
        "Tiene tres pedazos: qué es, de qué año, y qué número. "
        "CO-HUI-2026-0001.",
        "El truco está en una línea: parte la cadena por el último guion y se "
        "queda con el número, y de todos los que hay se queda con el más alto.",
        "Lo hicimos así y no con una función del motor de base de datos, porque "
        "cada motor la llama distinto. Así el mismo código sirve en PostgreSQL, "
        "en MySQL y en SQLite.",
    ],
    "puede_transicionar": [
        "Un envío no puede saltarse etapas. No podés marcarlo como entregado si "
        "no salió de puerto.",
        "La función devuelve sí o no, según si la diferencia entre el estado "
        "actual y el nuevo es de un paso o menos.",
        "Hay una excepción: se puede anular, pero solo antes de que el envío "
        "salga. Después ya no, porque el café ya está cargado.",
        "Esta regla es la que hace que la trazabilidad sea de fiar: nadie puede "
        "escribir una historia que no pasó.",
    ],
}

#: Preguntas que seguro llegan sobre este código.
PREGUNTAS: dict[str, list[tuple[str, str]]] = {
    "verificar_disponibilidad": [
        ("¿Por qué no lo valida el formulario de la pantalla?",
         "Porque la pantalla se puede esquivar: se puede llamar la API a mano o "
         "con otro programa. La regla tiene que estar en el servidor, que es el "
         "único sitio por el que pasa todo."),
        ("¿Y si dos usuarios venden al mismo tiempo?",
         "La base de datos es la que serializa las escrituras, y la función se "
         "vuelve a llamar al confirmar. En este prototipo es un detalle que "
         "quedaría pendiente."),
    ],
    "_siguiente_correlativo": [
        ("¿No es lento buscar todos los códigos?",
         "Con los nueve lotes de la demostración sí. Si el sistema creciera, "
         "esto se cambiaría por un contador en la base o por una secuencia. Lo "
         "elegimos así para que se pueda ver a simple vista."),
        ("¿Y si dos personas crean un lote al mismo tiempo?",
         "Podrían sacar el mismo número. Se resolvería con un índice único sobre "
         "la columna, que ya está en el modelo de datos."),
    ],
    "puede_transicionar": [
        ("¿Por qué se puede retroceder?",
         "Porque en la vida real hay errores. Un envío que se marcó como «en "
         "tránsito» y en realidad no salió se tiene que poder corregir."),
    ],
}


# --------------------------------------------------------------------------- #
# Utilidades de Word                                                          #
# --------------------------------------------------------------------------- #
def _sombrear(celda, color: str) -> None:
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), color)
    celda._tc.get_or_add_tcPr().append(shd)


def _bordes(tabla) -> None:
    borders = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "D8D0C2")
        borders.append(el)
    tabla._tbl.tblPr.append(borders)


def _ancho_fijo(tabla, anchos: list[int]) -> None:
    """Fija el reparto de columnas. En python-docx va en `columns[j].width`.

    Si se asigna solo `celda.width`, Word manda su propio reparto y la tabla se
    desborda de la página.
    """
    tabla.autofit = False
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tabla._tbl.tblPr.append(layout)
    for j, ancho in enumerate(anchos):
        tabla.columns[j].width = Mm(ancho)


def _texto(parrafo, contenido: str, tam: float, *, negrita=False,
           color=TINTA, mono=False) -> None:
    run = parrafo.add_run(contenido)
    run.font.size = Pt(tam)
    run.font.bold = negrita
    run.font.color.rgb = color
    run.font.name = F_MONO if mono else F_CUERPO
    if mono:
        run._element.rPr.rFonts.set(qn("w:eastAsia"), F_MONO)


def _p(doc, contenido: str, tam: float = 10.5, *, negrita=False, color=TINTA,
       antes=0, despues=4, mono=False, align=None) -> None:
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(antes)
    par.paragraph_format.space_after = Pt(despues)
    if align is not None:
        par.alignment = align
    _texto(par, contenido, tam, negrita=negrita, color=color, mono=mono)
    return par


def _h(doc, contenido: str, nivel: int, color=TINTA) -> None:
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(16 if nivel == 1 else 10)
    par.paragraph_format.space_after = Pt(6)
    _texto(par, contenido, 16 if nivel == 1 else 12.5, negrita=True, color=color)
    par.paragraph_format.keep_with_next = True


# --------------------------------------------------------------------------- #
# Bloques                                                                     #
# --------------------------------------------------------------------------- #
def _bloque_codigo(doc, codigo: str) -> None:
    """El código en una celda con fondo, en una fuente de ancho fijo."""
    lineas = codigo.rstrip().split("\n")
    tabla = doc.add_table(rows=1, cols=1)
    _ancho_fijo(tabla, [174])
    celda = tabla.cell(0, 0)
    _sombrear(celda, FONDO_CODIGO)
    celda.text = ""
    for n, linea in enumerate(lineas):
        par = celda.paragraphs[0] if n == 0 else celda.add_paragraph()
        par.paragraph_format.space_before = Pt(0)
        par.paragraph_format.space_after = Pt(0)
        par.paragraph_format.line_spacing = 1.0
        _texto(par, linea if linea.strip() else " ", 8.5, mono=True)
    _p(doc, "", despues=8)


def _recuadro(doc, titulo: str, lineas: list[str], color: str,
              color_titulo=VERDE) -> None:
    """Una celda con título y texto. Sirve para «qué decir» y para las notas."""
    tabla = doc.add_table(rows=1, cols=1)
    _ancho_fijo(tabla, [174])
    celda = tabla.cell(0, 0)
    _sombrear(celda, color)
    celda.text = ""
    par = celda.paragraphs[0]
    par.paragraph_format.space_after = Pt(4)
    _texto(par, titulo, 10, negrita=True, color=color_titulo)
    for linea in lineas:
        p = celda.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        _texto(p, linea, 10)
    _p(doc, "", despues=8)


def _tabla_explicacion(doc, filas: list[tuple[str, str]]) -> None:
    tabla = doc.add_table(rows=1, cols=2)
    _ancho_fijo(tabla, [42, 132])
    _bordes(tabla)
    tabla.alignment = WD_TABLE_ALIGNMENT.LEFT

    izq, der = tabla.rows[0].cells
    for celda, titulo in ((izq, "La línea"), (der, "Qué está haciendo")):
        _sombrear(celda, "2A1B13")
        celda.text = ""
        par = celda.paragraphs[0]
        par.paragraph_format.space_before = Pt(1)
        par.paragraph_format.space_after = Pt(1)
        _texto(par, titulo, 9, negrita=True, color=RGBColor(0xFF, 0xFF, 0xFF))

    for etiqueta, explicacion in filas:
        izq, der = tabla.add_row().cells
        for celda in (izq, der):
            celda.text = ""
        p = izq.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        _texto(p, etiqueta, 8, mono=True, color=RUST)
        p = der.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.1
        _texto(p, explicacion, 9)
    _p(doc, "", despues=8)


def _preguntas(doc, pares: list[tuple[str, str]]) -> None:
    for pregunta, respuesta in pares:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(1)
        _texto(p, pregunta, 10, negrita=True, color=ESPRESSO)
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Mm(5)
        p.paragraph_format.line_spacing = 1.15
        _texto(p, respuesta, 9.5, color=GRIS)


# --------------------------------------------------------------------------- #
# El código real                                                               #
# --------------------------------------------------------------------------- #
#: (nombre de la función, título, subtítulo). En ese orden salen.
PIEZAS = [
    ("verificar_disponibilidad", "1. La regla que hace útil al sistema",
     "No se puede vender más café del que hay en el lote"),
    ("_siguiente_correlativo", "2. El código del lote se arma solo",
     "CO-HUI-2026-0001, sin que nadie lo escriba"),
    ("puede_transicionar", "3. Un envío no puede saltarse etapas",
     "La regla que hace que la trazabilidad sea de fiar"),
]


def main() -> None:
    doc = Document()
    seccion = doc.sections[0]
    seccion.page_width = Mm(210)
    seccion.page_height = Mm(297)
    seccion.left_margin = seccion.right_margin = Mm(18)
    seccion.top_margin = Mm(18)
    seccion.bottom_margin = Mm(18)

    normal = doc.styles["Normal"]
    normal.font.name = F_CUERPO
    normal.font.size = Pt(10.5)

    # --- portada ---------------------------------------------------------- #
    _p(doc, "RiTech SAS · Sprint 2", 11, color=GRIS, despues=2)
    _p(doc, "Código para exponer", 30, negrita=True, color=ESPRESSO, despues=6)
    _p(doc, "Tres funciones, línea por línea, y qué decir en voz alta",
       13, color=VERDE, despues=14)

    _recuadro(doc, "Para qué es este documento", [
        "En la defensa lo difícil no es que el código exista, sino poder "
        "explicarlo en treinta segundos. Acá están las tres funciones más "
        "cortas del proyecto, con la explicación de cada línea y las frases "
        "exactas para decir.",
        "El código sale impreso del archivo real del proyecto "
        "(backend/app/services/reglas.py), no está copiado a mano.",
        "No hace falta leerlo todo. Con la función 1 ya alcanza para responder "
        "la mayoría de las preguntas, y las otras dos están por si preguntan.",
    ], FONDO_AVISO)

    _p(doc, "Las tres están en el mismo archivo porque son reglas que usan "
           "varios módulos. Cada ruta de la API las llama antes de guardar "
           "algo, así que no se pueden saltarse desde la pantalla.",
       10, color=GRIS, despues=12)

    # --- el guion corto --------------------------------------------------- #
    _h(doc, "Si solo te da tiempo para una", 1, ESPRESSO)
    _recuadro(doc, "La regla del inventario", [
        "Es la mejor para empezar, porque es la más corta y la más fácil de "
        "razonar: uno pide una cantidad, y el sistema contesta si alcanza o no.",
        "Decí: «El inventario no se actualiza a mano. Cuando alguien crea un "
        "pedido, el sistema mira cuánto café queda en el lote y, si no alcanza, "
        "no lo deja pasar.»",
    ], FONDO_CODIGO, color_titulo=RUST)

    # --- las tres piezas -------------------------------------------------- #
    for indice, (nombre, titulo, subtitulo) in enumerate(PIEZAS):
        if indice:
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

        funcion = getattr(reglas, nombre)
        codigo = inspect.getsource(funcion)
        # El código se imprime sin el decorador de @staticmethod ni el módulo.
        codigo = codigo.replace("@staticmethod\n", "")

        _p(doc, f"{nombre}()", 10, color=RUST, despues=2, mono=True)
        _p(doc, titulo, 17, negrita=True, color=ESPRESSO, despues=2)
        _p(doc, subtitulo, 11.5, color=VERDE, despues=10)

        _h(doc, "El código", 2)
        _bloque_codigo(doc, codigo)

        _h(doc, "Qué hace cada línea", 2)
        _tabla_explicacion(doc, EXPLICACIONES[nombre])

        _h(doc, "Qué decir", 2)
        _recuadro(doc, "Con estas frases", QUE_DECIR[nombre], FONDO_AVISO)

        if nombre in PREGUNTAS:
            _h(doc, "Si te preguntan", 2)
            _preguntas(doc, PREGUNTAS[nombre])

    # --- cómo se ejecuta ------------------------------------------------- #
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    _h(doc, "Cómo mostrarlo en vivo", 1, ESPRESSO)
    _p(doc, "Si el profesor quiere ver que no es un dibujo, esto corre las tres "
           "reglas contra la base de datos de verdad y muestra la salida:", 10.5)

    _bloque_codigo(doc, "python tools/demostrar_reglas.py")

    _recuadro(doc, "Lo que sale", [
        "1. La regla del inventario: pide la mitad de lo que hay (permitido) y "
        "mil kilos de más (rechazado, con el mensaje).",
        "2. El código del lote: muestra los que ya existen y dice cuál sería el "
        "siguiente, sin guardarlo.",
        "3. La cadena de estados: comprueba que no se puedan saltar etapas y que "
        "un envío entregado ya no se anula.",
    ], FONDO_CODIGO, color_titulo=RUST)

    _p(doc, "Ese script no modifica nada: solo lee. Por eso se puede correr "
           "delante de cualquiera sin miedo.", 10, color=GRIS)

    # --- plan B ---------------------------------------------------------- #
    _h(doc, "Si vas con retraso", 1, ESPRESSO)
    _p(doc, "Con la función 1 ya cubres la exposición. Si te sobra tiempo, sumá "
           "la 3, que se explica en dos frases. La 2 es la más difícil de "
           "explicar de memoria: suéltala primero si vas justo.", 10.5)

    salida = SALIDA / "5_Codigo_para_Exponer.docx"
    doc.save(salida)
    print(f"  {salida.name}")
    print(f"  en {salida}")


if __name__ == "__main__":
    main()
