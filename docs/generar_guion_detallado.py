"""Genera el tramo de `datos.py` que es indicación de escenografía.

    python -m docs.generar_guion_detallado

`GUION_DETALLADO` es lo que leen el guion de Word y el de PowerPoint: para cada
diapositiva, qué hay proyectado, qué frases dice esa persona y con qué puente
pasa a la siguiente. Como guarda una copia de las frases, se queda viejo en
cuanto se edita `EXPOSICION`; este script lo rehace para que no digan una cosa
la presentación y otra el guion.

Qué se genera y qué no:

  · las frases se copian de `EXPOSICION`, que es la fuente;
  · `PANTALLA`, `COMO`, `PUENTE`, `CIERRE`, `IDEA`, `PLAN_B` y `PRECAUCIONES`
    están en este archivo, porque son indicaciones de cómo presentarlo y se
    escriben a mano.

`python -m docs.generar_todo` llama a este módulo antes de generar nada.
"""

import pathlib
import sys

BASE = pathlib.Path(
    r"C:\Users\esteb\OneDrive\Documentos\Proyecto predeterminado\ritch-export"
    r"\docs"
)

# =========================================================================== #
# Qué hay proyectado en cada diapositiva                                      #
# =========================================================================== #
PANTALLA = {
    "portada": "Fondo oscuro con el título del proyecto y los cuatro nombres. No "
               "tiene información: es la portada.",
    "problema": "Dos columnas: «Antes» a la izquierda, con planillas y cuadernos; "
                "«Ahora» a la derecha, con el sistema.",
    "arquitectura": "Tres bloques apilados a la izquierda: pantalla, reglas de "
                    "negocio y base de datos.",
    "diagrama_er": "El diagrama de la base de datos a pantalla completa: las "
                  "nueve tablas en tres filas, con líneas que las unen.",
    "diagrama_uml": "El diagrama de casos de uso: cinco columnas, una por rol, con "
                    "las tareas de cada uno en óvalos.",
    "modulos": "Cuatro tarjetas: fincas y lotes, calidad, comercial y logística, y "
               "el portal del cliente.",
    "items": "Una tabla con las siete tareas del sprint, quién hizo cada una y el "
             "estado.",
    "estado": "Una captura del programa: los datos importantes arriba y el "
              "recorrido del envío abajo.",
    "calidad": "Dos listas: las reglas que el sistema no deja saltarse, y por qué "
               "importan.",
    "demo": "Una caja con el comando para levantar el sistema y los pasos que vas a "
            "hacer.",
    "siguiente": "A la izquierda lo que falta, a la derecha el cierre.",
    "pareja": "Dos tarjetas con los nombres de los dos y, a la derecha, lo que va a "
              "decir cada uno.",
}

# =========================================================================== #
# Cómo decirlo, y en qué momento conviene señalar                          #
# =========================================================================== #
COMO = {
    "portada": "No leas el título de la pantalla, ya lo tienen delante. Mira al "
               "frente. Los tres primeros segundos deciden si te toman en serio.",
    "problema": "Señala la columna de la izquierda y luego la de la derecha. Que "
                "te vean señalar ayuda a que te escuchen.",
    "arquitectura": "Señala el bloque del medio cuando digas «las reglas están "
                    "aparte». No leas las etiquetas de la derecha.",
    "diagrama_er": "No intentes leer todos los campos, se ve que están. Señala las "
                   "líneas que unen las tablas.",
    "diagrama_uml": "Empieza por los roles, que es lo primero que se entiende. No "
                    "leas los óvalos uno por uno.",
    "modulos": "No leas las cuatro tarjetas enteras. Menciona la de calidad y pasa "
               "a la siguiente.",
    "items": "La tabla es pequeña, no la leas. Di el dato: siete tareas, las siete "
             "hechas.",
    "estado": "Es la primera vez que ven el programa, así que dilo con seguridad. "
              "No te disculpes.",
    "calidad": "Lo importante es qué evitan las reglas, no cuántas hay. Escoge dos.",
    "demo": "No la conviertas en un recorrido largo: tres pasos. Si algo falla, di "
            "«el sistema responde» y sigue.",
    "siguiente": "Quince segundos y el «gracias». Quédate de pie para las "
                 "preguntas.",
    "pareja": "Di tus frases seguidas, sin mirar las del compañero, y después "
              "pásale el turno.",
}

# =========================================================================== #
# La frase con la que se pasa a la diapositiva siguiente                     #
# =========================================================================== #
PUENTE = {
    "portada": "Empiezo por el problema.",
    "problema": "Y así queda hecho el sistema. Esta es su estructura.",
    "arquitectura": "Con esto está la base. Sigue Juanprogramming con los datos.",
    "diagrama_er": "El mismo sistema, visto desde quién usa qué.",
    "diagrama_uml": "Entonces, qué hicimos los dos:",
    "modulos": "Esto es lo que dejamos hecho en el sprint.",
    "items": "Para cerrar mi parte, qué hicimos Juan Araujo y Dario.",
    "estado": "Pero que funcione no es todo, por eso pusimos estas reglas.",
    "calidad": "Y para que lo vean, se los muestro.",
    "demo": "Y para cerrar:",
    "siguiente": "Antes de las preguntas, digamos qué hicimos Dario y yo.",
}

#: Cómo cierra cada bloque la diapositiva compartida, que es la última.
CIERRE = ["Con esto terminamos el primer bloque. Sigue Juanprogramming.",
          "Con esto terminamos. Gracias por su atención."]

#: La idea que cada persona tiene que dejar instalada, en una frase.
IDEA = {
    0: "El sistema tiene tres partes: la pantalla, las reglas y la base de "
       "datos. Cada parte hace lo suyo.",
    1: "El lote es el centro de todo: de él sale la calidad, los certificados y "
       "la trazabilidad.",
    2: "De lo que nos pidieron en el informe sacamos diez historias de usuario, y "
       "eso es lo que construimos.",
    3: "El sistema no deja vender más café del que hay, ni aceptar una humedad "
       "fuera de rango.",
}

#: Qué recortar si se va con retraso, en orden.
PLAN_B = [
    "En «El problema», la tercera frase: las dos primeras ya dejan claro el "
    "asunto.",
    "En «Cómo está hecho», no leas la parte de la base de datos: la dices "
    "después.",
    "En «Los cuatro módulos», no leas la tarjeta de logística: se explica en la "
    "demostración.",
    "En «Lo que hicimos en el sprint», no leas la tabla: di el dato.",
    "En «Las reglas que pusimos», di una sola regla en vez de dos.",
]

#: Lo que conviene no hacer.
PRECAUCIONES = [
    "No leer las tablas ni los diagramas palabra por palabra: la sala no puede "
    "leer más rápido de lo que hablas.",
    "No disculparte por el prototipo. Está funcionando.",
    "Si no sabes una respuesta, di «no lo tenemos medido» y sigue. Es normal no "
    "saberlo todo.",
    "No dejar que un compañero se pase de tiempo: córtale con un «te toca».",
    "No terminar con «no hay más que decir». Cierra con el agradecimiento.",
]

#: Marcador de inicio del tramo que este módulo reescribe.
INICIO = "#: La idea que cada persona tiene que dejar instalada"

#: Marcador de fin: lo que viene después y no se toca.
FIN = "#: Palabras por minuto de habla normal"


def _diccionario(nombre: str, contenido) -> list:
    """Serializa un diccionario de listas como texto de Python."""
    lineas = [f"{nombre} = {{"]
    for clave, valor in contenido.items():
        lineas.append(f"    {clave}: [")
        for frase in valor:
            lineas.append(f"        {frase!r},")
        lineas.append("    ],")
    lineas.append("}")
    return lineas


def _lista(nombre: str, contenido) -> list:
    """Serializa una lista de cadenas como texto de Python."""
    return [f"{nombre} = ["] + [f"    {texto!r}," for texto in contenido] + ["]"]


def detailed() -> dict:
    """Arma `GUION_DETALLADO` a partir del guion de `EXPOSICION`.

    Las frases de la diapositiva compartida se reparten: cada persona del
    bloque se lleva solo las suyas, porque las dos están en pantalla a la vez.
    """
    sys.path.insert(0, str(BASE.parent))
    from docs import datos as d

    salida = {}
    for i in range(len(d.EQUIPO)):
        entradas = []
        for bloque in d.EXPOSICION:
            for clave, dueno, _titulo, _segundos, guion in bloque["diapositivas"]:
                autores = d.autores_de(guion)
                if dueno == i:
                    frases = [f for _a, f in d.guion_normalizado(guion)]
                    es_pareja = False
                elif dueno is None and i in autores:
                    frases = [f for a, f in d.guion_normalizado(guion) if a == i]
                    es_pareja = True
                else:
                    continue
                puente = (CIERRE[0] if i in (0, 1) else CIERRE[1]) if es_pareja \
                    else PUENTE.get(clave, "")
                entradas.append((clave, PANTALLA.get(clave, ""), frases,
                                 COMO.get(clave, ""), puente))
        if entradas:
            salida[i] = entradas
    return salida


def construir() -> list:
    """El tramo completo de `datos.py` que este módulo es dueño.

    Va desde `IDEA` hasta `PRECAUCIONES` porque los cuatro son indicación de
    escenografía y se escriben a mano. Lo único que se copia del guion son las
    frases de `GUION_DETALLADO`.
    """
    lineas = ["", INICIO]
    lineas += _diccionario("IDEA", IDEA)
    lineas += [
        "",
        "#: (clave, qué se ve en pantalla, qué dice, cómo lo dice, frase de puente)",
        "#: Las frases se copian de EXPOSICION, así que el guion de Word, el de",
        "#: PowerPoint y la presentación no pueden quedar desincronizados.",
    ]
    lineas += _diccionario("GUION_DETALLADO", detailed())
    lineas += ["", "#: Qué recortar si se va con retraso, en orden."]
    lineas += _lista("PLAN_B", PLAN_B)
    lineas += ["", "#: Lo que conviene no hacer."]
    lineas += _lista("PRECAUCIONES", PRECAUCIONES)
    return lineas


def main() -> None:
    p = BASE / "datos.py"
    s = p.read_text(encoding="utf-8", newline="")
    nuevo = "\n".join(construir()) + "\n\n\n"

    i = s.index(INICIO)
    j = s.index(FIN, i)
    p.write_text(s[:i] + nuevo + s[j:], encoding="utf-8", newline="")
    print("  ok  IDEA, GUION_DETALLADO, PLAN_B y PRECAUCIONES regenerados")


if __name__ == "__main__":
    main()
