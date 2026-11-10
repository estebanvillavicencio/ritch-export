# Documentación del Sprint 2

> **Alcance de esta carpeta.** Estos generadores producen los entregables
> escritos del **Sprint 2**. El avance de los Sprints 3 y 4 —financiero,
> notificaciones, auditoría, multimoneda, integraciones y respaldos— está
> documentado en el `README.md` de la raíz del proyecto, que es la referencia
> autoritativa del estado actual del software.

Generador de los entregables escritos del Sprint 2:

| Archivo | Qué es |
|---|---|
| `salida/1_Documento_Sprint2_RiTech.pdf` | Documento con los cinco puntos del enunciado (14 páginas) |
| `salida/1_Documento_Sprint2_RiTech.docx` | El mismo documento en Word, editable |
| `salida/3_Guion_de_Exposicion.docx` | Guion de los 10 minutos en Word: cronómetro, guion explicado persona por persona, consejos para la defensa y preguntas |
| `salida/4_Guion_de_Exposicion.pptx` | El mismo guion en PowerPoint, para leerlo desde el atril (7 diapositivas) |
| `salida/2_Presentacion_Sprint2_RiTech.pptx` | Presentación de 15 diapositivas, dividida en dos bloques |
| `salida/diagrama_casos_de_uso.pdf` | Diagrama UML de casos de uso |
| `salida/diagrama_entidad_relacion.pdf` | Diagrama entidad-relación |

## A qué nivel está escrito

El material está escrito **para un sprint de segundo semestre**: frases cortas,
sin jerga de arquitectura, y sin presumir de métricas. Concretamente:

- no se mencionan ni las 58 operaciones de la API ni las 51 pruebas;
- el backlog son **7 tareas del sprint**, no 13 elementos de tablero;
- el UML tiene **5 actores y 11 casos de uso**, no 6 y 37;
- las historias son **10**, con dos o tres criterios de aceptación en frases
  cortas, no 22 con formato *Dado / Cuando / Entonces*;
- se quitó la tabla de trazabilidad requisito-historia y la comparación entre
  motores de base de datos;
- no hay puntos de historia ni porcentajes de avance.

Los cuatro módulos sí se mantienen, porque están hechos. Lo que cambia es cómo
se explican. `python -m docs.verificar_entregables` comprueba que ninguna de
las cifras viejas se cuele en un archivo generado.

## Cómo se generan

Desde la raíz del proyecto (`ritch-export/`):

```
pip install reportlab python-docx python-pptx pymupdf

python -m docs.generar_todo
```

O por partes:

```
python -m docs.diagramas      # diagrama de casos de uso
python -m docs.diagrama_er    # diagrama entidad-relación
python -m docs.documento      # documento PDF
python -m docs.word           # documento Word
python -m docs.guion          # guion de exposición en Word
python -m docs.guion_pptx     # guion de exposición en PowerPoint
python -m docs.presentacion   # presentación PowerPoint
```

`generar_todo` empieza por `generar_guion_detallado`, que rehace
`GUION_DETALLADO` a partir de `EXPOSICION`. Si se edita el texto del guion hay
que correrlo, o correr `generar_todo`, para que el guion de Word y el de
PowerPoint digan lo mismo que la presentación.

`documento.py`, `word.py`, `guion.py`, `guion_pptx.py` y `presentacion.py`
generan los diagramas ellos mismos si no existen.

## Comprobaciones

```
python -m docs.resumen_guion          # reparto de tiempo y tamaño del guion
python -m docs.verificar_entregables  # frases que ya no aplican en los archivos
python -m docs.revisar_texto docs/datos.py   # fragmentos corruptos en la prosa
python -m docs.arreglar_escapes       # á literales -> á
```

Las cuatro salen con código 1 si encuentran algo, así que sirven para dejarlas
en un paso de compilación o antes de imprimir.

En la carpeta `tools/` hay las del backend y el frontend:

| Script | Qué comprueba |
|---|---|
| `check_js.py` | Errores de sintaxis y de referencias en el JavaScript |
| `check_refs.py` | Que los módulos JS importen lo que existe |
| `verificar_sql.py` | Que `sql/*.sql` declaren las mismas columnas que el modelo de Python |
| `verificar_portal.py` | Que una cuenta de cliente vea solo su empresa, contra el servidor real |
| `crear_cuenta_comprador.py` | Crea la cuenta de un cliente europeo para probar el portal |
| `probar_sql_mysql.py` | Carga `schema_mysql.sql` en el MySQL local (pide la clave de root) |
| `empaquetar.py` | Arma el zip del proyecto sin la base de datos ni `__pycache__` |

## El portal del cliente europeo (HU-10)

Una cuenta con el rol «Cliente europeo» entra a `/#/portal` y ve únicamente lo
suyo. Para que eso sea cierto, y no solo pareciera:

- `usuarios.id_cliente` dice de qué empresa es la cuenta. Sin esa columna no
  había forma de filtrar, así que el comprador habría visto los pedidos de los
  cinco clientes. La API la exige al crear la cuenta y descarta el valor si el
  rol no es de cliente.
- Las consultas de exportaciones y envíos se recortan por esa empresa **en el
  servidor**, antes de aplicar cualquier filtro de la URL, para que no se puedan
  ampliar con `?id_cliente=`. Al abrir un pedido o un envío ajeno se responde
  404 y no 403, para no confirmar que ese número existe.
- El panel general y los indicadores de la empresa están cerrados para ese rol.
  Antes solo exigían estar logueado, y un comprador veía los lotes y los kilos
  exportados de toda la operación.
- El resto del módulo comercial sigue siendo interno: cotizaciones,
  exportaciones y documentos no aceptan al cliente, porque el portal es de
  consulta.

Las 15 pruebas de `backend/tests/test_portal_cliente.py` cubren las dos caras: lo
que el cliente puede ver y lo que no.

**Migraciones.** `Base.metadata.create_all()` crea las tablas que faltan pero no
altera las que ya existen, así que añadir una columna al modelo y arrancar con
una base de una corrida anterior fallaba en el primer INSERT. Para eso está
`app/migraciones.py`, que se corre sola al arrancar la API y también a mano:

```
cd backend
python -m app.migraciones
```

Cada migración comprueba primero si hace falta, así que se puede correr las
veces que haga falta.

## El reparto de la exposición

Está en `datos.EXPOSICION`, y tanto la presentación como el guion lo leen, de
modo que no pueden desincronizarse. Diez minutos en dos bloques:

| | Integrantes | Tiempo | De qué se ocupa |
|---|---|---|---|
| **Bloque 1 · De dónde vienen los lotes** | Andres Villavicencio + Juanprogramming | 0:00 – 3:20 | El problema, cómo está hecho, el diagrama ER, el diagrama UML |
| **Bloque 2 · Qué hace el sistema** | Juan Araujo + Dario Paz | 3:20 – 10:00 | Los cuatro módulos, lo que hicimos, el programa, las reglas, la demostración y el cierre |

Cada bloque tiene una diapositiva final compartida, donde se anuncia qué hizo
la otra pareja. Dos detalles que hacen la defensa navegable:

- Cada diapositiva lleva en la esquina superior derecha un distintivo con el
  nombre de quien la explica, en el color de su bloque.
- Las diapositivas personales llevan **el texto que se va a decir**, así que se
  puede leer de la pantalla sin aprendérselo de memoria.

### De dónde sale lo que dice cada persona

`datos.GUION_DETALLADO` tiene, para cada diapositiva de cada persona, cinco
cosas: qué se ve proyectado, qué dice, cómo lo dice y con qué frase de puente
pasa a la siguiente. `datos.IDEA` es la idea que cada uno tiene que dejar
instalada. `datos.PLAN_B` y `datos.PRECAUCIONES` son los consejos para el día de
la defensa.

El texto hablado son unas 1.090 palabras, unos 6,8 minutos a ritmo de habla
normal (`datos.PALABRAS_POR_MINUTO = 160`). Quedan unos tres minutos de margen,
que es lo que se llena con la demostración y con las pausas. Cada persona va
entre el 66 % y el 74 % de su cupo, así que nadie tiene que acelerar.

`datos.guion_por_persona()` reparte cada diapositiva entre las frases que caben
en los segundos asignados y las de ampliación, sin partir ninguna frase: las
primeras son las que se dicen en el tiempo, las segundas están para quien tenga
más confianza, para ensayar o para responder preguntas.

Para cambiar el reparto se edita `datos.EXPOSICION`: la clave de cada
diapositiva (`portada`, `problema`, `diagrama_er`, `items`, `demo`…) la resuelve
`presentacion.py` contra su tabla `DIBUJANTES`. Si se pone una clave que no
exista, la construcción falla con un `KeyError` en vez de dejar la diapositiva
en blanco.

## Cuál de los dos documentos usar

**PDF** (`documento.py`) y **Word** (`word.py`) dicen exactamente lo mismo: leen
las mismas tablas de `datos.py`. La diferencia es práctica:

- El **PDF** tiene la maqueta fija: no se desarma al abrirlo ni al imprimirlo.
  Es lo que se entrega si no hay que corregir nada.
- El **Word** se puede editar, que es justo lo que hace falta si el reparto de
  responsables del sprint no coincide con el que está en `datos.CLAVE`.

Si se corrige `datos.py`, hay que regenerar **los dos** para que no se
desincronicen.

## Estructura del paquete

| Módulo | Responsabilidad |
|---|---|
| `datos.py` | Todo el contenido: requisitos, actores, casos de uso, historias, backlog, modelo de datos y guion. **Es el único archivo que hay que editar** para cambiar un dato. |
| `generar_guion_detallado.py` | Rehace `GUION_DETALLADO` desde `EXPOSICION`, y es dueño de `IDEA`, `PLAN_B` y `PRECAUCIONES`. |
| `nombres.py` | Integrantes del equipo, extraídos por script del PDF fuente. |
| `generar_nombres.py` | Regenera `nombres.py` desde el documento original. |
| `diagramas.py` | Diagrama UML de casos de uso. |
| `diagrama_er.py` | Diagrama entidad-relación. |
| `documento.py` | Arma el PDF de los cinco puntos (reportlab). |
| `word.py` | Arma el mismo documento en Word (python-docx). |
| `guion.py` | Arma el guion de exposición en Word (python-docx). |
| `guion_pptx.py` | Arma el guion de exposición en PowerPoint (python-pptx). |
| `presentacion.py` | Arma el PowerPoint (python-pptx). |
| `resumen_guion.py` | Imprime el reparto de tiempo y el tamaño del guion. |
| `verificar_entregables.py` | Busca en los archivos generados frases que ya no aplican. |
| `revisar_texto.py` | Busca fragmentos corruptos en la prosa de `datos.py`. |
| `arreglar_escapes.py` | Convierte los `\u00e1` literales a su carácter real. |

## De dónde sale cada dato

- **Requisitos, historias de usuario y estructura de las nueve tablas**:
  sacados del informe y del documento de base de datos del proyecto.
- **Actores y casos de uso**: derivados de los cinco roles del requisito RR-003
  y de las diez historias de usuario.
- **Criterios de aceptación**: escritos a partir del comportamiento real del
  software, en frases cortas.
- **Claves del backlog y responsables**: los mismos que aparecen en la
  presentación y en el guion, para que no se contradigan. Están en
  `datos.CLAVE`; si el reparto real del sprint es otro, se cambia ahí y se
  regenera todo.

## Notas de implementación

Cuatro cosas que no se ven en el código pero que hubo que descubrir al hacer los
diagramas y las tablas, por si hay que volver a tocarlos:

1. **`Canvas.ellipse` recibe las esquinas de la caja delimitadora, no ancho y alto.**
   `Canvas.rect` sí toma `(x, y, ancho, alto)`. Confundir las dos firmas produce
   elipses gigantes que cruzan la página entera.
2. **En `python-pptx` todas las coordenadas van en EMU.** Pasar pulgadas
   desnudas (`y = 1.78`) las colapsa en la esquina superior izquierda. Todas las
   posiciones se escriben como `Inches(...)`.
3. **En `python-docx` el ancho de tabla se fija por columna, no por celda.** Con el
   layout fijo (`tblLayout`), Word manda el `tblGrid`, y ese grid solo se escribe
   al asignar `tabla.columns[j].width`. Asignar solo `celda.width` deja el
   reparto por defecto y la tabla se desborda: el guion llegó a 36 páginas en vez
   de 9 por eso. Por eso `guion.py` tiene el helper `_ancho_fijo`.
4. **Al editar prosa en `datos.py` a través de una herramienta, los acentos a
   veces se escriben como `\u00f3` literal**, que en una cadena normal de Python
   no es un escape: el archivo compila pero el entregable sale con `\u00f3`
   impreso. `python -m docs.arreglar_escapes` lo corrige.

Además, las páginas de los diagramas se recortan a la altura que el contenido
necesita (`ALTO_PAG_1`, `ALTO_PAG_2`) para que, al incrustarlos en la
presentación, no quede media diapositiva en blanco.

## Imágenes de la aplicación

La diapositiva «El programa funcionando» usa `salida/app_resumen.png`, un
recorte del panel general tomado del prototipo en ejecución. Para regenerarlo:

1. Levantar la aplicación (`cd backend`, `python -m app.seed --reset`, `uvicorn app.main:app`).
2. Iniciar sesión y abrir el panel general.
3. Recortar las tarjetas de indicadores y la línea de tiempo del envío.
