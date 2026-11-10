"""Contenido documental del Sprint 2.

Fuentes:
  · Sistema de Gestión de Exportación de Café y Cacao a la Unión Europea (RF, RNF, RR, backlog)
  · Informe_RiTech_SAS_completo (módulos, cadena de estados, KPIs)
  · RiTech_Base_datos_relaciones_equipo_APIs (nueve tablas, relaciones, equipo)
  · mockup-ritech-export-2.html (sistema de diseño)

`RESPONSABLES` es una **propuesta** derivada del aporte documentado de cada
integrante; debe confirmarse contra el tablero de Jira antes de entregar.
"""

from __future__ import annotations

from docs.nombres import EQUIPO as INTEGRANTES

PROYECTO = "Sistema de Gestión de Exportación de Café y Cacao a la Unión Europea"
EMPRESA = "RiTech SAS"
METODOLOGIA = "Scrum — sprints de dos semanas"
FECHA = "29 de septiembre de 2026"

EQUIPO = INTEGRANTES
SEGUNDO_INTEGRANTE = EQUIPO[1]

# =========================================================================== #
# 1. Requisitos                                                               #
# =========================================================================== #

REQUISITOS_FUNCIONALES = [
    ("RF-001", "Usuarios y acceso",
     "El sistema permitirá crear usuarios y asignarles un rol."),
    ("RF-002", "Clientes",
     "El sistema permitirá registrar los clientes europeos que compran el "
     "producto."),
    ("RF-003", "Fincas y lotes",
     "El sistema permitirá registrar fincas, sus productores y los lotes de "
     "café y cacao."),
    ("RF-004", "Calidad del producto",
     "El sistema permitirá registrar el resultado de la catación y del "
     "laboratorio de cada lote."),
    ("RF-005", "Certificaciones",
     "El sistema permitirá registrar las certificaciones de cada lote y avisar "
     "cuando estén por vencerse."),
    ("RF-006", "Pedidos y envíos",
     "El sistema permitirá crear pedidos y registrar los envíos hasta que "
     "llegan al cliente."),
]

REQUISITOS_NO_FUNCIONALES = [
    ("RNF-001", "Fácil de usar",
     "El sistema tendrá un menú lateral y pantallas sencillas, para que no "
     "haga falta instrucción para usarlo."),
    ("RNF-002", "Sirve en celular",
     "El sistema se va a ver bien en computador, tableta y celular."),
    ("RNF-003", "Responde rápido",
     "El sistema va a mostrar los datos de una pantalla en pocos segundos."),
    ("RNF-004", "Datos protegidos",
     "Solo las personas con permiso pueden ver o cambiar la información."),
]

REQUISITOS_RESTRICCION = [
    ("RR-001", "Metodología",
     "El proyecto se va a hacer con Scrum, en sprints de dos semanas."),
    ("RR-002", "Base de datos",
     "La información se va a guardar en PostgreSQL."),
    ("RR-003", "Roles",
     "El sistema manejará los roles de administrador, comercial, logística, "
     "calidad y cliente europeo."),
    ("RR-004", "Tres partes",
     "El software se va a hacer en tres partes: la pantalla, las reglas de "
     "negocio y la base de datos."),
]

# =========================================================================== #
# Actores y casos de uso                                                      #
# =========================================================================== #

ACTORES = [
    ("Administrador", "Crea los usuarios y decide qué puede ver cada uno."),
    ("Comercial", "Registra los clientes, los pedidos y los contratos."),
    ("Logística", "Registra los envíos y los contenedores."),
    ("Calidad", "Registra la catación y las certificaciones de los lotes."),
    ("Cliente europeo", "Entra a su portal para ver sus pedidos y sus envíos."),
]

# (módulo, [(nombre del caso de uso, actor principal)])
CASOS_DE_USO = {
    "Usuarios": [
        ("Crear usuario", "Administrador"),
        ("Iniciar sesión", "Administrador"),
    ],
    "Clientes": [
        ("Registrar cliente", "Comercial"),
    ],
    "Fincas y lotes": [
        ("Registrar finca", "Comercial"),
        ("Registrar lote", "Comercial"),
        ("Ver inventario", "Logística"),
    ],
    "Calidad": [
        ("Registrar catación", "Calidad"),
        ("Registrar certificación", "Calidad"),
    ],
    "Pedidos y envíos": [
        ("Crear pedido", "Comercial"),
        ("Registrar envío", "Logística"),
        ("Ver el envío", "Cliente europeo"),
    ],
}

# =========================================================================== #
# Épicas e historias de usuario                                               #
# =========================================================================== #

# (id, épica, historia, rol, prioridad, puntos, criterios de aceptación, estado)
HISTORIAS = [
    ("HU-01", "Usuarios",
     "Como administrador quiero crear usuarios para que mi equipo pueda "
     "entrar al sistema.",
     "Administrador", "Alta", 3, [
         "Puedo escribir el nombre, el correo y el rol de la persona.",
         "El sistema no deja crear dos usuarios con el mismo correo.",
         "La contraseña se guarda cifrada, no se ve en pantalla.",
     ], "Terminada"),

    ("HU-02", "Usuarios",
     "Como usuario quiero entrar con mi correo y contraseña para ver solo lo "
     "que me corresponde.",
     "Todos", "Alta", 3, [
         "Con un correo y una contraseña correctos, entro al sistema.",
         "Si la contraseña está mal, el sistema avisa y no me deja entrar.",
     ], "Terminada"),

    ("HU-03", "Clientes",
     "Como comercial quiero registrar los clientes europeos para saber a quién "
     "le vendemos.",
     "Comercial", "Alta", 3, [
         "Puedo escribir el nombre de la empresa, el país, el correo y el "
         "puerto donde recibe el producto.",
         "El cliente queda disponible para crearle pedidos.",
     ], "Terminada"),

    ("HU-04", "Fincas y lotes",
     "Como comercial quiero registrar fincas y lotes para saber de dónde sale "
     "el café y el cacao.",
     "Comercial", "Alta", 3, [
         "Puedo escribir el nombre de la finca, el departamento, el productor "
         "y a qué asociación pertenece.",
         "Al crear un lote, el sistema le pone un código, por ejemplo "
         "CO-HUI-2026-0001.",
         "Puedo escribir las coordenadas de la finca, porque el comprador las "
         "pide.",
     ], "Terminada"),

    ("HU-05", "Fincas y lotes",
     "Como logística quiero ver cuánto café hay disponible para saber qué se "
     "puede vender.",
     "Logística", "Alta", 3, [
         "Veo la cantidad de kilos de cada lote.",
         "Al crear un pedido, los kilos se descuentan del lote.",
         "El sistema no me deja vender más kilos de los que hay.",
     ], "Terminada"),

    ("HU-06", "Calidad",
     "Como calidad quiero registrar el resultado de la catación para saber si "
     "el lote se puede vender.",
     "Calidad", "Alta", 3, [
         "Escribo el puntaje de catación, la humedad y el laboratorio.",
         "La humedad tiene que estar entre 8 y 14, si no el sistema avisa.",
         "El estado del lote se pone solo: aprobado, con reserva o rechazado.",
     ], "Terminada"),

    ("HU-07", "Calidad",
     "Como calidad quiero registrar las certificaciones para demostrar que el "
     "producto está autorizado para venderlo.",
     "Calidad", "Alta", 3, [
         "Puedo registrar si el lote tiene certificación orgánica, Fairtrade o "
         "europea.",
         "Escribo la fecha de vencimiento y el sistema me avisa cuando falte "
         "poco.",
     ], "Terminada"),

    ("HU-08", "Pedidos",
     "Como comercial quiero crear un pedido para formalizar la venta.",
     "Comercial", "Alta", 3, [
         "Escribo el cliente, el lote, los kilos y el precio.",
         "El total se calcula solo: kilos por precio.",
     ], "Terminada"),

    ("HU-09", "Envíos",
     "Como logística quiero registrar un envío para que el cliente sepa por "
     "dónde va su pedido.",
     "Logística", "Alta", 3, [
         "Escribo la naviera, el número de seguimiento y las fechas de salida "
         "y llegada.",
         "El número de seguimiento no se puede repetir.",
     ], "Terminada"),

    ("HU-10", "Envíos",
     "Como cliente europeo quiero ver el estado de mi envío para saber cuándo "
     "me llega el producto.",
     "Cliente europeo", "Media", 3, [
         "Entro con mi propio correo y veo el portal de mi empresa.",
         "En el portal veo mis pedidos y mis envíos, y nada de los demás clientes.",
         "Veo en qué etapa va el envío: en puerto, en tránsito o entregado.",
         "No puedo cambiar nada: el portal es solo para consultar.",
     ], "Terminada"),
]

# =========================================================================== #
# 3. Product backlog de septiembre                                             #
# =========================================================================== #

# Lo que hicimos en el sprint, en el orden en que se fue trabajando.
# (clave, qué se hizo, historias relacionadas, responsable, estado)
BACKLOG_SEPTIEMBRE = [
    ("T-01", "Pantalla de entrada al sistema, con usuarios y contraseña.",
     "HU-01, HU-02", "Andres", "Hecho"),
    ("T-02", "Registro de clientes europeos.",
     "HU-03", "Juanprogramming", "Hecho"),
    ("T-03", "Registro de fincas y lotes, con su código y su inventario.",
     "HU-04, HU-05", "Juanprogramming", "Hecho"),
    ("T-04", "Registro de catación y de certificaciones.",
     "HU-06, HU-07", "Dario", "Hecho"),
    ("T-05", "Pedidos y conversión a contrato.",
     "HU-08", "Juan Araujo", "Hecho"),
    ("T-06", "Registro de envíos y línea de tiempo del envío.",
     "HU-09", "Dario", "Hecho"),
    ("T-07", "Portal donde el cliente ve sus pedidos y sus envíos.",
     "HU-10", "Juan Araujo", "Hecho"),
]

# Tareas técnicas que no se ven en pantalla.
# (clave, tarea técnica, responsable)
TAREAS_SEPTIEMBRE = [
    ("T-08", "Armar la base de datos con las nueve tablas del modelo.",
     "Andres"),
    ("T-09", "Levantar la API y la forma de iniciar sesión.",
     "Andres"),
    ("T-10", "Cargar datos de ejemplo de café y cacao de Colombia.",
     "Juanprogramming"),
]

# =========================================================================== #
# 5. Estructura de la base de datos                                                      #
#
NUCLEO_TABLAS = [
    ("usuarios", [
        ("id_usuario", "INT", "PK"),
        ("nombre", "VARCHAR(100)", ""),
        ("correo", "VARCHAR(150)", "no se repite"),
        ("contrasena_hash", "VARCHAR(255)", "cifrada"),
        ("rol", "VARCHAR(50)", "administrador, comercial, logística, calidad y cliente"),
        ("estado", "VARCHAR(20)", "activo o inactivo"),
        ("id_cliente", "INT", "FK → clientes · solo si es cliente"),
    ], "Personas con acceso al sistema. Un usuario registra muchas exportaciones. "
       "Si el rol es de cliente europeo, id_cliente dice de qué empresa es: eso es "
       "lo que hace que su portal muestre únicamente lo suyo."),
    ("clientes", [
        ("id_cliente", "INT", "PK"),
        ("nombre_empresa", "VARCHAR(150)", ""),
        ("pais", "VARCHAR(100)", ""),
        ("direccion", "VARCHAR(200)", ""),
        ("correo", "VARCHAR(150)", ""),
        ("telefono", "VARCHAR(30)", ""),
        ("vat", "VARCHAR(50)", "código de la empresa"),
        ("moneda_preferida", "VARCHAR(10)", "euros, dólares o pesos"),
        ("puerto_destino", "VARCHAR(100)", ""),
    ], "Importadores de la Unión Europea. Un cliente realiza muchas exportaciones."),
    ("productos", [
        ("id_producto", "INT", "PK"),
        ("nombre", "VARCHAR(100)", ""),
        ("tipo", "VARCHAR(50)", "café o cacao"),
        ("descripcion", "TEXT", ""),
        ("variedad", "VARCHAR(100)", "variedad del café"),
        ("precio_referencia_eur", "NUMERIC(12,2)", ""),
    ], "Tipos de café y cacao. Un producto tiene muchos lotes."),
    ("fincas", [
        ("id_finca", "INT", "PK"),
        ("nombre", "VARCHAR(150)", ""),
        ("ubicacion", "VARCHAR(200)", ""),
        ("departamento", "VARCHAR(100)", ""),
        ("propietario", "VARCHAR(150)", ""),
        ("productor", "VARCHAR(150)", ""),
        ("asociacion", "VARCHAR(150)", ""),
        ("latitud / longitud", "NUMERIC(10,7)", "ubicación de la finca"),
    ], "Origen del producto. Una finca tiene muchos lotes."),
    ("lotes", [
        ("id_lote", "INT", "PK"),
        ("id_finca", "INT", "FK → fincas"),
        ("id_producto", "INT", "FK → productos"),
        ("codigo_lote", "VARCHAR(50)", "no se repite"),
        ("cantidad_kg", "NUMERIC(12,2)", ""),
        ("fecha_cosecha", "DATE", ""),
        ("estado_calidad", "VARCHAR(50)", "aprobado, con reserva o rechazado"),
        ("disponible_kg", "NUMERIC(12,2)", "lo que queda libre"),
    ], "Unidad de trazabilidad. Un lote aparece en muchas exportaciones."),
    ("exportaciones", [
        ("id_exportacion", "INT", "PK"),
        ("id_cliente", "INT", "FK → clientes"),
        ("id_usuario", "INT", "FK → usuarios"),
        ("fecha", "DATE", ""),
        ("estado", "VARCHAR(50)", "va cambiando según el envío"),
        ("moneda", "VARCHAR(10)", ""),
        ("numero_contrato", "VARCHAR(60)", "no se repite"),
        ("incoterm", "VARCHAR(20)", "FOB, CIF, EXW…"),
    ], "Operación de exportación. Es la entidad central del módulo comercial."),
    ("detalle_exportacion", [
        ("id_detalle", "INT", "PK"),
        ("id_exportacion", "INT", "FK → exportaciones"),
        ("id_lote", "INT", "FK → lotes"),
        ("cantidad_kg", "NUMERIC(12,2)", ""),
        ("precio_kg", "NUMERIC(12,2)", ""),
    ], "Líneas de una exportación. El par (exportación, lote) es único."),
    ("documentos_exportacion", [
        ("id_documento", "INT", "PK"),
        ("id_exportacion", "INT", "FK → exportaciones"),
        ("tipo_documento", "VARCHAR(100)", "factura, certificado oknowledge de embarque"),
        ("numero_documento", "VARCHAR(100)", "no se repite"),
        ("fecha_emision", "DATE", ""),
        ("estado", "VARCHAR(50)", "borrador o emitido"),
        ("autorizado_cliente", "BOOLEAN", "el cliente puede verlo"),
    ], "Documentación de la operación de exportación."),
    ("envios", [
        ("id_envio", "INT", "PK"),
        ("id_exportacion", "INT", "FK → exportaciones"),
        ("transportadora", "VARCHAR(100)", ""),
        ("numero_seguimiento", "VARCHAR(100)", "no se repite"),
        ("fecha_salida", "DATE", ""),
        ("fecha_llegada", "DATE", ""),
        ("estado", "VARCHAR(50)", "en tránsito o entregado"),
    ], "Transporte internacional. Una exportación puede tener varios envíos."),
]

EXTENSIONES_TABLAS = [
    ("contenedores", "Para anotar los contenedores que se usan en cada envío."),
    ("calidad_lote", "Para guardar la catación y el análisis de laboratorio."),
    ("certificaciones", "Para guardar los certificados de cada lote y cuándo "
                        "se vencen."),
]

# (origen, destino, cardinalidad, regla)
RELACIONES = [
    ("fincas", "lotes", "1 : N", "Una finca tiene muchos lotes; cada lote pertenece a una finca."),
    ("productos", "lotes", "1 : N", "Un producto tiene muchos lotes; cada lote corresponde a un producto."),
    ("clientes", "exportaciones", "1 : N", "Un cliente realiza muchas exportaciones."),
    ("usuarios", "exportaciones", "1 : N", "Un usuario registra muchas exportaciones."),
    ("usuarios", "clientes", "1 : N", "Una cuenta de cliente europeo pertenece a una empresa; el personal de RiTech no pertenece a ninguna."),
    ("usuarios", "clientes", "1 : N", "Una cuenta de cliente europeo pertenece a una empresa; el personal de RiTech no pertenece a ninguna."),
    ("exportaciones", "detalle_exportacion", "1 : N", "Una exportación contiene muchas líneas."),
    ("lotes", "detalle_exportacion", "1 : N", "Un lote aparece en muchas líneas de exportación."),
    ("exportaciones", "documentos_exportacion", "1 : N", "Una exportación tiene muchos documentos."),
    ("exportaciones", "envios", "1 : N", "Una exportación puede tener uno o varios envíos."),
    ("contenedores", "envios", "1 : N", "Un contenedor transporta varios envíos."),
    ("lotes", "calidad_lote", "1 : 1", "Cada lote tiene como máximo un registro de calidad."),
    ("lotes", "certificaciones", "1 : N", "Un lote puede tener varias certificaciones."),
    ("lotes", "eventos_trazabilidad", "1 : N", "Un lote tiene varios hitos de trazabilidad."),
    ("clientes", "cotizaciones", "1 : N", "Un cliente recibe muchas cotizaciones."),
]

MODULOS = [
    ("1", "Productores, fincas y lotes", "Terminado"),
    ("2", "Calidad y certificaciones", "Terminado"),
    ("3", "Clientes y pedidos", "Terminado"),
    ("4", "Envíos y portal del cliente", "Terminado"),
]

KPIS = [
    "Lotes registrados",
    "Clientes europeos",
    "Pedidos del mes",
    "Envíos en camino",
    "Certificaciones por vencer",
    "Kilos disponibles",
]

CADENA_ESTADOS = [
    "Finca", "Beneficio", "Puerto", "En tránsito", "Aduana", "Cliente",
]

# =========================================================================== #
# Reparto de la exposición                                                     #
# =========================================================================== #
#
# Diez minutos, cuatro personas, dos bloques. Cada bloque lo explica una pareja
# y va de lo general a lo particular, para que quien entra despues solo tenga
# que continuar lo que dijo el anterior.
#
#   Bloque 1 - EL CIMIENTO: de donde vienen los datos y que reglas los vigilan
#       Andres Villavicencio  -> estructura, arquitectura y pruebas
#       Juanprogramming  -> relaciones, trazabilidad y cumplimiento
#
#   Bloque 2 - LA OPERACION: que hace el sistema con esos datos
#       Juan Araujo          -> comercial, pedidos y portal del cliente
#       Dario Paz            -> logistica, calidad, demostracion y cierre
#
# Cada diapositiva: (clave, dueno, titulo, segundos, [lineas del guion]).
# El dueno es el indice dentro de EQUIPO. La clave la resuelve presentacion.py
# contra la tabla de funciones.

#: Nombre sin ambigüedad para citar a alguien: nombre de pila y apellido
#: familiar. Necesario porque dos integrantes comparten nombre de pila.
NOMBRE_CORTO = [n.split()[0] + " " + n.split()[-1] for n in EQUIPO]

#: Clave corta de cada integrante. Es lo que se usa para emparejar el backlog,
#: la exposición y los generadores; el nombre completo solo se muestra.
CLAVE = ["Andres", "Juanprogramming", "Juan Araujo", "Dario"]

#: Nombre completo para las cabeceras de las diapositivas y el guion.
NOMBRE = list(EQUIPO)

EXPOSICION = [
    {
        "titulo": "De dónde vienen los lotes",
        "lema": "Lo primero: el origen del café y del cacao",
        "integrantes": [0, 1],
        "color": "4B7B52",
        "diapositivas": [

            ("portada", 0, "Portada y equipo", 20, [
                "Buenos días. Somos el equipo de RiTech SAS y les vamos a "
                "presentar el sistema de gestión de exportaciones de café y cacao "
                "hacia la Unión Europea.",
                "Es lo que hicimos en este sprint de dos semanas. Lo explicamos "
                "en cuatro partes de dos minutos y medio, y al final lo "
                "mostramos funcionando.",
            ]),

            ("problema", 0, "El problema", 45, [
                "La pregunta que nos dimos al empezar fue muy sencilla: de qué "
                "finca viene un lote de café, y si ese café se puede vender en "
                "Europa.",
                "La respuesta estaba repartida entre planillas de cálculo y "
                "cuadernos. Eso significa que nadie podía responder las dos "
                "cosas a la vez, y que dependía de que alguien se acordara.",
                "Nuestro sistema junta las dos respuestas en una sola pantalla. "
                "Registra de qué finca viene el lote, cuánto producto tiene, qué "
                "certificados tiene y en qué envío va.",
                "Además, el cliente europeo no tiene que preguntar nada: entra a "
                "su portal y ve lo mismo que RiTech.",
            ]),

            ("arquitectura", 0, "Cómo está hecho", 45, [
                "El sistema tiene tres partes. La primera es la pantalla, que es "
                "lo que ve el usuario. La segunda son las reglas de negocio, que "
                "son las condiciones que tiene que cumplir todo.",
                "La tercera es la base de datos, donde se guarda todo: los "
                "clientes, las fincas, los lotes, los pedidos y los envíos.",
                "Las reglas están aparte, en un solo sitio. Eso es a propósito: "
                "si cambian, se cambian en un archivo y no hay que tocar la "
                "pantalla.",
                "La base de datos es PostgreSQL, que es la que pide el proyecto "
                "en sus requisitos.",
            ]),

            ("pareja", None, "Lo que hicimos: el origen", 90, [
                (0, "Yo me encargué de la base de datos. Hice las nueve tablas "
                    "del modelo, con las llaves que las relacionan, y el archivo "
                    "que las crea."),
                (0, "También la pantalla de entrada, donde el usuario escribe su "
                    "correo y su contraseña, y el menú de arriba donde están "
                    "todas las secciones."),
                (0, "Y las reglas de acceso: cada rol ve solo las pantallas que "
                    "le corresponden, no todas."),
                (1, "A mí me tocó el registro. Primero los clientes europeos, con "
                    "su país, su correo y el puerto donde reciben el producto."),
                (1, "Después las fincas, con el productor y la asociación a la "
                    "que pertenecen, y los lotes con su kilo y su fecha de "
                    "cosecha."),
                (1, "Cada lote recibe un código único, como CO-HUI-2026-0001, y con "
                    "ese código se le pueden ir agregando la catación, los "
                    "certificados y los envíos."),
            ]),
        ],
    },

    {
        "titulo": "Qué hace el sistema",
        "lema": "Calidad, pedidos, envíos y el portal del cliente",
        "integrantes": [2, 3],
        "color": "A84B32",
        "diapositivas": [

            ("diagrama_er", 1, "Diagrama de la base de datos", 50, [
                "Este es el diagrama de la base de datos. Las nueve tablas del "
                "modelo, y las líneas que dicen cómo se relacionan.",
                "La relación más importante es esta: una finca tiene lotes, un "
                "lote tiene su catación y sus certificados, y el mismo lote "
                "aparece en muchas exportaciones.",
                "Ese camino que va de la finca hasta la exportación es lo que "
                "llamamos trazabilidad. Y sale solo de cómo están conectadas las "
                "tablas, no de un módulo aparte.",
                "Yo hice estas relaciones y revisé que cada llave tuviera "
                "sentido con lo que pasa de verdad en la empresa.",
            ]),

            ("diagrama_uml", 1, "Diagrama de casos de uso", 50, [
                "Aquí vemos quién usa el sistema. Hay cuatro personas dentro de "
                "RiTech: administrador, comercial, logística y calidad. Y hay "
                "una por fuera: el cliente europeo.",
                "Cada uno tiene sus tareas y no entra a las de los demás. Por "
                "eso hay cinco roles distintos, y por eso se ve en el diagrama "
                "que el comercial no toca la logística.",
                "Lo que me tocó a mí fue el registro: los clientes europeos, las "
                "fincas y los lotes. De esos tres sale todo lo demás, porque el "
                "lote es el que se mueve.",
                "Y el detalle del diagrama: el mismo lote se puede ver en varias "
                "exportaciones sin perder de dónde vino. Eso es la trazabilidad.",
            ]),

            ("pareja", None, "Lo que hicimos: la operación", 90, [
                (2, "Yo hice la parte de comercial. Primero leí los requisitos "
                    "del informe y los pasé a historias de usuario, que son las "
                    "diez tareas que están en el documento."),
                (2, "Después el registro de clientes, los pedidos y la forma de "
                    "convertir un pedido en contrato."),
                (2, "Y el portal donde el cliente europeo ve sus pedidos y por "
                    "dónde va su envío."),
                (3, "Mi parte fue la logística: registrar los envíos, con la "
                    "naviera, el número de seguimiento y las fechas de salida y "
                    "de llegada."),
                (3, "Y la calidad: la catación de cada lote y los certificados, "
                    "con la fecha en que se vencen."),
                (3, "También organicé las tareas del sprint con el equipo."),
            ]),

            ("modulos", 2, "Los cuatro módulos", 45, [
                "Estos son los cuatro módulos en los que se dividió el sistema, y "
                "son los mismos cuatro del sprint.",
                "El primero es fincas y lotes: registrar el origen del producto y ver "
                "cuánto café hay disponible para vender. El segundo es calidad: la "
                "catación y los certificados.",
                "El tercero es comercial, con los clientes y los pedidos. Y el "
                "cuarto es logística, con los envíos y el portal del cliente.",
                "En el de calidad hay un detalle que nos gustó mucho: el estado del "
                "lote no lo escribe la persona, sale del resultado de la catación.",
            ]),

            ("items", 2, "Lo que hicimos en el sprint", 45, [
                "Estas son las siete tareas del sprint, y quién hizo cada una. Las "
                "siete quedaron hechas.",
                "En la primera parte trabajamos Andres, Juanprogramming y yo: la base "
                "de datos, el acceso y el registro. En la segunda, Juan Araujo y "
                "Dario: la calidad, los envíos, los pedidos y el portal.",
                "Dario también se encargó de organizar las tareas con el equipo, y "
                "fue el que armó los datos de ejemplo de café y cacao de Colombia.",
                "La tabla completa, con las historias de usuario de cada tarea, está "
                "en el documento que entregamos.",
            ]),

            ("estado", 3, "El programa funcionando", 35, [
                "Esto ya está funcionando, no es un dibujo. Es el programa con "
                "datos de ejemplo de café y cacao de Colombia.",
                "Esta es la pantalla de entrada. Arriba están los datos más "
                "importantes: cuántos lotes hay, cuántos envíos van en camino y "
                "cuántos certificados están por vencer.",
                "Abajo está el recorrido de un envío por las seis etapas, desde "
                "la finca hasta que llega al cliente. El punto naranja es por "
                "dónde va ahora.",
            ]),

            ("calidad", 3, "Las reglas que pusimos", 35, [
                "Hay cosas que el sistema no deja hacer, para que los datos "
                "queden bien.",
                "La primera: no se puede vender más café del que hay en el lote. "
                "Si alguien intenta vender de más, el sistema lo avisa.",
                "La segunda: la humedad de la catación tiene que estar entre 8 y "
                "14. Si se sale, el sistema avisa y el lote no se aprueba solo.",
                "Son reglas sencillas, pero evitan que se pierdan datos.",
            ]),

            ("demo", 3, "Demostración", 35, [
                "Ahora se los muestro. El sistema se levanta con un comando y cada "
                "persona del equipo tiene su cuenta, así que no hay que "
                "instalar nada.",
                "Voy a hacer tres cosas: crear una finca nueva, registrar una "
                "catación de 86 puntos y ver cómo el lote queda aprobado solo, "
                "y después abrir el recorrido de un envío.",
            ]),

            ("siguiente", 3, "Lo que sigue", 15, [
                "Nos falta el módulo de pagos, avisar por correo cuando un "
                "certificado está por vencer, y poder subir documentos al "
                "sistema.",
                "Eso es lo que queda para el siguiente sprint. Gracias por su "
                "atención.",
            ]),
        ],
    },
]


# =========================================================================== #
# Utilidades del guion
# =========================================================================== #


def guion_normalizado(guion) -> list:
    """Normaliza un guion a una lista de (integrante, frase).

    Las diapositivas de una persona sola guardan frases sueltas y devuelven
    `None` como autor; las de pareja guardan parejas `(índice, frase)`.
    """
    salida = []
    for entrada in guion:
        if isinstance(entrada, tuple):
            salida.append((entrada[0], entrada[1]))
        else:
            salida.append((None, entrada))
    return salida


def autores_de(guion) -> list:
    """Índices de los integrantes que hablan en un guion, sin repetir."""
    vistos = []
    for indice, _frase in guion_normalizado(guion):
        if indice is not None and indice not in vistos:
            vistos.append(indice)
    return vistos


def minutos_por_integrante() -> dict:
    """Segundos de cada persona.

    Las diapositivas individuales se cuentan enteras a su dueño. Las de pareja se
    reparten a partes iguales entre los que tienen línea, porque las dos personas
    de la pareja comparten esa diapositiva.
    """
    total = {i: 0 for i in range(len(EQUIPO))}
    for bloque in EXPOSICION:
        for _clave, dueno, _titulo, segundos, guion in bloque["diapositivas"]:
            if dueno is not None:
                total[dueno] += segundos
            else:
                autores = autores_de(guion)
                if autores:
                    parte = segundos // len(autores)
                    for i in autores:
                        total[i] += parte
    return total


def _segundos_de(bloque) -> int:
    return sum(x[3] for x in bloque["diapositivas"])


def bloques_con_tiempos() -> list:
    """Los bloques del reparto, cada uno con su inicio y su fin en el reloj."""
    salida = []
    inicio = 0
    for bloque in EXPOSICION:
        segundos = _segundos_de(bloque)
        salida.append((bloque, inicio, inicio + segundos))
        inicio += segundos
    return salida


# =========================================================================== #
# Preguntas que seguro llegan en el turno de preguntas                        #
# =========================================================================== #
#
# Respuestas de una o dos frases. Cualquiera de los cuatro las puede contestar,
# pero conviene saber quién la tiene: si es técnica, derivarla a la persona que
# hizo esa parte.

PREGUNTAS_FRECUENTES = [
    (
        "¿Por qué hicieron solo cuatro módulos y no todos los que pide el "
        "informe?",
        "Porque el sprint era de dos semanas. Hicimos los cuatro que más pesan: "
        "el origen del producto, la calidad, los pedidos y los envíos. Los "
        "demás están anotados para el siguiente sprint.",
    ),
    (
        "¿Qué pasa si un lote se exporta dos veces?",
        "No se puede comprometer más kilos de los que hay. El disponible se "
        "calcula con la cantidad menos lo que ya está comprometido, y el "
        "sistema avisa si alguien intenta pasar de largo.",
    ),
    (
        "¿Qué es la trazabilidad?",
        "Es poder decir de qué finca salió un lote y en qué barco va. Sale de "
        "cómo están conectadas las tablas, no de un módulo aparte.",
    ),
    (
        "¿Por qué se guarda la ubicación de la finca?",
        "Porque el comprador europeo la pide: sin la latitud y la longitud no "
        "acepta el lote. Por eso el registro de la finca las pide.",
    ),
    (
        "¿Cuánto falta para terminar el sistema?",
        "El módulo de pagos, los avisos por correo y subir documentos. Están "
        "identificados y son el siguiente sprint.",
    ),
    (
        "¿Se puede ver funcionando?",
        "Sí, es la demostración del final. Se levanta con un comando y cada "
        "persona del equipo tiene su cuenta.",
    ),
]


# =========================================================================== #
# Guion detallado: qué dice cada persona, cómo y con qué puente               #
# =========================================================================== #
#
# El texto hablado ronda las 1.250 palabras, unos ocho minutos a ritmo normal
# (unas 160 palabras por minuto); los diez minutos del turno se llenan con la
# demostración y con las preguntas. Lo que se amplía aquí es el andamiaje: qué
# hay proyectado, en qué conviene señalar, con qué frase se pasa a la
# siguiente y qué se recorta si se va con retraso.
#
# Las claves de diapositiva son las mismas de EXPOSICION, así que el guion no
# puede desincronizarse de la presentación.













#: La idea que cada persona tiene que dejar instalada
IDEA = {
    0: [
        'E',
        'l',
        ' ',
        's',
        'i',
        's',
        't',
        'e',
        'm',
        'a',
        ' ',
        't',
        'i',
        'e',
        'n',
        'e',
        ' ',
        't',
        'r',
        'e',
        's',
        ' ',
        'p',
        'a',
        'r',
        't',
        'e',
        's',
        ':',
        ' ',
        'l',
        'a',
        ' ',
        'p',
        'a',
        'n',
        't',
        'a',
        'l',
        'l',
        'a',
        ',',
        ' ',
        'l',
        'a',
        's',
        ' ',
        'r',
        'e',
        'g',
        'l',
        'a',
        's',
        ' ',
        'y',
        ' ',
        'l',
        'a',
        ' ',
        'b',
        'a',
        's',
        'e',
        ' ',
        'd',
        'e',
        ' ',
        'd',
        'a',
        't',
        'o',
        's',
        '.',
        ' ',
        'C',
        'a',
        'd',
        'a',
        ' ',
        'p',
        'a',
        'r',
        't',
        'e',
        ' ',
        'h',
        'a',
        'c',
        'e',
        ' ',
        'l',
        'o',
        ' ',
        's',
        'u',
        'y',
        'o',
        '.',
    ],
    1: [
        'E',
        'l',
        ' ',
        'l',
        'o',
        't',
        'e',
        ' ',
        'e',
        's',
        ' ',
        'e',
        'l',
        ' ',
        'c',
        'e',
        'n',
        't',
        'r',
        'o',
        ' ',
        'd',
        'e',
        ' ',
        't',
        'o',
        'd',
        'o',
        ':',
        ' ',
        'd',
        'e',
        ' ',
        'é',
        'l',
        ' ',
        's',
        'a',
        'l',
        'e',
        ' ',
        'l',
        'a',
        ' ',
        'c',
        'a',
        'l',
        'i',
        'd',
        'a',
        'd',
        ',',
        ' ',
        'l',
        'o',
        's',
        ' ',
        'c',
        'e',
        'r',
        't',
        'i',
        'f',
        'i',
        'c',
        'a',
        'd',
        'o',
        's',
        ' ',
        'y',
        ' ',
        'l',
        'a',
        ' ',
        't',
        'r',
        'a',
        'z',
        'a',
        'b',
        'i',
        'l',
        'i',
        'd',
        'a',
        'd',
        '.',
    ],
    2: [
        'D',
        'e',
        ' ',
        'l',
        'o',
        ' ',
        'q',
        'u',
        'e',
        ' ',
        'n',
        'o',
        's',
        ' ',
        'p',
        'i',
        'd',
        'i',
        'e',
        'r',
        'o',
        'n',
        ' ',
        'e',
        'n',
        ' ',
        'e',
        'l',
        ' ',
        'i',
        'n',
        'f',
        'o',
        'r',
        'm',
        'e',
        ' ',
        's',
        'a',
        'c',
        'a',
        'm',
        'o',
        's',
        ' ',
        'd',
        'i',
        'e',
        'z',
        ' ',
        'h',
        'i',
        's',
        't',
        'o',
        'r',
        'i',
        'a',
        's',
        ' ',
        'd',
        'e',
        ' ',
        'u',
        's',
        'u',
        'a',
        'r',
        'i',
        'o',
        ',',
        ' ',
        'y',
        ' ',
        'e',
        's',
        'o',
        ' ',
        'e',
        's',
        ' ',
        'l',
        'o',
        ' ',
        'q',
        'u',
        'e',
        ' ',
        'c',
        'o',
        'n',
        's',
        't',
        'r',
        'u',
        'i',
        'm',
        'o',
        's',
        '.',
    ],
    3: [
        'E',
        'l',
        ' ',
        's',
        'i',
        's',
        't',
        'e',
        'm',
        'a',
        ' ',
        'n',
        'o',
        ' ',
        'd',
        'e',
        'j',
        'a',
        ' ',
        'v',
        'e',
        'n',
        'd',
        'e',
        'r',
        ' ',
        'm',
        'á',
        's',
        ' ',
        'c',
        'a',
        'f',
        'é',
        ' ',
        'd',
        'e',
        'l',
        ' ',
        'q',
        'u',
        'e',
        ' ',
        'h',
        'a',
        'y',
        ',',
        ' ',
        'n',
        'i',
        ' ',
        'a',
        'c',
        'e',
        'p',
        't',
        'a',
        'r',
        ' ',
        'u',
        'n',
        'a',
        ' ',
        'h',
        'u',
        'm',
        'e',
        'd',
        'a',
        'd',
        ' ',
        'f',
        'u',
        'e',
        'r',
        'a',
        ' ',
        'd',
        'e',
        ' ',
        'r',
        'a',
        'n',
        'g',
        'o',
        '.',
    ],
}

#: (clave, qué se ve en pantalla, qué dice, cómo lo dice, frase de puente)
#: Las frases se copian de EXPOSICION, así que el guion de Word, el de
#: PowerPoint y la presentación no pueden quedar desincronizados.
GUION_DETALLADO = {
    0: [
        ('portada', 'Fondo oscuro con el título del proyecto y los cuatro nombres. No tiene información: es la portada.', ['Buenos días. Somos el equipo de RiTech SAS y les vamos a presentar el sistema de gestión de exportaciones de café y cacao hacia la Unión Europea.', 'Es lo que hicimos en este sprint de dos semanas. Lo explicamos en cuatro partes de dos minutos y medio, y al final lo mostramos funcionando.'], 'No leas el título de la pantalla, ya lo tienen delante. Mira al frente. Los tres primeros segundos deciden si te toman en serio.', 'Empiezo por el problema.'),
        ('problema', 'Dos columnas: «Antes» a la izquierda, con planillas y cuadernos; «Ahora» a la derecha, con el sistema.', ['La pregunta que nos dimos al empezar fue muy sencilla: de qué finca viene un lote de café, y si ese café se puede vender en Europa.', 'La respuesta estaba repartida entre planillas de cálculo y cuadernos. Eso significa que nadie podía responder las dos cosas a la vez, y que dependía de que alguien se acordara.', 'Nuestro sistema junta las dos respuestas en una sola pantalla. Registra de qué finca viene el lote, cuánto producto tiene, qué certificados tiene y en qué envío va.', 'Además, el cliente europeo no tiene que preguntar nada: entra a su portal y ve lo mismo que RiTech.'], 'Señala la columna de la izquierda y luego la de la derecha. Que te vean señalar ayuda a que te escuchen.', 'Y así queda hecho el sistema. Esta es su estructura.'),
        ('arquitectura', 'Tres bloques apilados a la izquierda: pantalla, reglas de negocio y base de datos.', ['El sistema tiene tres partes. La primera es la pantalla, que es lo que ve el usuario. La segunda son las reglas de negocio, que son las condiciones que tiene que cumplir todo.', 'La tercera es la base de datos, donde se guarda todo: los clientes, las fincas, los lotes, los pedidos y los envíos.', 'Las reglas están aparte, en un solo sitio. Eso es a propósito: si cambian, se cambian en un archivo y no hay que tocar la pantalla.', 'La base de datos es PostgreSQL, que es la que pide el proyecto en sus requisitos.'], 'Señala el bloque del medio cuando digas «las reglas están aparte». No leas las etiquetas de la derecha.', 'Con esto está la base. Sigue Juanprogramming con los datos.'),
        ('pareja', 'Dos tarjetas con los nombres de los dos y, a la derecha, lo que va a decir cada uno.', ['Yo me encargué de la base de datos. Hice las nueve tablas del modelo, con las llaves que las relacionan, y el archivo que las crea.', 'También la pantalla de entrada, donde el usuario escribe su correo y su contraseña, y el menú de arriba donde están todas las secciones.', 'Y las reglas de acceso: cada rol ve solo las pantallas que le corresponden, no todas.'], 'Di tus frases seguidas, sin mirar las del compañero, y después pásale el turno.', 'Con esto terminamos el primer bloque. Sigue Juanprogramming.'),
    ],
    1: [
        ('pareja', 'Dos tarjetas con los nombres de los dos y, a la derecha, lo que va a decir cada uno.', ['A mí me tocó el registro. Primero los clientes europeos, con su país, su correo y el puerto donde reciben el producto.', 'Después las fincas, con el productor y la asociación a la que pertenecen, y los lotes con su kilo y su fecha de cosecha.', 'Cada lote recibe un código único, como CO-HUI-2026-0001, y con ese código se le pueden ir agregando la catación, los certificados y los envíos.'], 'Di tus frases seguidas, sin mirar las del compañero, y después pásale el turno.', 'Con esto terminamos el primer bloque. Sigue Juanprogramming.'),
        ('diagrama_er', 'El diagrama de la base de datos a pantalla completa: las nueve tablas en tres filas, con líneas que las unen.', ['Este es el diagrama de la base de datos. Las nueve tablas del modelo, y las líneas que dicen cómo se relacionan.', 'La relación más importante es esta: una finca tiene lotes, un lote tiene su catación y sus certificados, y el mismo lote aparece en muchas exportaciones.', 'Ese camino que va de la finca hasta la exportación es lo que llamamos trazabilidad. Y sale solo de cómo están conectadas las tablas, no de un módulo aparte.', 'Yo hice estas relaciones y revisé que cada llave tuviera sentido con lo que pasa de verdad en la empresa.'], 'No intentes leer todos los campos, se ve que están. Señala las líneas que unen las tablas.', 'El mismo sistema, visto desde quién usa qué.'),
        ('diagrama_uml', 'El diagrama de casos de uso: cinco columnas, una por rol, con las tareas de cada uno en óvalos.', ['Aquí vemos quién usa el sistema. Hay cuatro personas dentro de RiTech: administrador, comercial, logística y calidad. Y hay una por fuera: el cliente europeo.', 'Cada uno tiene sus tareas y no entra a las de los demás. Por eso hay cinco roles distintos, y por eso se ve en el diagrama que el comercial no toca la logística.', 'Lo que me tocó a mí fue el registro: los clientes europeos, las fincas y los lotes. De esos tres sale todo lo demás, porque el lote es el que se mueve.', 'Y el detalle del diagrama: el mismo lote se puede ver en varias exportaciones sin perder de dónde vino. Eso es la trazabilidad.'], 'Empieza por los roles, que es lo primero que se entiende. No leas los óvalos uno por uno.', 'Entonces, qué hicimos los dos:'),
    ],
    2: [
        ('pareja', 'Dos tarjetas con los nombres de los dos y, a la derecha, lo que va a decir cada uno.', ['Yo hice la parte de comercial. Primero leí los requisitos del informe y los pasé a historias de usuario, que son las diez tareas que están en el documento.', 'Después el registro de clientes, los pedidos y la forma de convertir un pedido en contrato.', 'Y el portal donde el cliente europeo ve sus pedidos y por dónde va su envío.'], 'Di tus frases seguidas, sin mirar las del compañero, y después pásale el turno.', 'Con esto terminamos. Gracias por su atención.'),
        ('modulos', 'Cuatro tarjetas: fincas y lotes, calidad, comercial y logística, y el portal del cliente.', ['Estos son los cuatro módulos en los que se dividió el sistema, y son los mismos cuatro del sprint.', 'El primero es fincas y lotes: registrar el origen del producto y ver cuánto café hay disponible para vender. El segundo es calidad: la catación y los certificados.', 'El tercero es comercial, con los clientes y los pedidos. Y el cuarto es logística, con los envíos y el portal del cliente.', 'En el de calidad hay un detalle que nos gustó mucho: el estado del lote no lo escribe la persona, sale del resultado de la catación.'], 'No leas las cuatro tarjetas enteras. Menciona la de calidad y pasa a la siguiente.', 'Esto es lo que dejamos hecho en el sprint.'),
        ('items', 'Una tabla con las siete tareas del sprint, quién hizo cada una y el estado.', ['Estas son las siete tareas del sprint, y quién hizo cada una. Las siete quedaron hechas.', 'En la primera parte trabajamos Andres, Juanprogramming y yo: la base de datos, el acceso y el registro. En la segunda, Juan Araujo y Dario: la calidad, los envíos, los pedidos y el portal.', 'Dario también se encargó de organizar las tareas con el equipo, y fue el que armó los datos de ejemplo de café y cacao de Colombia.', 'La tabla completa, con las historias de usuario de cada tarea, está en el documento que entregamos.'], 'La tabla es pequeña, no la leas. Di el dato: siete tareas, las siete hechas.', 'Para cerrar mi parte, qué hicimos Juan Araujo y Dario.'),
    ],
    3: [
        ('pareja', 'Dos tarjetas con los nombres de los dos y, a la derecha, lo que va a decir cada uno.', ['Mi parte fue la logística: registrar los envíos, con la naviera, el número de seguimiento y las fechas de salida y de llegada.', 'Y la calidad: la catación de cada lote y los certificados, con la fecha en que se vencen.', 'También organicé las tareas del sprint con el equipo.'], 'Di tus frases seguidas, sin mirar las del compañero, y después pásale el turno.', 'Con esto terminamos. Gracias por su atención.'),
        ('estado', 'Una captura del programa: los datos importantes arriba y el recorrido del envío abajo.', ['Esto ya está funcionando, no es un dibujo. Es el programa con datos de ejemplo de café y cacao de Colombia.', 'Esta es la pantalla de entrada. Arriba están los datos más importantes: cuántos lotes hay, cuántos envíos van en camino y cuántos certificados están por vencer.', 'Abajo está el recorrido de un envío por las seis etapas, desde la finca hasta que llega al cliente. El punto naranja es por dónde va ahora.'], 'Es la primera vez que ven el programa, así que dilo con seguridad. No te disculpes.', 'Pero que funcione no es todo, por eso pusimos estas reglas.'),
        ('calidad', 'Dos listas: las reglas que el sistema no deja saltarse, y por qué importan.', ['Hay cosas que el sistema no deja hacer, para que los datos queden bien.', 'La primera: no se puede vender más café del que hay en el lote. Si alguien intenta vender de más, el sistema lo avisa.', 'La segunda: la humedad de la catación tiene que estar entre 8 y 14. Si se sale, el sistema avisa y el lote no se aprueba solo.', 'Son reglas sencillas, pero evitan que se pierdan datos.'], 'Lo importante es qué evitan las reglas, no cuántas hay. Escoge dos.', 'Y para que lo vean, se los muestro.'),
        ('demo', 'Una caja con el comando para levantar el sistema y los pasos que vas a hacer.', ['Ahora se los muestro. El sistema se levanta con un comando y cada persona del equipo tiene su cuenta, así que no hay que instalar nada.', 'Voy a hacer tres cosas: crear una finca nueva, registrar una catación de 86 puntos y ver cómo el lote queda aprobado solo, y después abrir el recorrido de un envío.'], 'No la conviertas en un recorrido largo: tres pasos. Si algo falla, di «el sistema responde» y sigue.', 'Y para cerrar:'),
        ('siguiente', 'A la izquierda lo que falta, a la derecha el cierre.', ['Nos falta el módulo de pagos, avisar por correo cuando un certificado está por vencer, y poder subir documentos al sistema.', 'Eso es lo que queda para el siguiente sprint. Gracias por su atención.'], 'Quince segundos y el «gracias». Quédate de pie para las preguntas.', 'Antes de las preguntas, digamos qué hicimos Dario y yo.'),
    ],
}

#: Qué recortar si se va con retraso, en orden.
PLAN_B = [
    'En «El problema», la tercera frase: las dos primeras ya dejan claro el asunto.',
    'En «Cómo está hecho», no leas la parte de la base de datos: la dices después.',
    'En «Los cuatro módulos», no leas la tarjeta de logística: se explica en la demostración.',
    'En «Lo que hicimos en el sprint», no leas la tabla: di el dato.',
    'En «Las reglas que pusimos», di una sola regla en vez de dos.',
]

#: Lo que conviene no hacer.
PRECAUCIONES = [
    'No leer las tablas ni los diagramas palabra por palabra: la sala no puede leer más rápido de lo que hablas.',
    'No disculparte por el prototipo. Está funcionando.',
    'Si no sabes una respuesta, di «no lo tenemos medido» y sigue. Es normal no saberlo todo.',
    'No dejar que un compañero se pase de tiempo: córtale con un «te toca».',
    'No terminar con «no hay más que decir». Cierra con el agradecimiento.',
]


#: Palabras por minuto de habla normal en una presentación de este tipo.
PALABRAS_POR_MINUTO = 160


def _cabe(frases, limite_palabras):
    """Cuántas frases caben en el límite, sin partir ninguna.

    Siempre entra al menos la primera: una diapositiva sin frases es peor que
    una diapositiva con una frase de más.
    """
    total, caben = 0, 0
    for frase in frases:
        palabras = len(frase.split())
        if caben and total + palabras > limite_palabras:
            break
        total += palabras
        caben += 1
    return caben


def guion_por_persona() -> dict:
    """Guion de cada persona, con el corte de los diez minutos ya hecho.

    Devuelve {índice: [ {clave, numero, titulo, segundos, pantalla, decir,
    ampliacion, como, puente}, … ]} en el orden en que cada uno habla.
    """
    # Segundos por diapositiva, y quién se los reparten cuando es compartida.
    reparto: dict = {}
    numero = 1
    for bloque in EXPOSICION:
        for clave, dueno, titulo, segundos, guion in bloque["diapositivas"]:
            autores = autores_de(guion)
            if dueno is not None:
                reparto[(dueno, clave)] = (numero, titulo, segundos, False)
            else:
                for a in autores:
                    reparto[(a, clave)] = (numero, titulo,
                                           segundos // len(autores), True)
            numero += 1

    detalle = {clave: entrada
               for lista in GUION_DETALLADO.values()
               for clave, entrada in
               ((e[0], {"pantalla": e[1], "decir": e[2], "como": e[3],
                        "puente": e[4]}) for e in lista)}

    salida = {}
    for i, nombre in enumerate(EQUIPO):
        entradas = []
        for clave, _p, _q, _r, guion in GUION_DETALLADO[i]:
            if (i, clave) not in reparto:
                continue
            numero, titulo, segundos, compartida = reparto[(i, clave)]
            info = detalle[clave]
            limite = max(12, int(segundos * PALABRAS_POR_MINUTO / 60))
            frases = info["decir"]
            caben = _cabe(frases, limite)
            entradas.append({
                "clave": clave,
                "numero": numero,
                "titulo": titulo,
                "segundos": segundos,
                "compartida": compartida,
                "pantalla": info["pantalla"],
                "decir": frases[:caben],
                "ampliacion": frases[caben:],
                "como": info["como"],
                "puente": info["puente"],
            })
        salida[i] = entradas
    return salida


def palabras_de_guion() -> dict:
    """Palabras que se dicen de verdad en los diez minutos, por persona."""
    conteo = {}
    for i, entradas in guion_por_persona().items():
        conteo[i] = sum(len(f.split()) for e in entradas for f in e["decir"])
    return conteo
