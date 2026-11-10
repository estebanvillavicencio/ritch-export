-- ===========================================================================
-- RiTech SAS · Sistema de Gestión de Exportación de Café y Cacao a la UE
-- Esquema para PostgreSQL (RR-003 · «La información transaccional del sistema
-- deberá almacenarse utilizando PostgreSQL»).
--
-- Contiene las nueve tablas del modelo de datos y, en una sección aparte,
-- las tablas de extensión que requieren los módulos del Sprint 2.
--
--   psql -U riuser -d ritch -f sql/schema_postgres.sql
-- ===========================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. usuarios
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario      SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    correo          VARCHAR(150) NOT NULL UNIQUE,
    contrasena_hash VARCHAR(255) NOT NULL,
    rol             VARCHAR(50)  NOT NULL DEFAULT 'Administrador'
                    CHECK (rol IN ('Administrador', 'Comercial', 'Logística',
                                   'Calidad', 'Financiero', 'Cliente europeo')),
    estado          VARCHAR(20)  NOT NULL DEFAULT 'activo'
                    CHECK (estado IN ('activo', 'inactivo', 'bloqueado')),
    creado_en       TIMESTAMP    NOT NULL DEFAULT NOW(),
    ultimo_acceso   TIMESTAMP,
    -- HU-10 · De qué empresa es la cuenta, cuando el rol es «Cliente europeo».
    -- Es lo que hace que su portal muestre solo sus propios pedidos y envíos.
    -- El personal de RiTech la deja en NULL. La clave foránea se agrega más
    -- abajo, después de crear `clientes`.
    id_cliente      INTEGER
);
CREATE INDEX IF NOT EXISTS ix_usuarios_rol ON usuarios (rol);
CREATE INDEX IF NOT EXISTS ix_usuarios_cliente ON usuarios (id_cliente);

-- ---------------------------------------------------------------------------
-- 2. clientes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente        SERIAL PRIMARY KEY,
    nombre_empresa    VARCHAR(150) NOT NULL,
    pais              VARCHAR(100) NOT NULL,
    direccion         VARCHAR(200),
    correo            VARCHAR(150),
    telefono          VARCHAR(30),
    -- extensiones del módulo comercial
    contacto          VARCHAR(150),
    vat               VARCHAR(50),
    moneda_preferida  VARCHAR(10)  NOT NULL DEFAULT 'EUR',
    puerto_destino    VARCHAR(100),
    activo            BOOLEAN      NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS ix_clientes_pais ON clientes (pais);

-- La columna ya existía, pero la clave foranja necesita que `clientes` esté
-- creada, y en este script `usuarios` va primero.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'fk_usuarios_cliente') THEN
        ALTER TABLE usuarios
            ADD CONSTRAINT fk_usuarios_cliente
            FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
            ON DELETE RESTRICT;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 3. productos
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS productos (
    id_producto          SERIAL PRIMARY KEY,
    nombre               VARCHAR(100) NOT NULL,
    tipo                 VARCHAR(50)  NOT NULL CHECK (tipo IN ('Café', 'Cacao')),
    descripcion          TEXT,
    -- extensiones comerciales
    variedad             VARCHAR(100),
    unidad_medida        VARCHAR(20)  NOT NULL DEFAULT 'kg',
    precio_referencia_eur NUMERIC(12, 2),
    activo               BOOLEAN      NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS ix_productos_tipo ON productos (tipo);

-- ---------------------------------------------------------------------------
-- 4. fincas
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fincas (
    id_finca              SERIAL PRIMARY KEY,
    nombre                VARCHAR(150) NOT NULL,
    ubicacion             VARCHAR(200) NOT NULL,
    departamento          VARCHAR(100) NOT NULL,
    propietario           VARCHAR(150) NOT NULL,
    -- extensiones del módulo de productores y del EUDR
    productor             VARCHAR(150),
    asociacion            VARCHAR(150),
    altura_msnm           INTEGER,
    superficie_ha         NUMERIC(10, 2),
    capacidad_produccion_kg NUMERIC(12, 2),
    latitud               NUMERIC(10, 7),
    longitud              NUMERIC(10, 7)
);
CREATE INDEX IF NOT EXISTS ix_fincas_departamento ON fincas (departamento);

-- ---------------------------------------------------------------------------
-- 5. lotes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lotes (
    id_lote         SERIAL PRIMARY KEY,
    id_finca        INTEGER       NOT NULL REFERENCES fincas (id_finca)    ON DELETE CASCADE,
    id_producto     INTEGER       NOT NULL REFERENCES productos (id_producto) ON DELETE RESTRICT,
    codigo_lote     VARCHAR(50)   NOT NULL UNIQUE,
    cantidad_kg     NUMERIC(12, 2) NOT NULL CHECK (cantidad_kg > 0),
    fecha_cosecha   DATE          NOT NULL,
    estado_calidad  VARCHAR(50)   NOT NULL DEFAULT 'Pendiente'
                    CHECK (estado_calidad IN ('Pendiente', 'En análisis', 'Aprobado',
                                             'Aprobado con reserva', 'Rechazado')),
    -- extensiones: reserva de inventario
    disponible_kg   NUMERIC(12, 2),
    consumo_kg      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    variedad        VARCHAR(100),
    altura_msnm     INTEGER,
    created_at      TIMESTAMP     NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_lotes_finca          ON lotes (id_finca);
CREATE INDEX IF NOT EXISTS ix_lotes_producto       ON lotes (id_producto);
CREATE INDEX IF NOT EXISTS ix_lotes_estado_calidad ON lotes (estado_calidad);

-- ---------------------------------------------------------------------------
-- 6. exportaciones
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exportaciones (
    id_exportacion   SERIAL PRIMARY KEY,
    id_cliente       INTEGER         NOT NULL REFERENCES clientes (id_cliente) ON DELETE RESTRICT,
    id_usuario       INTEGER         NOT NULL REFERENCES usuarios (id_usuario) ON DELETE RESTRICT,
    fecha            DATE            NOT NULL,
    estado           VARCHAR(50)     NOT NULL DEFAULT 'Pedido recibido'
                     CHECK (estado IN ('Pedido recibido', 'En preparación', 'En producción',
                                       'En puerto', 'En tránsito', 'En destino',
                                       'Entregado', 'Anulado')),
    moneda           VARCHAR(10)     NOT NULL DEFAULT 'EUR',
    -- extensiones del módulo comercial
    numero_contrato  VARCHAR(60) UNIQUE,
    incoterm         VARCHAR(20),
    puerto_origen    VARCHAR(100),
    puerto_destino   VARCHAR(100),
    valor_total      NUMERIC(14, 2) NOT NULL DEFAULT 0,
    observaciones    TEXT,
    created_at       TIMESTAMP       NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_exportaciones_cliente ON exportaciones (id_cliente);
CREATE INDEX IF NOT EXISTS ix_exportaciones_usuario ON exportaciones (id_usuario);
CREATE INDEX IF NOT EXISTS ix_exportaciones_estado  ON exportaciones (estado);

-- ---------------------------------------------------------------------------
-- 7. detalle_exportacion
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_exportacion (
    id_detalle      SERIAL PRIMARY KEY,
    id_exportacion  INTEGER         NOT NULL REFERENCES exportaciones (id_exportacion) ON DELETE CASCADE,
    id_lote         INTEGER         NOT NULL REFERENCES lotes (id_lote) ON DELETE RESTRICT,
    cantidad_kg     NUMERIC(12, 2)  NOT NULL CHECK (cantidad_kg > 0),
    precio_kg       NUMERIC(12, 2)  NOT NULL CHECK (precio_kg > 0),
    CONSTRAINT uq_detalle_exportacion_lote UNIQUE (id_exportacion, id_lote)
);
CREATE INDEX IF NOT EXISTS ix_detalle_exportacion ON detalle_exportacion (id_exportacion);

-- ---------------------------------------------------------------------------
-- 8. documentos_exportacion
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documentos_exportacion (
    id_documento        SERIAL PRIMARY KEY,
    id_exportacion      INTEGER      NOT NULL REFERENCES exportaciones (id_exportacion) ON DELETE CASCADE,
    tipo_documento      VARCHAR(100) NOT NULL
                        CHECK (tipo_documento IN ('Factura comercial', 'Packing list',
                                                  'Certificado de origen', 'BL', 'AWB',
                                                  'Certificado', 'Documento aduanero')),
    numero_documento    VARCHAR(100) NOT NULL UNIQUE,
    fecha_emision       DATE         NOT NULL,
    estado              VARCHAR(50)  NOT NULL DEFAULT 'Borrador'
                        CHECK (estado IN ('Borrador', 'Emitido', 'Validado', 'Anulado')),
    -- extensiones: archivo en S3 / Azure Blob Storage
    archivo             VARCHAR(300),
    tamano_bytes        INTEGER,
    autorizado_cliente  BOOLEAN      NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_documentos_exportacion ON documentos_exportacion (id_exportacion);

-- ---------------------------------------------------------------------------
-- 9. envios
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS envios (
    id_envio         SERIAL PRIMARY KEY,
    id_exportacion   INTEGER      NOT NULL REFERENCES exportaciones (id_exportacion) ON DELETE CASCADE,
    transportadora   VARCHAR(100) NOT NULL,
    numero_seguimiento VARCHAR(100) NOT NULL UNIQUE,
    fecha_salida     DATE,
    fecha_llegada    DATE,
    estado           VARCHAR(50)  NOT NULL DEFAULT 'Programado'
                     CHECK (estado IN ('Programado', 'En tránsito', 'En aduana',
                                       'En destino', 'Entregado', 'Demorado', 'Incidencia')),
    -- extensiones del módulo de logística
    id_contenedor    INTEGER      REFERENCES contenedores (id_contenedor) ON DELETE SET NULL,
    puerto_origen    VARCHAR(100),
    puerto_destino   VARCHAR(100),
    tipo_transporte  VARCHAR(20)  NOT NULL DEFAULT 'Marítimo',
    costo_flete      NUMERIC(12, 2),
    temperatura_c    NUMERIC(5, 2),
    CONSTRAINT ck_envio_fechas CHECK (fecha_llegada IS NULL OR fecha_salida IS NULL
                                      OR fecha_llegada >= fecha_salida)
);
CREATE INDEX IF NOT EXISTS ix_envios_exportacion ON envios (id_exportacion);
CREATE INDEX IF NOT EXISTS ix_envios_estado      ON envios (estado);

-- ===========================================================================
-- Extensiones de los módulos del Sprint 2
-- ===========================================================================

-- contenedores · módulo de logística (HU-12)
CREATE TABLE IF NOT EXISTS contenedores (
    id_contenedor  SERIAL PRIMARY KEY,
    codigo         VARCHAR(20)  NOT NULL UNIQUE,
    tipo           VARCHAR(10)  NOT NULL DEFAULT '20GP'
                   CHECK (tipo IN ('20GP', '40GP', '40HC', '20RF', '40RF', 'LCL')),
    capacidad_kg   NUMERIC(10, 2) NOT NULL CHECK (capacidad_kg > 0),
    naviera        VARCHAR(100),
    disponible     BOOLEAN      NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS ix_contenedores_disponible ON contenedores (disponible);

-- calidad_lote · módulo de calidad (HU-17)
CREATE TABLE IF NOT EXISTS calidad_lote (
    id_calidad      SERIAL PRIMARY KEY,
    id_lote         INTEGER      NOT NULL UNIQUE REFERENCES lotes (id_lote) ON DELETE CASCADE,
    humedad         NUMERIC(5, 2)  CHECK (humedad BETWEEN 0 AND 100),
    puntaje_cata    NUMERIC(6, 2)  CHECK (puntaje_cata BETWEEN 0 AND 100),
    actividad_agua  NUMERIC(5, 2),
    granulometria   NUMERIC(5, 2),
    impurezas       NUMERIC(5, 2),
    cafeina_pct     NUMERIC(5, 2),
    grasa_pct       NUMERIC(5, 2),
    prueba_metodos  VARCHAR(200),
    clasificacion   VARCHAR(50),
    laboratorio     VARCHAR(150),
    observaciones   TEXT,
    fecha_analisis  DATE,
    aprobado_por    VARCHAR(100)
);

-- certificaciones · cumplimiento normativo (Informe §6.4)
CREATE TABLE IF NOT EXISTS certificaciones (
    id_certificacion       SERIAL PRIMARY KEY,
    id_lote                INTEGER REFERENCES lotes (id_lote) ON DELETE CASCADE,
    id_finca               INTEGER REFERENCES fincas (id_finca) ON DELETE CASCADE,
    tipo                   VARCHAR(50)  NOT NULL
                           CHECK (tipo IN ('EUDR', 'Orgánico', 'Fairtrade', 'Fitosanitario',
                                           'Rainforest Alliance', 'Otro')),
    entidad_emisora        VARCHAR(150),
    numero_certificado     VARCHAR(100),
    fecha_emision          DATE         NOT NULL,
    fecha_vencimiento      DATE,
    archivo                VARCHAR(300),
    lote_georreferenciado  BOOLEAN      NOT NULL DEFAULT FALSE,
    notas                  TEXT,
    CONSTRAINT ck_cert_propietario CHECK (id_lote IS NOT NULL OR id_finca IS NOT NULL),
    CONSTRAINT ck_cert_vencimiento CHECK (fecha_vencimiento IS NULL
                                          OR fecha_vencimiento >= fecha_emision)
);
CREATE INDEX IF NOT EXISTS ix_certificaciones_lote         ON certificaciones (id_lote);
CREATE INDEX IF NOT EXISTS ix_certificaciones_finca        ON certificaciones (id_finca);
CREATE INDEX IF NOT EXISTS ix_certificaciones_vencimiento ON certificaciones (fecha_vencimiento);

-- eventos_trazabilidad · HU-06 (finca → beneficio → puerto → tránsito → aduana → cliente)
CREATE TABLE IF NOT EXISTS eventos_trazabilidad (
    id_evento    SERIAL PRIMARY KEY,
    id_lote      INTEGER      NOT NULL REFERENCES lotes (id_lote)  ON DELETE CASCADE,
    etapa        VARCHAR(50)  NOT NULL
                 CHECK (etapa IN ('Finca', 'Beneficio', 'Puerto origen',
                                  'Tránsito marítimo', 'Aduana UE', 'Cliente')),
    fecha        DATE         NOT NULL,
    ubicacion    VARCHAR(150),
    descripcion  VARCHAR(300),
    documento    VARCHAR(300),
    id_envio     INTEGER      REFERENCES envios (id_envio) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_eventos_lote  ON eventos_trazabilidad (id_lote);
CREATE INDEX IF NOT EXISTS ix_eventos_etapa ON eventos_trazabilidad (etapa);

-- cotizaciones · HU-08
CREATE TABLE IF NOT EXISTS cotizaciones (
    id_cotizacion   SERIAL PRIMARY KEY,
    numero          VARCHAR(60)  NOT NULL UNIQUE,
    id_cliente      INTEGER      NOT NULL REFERENCES clientes (id_cliente) ON DELETE CASCADE,
    id_usuario      INTEGER      NOT NULL REFERENCES usuarios (id_usuario) ON DELETE RESTRICT,
    fecha           DATE         NOT NULL,
    validez_dias    INTEGER      NOT NULL DEFAULT 15 CHECK (validez_dias BETWEEN 1 AND 365),
    moneda          VARCHAR(10)  NOT NULL DEFAULT 'EUR',
    incoterm        VARCHAR(20)  NOT NULL DEFAULT 'FOB',
    estado          VARCHAR(30)  NOT NULL DEFAULT 'Borrador'
                    CHECK (estado IN ('Borrador', 'Enviada', 'Aceptada', 'Rechazada', 'Vencida')),
    precio_kg       NUMERIC(12, 2) NOT NULL CHECK (precio_kg > 0),
    cantidad_kg     NUMERIC(12, 2) NOT NULL CHECK (cantidad_kg > 0),
    puerto_origen   VARCHAR(100),
    puerto_destino  VARCHAR(100),
    observaciones   TEXT,
    id_exportacion  INTEGER      REFERENCES exportaciones (id_exportacion) ON DELETE SET NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_cotizaciones_cliente ON cotizaciones (id_cliente);
CREATE INDEX IF NOT EXISTS ix_cotizaciones_estado  ON cotizaciones (estado);

-- El envío referencia al contenedor, que se declara después: se añade la FK.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_envios_contenedor'
    ) THEN
        ALTER TABLE envios
            ADD CONSTRAINT fk_envios_contenedor
            FOREIGN KEY (id_contenedor) REFERENCES contenedores (id_contenedor)
            ON DELETE SET NULL;
    END IF;
END $$;

-- ===========================================================================
-- Extensiones de los Sprint 3 y 4
-- ===========================================================================

-- pagos · HU-14
CREATE TABLE IF NOT EXISTS pagos (
    id_pago        SERIAL PRIMARY KEY,
    id_exportacion INTEGER      NOT NULL REFERENCES exportaciones (id_exportacion) ON DELETE CASCADE,
    id_usuario     INTEGER      NOT NULL REFERENCES usuarios (id_usuario) ON DELETE RESTRICT,
    fecha          DATE         NOT NULL,
    tipo           VARCHAR(50)  NOT NULL DEFAULT 'Anticipo'
                   CHECK (tipo IN ('Anticipo', 'Pago parcial', 'Pago final', 'Saldo', 'Reembolso')),
    metodo         VARCHAR(50)  NOT NULL DEFAULT 'Transferencia'
                   CHECK (metodo IN ('Transferencia', 'Carta de crédito', 'Cheque', 'Efectivo', 'Otro')),
    estado         VARCHAR(50)  NOT NULL DEFAULT 'Registrado'
                   CHECK (estado IN ('Registrado', 'Confirmado', 'Anulado')),
    valor          NUMERIC(14, 2) NOT NULL CHECK (valor > 0),
    moneda         VARCHAR(10)  NOT NULL DEFAULT 'EUR',
    referencia     VARCHAR(100),
    banco          VARCHAR(150),
    observaciones  TEXT,
    created_at     TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_pagos_exportacion ON pagos (id_exportacion);
CREATE INDEX IF NOT EXISTS ix_pagos_estado      ON pagos (estado);
CREATE INDEX IF NOT EXISTS ix_pagos_fecha       ON pagos (fecha);

-- notificaciones · HU-16
CREATE TABLE IF NOT EXISTS notificaciones (
    id_notificacion SERIAL PRIMARY KEY,
    id_usuario      INTEGER      REFERENCES usuarios (id_usuario) ON DELETE CASCADE,
    rol_destino     VARCHAR(50),
    tipo            VARCHAR(50)  NOT NULL DEFAULT 'Sistema'
                    CHECK (tipo IN ('Certificación', 'Envío', 'Pago', 'Pedido',
                                    'Sistema', 'Seguridad')),
    tono            VARCHAR(20)  NOT NULL DEFAULT 'azul',
    titulo          VARCHAR(200) NOT NULL,
    detalle         TEXT,
    enlace          VARCHAR(200),
    clave           VARCHAR(160) UNIQUE,
    leida           BOOLEAN      NOT NULL DEFAULT FALSE,
    fecha           TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_notificaciones_usuario ON notificaciones (id_usuario);
CREATE INDEX IF NOT EXISTS ix_notificaciones_rol     ON notificaciones (rol_destino);
CREATE INDEX IF NOT EXISTS ix_notificaciones_leida   ON notificaciones (leida);
CREATE INDEX IF NOT EXISTS ix_notificaciones_fecha   ON notificaciones (fecha);

-- auditoria · HU-21
CREATE TABLE IF NOT EXISTS auditoria (
    id_auditoria   SERIAL PRIMARY KEY,
    id_usuario     INTEGER      REFERENCES usuarios (id_usuario) ON DELETE SET NULL,
    usuario_correo VARCHAR(150),
    accion         VARCHAR(100) NOT NULL,
    entidad        VARCHAR(80),
    id_entidad     VARCHAR(50),
    detalle        TEXT,
    metodo         VARCHAR(10),
    ruta           VARCHAR(300),
    estado_http    INTEGER,
    ip             VARCHAR(60),
    fecha          TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_auditoria_usuario ON auditoria (id_usuario);
CREATE INDEX IF NOT EXISTS ix_auditoria_fecha   ON auditoria (fecha);
CREATE INDEX IF NOT EXISTS ix_auditoria_entidad ON auditoria (entidad);

-- tipos_cambio · HU-19. `tasa` son unidades de la moneda por 1 EUR.
CREATE TABLE IF NOT EXISTS tipos_cambio (
    id_tipo_cambio SERIAL PRIMARY KEY,
    moneda         VARCHAR(10)   NOT NULL,
    tasa           NUMERIC(18, 6) NOT NULL CHECK (tasa > 0),
    fecha          DATE          NOT NULL,
    fuente         VARCHAR(100),
    created_at     TIMESTAMP     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tipo_cambio_moneda_fecha UNIQUE (moneda, fecha)
);
CREATE INDEX IF NOT EXISTS ix_tipos_cambio_fecha ON tipos_cambio (fecha);

-- respaldos · HU-22
CREATE TABLE IF NOT EXISTS respaldos (
    id_respaldo   SERIAL PRIMARY KEY,
    nombre        VARCHAR(200) NOT NULL,
    ruta          VARCHAR(400) NOT NULL,
    tamano_bytes  INTEGER      NOT NULL DEFAULT 0,
    checksum      VARCHAR(64),
    tipo          VARCHAR(50)  NOT NULL DEFAULT 'Manual'
                  CHECK (tipo IN ('Manual', 'Automática')),
    estado        VARCHAR(50)  NOT NULL DEFAULT 'Completado'
                  CHECK (estado IN ('Completado', 'Fallido', 'Restaurado')),
    tablas        INTEGER      NOT NULL DEFAULT 0,
    registros     INTEGER      NOT NULL DEFAULT 0,
    detalle       TEXT,
    id_usuario    INTEGER      REFERENCES usuarios (id_usuario) ON DELETE SET NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_respaldos_fecha ON respaldos (created_at);

-- registros_integracion · HU-20
CREATE TABLE IF NOT EXISTS registros_integracion (
    id_registro SERIAL PRIMARY KEY,
    servicio    VARCHAR(60)  NOT NULL,
    accion      VARCHAR(100) NOT NULL,
    estado      VARCHAR(30)  NOT NULL DEFAULT 'ok',
    mensaje     TEXT,
    detalle     TEXT,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_registros_integracion_servicio ON registros_integracion (servicio);
CREATE INDEX IF NOT EXISTS ix_registros_integracion_fecha    ON registros_integracion (created_at);

COMMIT;

-- ===========================================================================
-- Consultas de verificación
-- ===========================================================================
-- SELECT * FROM lotes ORDER BY fecha_cosecha DESC;
-- SELECT e.id_exportacion, c.nombre_empresa, e.estado, e.valor_total,
--        SUM(d.cantidad_kg) AS kilos
--   FROM exportaciones e
--   JOIN clientes c        ON c.id_cliente = e.id_cliente
--   JOIN detalle_exportacion d ON d.id_exportacion = e.id_exportacion
--  WHERE e.estado <> 'Anulado'
--  GROUP BY e.id_exportacion, c.nombre_empresa, e.estado, e.valor_total;
--
-- -- Trazabilidad completa de un lote
-- SELECT l.codigo_lote, ev.etapa, ev.fecha, ev.ubicacion
--   FROM lotes l JOIN eventos_trazabilidad ev ON ev.id_lote = l.id_lote
--  WHERE l.codigo_lote = 'CO-HUI-2026-0001'
--  ORDER BY ev.fecha;

-- solicitudes_pedido · solicitudes recibidas desde el portal de compradores
CREATE TABLE IF NOT EXISTS solicitudes_pedido (
    id_solicitud  SERIAL PRIMARY KEY,
    id_cliente    INTEGER      NOT NULL REFERENCES clientes (id_cliente) ON DELETE CASCADE,
    id_usuario    INTEGER      NOT NULL REFERENCES usuarios (id_usuario) ON DELETE RESTRICT,
    id_producto   INTEGER      NOT NULL REFERENCES productos (id_producto) ON DELETE RESTRICT,
    cantidad_kg   NUMERIC(12, 2) NOT NULL CHECK (cantidad_kg > 0),
    incoterm      VARCHAR(20)  NOT NULL DEFAULT 'FOB',
    puerto_destino VARCHAR(100),
    observaciones TEXT,
    estado        VARCHAR(30)  NOT NULL DEFAULT 'Pendiente',
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_solicitudes_pedido_cliente ON solicitudes_pedido (id_cliente);
CREATE INDEX IF NOT EXISTS ix_solicitudes_pedido_estado ON solicitudes_pedido (estado);
