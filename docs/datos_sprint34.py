"""Contenido de los documentos de los Sprints 3 y 4 y del guion de exposición.

Los datos salen del código que ya está en el repositorio: modelos, rutas,
servicios y pruebas de `backend/`. Si cambia una regla, un endpoint o una tabla,
se actualiza este archivo y se regeneran los tres entregables:

    python -m docs.sprint34
    python -m docs.guion_sprint34
"""

from __future__ import annotations

from docs.nombres import EQUIPO

EMPRESA = "RiTech SAS"
PROYECTO = "Sistema de Gestión de Exportación de Café y Cacao a la Unión Europea"
FECHA = "10 de noviembre de 2026"
METODOLOGIA = "Scrum — sprints de dos semanas"

#: Nombres cortos para el guion, en el mismo orden de `EQUIPO`.
NOMBRES_CORTOS = ["Andres", "Juan Sebastian", "Juan Camilo", "Dario"]

# =========================================================================== #
# Sprint 3                                                                    #
# =========================================================================== #
SPRINT3 = {
    "numero": 3,
    "titulo": "Financiero, notificaciones y auditoría",
    "lema": "Cerrar el ciclo del dinero, avisar a tiempo y dejar rastro.",
    "periodo": "Octubre de 2026",
    "resumen": [
        "El Sprint 3 cierra el ciclo operativo de la exportación. Después de "
        "vender y despachar, el sistema registra el dinero, avisa lo que exige "
        "atención y deja constancia de las acciones críticas. Sin este sprint, "
        "la operación funcionaba pero no se podía cobrar ni responder por los "
        "cambios.",
        "Se añadieron tres tablas nuevas —`pagos`, `notificaciones` y "
        "`auditoria`— sin alterar ninguna de las nueve tablas del modelo "
        "original. La API sumó los módulos financiero, de notificaciones y de "
        "auditoría, y el frontend estrenó tres pantallas: Financiero, "
        "Notificaciones y Auditoría.",
        "Al cerrar el sprint, trece pruebas nuevas cubren los tres módulos y la "
        "suite completa queda en noventa pruebas. El cliente europeo ve su "
        "propia cartera y sus propios avisos; el administrador ve el rastro "
        "completo.",
    ],
    "objetivos": [
        "Registrar anticipos, pagos parciales, pagos finales, saldos y "
        "reembolsos por contrato, con su moneda y su método.",
        "Consolidar la cartera en EUR, incluidos los pagos recibidos en USD o "
        "COP, y detectar la cartera vencida.",
        "Generar avisos de certificaciones, envíos y saldos sin duplicarlos.",
        "Auditar accesos y cambios críticos con usuario, entidad, ruta, IP y "
        "resultado.",
        "Aislar la información del cliente europeo para que no vea datos de "
        "otros importadores.",
    ],
    "historias": [
        {
            "id": "HU-14",
            "modulo": "Financiero",
            "historia": "Como financiero quiero registrar los pagos de cada "
                        "contrato para saber cuánto ha pagado el cliente y "
                        "cuánto falta por cobrar.",
            "rol": "Financiero",
            "prioridad": "Alta",
            "estado": "Terminada",
            "criterios": [
                "Puedo registrar un anticipo, un pago parcial, un pago final, "
                "un saldo o un reembolso con fecha, método, valor y moneda.",
                "El sistema rechaza un pago que deje el contrato sobrecobrado.",
                "Un pago anulado no cuenta para la cartera.",
                "Un pago confirmado no se borra: se anula para conservar el "
                "historial.",
                "El resumen muestra contratado, cobrado, pendiente, anticipos "
                "y cartera vencida en EUR.",
                "El cliente europeo solo ve los pagos y el resumen de su "
                "empresa.",
            ],
        },
        {
            "id": "HU-16",
            "modulo": "Notificaciones",
            "historia": "Como usuario quiero recibir avisos de lo que requiere "
                        "atención para no dejar vencer una certificación ni "
                        "perder un pago.",
            "rol": "Todos los roles",
            "prioridad": "Alta",
            "estado": "Terminada",
            "criterios": [
                "La bandeja muestra los avisos dirigidos a mi cuenta, los de "
                "mi rol y los globales.",
                "Los avisos derivados de certificaciones, envíos y saldos se "
                "crean sin duplicarse.",
                "La campana muestra el número de notificaciones no leídas.",
                "Puedo marcar una notificación o todas como leídas.",
                "El cliente europeo solo ve los avisos dirigidos a su cuenta.",
            ],
        },
        {
            "id": "HU-21",
            "modulo": "Auditoría",
            "historia": "Como administrador quiero consultar quién hizo qué "
                        "para resolver una inconsistencia y responder por los "
                        "cambios.",
            "rol": "Administrador",
            "prioridad": "Alta",
            "estado": "Terminada",
            "criterios": [
                "Cada acción crítica guarda usuario, correo, acción, entidad, "
                "ruta, método, estado HTTP y fecha.",
                "El registro se escribe en la misma transacción de la "
                "operación que lo origina.",
                "Puedo filtrar por texto, acción, entidad, usuario y rango de "
                "fechas.",
                "Solo el administrador consulta el rastro completo.",
                "Si una cuenta se elimina, el correo del rastro se conserva.",
            ],
        },
    ],
    "alcance_incluye": [
        "Pagos, anticipos, saldos, reembolsos y cartas de crédito.",
        "Cartera consolidada en EUR y cartera vencida a 30 días.",
        "Bandeja de notificaciones con contador y marcado de leídas.",
        "Avisos derivados de certificaciones, envíos y saldos.",
        "Auditoría de accesos, contraseña, pagos, estados, tasas, "
        "integraciones y respaldos.",
        "Rol Financiero y pantallas de Financiero, Notificaciones y Auditoría.",
    ],
    "alcance_excluye": [
        "Pasarela de pago real y conciliación bancaria automática.",
        "Envío real de correo (se resuelve en el Sprint 4 en modo simulado).",
        "Firma electrónica de contratos.",
        "Facturación electrónica ante la DIAN.",
    ],
    "modulos": [
        {
            "nombre": "Financiero",
            "historia": "HU-14",
            "pantalla": "#/financiero",
            "que_hace": "Cartera consolidada, pagos por contrato, anticipos, "
                        "cartas de crédito, anulación con rastro y barra de "
                        "avance de cobro.",
            "roles": "Administrador y Financiero escriben; Comercial, Logística "
                     "y Cliente europeo consultan lo que les corresponde.",
        },
        {
            "nombre": "Notificaciones",
            "historia": "HU-16",
            "pantalla": "#/notificaciones",
            "que_hace": "Bandeja con avisos propios, por rol y globales; "
                        "contador en la campana; marcado individual y masivo.",
            "roles": "Todos los roles autenticados ven su bandeja. Solo el "
                     "administrador crea avisos manuales.",
        },
        {
            "nombre": "Auditoría",
            "historia": "HU-21",
            "pantalla": "#/auditoria",
            "que_hace": "Búsqueda por acción, correo, entidad o detalle y ficha "
                        "completa de cada registro.",
            "roles": "Solo el administrador.",
        },
    ],
    "tablas": [
        {
            "nombre": "pagos",
            "proposito": "Anticipos, pagos parciales, saldos y cartas de crédito "
                         "de cada contrato.",
            "campos": [
                ("id_pago", "INT", "PK"),
                ("id_exportacion", "INT", "FK → exportaciones"),
                ("id_usuario", "INT", "FK → usuarios"),
                ("fecha", "DATE", ""),
                ("tipo", "VARCHAR(50)", "anticipo, pago parcial, final, saldo, reembolso"),
                ("metodo", "VARCHAR(50)", "transferencia, carta de crédito, cheque…"),
                ("estado", "VARCHAR(50)", "registrado, confirmado o anulado"),
                ("valor", "NUMERIC(14,2)", ""),
                ("moneda", "VARCHAR(10)", "EUR, USD o COP"),
                ("referencia / banco", "VARCHAR", "opcionales"),
            ],
            "nota": "Una exportación tiene muchos pagos. El pago guarda quién lo "
                    "registró para poder auditar la operación.",
        },
        {
            "nombre": "notificaciones",
            "proposito": "Bandeja de avisos de vencimientos, envíos, pagos y "
                         "cambios de estado.",
            "campos": [
                ("id_notificacion", "INT", "PK"),
                ("id_usuario", "INT", "FK → usuarios · opcional"),
                ("rol_destino", "VARCHAR(50)", "aviso para todo un rol"),
                ("tipo", "VARCHAR(50)", "certificación, envío, pago, pedido, sistema"),
                ("tono", "VARCHAR(20)", "azul, verde, dorado o rust"),
                ("titulo / detalle", "VARCHAR / TEXT", ""),
                ("clave", "VARCHAR(160)", "única · evita duplicados"),
                ("leida", "BOOLEAN", "estado de la bandeja"),
                ("fecha", "DATETIME", ""),
            ],
            "nota": "La clave estable es lo que hace idempotente la sincronización: "
                    "dos ejecuciones del mismo hecho dejan una sola fila.",
        },
        {
            "nombre": "auditoria",
            "proposito": "Rastro de las acciones críticas del sistema.",
            "campos": [
                ("id_auditoria", "INT", "PK"),
                ("id_usuario", "INT", "FK → usuarios · SET NULL"),
                ("usuario_correo", "VARCHAR(150)", "se conserva si se borra la cuenta"),
                ("accion", "VARCHAR(100)", "qué se hizo"),
                ("entidad / id_entidad", "VARCHAR", "sobre qué se hizo"),
                ("detalle", "TEXT", "contexto legible"),
                ("metodo / ruta", "VARCHAR", "origen HTTP"),
                ("estado_http / ip", "INT / VARCHAR", ""),
                ("fecha", "DATETIME", ""),
            ],
            "nota": "No hay middleware global: cada ruta instrumentada registra la "
                    "acción en su propia transacción.",
        },
    ],
    "endpoints": [
        ("Financiero", [
            ("GET", "/api/pagos", "Lista paginada con filtros por contrato, estado, moneda y texto.", "Administrador, Financiero, Comercial, Logística y Cliente europeo"),
            ("POST", "/api/pagos", "Registra un pago y valida que no supere el saldo.", "Administrador y Financiero"),
            ("PATCH", "/api/pagos/{id}", "Corrige un pago no anulado.", "Administrador y Financiero"),
            ("POST", "/api/pagos/{id}/anular", "Anula conservando el historial.", "Administrador"),
            ("DELETE", "/api/pagos/{id}", "Elimina un pago registrado por error.", "Administrador"),
            ("GET", "/api/financiero/resumen", "Cartera, cobros, anticipos y vencimientos en EUR.", "Los mismos roles de lectura, con recorte por cliente"),
        ]),
        ("Notificaciones", [
            ("GET", "/api/notificaciones", "Bandeja del usuario, con filtro de no leídas.", "Cualquier usuario autenticado"),
            ("GET", "/api/notificaciones/contador", "Total y no leídas para la campana.", "Cualquier usuario autenticado"),
            ("POST", "/api/notificaciones/{id}/leer", "Marca una notificación como leída.", "Cualquier usuario autenticado"),
            ("POST", "/api/notificaciones/leer-todas", "Marca todas como leídas.", "Cualquier usuario autenticado"),
            ("POST", "/api/notificaciones", "Crea un aviso manual.", "Administrador"),
        ]),
        ("Auditoría", [
            ("GET", "/api/auditoria", "Listado paginado con filtros por texto, acción, entidad, usuario y fechas.", "Administrador"),
            ("GET", "/api/auditoria/{id}", "Detalle de una acción.", "Administrador"),
        ]),
    ],
    "reglas": [
        ("Un pago anulado no cuenta", "El saldo del contrato se calcula solo con pagos registrados o confirmados."),
        ("No se puede sobrecobrar", "El total cobrado, convertido a la moneda del contrato, no puede superar su valor; la tolerancia es de 0,01."),
        ("Conversión a EUR", "Cada pago se convierte con la tasa vigente y el resumen se consolida en EUR para comparar contratos en monedas distintas."),
        ("Confirmado no se borra", "Un pago confirmado se anula; así el historial y la auditoría conservan el hecho."),
        ("Contrato anulado", "Una exportación anulada no acepta pagos nuevos."),
        ("Avisos idempotentes", "Cada aviso derivado lleva una clave estable; sincronizar dos veces no duplica la bandeja."),
        ("Bandeja por destinatario", "Cada cuenta ve lo suyo, lo de su rol y lo global; el cliente europeo solo lo suyo."),
        ("Auditoría en la transacción", "Si la operación falla y hay rollback, el rastro tampoco queda."),
    ],
    "seguridad": [
        "El rol Financiero se sumó a los roles de RR-003 para separar quien vende de quien cobra.",
        "Registrar y corregir pagos exige Administrador o Financiero; anular y eliminar exige Administrador.",
        "El cliente europeo consulta pagos y resumen, pero el servidor recorta por `id_cliente` antes de aplicar filtros de la URL.",
        "La auditoría completa es solo del administrador; el resto de roles no puede listarla ni abrir un registro.",
        "El rastro guarda el correo además de la llave foránea, para que borrar una cuenta no borre la historia.",
    ],
    "pruebas": [
        ("Financiero", 7, "Pago, sobrecobro, anulación, pago confirmado, permisos, moneda extranjera y cartera aislada del cliente."),
        ("Notificaciones", 3, "Bandeja y marcado, idempotencia por clave y marcado masivo."),
        ("Auditoría", 3, "El login deja rastro, un pago queda auditado y solo el administrador consulta."),
    ],
    "pruebas_total": 13,
    "demo": [
        ("1", "Entrar como administrador", "Abrir `#/financiero`. La cartera muestra contratado, cobrado, pendiente, anticipos y cartera vencida."),
        ("2", "Registrar un anticipo", "Pulsar «Registrar pago», elegir un contrato y guardar 300 EUR. La barra de avance y el saldo cambian en el acto."),
        ("3", "Intentar un sobrecobro", "Registrar un valor mayor que el saldo: la API responde 400 y explica cuánto falta."),
        ("4", "Anular el pago", "Como administrador, anular el pago. Deja de contar para la cartera, pero sigue en el historial."),
        ("5", "Revisar la bandeja", "Abrir `#/notificaciones`. Se ven los avisos derivados; la campana muestra las no leídas."),
        ("6", "Marcar y auditar", "Marcar una notificación como leída y abrir `#/auditoria`; buscar «Registrar pago» y abrir la ficha."),
        ("7", "Entrar al portal", "Con la cuenta de cliente europeo, abrir `#/portal` y comprobar que la cartera es solo la de su empresa."),
    ],
    "resultados": [
        "Tres módulos terminados: financiero, notificaciones y auditoría.",
        "Tres tablas nuevas, sin tocar las nueve del modelo original.",
        "Trece pruebas nuevas; la suite completa queda en noventa.",
        "Cero avisos en las comprobaciones de JavaScript y referencias.",
        "Los guiones SQL de PostgreSQL y MySQL coinciden con el modelo de Python.",
    ],
    "siguiente": [
        "Multimoneda e idiomas del portal (HU-19).",
        "Integraciones externas con bitácora (HU-20).",
        "Copias de seguridad verificables (HU-22).",
        "Cierre del portal del cliente y del backlog.",
    ],
    "config": [],
}

# =========================================================================== #
# Sprint 4                                                                    #
# =========================================================================== #
SPRINT4 = {
    "numero": 4,
    "titulo": "Multimoneda, integraciones y continuidad",
    "lema": "Hablar el idioma y la moneda del cliente, y no perder la información.",
    "periodo": "Noviembre de 2026",
    "resumen": [
        "El Sprint 4 cierra el backlog. El portal del cliente pasa a hablar siete "
        "idiomas y a mostrar los importes en EUR, USD o COP con tasas que llegan "
        "de la API. El sistema gana una pantalla de integraciones para saber qué "
        "servicio está conectado y cuál está simulado, y estrena copias de "
        "seguridad verificables.",
        "Se añadieron tres tablas nuevas —`tipos_cambio`, `respaldos` y "
        "`registros_integracion`—, otra vez sin modificar las nueve tablas "
        "originales. El portal dejó de tener tasas escritas en el código: las "
        "consulta y las guarda en `localStorage` junto con el idioma.",
        "Al terminar, once pruebas nuevas cubren multimoneda, integraciones y "
        "respaldos; con las trece del Sprint 3, la suite suma noventa pruebas. "
        "Los seis elementos del backlog pendiente quedan terminados y el "
        "proyecto se entrega completo.",
    ],
    "objetivos": [
        "Guardar tipos de cambio por fecha y convertir EUR, USD y COP con una "
        "convención única.",
        "Traducir el portal a siete idiomas y formatear los importes con el "
        "locale correcto.",
        "Mostrar el estado de correo, seguimiento, tasas y almacenamiento, con "
        "bitácora de cada ejecución.",
        "Funcionar sin internet: si no hay red, las integraciones caen a un "
        "modo simulado determinista.",
        "Crear copias de seguridad JSON con SHA-256, verificables y portables "
        "entre SQLite, PostgreSQL y MySQL.",
        "Cerrar el portal y dejar el proyecto sin backlog pendiente.",
    ],
    "historias": [
        {
            "id": "HU-19",
            "modulo": "Multimoneda e idiomas",
            "historia": "Como cliente europeo quiero ver los precios en mi "
                        "moneda y en mi idioma para entender la oferta sin "
                        "hacer cuentas.",
            "rol": "Cliente europeo",
            "prioridad": "Alta",
            "estado": "Terminada",
            "criterios": [
                "El portal ofrece español, inglés, alemán, francés, italiano, "
                "neerlandés y sueco.",
                "Puedo elegir EUR, USD o COP y los importes se formatean con el "
                "locale del idioma.",
                "Las tasas se cargan desde `/api/tipos-cambio`; no hay tasas "
                "escritas en el código.",
                "La preferencia de idioma y moneda queda en `localStorage`.",
                "La convención es `tasa` = unidades de la moneda por 1 EUR.",
                "Si falta una tasa en la base, se usa el respaldo local "
                "determinista.",
            ],
        },
        {
            "id": "HU-20",
            "modulo": "Integraciones",
            "historia": "Como administrador quiero ver el estado de los "
                        "servicios externos para saber qué está conectado y "
                        "qué está simulado.",
            "rol": "Administrador",
            "prioridad": "Alta",
            "estado": "Terminada",
            "criterios": [
                "La pantalla Sistema muestra correo, seguimiento de navieras, "
                "tipos de cambio y almacenamiento documental.",
                "Cada ejecución queda en la bitácora con servicio, acción, "
                "estado, mensaje y fecha.",
                "Sin internet, las integraciones funcionan en modo simulado.",
                "La consulta de seguimiento lee el envío registrado en RiTech y "
                "no depende de la naviera.",
                "Solo el administrador prueba el correo y consulta la bitácora.",
            ],
        },
        {
            "id": "HU-22",
            "modulo": "Respaldos",
            "historia": "Como administrador quiero crear copias de seguridad "
                        "verificables para recuperar la información si algo "
                        "falla.",
            "rol": "Administrador",
            "prioridad": "Alta",
            "estado": "Terminada",
            "criterios": [
                "Cada copia es un JSON con todas las tablas del modelo.",
                "Se guardan tamaño, número de tablas, registros y SHA-256.",
                "La verificación detecta un archivo alterado o desaparecido.",
                "La copia se puede descargar desde la pantalla Sistema.",
                "Al arrancar se crea una copia automática si la última tiene "
                "más de 24 horas.",
                "El formato es portable entre SQLite, PostgreSQL y MySQL.",
            ],
        },
    ],
    "alcance_incluye": [
        "Tipos de cambio por fecha y conversión entre EUR, USD y COP.",
        "Portal en siete idiomas y tres monedas, con preferencia persistida.",
        "Estado de integraciones y bitácora de correo, seguimiento, tasas y "
        "almacenamiento.",
        "Modo simulado sin internet.",
        "Respaldos JSON con SHA-256, verificación, descarga y copia automática.",
        "Cierre del portal y del backlog del proyecto.",
    ],
    "alcance_excluye": [
        "Pasarela de pago real.",
        "Llamada real a la API de cada naviera durante la demostración.",
        "Restauración automática desde la interfaz (se entrega la copia y la "
        "verificación).",
        "Multiempresa o múltiples bases por cliente.",
    ],
    "modulos": [
        {
            "nombre": "Multimoneda e idiomas",
            "historia": "HU-19",
            "pantalla": "#/portal",
            "que_hace": "Siete idiomas, tres monedas, formato local y tasas "
                        "cargadas desde la API.",
            "roles": "Cliente europeo; el personal interno consulta tasas y "
                     "conversiones desde Sistema.",
        },
        {
            "nombre": "Integraciones",
            "historia": "HU-20",
            "pantalla": "#/sistema",
            "que_hace": "Estado de cuatro servicios, prueba de correo, consulta "
                        "de seguimiento y bitácora.",
            "roles": "Administrador y Financiero ven la pantalla; el "
                     "administrador ejecuta pruebas y ve la bitácora.",
        },
        {
            "nombre": "Respaldos",
            "historia": "HU-22",
            "pantalla": "#/sistema",
            "que_hace": "Crear, listar, verificar y descargar copias JSON con "
                        "tamaño, registros y SHA-256.",
            "roles": "Solo el administrador.",
        },
    ],
    "tablas": [
        {
            "nombre": "tipos_cambio",
            "proposito": "Tasa de cada moneda contra el euro, con fecha y fuente.",
            "campos": [
                ("id_tipo_cambio", "INT", "PK"),
                ("moneda", "VARCHAR(10)", "USD o COP"),
                ("tasa", "NUMERIC(18,6)", "unidades de la moneda por 1 EUR"),
                ("fecha", "DATE", "vigencia"),
                ("fuente", "VARCHAR(100)", "Frankfurter o respaldo local"),
                ("created_at", "DATETIME", ""),
            ],
            "nota": "La pareja (moneda, fecha) es única: actualizar dos veces el "
                    "mismo día corrige la tasa, no crea otra fila.",
        },
        {
            "nombre": "respaldos",
            "proposito": "Metadatos y huella de cada copia de seguridad.",
            "campos": [
                ("id_respaldo", "INT", "PK"),
                ("nombre", "VARCHAR(200)", "ritch-AAAAMMDD-HHMMSS.json"),
                ("ruta", "VARCHAR(400)", "ubicación del archivo"),
                ("tamano_bytes", "INT", ""),
                ("checksum", "VARCHAR(64)", "SHA-256"),
                ("tipo", "VARCHAR(50)", "manual o automática"),
                ("estado", "VARCHAR(50)", "completado, fallido o restaurado"),
                ("tablas / registros", "INT", "contenido de la copia"),
                ("id_usuario", "INT", "FK → usuarios · SET NULL"),
                ("created_at", "DATETIME", ""),
            ],
            "nota": "No es una copia del archivo del motor: es un JSON portable "
                    "que se puede inspeccionar sin la base original.",
        },
        {
            "nombre": "registros_integracion",
            "proposito": "Bitácora de los servicios externos y de las copias.",
            "campos": [
                ("id_registro", "INT", "PK"),
                ("servicio", "VARCHAR(60)", "correo, seguimiento, tasas…"),
                ("accion", "VARCHAR(100)", "qué se intentó"),
                ("estado", "VARCHAR(30)", "ok, simulado o error"),
                ("mensaje", "TEXT", "resultado legible"),
                ("detalle", "TEXT", "JSON con el contexto"),
                ("created_at", "DATETIME", ""),
            ],
            "nota": "Toda ejecución queda registrada, incluso cuando el servicio "
                    "está simulado o falla.",
        },
    ],
    "endpoints": [
        ("Multimoneda", [
            ("GET", "/api/tipos-cambio", "Última tasa conocida de cada moneda.", "Cualquier usuario autenticado"),
            ("POST", "/api/tipos-cambio", "Carga manual de una tasa; corrige la del día si ya existe.", "Administrador"),
            ("POST", "/api/tipos-cambio/actualizar", "Actualiza las tasas del día desde el proveedor o el respaldo local.", "Administrador"),
            ("GET", "/api/monedas/convertir", "Convierte un importe entre dos monedas.", "Cualquier usuario autenticado"),
        ]),
        ("Integraciones", [
            ("GET", "/api/integraciones", "Estado de los cuatro servicios.", "Administrador, Comercial, Financiero, Logística y Calidad"),
            ("POST", "/api/integraciones/correo", "Prueba de envío y registro en la bitácora.", "Administrador"),
            ("POST", "/api/integraciones/seguimiento/{numero}", "Consulta un envío registrado.", "Roles internos"),
            ("GET", "/api/integraciones/bitacora", "Últimas ejecuciones.", "Administrador"),
        ]),
        ("Respaldos", [
            ("GET", "/api/respaldos", "Lista las copias con sus metadatos.", "Administrador"),
            ("POST", "/api/respaldos", "Crea la copia JSON y calcula su SHA-256.", "Administrador"),
            ("POST", "/api/respaldos/{id}/verificar", "Recalcula el hash y lo compara con el registrado.", "Administrador"),
            ("GET", "/api/respaldos/{id}/descargar", "Descarga el archivo JSON.", "Administrador"),
        ]),
    ],
    "reglas": [
        ("Tasa por euro", "`tasa` son las unidades de la moneda por 1 EUR: 1 EUR = 1,09 USD se guarda como 1.09; 1 EUR = 4.300 COP se guarda como 4300."),
        ("Tasa vigente", "Se usa la fila más reciente de la moneda; EUR siempre vale 1."),
        ("Actualización idempotente", "La pareja (moneda, fecha) es única: dos actualizaciones del mismo día corrigen la tasa, no duplican filas."),
        ("Respaldo local", "Si `RITECH_INTEGRACIONES_RED=0` o el proveedor falla, se usan las tasas de respaldo y se registra el modo simulado."),
        ("Integraciones sin internet", "Correo y seguimiento tienen un camino simulado determinista; la bitácora guarda el intento igual."),
        ("Respaldo portable", "La copia es un JSON con todas las tablas, no el archivo del motor; funciona sobre SQLite, PostgreSQL y MySQL."),
        ("Integridad verificable", "Cada copia guarda su SHA-256; la verificación detecta cambios o desaparición del archivo."),
        ("Copia automática", "Al arrancar se crea una copia si la última tiene más de 24 horas."),
        ("Portal sin tasas fijas", "El frontend pide las tasas a la API y guarda idioma y moneda en `localStorage`."),
    ],
    "seguridad": [
        "Las tasas manuales, la prueba de correo, la bitácora y los respaldos son solo del administrador.",
        "El estado de integraciones y la consulta de seguimiento son para roles internos.",
        "Cualquier usuario autenticado puede listar tasas y convertir importes; el portal del cliente las usa para mostrar su catálogo.",
        "El respaldo se escribe en `RITECH_BACKUP_DIR`; la descarga valida que el archivo exista antes de servirlo.",
        "Las operaciones de tasas, integraciones y respaldos también dejan rastro en la auditoría del Sprint 3.",
    ],
    "pruebas": [
        ("Multimoneda", 3, "Conversión con la tasa vigente, actualización idempotente y moneda desconocida con 400."),
        ("Integraciones", 5, "Estado de servicios, correo simulado con bitácora, correo inválido, seguimiento inexistente y bitácora solo para administradores."),
        ("Respaldos", 3, "Crear, verificar y descargar; archivo borrado no es íntegro; solo el administrador respalda."),
    ],
    "pruebas_total": 11,
    "demo": [
        ("1", "Abrir Sistema", "Como administrador, abrir `#/sistema` y leer el estado de los cuatro servicios: correo, seguimiento, tasas y almacenamiento."),
        ("2", "Actualizar tasas", "Pulsar «Actualizar tasas» y luego otra vez: la segunda ejecución no duplica filas."),
        ("3", "Convertir", "Abrir «Convertir», pasar 100 EUR a USD y a COP. La tasa usada queda visible."),
        ("4", "Probar correo", "Enviar la prueba de correo y abrir la bitácora: aparece el intento en modo simulado."),
        ("5", "Consultar seguimiento", "Buscar un número de seguimiento registrado; el sistema responde con transportadora, estado y ruta."),
        ("6", "Crear respaldo", "Pulsar «Crear respaldo», verificar el SHA-256 y descargar el JSON."),
        ("7", "Cambiar el portal", "Entrar como cliente, cambiar idioma y moneda, recargar y comprobar que la preferencia se conserva y las tasas salen de la API."),
        ("8", "Cerrar con las pruebas", "Mostrar la salida de `python -m pytest -q`: noventa pruebas en verde."),
    ],
    "resultados": [
        "Seis elementos del backlog terminados: HU-14, HU-16, HU-19, HU-20, HU-21 y HU-22.",
        "Seis tablas nuevas en total entre los dos sprints, sin alterar las nueve originales.",
        "Once pruebas nuevas; veinticuatro entre Sprint 3 y Sprint 4; noventa en la suite.",
        "Portal en siete idiomas y tres monedas, con tasas dinámicas.",
        "Integraciones que funcionan sin internet y respaldos verificables.",
        "Proyecto completo: no queda backlog pendiente.",
    ],
    "siguiente": [
        "Mantenimiento: actualizar tasas y revisar la bitácora de integraciones.",
        "Operación: programar la copia automática y conservar los SHA-256.",
        "Evolución futura: pasarela de pago real, API de navieras y restauración guiada.",
    ],
    "config": [
        ("RITECH_BACKUP_DIR", "./respaldos", "Carpeta donde se escriben las copias."),
        ("RITECH_BACKUP_AUTO_HORAS", "24", "Frecuencia del respaldo automático."),
        ("RITECH_INTEGRACIONES_RED", "0", "1 = consultar el proveedor público de tasas."),
        ("RITECH_INTEGRACIONES_TIMEOUT", "4", "Segundos de espera para la red."),
        ("RITECH_DB_URL", "sqlite:///./ritch.db", "Motor y base de datos; también admite PostgreSQL y MySQL."),
    ],
}

# =========================================================================== #
# Guion de exposición                                                         #
# =========================================================================== #
GUION = {
    "titulo": "Guion de exposición · Sprints 3 y 4",
    "subtitulo": "Doce minutos, cuatro personas, dos sprints",
    "duracion": "12 minutos",
    "reparto": [
        {
            "persona": NOMBRES_CORTOS[0],
            "nombre": EQUIPO[0],
            "bloque": "Apertura y financiero",
            "inicio": "0:00",
            "fin": "3:00",
            "tema": "Contexto, Sprint 3, HU-14 y demostración de cartera.",
        },
        {
            "persona": NOMBRES_CORTOS[1],
            "nombre": EQUIPO[1],
            "bloque": "Avisos y auditoría",
            "inicio": "3:00",
            "fin": "6:00",
            "tema": "HU-16 y HU-21: bandeja, contador y rastro de acciones.",
        },
        {
            "persona": NOMBRES_CORTOS[2],
            "nombre": EQUIPO[2],
            "bloque": "Multimoneda e integraciones",
            "inicio": "6:00",
            "fin": "9:00",
            "tema": "Sprint 4, HU-19, HU-20, portal y bitácora.",
        },
        {
            "persona": NOMBRES_CORTOS[3],
            "nombre": EQUIPO[3],
            "bloque": "Respaldos y cierre",
            "inicio": "9:00",
            "fin": "12:00",
            "tema": "HU-22, demostración de respaldo, cierre y preguntas.",
        },
    ],
    "bloques": [
        {
            "persona": NOMBRES_CORTOS[0],
            "nombre": EQUIPO[0],
            "bloque": "Apertura y financiero",
            "inicio": "0:00",
            "fin": "3:00",
            "objetivo": "Ubicar al público, presentar el Sprint 3 y demostrar que "
                        "el sistema ya cobra y controla la cartera.",
            "pantalla": "Panel general y `#/financiero`.",
            "guion": [
                "Buenos días. Somos el equipo de RiTech SAS y hoy les mostramos "
                "los dos últimos sprints del sistema de exportación de café y "
                "cacao hacia la Unión Europea.",
                "En el Sprint 2 dejamos funcionando el recorrido físico: la "
                "finca, el lote, la calidad, el contrato y el envío. Faltaba lo "
                "que pasa después de vender: cobrar, avisar y responder por los "
                "cambios. Eso es el Sprint 3.",
                "El primer módulo es el financiero, la historia HU-14. Antes el "
                "sistema sabía cuánto valía un contrato, pero no cuánto se había "
                "cobrado. Ahora cada pago se registra contra un contrato, con su "
                "tipo —anticipo, pago parcial, pago final, saldo o reembolso—, "
                "su método y su moneda.",
                "En pantalla ven la cartera consolidada: contratado, cobrado, "
                "pendiente, anticipos y cartera vencida. Si el pago llega en "
                "dólares o en pesos, el sistema lo convierte con la tasa vigente "
                "y consolida todo en euros para poder comparar contratos.",
                "Hay tres reglas que nos importan. La primera: un pago anulado "
                "no cuenta para el saldo. La segunda: el total cobrado no puede "
                "superar el valor del contrato; si alguien intenta pagar de más, "
                "la API lo rechaza y dice cuánto falta. La tercera: un pago "
                "confirmado no se borra, se anula, para no perder el historial.",
                "Voy a registrar un anticipo de 300 euros. Miren cómo cambian "
                "la barra de avance y el saldo. Ahora intento un valor mayor que "
                "el pendiente: el sistema responde con el error y no deja "
                "sobrecobrar. Después lo anulo: deja de contar para la cartera, "
                "pero sigue en la lista con su estado.",
                "Un detalle de seguridad: el cliente europeo entra al portal y "
                "ve solo su propia cartera. El recorte lo hace el servidor por "
                "la empresa de la cuenta, no el navegador.",
                "Con esto el sistema ya sabe cuánto entró y cuánto falta. Pero "
                "un saldo pendiente no sirve si nadie se entera. De eso se "
                "encarga Juan Sebastian.",
            ],
            "frases": [
                "El Sprint 2 movió el producto; el Sprint 3 mueve el dinero.",
                "La cartera se consolida en euros aunque el pago llegue en otra moneda.",
                "Un pago no se borra: se anula, para conservar la historia.",
            ],
            "puente": "Un saldo pendiente no sirve si nadie se entera: pasamos a "
                      "notificaciones y auditoría.",
        },
        {
            "persona": NOMBRES_CORTOS[1],
            "nombre": EQUIPO[1],
            "bloque": "Avisos y auditoría",
            "inicio": "3:00",
            "fin": "6:00",
            "objetivo": "Mostrar que el sistema avisa a tiempo y que toda acción "
                        "crítica deja un rastro consultable.",
            "pantalla": "`#/notificaciones`, campana de la cabecera y `#/auditoria`.",
            "guion": [
                "Gracias, Andres. Yo sigo con las otras dos historias del "
                "Sprint 3: notificaciones y auditoría.",
                "La historia HU-16 nació de un problema concreto: una "
                "certificación puede vencer sin que nadie se dé cuenta, un envío "
                "puede quedar demorado y un contrato puede seguir con saldo. La "
                "bandeja reúne esos tres mundos en un solo lugar.",
                "Los avisos se generan de dos formas. Unos son derivados: el "
                "sistema revisa certificaciones próximas a vencer, envíos con "
                "incidencia y contratos con saldo pendiente. Otros son directos: "
                "al registrar un pago o cambiar el estado de un pedido, la misma "
                "operación crea el aviso.",
                "Lo importante es que no se duplican. Cada aviso derivado lleva "
                "una clave estable; si la sincronización corre dos veces, la "
                "segunda no crea otra fila. La campana de la cabecera muestra "
                "cuántas no se han leído, y desde la bandeja puedo marcar una o "
                "todas.",
                "Cada cuenta ve lo suyo, lo de su rol y los avisos globales. El "
                "cliente europeo es la excepción: solo ve los avisos dirigidos a "
                "su cuenta, nunca los del personal de RiTech.",
                "La segunda historia es la HU-21, auditoría. Como administrador "
                "necesito responder quién hizo qué, sobre qué entidad, desde qué "
                "ruta y con qué resultado. Cada acción crítica guarda el usuario, "
                "su correo, la acción, la entidad, el método HTTP, la ruta, el "
                "estado y la fecha.",
                "El rastro se escribe en la misma transacción de la operación. "
                "Eso significa que si la operación falla y hay rollback, el "
                "registro tampoco queda: no hay auditoría de cosas que no "
                "pasaron. Y si una cuenta se elimina, el correo se conserva para "
                "no perder la historia.",
                "Voy a mostrar la bandeja, marcar un aviso como leído y abrir "
                "auditoría. Busco «Registrar pago» y abro la ficha: ahí están el "
                "usuario, la ruta, el estado y el detalle. Solo el administrador "
                "puede ver esta pantalla.",
                "Con esto el Sprint 3 queda cerrado: el sistema cobra, avisa y "
                "deja rastro. Ahora Juan Camilo les cuenta cómo el Sprint 4 "
                "lleva todo esto al idioma y a la moneda del cliente.",
            ],
            "frases": [
                "La clave estable es lo que evita que la bandeja se llene de repetidos.",
                "Cada cuenta ve lo suyo, lo de su rol y lo global.",
                "La auditoría se escribe en la misma transacción: si falla la operación, no queda el rastro.",
            ],
            "puente": "El Sprint 3 deja el dinero y los avisos en orden; el "
                      "Sprint 4 los pone en el idioma y la moneda del cliente.",
        },
        {
            "persona": NOMBRES_CORTOS[2],
            "nombre": EQUIPO[2],
            "bloque": "Multimoneda e integraciones",
            "inicio": "6:00",
            "fin": "9:00",
            "objetivo": "Demostrar el portal multilingüe y multimoneda y la "
                        "pantalla de integraciones con su bitácora.",
            "pantalla": "`#/sistema` y `#/portal`.",
            "guion": [
                "Gracias, Juan Sebastian. Yo abro el Sprint 4, que tiene dos "
                "frentes: hablar el idioma del cliente y conectarse con el mundo "
                "sin depender de internet.",
                "La historia HU-19 es la multimoneda y los idiomas. El portal "
                "está en español, inglés, alemán, francés, italiano, neerlandés "
                "y sueco. El cliente elige idioma y moneda —EUR, USD o COP— y la "
                "preferencia queda guardada en su navegador, así que al volver "
                "la encuentra igual.",
                "Un cambio importante: antes las tasas estaban escritas en el "
                "código. Ahora el portal las pide a `/api/tipos-cambio`. La "
                "convención es una sola: la tasa son las unidades de la moneda "
                "por un euro. Si un euro vale 1,09 dólares, la tasa del dólar es "
                "1,09; si vale 4.300 pesos, la tasa del peso es 4.300.",
                "En la pantalla Sistema pueden ver las tasas vigentes, cargar "
                "una manual o actualizarlas. La actualización es idempotente por "
                "moneda y fecha: si se corre dos veces el mismo día, corrige la "
                "tasa, no duplica la fila. Si no hay red, usa las tasas de "
                "respaldo y lo deja anotado.",
                "El otro frente es la historia HU-20, integraciones. El sistema "
                "trabaja con cuatro servicios: correo, seguimiento de navieras, "
                "tipos de cambio y almacenamiento documental. La pantalla dice "
                "cuál está operativo, cuál está simulado y cuándo fue la última "
                "ejecución.",
                "Cada intento queda en la bitácora: qué servicio, qué acción, "
                "qué resultado y cuándo. Eso es clave para una demostración: no "
                "necesitamos internet. Si el correo real no está configurado, se "
                "simula y la bitácora muestra el intento. Si el número de "
                "seguimiento no existe, también queda registrado como error.",
                "Voy a actualizar las tasas, convertir 100 euros a dólares y a "
                "pesos, probar el correo y consultar un envío. Después entro al "
                "portal, cambio el idioma a inglés y la moneda a dólares: los "
                "importes se formatean con el locale y las tasas siguen saliendo "
                "de la API.",
                "Con esto el portal queda cerrado y las integraciones quedan "
                "visibles. Falta lo que sostiene todo: poder recuperar la "
                "información si algo falla. De eso se encarga Dario.",
            ],
            "frases": [
                "La tasa siempre significa unidades de la moneda por un euro.",
                "Sin internet, la integración se simula y la bitácora guarda el intento.",
                "El portal no tiene tasas escritas: las pide a la API.",
            ],
            "puente": "Un sistema que cobra, avisa y habla varios idiomas "
                      "necesita una red de seguridad: los respaldos.",
        },
        {
            "persona": NOMBRES_CORTOS[3],
            "nombre": EQUIPO[3],
            "bloque": "Respaldos y cierre",
            "inicio": "9:00",
            "fin": "12:00",
            "objetivo": "Cerrar con la historia HU-22, la demostración del "
                        "respaldo verificable y el estado final del proyecto.",
            "pantalla": "`#/sistema`, sección Respaldos, y salida de pruebas.",
            "guion": [
                "Gracias, Juan Camilo. Cierro yo con la historia HU-22, copias "
                "de seguridad, y con el estado final del proyecto.",
                "Una copia de seguridad no sirve si no se puede comprobar. Por "
                "eso cada respaldo es un archivo JSON con todas las tablas, y "
                "además guarda su tamaño, cuántas tablas y registros contiene y "
                "un SHA-256, que es una huella digital del archivo.",
                "Elegimos JSON y no una copia del archivo de SQLite por una "
                "razón de portabilidad: el mismo respaldo funciona sobre SQLite, "
                "PostgreSQL y MySQL, que es lo que pide el requisito de base de "
                "datos. Y se puede abrir y revisar sin el motor original.",
                "La verificación vuelve a calcular el SHA-256 y lo compara con "
                "el registrado. Si el archivo cambió o desapareció, lo dice. "
                "También podemos descargarlo desde la pantalla Sistema. Al "
                "arrancar la API se crea una copia automática si la última tiene "
                "más de 24 horas.",
                "Voy a crear un respaldo, verificar que está íntegro y "
                "descargarlo. Luego muestro que la suite completa pasa: noventa "
                "pruebas, de las cuales veinticuatro son de estos dos sprints.",
                "Con esto terminamos los seis elementos que quedaban del "
                "backlog: pagos, notificaciones, auditoría, multimoneda, "
                "integraciones y respaldos. El proyecto queda completo y "
                "funcionando sin internet para la demostración.",
                "Tres ideas para llevarse: el sistema no solo registra la "
                "operación, también la puede explicar; funciona en el idioma y "
                "la moneda del cliente; y deja una copia verificable de todo. "
                "Gracias. Quedamos atentos a sus preguntas.",
            ],
            "frases": [
                "Un respaldo sin verificación es solo un archivo con suerte.",
                "El JSON es portable: el mismo respaldo sirve en SQLite, PostgreSQL y MySQL.",
                "Noventa pruebas en verde y seis historias cerradas: el proyecto queda completo.",
            ],
            "puente": "Con esto cerramos los dos sprints y el proyecto. Gracias; "
                      "abrimos preguntas.",
        },
    ],
    "demo_orden": [
        ("1", "0:40", "Financiero", "Registrar un anticipo y mostrar cómo cambia la cartera.", "Andres"),
        ("2", "1:40", "Financiero", "Intentar un sobrecobro y anular el pago.", "Andres"),
        ("3", "3:20", "Notificaciones", "Abrir la bandeja, marcar una leída y mostrar la campana.", "Juan Sebastian"),
        ("4", "4:40", "Auditoría", "Buscar «Registrar pago» y abrir la ficha.", "Juan Sebastian"),
        ("5", "6:20", "Sistema", "Actualizar tasas y convertir 100 EUR a USD y COP.", "Juan Camilo"),
        ("6", "7:30", "Sistema", "Probar correo, consultar seguimiento y abrir la bitácora.", "Juan Camilo"),
        ("7", "8:20", "Portal", "Cambiar idioma y moneda, recargar y ver la preferencia.", "Juan Camilo"),
        ("8", "9:20", "Sistema", "Crear respaldo, verificar SHA-256 y descargar.", "Dario"),
        ("9", "10:40", "Cierre", "Mostrar la salida de las noventa pruebas y cerrar.", "Dario"),
    ],
    "checklist": [
        "Sembrar la base con `cd backend && python -m app.seed --reset`.",
        "Levantar la API con `uvicorn app.main:app --reload` y abrir el frontend.",
        "Tener dos pestañas: una con el administrador y otra con el cliente europeo.",
        "Verificar que la pantalla Financiero tenga al menos un contrato con saldo.",
        "Tener a mano un número de seguimiento de la base sembrada.",
        "Confirmar que `RITECH_BACKUP_DIR` apunte a una carpeta con permisos de escritura.",
        "Cerrar notificaciones y correo del sistema para que no tapen la pantalla.",
        "Ensayar una vez con cronómetro: cada persona tiene tres minutos.",
    ],
    "credenciales": [
        ("Administrador", "andres.villavicencio@ritch.com", "RiTech2026*"),
        ("Administrador", "juan.iguia@ritch.com", "RiTech2026*"),
        ("Comercial", "juan.araujo@ritch.com", "RiTech2026*"),
        ("Logística", "dario.paz@ritch.com", "RiTech2026*"),
        ("Cliente europeo", "comprador@cafe-rotterdam.nl", "ClienteUE2026*"),
    ],
    "preguntas": [
        ("¿Por qué el resumen financiero se muestra en euros?",
         "Porque los contratos pueden estar en monedas distintas y, para comparar "
         "cartera y cartera vencida, hace falta una unidad común. Cada pago se "
         "convierte con la tasa vigente y el detalle por moneda queda visible."),
        ("¿Qué pasa si se registra dos veces el mismo pago?",
         "El sistema no tiene una clave única por referencia bancaria; por eso el "
         "administrador puede anular el duplicado. La anulación no borra: deja el "
         "pago en el historial y lo saca del saldo."),
        ("¿Las notificaciones se pueden duplicar?",
         "No. Los avisos derivados llevan una clave estable construida con el "
         "hecho que los origina; si la sincronización corre otra vez, encuentra la "
         "clave y no crea una fila nueva."),
        ("¿Por qué las integraciones funcionan sin internet?",
         "Porque la demostración no puede depender de la red. Cada servicio tiene "
         "un modo simulado determinista y deja el mismo rastro en la bitácora; si "
         "se configura la red, usa el servicio real."),
        ("¿Por qué el respaldo es JSON y no una copia de SQLite?",
         "Porque el proyecto debe funcionar sobre SQLite, PostgreSQL y MySQL. Un "
         "JSON con todas las tablas es portable, se puede inspeccionar y su "
         "SHA-256 permite verificar que nadie lo cambió."),
        ("¿La auditoría se puede borrar?",
         "Solo el administrador la consulta, y no hay un endpoint para borrarla. "
         "Si se elimina una cuenta, el registro conserva el correo; la llave "
         "foránea queda en NULL para no perder la historia."),
        ("¿El cliente europeo puede ver datos de otros clientes?",
         "No. El servidor recorta pagos, resumen, notificaciones y portal por la "
         "empresa de la cuenta antes de aplicar filtros de la URL. Abrir un "
         "recurso ajeno responde 404."),
    ],
    "consejos": [
        "No leer el guion palabra por palabra: cada bloque tiene la idea y las frases clave.",
        "Señalar la pantalla mientras se habla; el público sigue mejor una demostración que una lista.",
        "Si una demo falla, seguir con la siguiente: la bitácora y las pruebas también cuentan la historia.",
        "Respetar el minuto de cierre: el espacio para preguntas vale tanto como la demostración.",
        "Tener la salida de `python -m pytest -q` lista por si alguien pide evidencia.",
    ],
}
