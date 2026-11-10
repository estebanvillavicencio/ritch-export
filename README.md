# RiTech SAS — Sistema de Gestión de Exportación de Café y Cacao a la Unión Europea

Software empresarial para la gestión integral de las exportaciones de café y cacao
hacia la Unión Europea. Cubre los **Sprints 2, 3 y 4** de la planificación Scrum de
RiTech SAS:

- **Sprint 2** — Productores, fincas y lotes · Calidad · Comercial · Logística,
  más el armazón de usuarios y roles del que dependen.
- **Sprint 3** — Financiero y cartera (HU-14) · Notificaciones (HU-16) ·
  Auditoría (HU-21).
- **Sprint 4** — Multimoneda (HU-19) · Integraciones (HU-20) · Copias de
  seguridad (HU-22) · Cierre del portal del cliente.
- **Portal del cliente** — El comprador europeo puede enviar solicitudes de
  pedido de café o cacao; el equipo comercial las revisa desde su módulo.

Todo el diseño (paleta, tipografías, barra lateral, tarjetas KPI, línea de tiempo
de envíos, ticket de «Ficha de lote» y barras de cumplimiento) reproduce el
mockup `mockup-ritech-export-2.html`.

---

## 1. Puesta en marcha

```bash
cd backend
python -m pip install -r requirements.txt

# 1) Preparar la base y cargar datos de demostración
python -m app.seed --reset

# 2) Levantar la aplicación
uvicorn app.main:app --reload
```

O, más fácil y sin acordarse de la carpeta, desde la raíz del proyecto:

```bash
python tools/levantar.py            # solo en tu computador
python tools/levantar.py --tunel    # además, con enlace público para compartir
python tools/bajar.py               # apagar todo
```

`levantar.py` deja los procesos en segundo plano, escribe el registro en
`tools/logs/` y guarda sus identificadores, para que `bajar.py` los apague. Se
puede correr las veces que haga falta: si el puerto 8000 ya está ocupado, lo dice
y no toca el proceso que encontró.

### Que la página no se caiga

El enlace público de Cloudflare es **temporal**: se cae si el equipo se suspende,
si se reinicia o si se corta la red. Para que eso no haya que resolverlo a mano
en medio de la demostración, está el vigilante:

```bash
python tools/vigilante.py --arrancar   # lo enciende ahora
python tools/vigilante.py --instalar   # lo deja arrancando al iniciar sesión
```

Cada 20 segundos comprueba que la API responda y que el túnel esté vivo, y los
vuelve a levantar si no lo están. Medido: con la API y el túnel matados a la
vez, tardó **91 segundos** en dejar todo de nuevo funcionando.

El enlace de siempre se puede ver en un solo lugar:

```
tools/logs/enlace.txt
```

Y el registro de todo lo que hizo, en `tools/logs/vigilante.log`.

**Aviso importante:** el enlace **cambia cada vez que se crea un túnel nuevo**,
porque es un enlace temporal de los que da Cloudflare sin cuenta. Para que fuera
fijo hace falta alojar la aplicación en un servicio de verdad; eso está
explicado paso a paso en **[PUBLICAR.md](PUBLICAR.md)**, con Render y con
PythonAnywhere. Si la presentación es en el salón, **usa
`http://localhost:8000`**: no depende de internet, no cambia nunca y arranca al
instante.

Los archivos que el servicio necesita ya están en el repositorio
(`requirements.txt`, `render.yaml`, `Procfile`, `runtime.txt`, `wsgi.py`), así que
no hay nada que preparar.

### Desde Visual Studio Code

La carpeta trae `.vscode/`, así que el proyecto corre sin configurar nada:

| Atajo | Qué hace |
|---|---|
| **F5** | Levanta la aplicación y muestra el enlace público |
| **Ctrl+Shift+B** | Menú de tareas: levantar, apagar, pruebas, regenerar entregables |
| **F5** con otro nombre | Correr un solo archivo, las pruebas, o la app sin enlace |

Para elegir cuál de las cuatro opciones de F5: panel **Ejecutar y depurar**
(Ctrl+Shift+D), la flechita al lado de F5, o el archivo `.vscode/launch.json`.

| Dirección | Qué es |
|---|---|
| http://127.0.0.1:8000/ | Aplicación interna de RiTech SAS |
| http://127.0.0.1:8000/#/portal | Portal del cliente europeo |
| http://127.0.0.1:8000/api/docs | Documentación interactiva (OpenAPI) |

La aplicación es de una sola página y usa rutas con `#`: siempre
`http://127.0.0.1:8000/`, y lo que cambia es lo que va después del `#`.

### Cuentas de demostración

En local, la contraseña inicial del equipo es **`RiTech2026*`**:

| Correo | Rol | Alcance |
|---|---|---|
| `andres.villavicencio@ritch.com` | Administrador | Acceso completo |
| `juan.iguia@ritch.com` | Administrador | Base de datos y registro |
| `juan.araujo@ritch.com` | Comercial | Clientes, cotizaciones, pedidos |
| `dario.paz@ritch.com` | Logística | Envíos, contenedores, seguimiento |

La cuenta local del comprador europeo es:

| Correo | Clave | Empresa |
|---|---|---|
| `comprador@cafe-rotterdam.nl` | `ClienteUE2026*` | Café Rotterdam BV |

```bash
python tools/crear_cuenta_comprador.py
```

La pantalla pública de inicio de sesión no muestra accesos rápidos ni contraseñas.
En Render, las contraseñas iniciales se generan como secretos separados para el
equipo y el comprador (`RITECH_DEMO_PASSWORD` y `RITECH_BUYER_PASSWORD`). La cuenta
del comprador ve únicamente los pedidos y envíos de su empresa.

### Configuración

La aplicación lee las variables de entorno de `.env` (ver `.env.example`).
Por defecto usa **SQLite** para que funcione sin instalar nada; para PostgreSQL:

```bash
RITECH_DB_URL=postgresql+psycopg://ritch:ritch@localhost:5432/ritch
```

El esquema también está disponible como DDL en `sql/`. Los dos archivos están
sincronizados con el modelo de Python, y `python tools/verificar_sql.py` lo
comprueba tabla por tabla.

### Migraciones del esquema

`create_all()` crea las tablas que faltan, pero no altera las que ya existen. Si
se añade una columna al modelo y se arranca con una base de una corrida
anterior, el primer INSERT falla con un error del motor que no señala el código.
Para eso está `app/migraciones.py`, que se corre solo al arrancar la API:

```bash
cd backend
python -m app.migraciones
```

Cada migración mira primero si hace falta, así que no hay que llevar la cuenta.

### Pruebas

```bash
cd backend
python -m pytest
```

90 pruebas que recorren los módulos de los tres sprints: autenticación y roles,
control de inventario, cadena de estados, certificaciones (incluido el
georreferenciamiento del EUDR), trazabilidad, sincronización de envíos, KPIs, el
portal del cliente europeo, pagos y cartera, notificaciones, auditoría,
multimoneda, integraciones y copias de seguridad. Corren contra una base SQLite
temporal, así que no requieren ningún servidor.

---

## 2. Arquitectura

```
ritch-export/
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI, CORS y servicio del frontend
│   │   ├── config.py          Configuración (pydantic-settings)
│   │   ├── database.py        Motor, sesión y base declarativa
│   │   ├── security.py        bcrypt + JWT
│   │   ├── seed.py            Datos de demostración
│   │   ├── models/
│   │   │   ├── enums.py       Roles, estados y dominios (VARCHAR + CHECK)
│   │   │   ├── core.py        Las nueve tablas del modelo de datos
│   │   │   ├── sprint2.py     Extensiones de los módulos del Sprint 2
│   │   │   └── sprint3.py     Pagos, avisos, auditoría, monedas, respaldos
│   │   ├── schemas/           Contratos de entrada y salida (Pydantic v2)
│   │   ├── services/
│   │   │   ├── reglas.py      Correlativos, inventario, estados, trazabilidad
│   │   │   ├── indicadores.py KPIs y agregados del panel
│   │   │   ├── financiero.py  Saldos, cobros y cartera en EUR
│   │   │   ├── notificaciones.py  Avisos derivados y bandeja por rol
│   │   │   ├── auditoria.py   Registro de acciones críticas
│   │   │   ├── monedas.py     Tipos de cambio y conversión
│   │   │   ├── integraciones.py   Correo, seguimiento y bitácora
│   │   │   └── respaldos.py   Instantáneas JSON con SHA-256
│   │   └── api/routes/        Endpoints agrupados por módulo
│   ├── tests/                 pytest
│   └── requirements.txt
├── frontend/                  SPA sin paso de compilación (ES Modules)
│   ├── index.html             Aplicación de una sola página
│   ├── css/ritch.css          Sistema de diseño
│   └── js/
│       ├── api.js             Cliente REST + sesión
│       ├── ui.js              Componentes, formato, iconos
│       ├── app.js             Armazón y enrutado
│       ├── login.js           Inicio de sesión
│       └── views/             panel · lotes · comercial · logistica ·
│                              financiero · notificaciones · auditoria ·
│                              sistema · usuarios · portal
├── tools/                     Comprobaciones y utilidades
│   ├── levantar.py            Levanta la API y, con --tunel, el enlace público
│   ├── vigilante.py           Los deja siempre arriba; --instalar los autoarranca
│   ├── bajar.py                Apaga lo que se levantó
│   ├── demostrar_reglas.py     Corre las tres reglas de negocio, en vivo
│   ├── check_js.py            Sintaxis y referencias del JavaScript
│   ├── check_refs.py          Imports de los módulos JS
│   ├── verificar_sql.py       El .sql coincide con el modelo de Python
│   ├── verificar_portal.py    El cliente ve solo su empresa
│   ├── crear_cuenta_comprador.py  Crea otra cuenta de cliente europeo
│   ├── probar_sql_mysql.py    Carga schema_mysql.sql en el MySQL local
│   └── empaquetar.py          Arma el zip del proyecto
├── .vscode/                   Configuración de depuración (F5 y Ctrl+Shift+B)
├── wsgi.py                    Punto de entrada WSGI para hosting sin servidor
├── render.yaml                Configuración del servicio en Render
├── Procfile                   Para Railway / Heroku
├── requirements.txt           Lo que instala el hosting
└── sql/
    ├── schema_postgres.sql    DDL para PostgreSQL (RR-003)
    └── schema_mysql.sql       DDL para MySQL 8
```

**Petición → ruta → servicio → modelo.** Las rutas validan con Pydantic y
resuelven permisos; la lógica de negocio vive en `services/`; `models/` solo
describe la base de datos. Ninguna ruta escribe SQL.

---

## 3. Modelo de datos

Las **nueve tablas** del documento *RiTech_Base_datos_relaciones_equipo_APIs*,
con sus relaciones intactas:

```
fincas        1 ──< lotes        >── 1 productos
clientes      1 ──< exportaciones >── 1 usuarios
usuarios      1 ──< clientes     (solo las cuentas de cliente europeo)
exportaciones 1 ──< detalle_exportacion >── 1 lotes
exportaciones 1 ──< documentos_exportacion
exportaciones 1 ──< envios
```

`usuarios.id_cliente` es la columna que hace que el portal del cliente europeo
muestre únicamente lo suyo: dice de qué empresa es la cuenta, y el servidor
recorta con ella las consultas de exportaciones y envíos. El personal de RiTech
la deja en NULL.

Los módulos del Sprint 2 necesitan registrar datos que no caben en esas nueve
tablas, así que se añaden como **extensiones**, sin alterar el modelo original:

| Tabla | Módulo | Por qué |
|---|---|---|
| `calidad_lote` | Calidad | Humedad, puntaje de cata, actividad de agua (HU-17) |
| `certificaciones` | Cumplimiento | EUDR, orgánico, Fairtrade, fitosanitario con emisión y vencimiento |
| `eventos_trazabilidad` | Trazabilidad | Hitos finca → beneficio → puerto → tránsito → aduana → cliente (HU-06) |
| `cotizaciones` | Comercial | Cotizaciones en distintas monedas e Incoterms (HU-08) |
| `contenedores` | Logística | Códigos, capacidad y navieras (HU-12) |
| `pagos` | Financiero | Anticipos, pagos parciales, saldos y cartas de crédito (HU-14) |
| `notificaciones` | Notificaciones | Bandeja de vencimientos y cambios de estado, idempotente por `clave` (HU-16) |
| `auditoria` | Seguridad | Quién hizo qué, sobre qué entidad, desde qué ruta e IP (HU-21) |
| `tipos_cambio` | Multimoneda | Unidades de cada moneda por 1 EUR, con fuente y fecha (HU-19) |
| `respaldos` | Continuidad | Metadatos, tamaño y SHA-256 de cada copia (HU-22) |
| `registros_integracion` | Integraciones | Bitácora de correo, seguimiento y actualización de tasas (HU-20) |

**Sobre el motor.** RR-003 exige PostgreSQL, mientras que el documento de base
de datos menciona MySQL. El modelo se escribió con tipos portables y se
entregan los dos DDL: `sql/schema_postgres.sql` (producción) y
`sql/schema_mysql.sql` (por si se prefiere el motor del documento). Los
dominios se guardan como `VARCHAR` + `CHECK`, nunca como tipo `ENUM` nativo, para
que el esquema sea idéntico en ambos motores y las migraciones no dependan del
motor.

---

## 4. Reglas de negocio

Implementadas en `services/reglas.py` y cubiertas por pruebas:

- **Códigos correlativos.** `CO-HUI-AAAA-NNNN` para lotes, `CT-…` para
  contratos, `QT-…` para cotizaciones. El correlativo se calcula en Python para no
  depender de funciones de cadenas del motor.
- **Inventario (HU-05).** `disponible_kg = cantidad_kg − Σ comprometido`. Anular
  una exportación libera el inventario; reducir un lote por debajo de lo
  comprometido se rechaza.
- **Lotes y trazabilidad (HU-06).** Crear un lote registra automáticamente el hito
  «Finca». La línea de tiempo marca la primera etapa sin registro como *actual*.
- **Cadena de estados (Informe §6.9).** `Pedido recibido → En preparación →
  En producción → En puerto → En tránsito → En destino → Entregado`. Solo se
  admite avanzar o retroceder un paso, y anular antes de entrar en producción.
- **Calidad (HU-17).** El estado del lote se deriva de la catación y la humedad:
  Special (≥ 85) con responsable → Aprobado; 80–84.99 con humedad ≤ 12 % →
  Aprobado; 60–79.99 → Con reserva. La humedad se valida entre 8 % y 14 %.
- **Certificaciones (Informe §6.4).** El estado se deriva de las fechas
  (Vigente / Por renovar a 45 días / Vencida). **El EUDR solo cuenta si el lote
  está georreferenciado**, por eso el panel lo refleja en las barras de
  cumplimiento.
- **Envíos (HU-12).** Crear o actualizar un envío sincroniza el estado de la
  exportación; un contenedor no puede asignarse si la exportación pesa más que su
  capacidad; la llegada nunca puede ser anterior a la salida.
- **Documentos (HU-10).** Solo los documentos emitidos o validados pueden
  autorizarse para el portal del cliente.
- **Pagos y cartera (HU-14).** Un pago anulado no cuenta para el saldo; el total
  cobrado no puede superar el valor del contrato; los pagos en otra moneda se
  convierten con el tipo de cambio vigente y el resumen se consolida en EUR. Un
  pago confirmado se anula, no se borra.
- **Notificaciones (HU-16).** Los avisos derivados (certificaciones por vencer,
  envíos con incidencia y saldos pendientes) se sincronizan de forma idempotente
  con una clave estable; cada cuenta ve los suyos, los de su rol y los globales.
- **Auditoría (HU-21).** Los accesos, cambios de contraseña, pagos, cambios de
  estado, tipos de cambio, integraciones y respaldos dejan rastro en la misma
  transacción de la operación.
- **Multimoneda (HU-19).** `tasa` son las unidades de la moneda por 1 EUR. El
  portal carga las tasas desde la API —nunca desde el código— y permite elegir
  entre siete idiomas y EUR/USD/COP.
- **Integraciones (HU-20).** Funcionan sin internet: si no hay red o el servicio
  no está configurado, se usa un modo simulado determinista y la bitácora
  registra el intento con su resultado.
- **Respaldos (HU-22).** Cada copia es una instantánea JSON portable (SQLite,
  PostgreSQL o MySQL) con tamaño y SHA-256; la verificación detecta archivos
  alterados o desaparecidos. Al arrancar se crea una copia automática si la
  última tiene más de 24 horas.

---

## 5. Seguridad

- Contraseñas con **bcrypt** (coste 12); nunca se almacenan en claro.
- Sesión con **JWT** firmado (HS256) que incluye id, rol y correo.
- **RBAC por rol** (RR-004): Administrador, Comercial, Logística, Calidad,
  Financiero y Cliente europeo. Cada endpoint declara a qué roles accede.
- El login responde siempre lo mismo ante correo inexistente o contraseña
  incorrecta, para no revelar qué cuentas existen.
- Los usuarios no se borran: se les cambia el estado, conservando la
  trazabilidad de las exportaciones que registraron.
- Un administrador no puede degradar su propio rol ni desactivar su cuenta.
- Auditoría de acciones críticas en la tabla `auditoria` (HU-21): accesos,
  cambios de contraseña, pagos, estados, tasas, integraciones y respaldos. Solo
  el administrador consulta el rastro completo.

---

## 6. Trazabilidad de los requisitos

| Historia | Módulo | Dónde |
|---|---|---|
| HU-01, HU-02 | Usuarios y roles | `api/routes/usuarios.py`, `auth.py` |
| HU-03 | Comercial · clientes | `api/routes/catalogos.py` |
| HU-04 | Productores · fincas | `api/routes/catalogos.py`, vista `lotes.js` |
| HU-05 | Productores · lotes e inventario | `api/routes/operacion.py` |
| HU-06 | Trazabilidad | `api/routes/operacion.py`, `services/reglas.py` |
| HU-07, HU-17 | Cumplimiento y calidad | `api/routes/operacion.py` |
| HU-08 | Comercial · cotizaciones | `api/routes/comercial.py` |
| HU-09 | Comercial · pedidos | `api/routes/comercial.py` |
| HU-10 | Documentación | `api/routes/comercial.py` |
| HU-11, HU-12, HU-13 | Logística | `api/routes/logistica.py` |
| HU-14 | Financiero · pagos y cartera | `api/routes/financiero.py`, `services/financiero.py`, vista `financiero.js` |
| HU-15 | Reportes y KPIs | `api/routes/panel.py`, `services/indicadores.py` |
| HU-16 | Notificaciones | `api/routes/notificaciones.py`, `services/notificaciones.py` |
| HU-18 | Portal cliente UE | `views/portal.js`, `portal.html` |
| HU-19 | Multimoneda e idiomas | `api/routes/sistema.py`, `services/monedas.py`, `views/portal.js` |
| HU-20 | Integraciones externas | `api/routes/sistema.py`, `services/integraciones.py` |
| HU-21 | Auditoría | `api/routes/auditoria.py`, `services/auditoria.py`, vista `auditoria.js` |
| HU-22 | Copias de seguridad | `api/routes/sistema.py`, `services/respaldos.py` |
| RF-001…RF-009 | — | `api/routes/` |
| RNF-001…RNF-005 | — | `security.py`, `deps.py`, `main.py` |
| RR-003, RR-004, RR-005 | — | `sql/`, `deps.py`, enums |

Con esto queda cubierto el backlog pendiente: pagos, notificaciones,
multilenguaje y multimoneda, integraciones, auditoría y copias de seguridad.

---

## 7. Desviaciones respecto de los documentos

Son deliberadas y estão argumentadas:

1. **Stack.** RR-002 fija React + TypeScript + Tailwind y NestJS. Aquí se usa
   **Python (FastAPI + SQLAlchemy + PostgreSQL)** porque es el único runtime
   disponible en el equipo de desarrollo; el frontend es una SPA de ES Modules sin
   compilación. La API REST, el modelo y los nombres de las tablas sí respetan el
   documento.

2. **Motor de base de datos.** Se entrega el modelo de nueve tablas del documento
   de base de datos, y los dos DDL, para no elegir entre PostgreSQL (RR-003) y
   MySQL.

3. **Interfaz.** React y Tailwind se sustituyen por DOM nativo y una hoja de
   estilos que reproduce el mockup. El sistema de diseño (colores, tipografías,
   medidas) es el del mockup, de modo que al migrar a React el resultado visual no
   cambia.

4. **Alcance.** Los tres sprints planificados: los cuatro módulos operativos del
   Sprint 2, el cierre financiero y de gobierno del Sprint 3, y las integraciones,
   la multimoneda y la continuidad del Sprint 4. El panel general y el control de
   acceso se incluyen porque todas las pantallas dependen de ellos.

---

## 8. Utilidades de verificación

El frontend no tiene paso de compilación, así que se acompañan de dos
comprobaciones estáticas que se ejecutan sin Node:

```bash
python tools/check_js.py     # sintaxis, símbolos importados, métodos de la API
python tools/check_refs.py   # referencias sin resolver
```

Y en `backend/` hay un listado de la API para revisar qué expone el servicio:

```bash
cd backend && python listar_rutas.py
```

La primera comprueba que todo `api.<ns>.<método>()` exista realmente en
`api.js` y que cada símbolo importado se exporte en su módulo; la segunda detecta
identificadores usados pero no definidos, el tipo de fallo que en el navegador se
manifiesta como *«X is not defined»*.

---

## 9. Documentación del Sprint 2

En `docs/` están los generadores de los dos entregables escritos, con el código
que los produce (no son archivos hechos a mano):

| Entregable | Contenido |
|---|---|
| `docs/salida/1_Documento_Sprint2_RiTech.docx` | **El documento del enunciado, en Word y editable.** 19 páginas con los cinco puntos: requisitos, diagrama UML, backlog de septiembre con responsables, épicas e historias con criterios de aceptación, y estructura de la base de datos. |
| `docs/salida/1_Documento_Sprint2_RiTech.pdf` | El mismo documento en PDF, con la maqueta fija. 20 páginas. |
| `docs/salida/3_Guion_de_Exposicion.docx` | **El guion de los 10 minutos, en Word.** Cronómetro, guion explicado diapositiva por diapositiva (qué hay en pantalla, qué se dice, cómo, y la frase de puente), consejos si se va con retraso y preguntas. 12 páginas. |
| `docs/salida/4_Guion_de_Exposicion.pptx` | **El mismo guion en PowerPoint**, en letra grande sobre fondo oscuro, para tenerlo abierto en el portátil mientras se expone. 7 diapositivas. |
| `docs/salida/2_Presentacion_Sprint2_RiTech.pptx` | 17 diapositivas en dos bloques de dos personas, con el nombre del que habla en cada una. |
| `docs/salida/diagrama_casos_de_uso.pdf` | Diagrama UML con los seis actores y los 37 casos de uso. |
| `docs/salida/diagrama_entidad_relacion.pdf` | Diagrama entidad-relación de las nueve tablas, más la tabla de relaciones y las extensiones. |

Para regenerarlos, desde la raíz del proyecto:

```bash
pip install reportlab python-docx python-pptx pymupdf
python -m docs.generar_todo
```

El PDF y el Word del documento salen de las mismas tablas de `docs/datos.py`, y
la presentación y el guion salen de `docs/datos.py:EXPOSICION`, así que no pueden
contradecirse. Para corregir un requisito, una historia, un responsable o un
minuto del reparto se edita ese archivo y se regenera todo. Ver `docs/README.md`
para el detalle, incluida la advertencia de qué datos son copia literal de los
documentos del proyecto y cuáles son propuesta propia.

---

## 10. Sprint 3 y Sprint 4: módulos añadidos

### Financiero · HU-14

Pantalla **Financiero** (`#/financiero`) con cartera consolidada, pagos por
contrato, anticipos, cartas de crédito, anulación con rastro y barra de avance
de cobro. El cliente europeo ve solo su propia cartera.

| Endpoint | Uso |
|---|---|
| `GET/POST /api/pagos` | Listar y registrar pagos |
| `PATCH /api/pagos/{id}` | Corregir un pago no anulado |
| `POST /api/pagos/{id}/anular` | Anular conservando el historial (administrador) |
| `DELETE /api/pagos/{id}` | Eliminar un pago registrado por error |
| `GET /api/financiero/resumen` | Cartera, cobros, anticipos y vencimientos en EUR |

### Notificaciones · HU-16

Bandeja (`#/notificaciones`) con avisos propios, por rol y globales, contador en
la campana de la cabecera y marcado individual o masivo. Los avisos derivados se
sincronizan al consultar la bandeja y no se duplican gracias a `clave`.

| Endpoint | Uso |
|---|---|
| `GET /api/notificaciones` | Bandeja del usuario, con filtro de no leídas |
| `GET /api/notificaciones/contador` | Total y no leídas para la campana |
| `POST /api/notificaciones/{id}/leer` | Marcar una como leída |
| `POST /api/notificaciones/leer-todas` | Marcar todas como leídas |
| `POST /api/notificaciones` | Crear un aviso manual (administrador) |

### Auditoría · HU-21

Pantalla **Auditoría** (`#/auditoria`), solo para administradores, con búsqueda
por acción, correo, entidad o detalle y ficha completa de cada registro.

| Endpoint | Uso |
|---|---|
| `GET /api/auditoria` | Listado paginado con filtros |
| `GET /api/auditoria/{id}` | Detalle de una acción |

### Multimoneda e idiomas · HU-19

El portal del cliente carga los tipos de cambio desde la API y permite alternar
entre **español, inglés, alemán, francés, italiano, neerlandés y sueco**, y entre
**EUR, USD y COP**. La preferencia queda en `localStorage`; no hay tasas escritas
en el frontend. La convención es `tasa` = unidades de la moneda por 1 EUR.

| Endpoint | Uso |
|---|---|
| `GET /api/tipos-cambio` | Última tasa conocida de cada moneda |
| `POST /api/tipos-cambio` | Carga manual de una tasa (administrador) |
| `POST /api/tipos-cambio/actualizar` | Actualiza las tasas del día |
| `GET /api/monedas/convertir` | Convierte un importe entre monedas |

### Integraciones · HU-20

Pantalla **Sistema** (`#/sistema`) con el estado de correo, seguimiento de
navieras, tipos de cambio y almacenamiento documental, además de la bitácora de
ejecuciones. Con `RITECH_INTEGRACIONES_RED=0` (valor por defecto) todo funciona
en modo simulado y no depende de internet.

| Endpoint | Uso |
|---|---|
| `GET /api/integraciones` | Estado de los cuatro servicios |
| `POST /api/integraciones/correo` | Prueba de envío (administrador) |
| `POST /api/integraciones/seguimiento/{numero}` | Consulta un envío registrado |
| `GET /api/integraciones/bitacora` | Últimas ejecuciones (administrador) |

### Copias de seguridad · HU-22

Cada respaldo es una **instantánea JSON** de todas las tablas, con tamaño,
número de registros y **SHA-256**. Se puede verificar y descargar desde la
pantalla **Sistema**, y al arrancar la API se crea una copia automática si la
última tiene más de `RITECH_BACKUP_AUTO_HORAS` (24 por defecto). El formato es
portable entre SQLite, PostgreSQL y MySQL; no es una copia del archivo del motor.

| Endpoint | Uso |
|---|---|
| `GET/POST /api/respaldos` | Listar y crear copias (administrador) |
| `POST /api/respaldos/{id}/verificar` | Recalcular el SHA-256 y comparar |
| `GET /api/respaldos/{id}/descargar` | Descargar el JSON |

### Configuración nueva

```bash
RITECH_BACKUP_DIR=./respaldos          # carpeta de las copias
RITECH_BACKUP_AUTO_HORAS=24            # frecuencia del respaldo automático
RITECH_INTEGRACIONES_RED=0             # 1 = consultar el proveedor público de tasas
RITECH_INTEGRACIONES_TIMEOUT=4         # segundos de espera para la red
```
