-- ===========================================================================
-- RiTech SAS · Sistema de Gestión de Exportación de Café y Cacao a la UE
-- Esquema para MySQL 8 (motor citado en «RiTech_Base_datos_relaciones_equipo_APIs.pdf»).
--
-- El modelo lógico es idéntico al de PostgreSQL: las mismas nueve tablas y las
-- mismas extensiones del Sprint 2. Solo cambian los tipos físicos.
--
--   mysql -u root -p < sql/schema_mysql.sql
-- ===========================================================================

CREATE DATABASE IF NOT EXISTS ritch
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE ritch;

-- ---------------------------------------------------------------------------
-- 1. usuarios
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario      INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    correo          VARCHAR(150) NOT NULL UNIQUE,
    contrasena_hash VARCHAR(255) NOT NULL,
    rol             VARCHAR(50)  NOT NULL DEFAULT 'Administrador'
                    CHECK (rol IN ('Administrador', 'Comercial', 'Logística',
                                   'Calidad', 'Financiero', 'Cliente europeo')),
    estado          VARCHAR(20)  NOT NULL DEFAULT 'activo'
                    CHECK (estado IN ('activo', 'inactivo', 'bloqueado')),
    creado_en       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso   DATETIME     NULL,
    -- HU-10 · De qué empresa es la cuenta, cuando el rol es «Cliente europeo».
    -- La clave foránea se agrega después de crear `clientes`, más abajo.
    id_cliente      INT          NULL,
    INDEX ix_usuarios_rol (rol)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 2. clientes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente        INT AUTO_INCREMENT PRIMARY KEY,
    nombre_empresa    VARCHAR(150) NOT NULL,
    pais              VARCHAR(100) NOT NULL,
    direccion         VARCHAR(200) NULL,
    correo            VARCHAR(150) NULL,
    telefono          VARCHAR(30)  NULL,
    contacto          VARCHAR(150) NULL,
    vat               VARCHAR(50)  NULL,
    moneda_preferida  VARCHAR(10)  NOT NULL DEFAULT 'EUR',
    puerto_destino    VARCHAR(100) NULL,
    activo            BOOLEAN      NOT NULL DEFAULT TRUE,
    INDEX ix_clientes_pais (pais)
) ENGINE=InnoDB;

-- La FK necesita que `clientes` exista, y en este script `usuarios` va primero.
-- MySQL no tiene «ADD CONSTRAINT IF NOT EXISTS», así que se revisa antes el
-- nombre de la restricción en information_schema.
SET @ya_existe := (
    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = DATABASE()
      AND TABLE_NAME = 'usuarios'
      AND CONSTRAINT_NAME = 'fk_usuarios_cliente'
);
SET @agregar := IF(@ya_existe = 0,
    'ALTER TABLE usuarios ADD CONSTRAINT fk_usuarios_cliente
        FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
        ON DELETE RESTRICT',
    'DO 0');
PREPARE stmt FROM @agregar;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

CREATE INDEX IF NOT EXISTS ix_usuarios_cliente ON usuarios (id_cliente);

-- ---------------------------------------------------------------------------
-- 3. productos
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS productos (
    id_producto           INT AUTO_INCREMENT PRIMARY KEY,
    nombre                VARCHAR(100) NOT NULL,
    tipo                  VARCHAR(50)  NOT NULL CHECK (tipo IN ('Café', 'Cacao')),
    descripcion           TEXT         NULL,
    variedad              VARCHAR(100) NULL,
    unidad_medida         VARCHAR(20)  NOT NULL DEFAULT 'kg',
    precio_referencia_eur DECIMAL(12, 2) NULL,
    activo                BOOLEAN      NOT NULL DEFAULT TRUE,
    INDEX ix_productos_tipo (tipo)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 4. fincas
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fincas (
    id_finca                INT AUTO_INCREMENT PRIMARY KEY,
    nombre                  VARCHAR(150) NOT NULL,
    ubicacion               VARCHAR(200) NOT NULL,
    departamento            VARCHAR(100) NOT NULL,
    propietario             VARCHAR(150) NOT NULL,
    productor               VARCHAR(150) NULL,
    asociacion              VARCHAR(150) NULL,
    altura_msnm             INT          NULL,
    superficie_ha           DECIMAL(10, 2) NULL,
    capacidad_produccion_kg DECIMAL(12, 2) NULL,
    latitud                 DECIMAL(10, 7) NULL,
    longitud                DECIMAL(10, 7) NULL,
    INDEX ix_fincas_departamento (departamento)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 5. lotes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lotes (
    id_lote        INT AUTO_INCREMENT PRIMARY KEY,
    id_finca       INT             NOT NULL,
    id_producto    INT             NOT NULL,
    codigo_lote    VARCHAR(50)     NOT NULL UNIQUE,
    cantidad_kg    DECIMAL(12, 2)  NOT NULL,
    fecha_cosecha  DATE            NOT NULL,
    estado_calidad VARCHAR(50)     NOT NULL DEFAULT 'Pendiente'
                   CHECK (estado_calidad IN ('Pendiente', 'En análisis', 'Aprobado',
                                            'Aprobado con reserva', 'Rechazado')),
    disponible_kg  DECIMAL(12, 2)  NULL,
    consumo_kg     DECIMAL(12, 2)  NOT NULL DEFAULT 0,
    variedad       VARCHAR(100)    NULL,
    altura_msnm    INT             NULL,
    created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_lotes_finca    FOREIGN KEY (id_finca)    REFERENCES fincas (id_finca)    ON DELETE CASCADE,
    CONSTRAINT fk_lotes_producto FOREIGN KEY (id_producto) REFERENCES productos (id_producto) ON DELETE RESTRICT,
    CONSTRAINT ck_lotes_cantidad CHECK (cantidad_kg > 0),
    INDEX ix_lotes_finca          (id_finca),
    INDEX ix_lotes_producto       (id_producto),
    INDEX ix_lotes_estado_calidad (estado_calidad)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 6. exportaciones
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exportaciones (
    id_exportacion  INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente      INT NOT NULL,
    id_usuario      INT NOT NULL,
    fecha           DATE         NOT NULL,
    estado          VARCHAR(50)  NOT NULL DEFAULT 'Pedido recibido'
                    CHECK (estado IN ('Pedido recibido', 'En preparación', 'En producción',
                                      'En puerto', 'En tránsito', 'En destino',
                                      'Entregado', 'Anulado')),
    moneda          VARCHAR(10)  NOT NULL DEFAULT 'EUR',
    numero_contrato VARCHAR(60) NULL UNIQUE,
    incoterm        VARCHAR(20) NULL,
    puerto_origen   VARCHAR(100) NULL,
    puerto_destino  VARCHAR(100) NULL,
    valor_total     DECIMAL(14, 2) NOT NULL DEFAULT 0,
    observaciones   TEXT         NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_exportaciones_cliente FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente) ON DELETE RESTRICT,
    CONSTRAINT fk_exportaciones_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE RESTRICT,
    INDEX ix_exportaciones_cliente (id_cliente),
    INDEX ix_exportaciones_usuario (id_usuario),
    INDEX ix_exportaciones_estado  (estado)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 7. detalle_exportacion
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_exportacion (
    id_detalle     INT AUTO_INCREMENT PRIMARY KEY,
    id_exportacion INT            NOT NULL,
    id_lote        INT            NOT NULL,
    cantidad_kg    DECIMAL(12, 2) NOT NULL,
    precio_kg      DECIMAL(12, 2) NOT NULL,
    CONSTRAINT fk_detalle_exportacion FOREIGN KEY (id_exportacion) REFERENCES exportaciones (id_exportacion) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_lote        FOREIGN KEY (id_lote)        REFERENCES lotes (id_lote) ON DELETE RESTRICT,
    CONSTRAINT uq_detalle_exportacion_lote UNIQUE (id_exportacion, id_lote),
    CONSTRAINT ck_detalle_cantidad CHECK (cantidad_kg > 0),
    CONSTRAINT ck_detalle_precio   CHECK (precio_kg > 0),
    INDEX ix_detalle_exportacion (id_exportacion)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 8. documentos_exportacion
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documentos_exportacion (
    id_documento       INT AUTO_INCREMENT PRIMARY KEY,
    id_exportacion     INT          NOT NULL,
    tipo_documento     VARCHAR(100) NOT NULL
                       CHECK (tipo_documento IN ('Factura comercial', 'Packing list',
                                                 'Certificado de origen', 'BL', 'AWB',
                                                 'Certificado', 'Documento aduanero')),
    numero_documento   VARCHAR(100) NOT NULL UNIQUE,
    fecha_emision      DATE         NOT NULL,
    estado             VARCHAR(50)  NOT NULL DEFAULT 'Borrador'
                       CHECK (estado IN ('Borrador', 'Emitido', 'Validado', 'Anulado')),
    archivo            VARCHAR(300) NULL,
    tamano_bytes       INT          NULL,
    autorizado_cliente BOOLEAN      NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_documentos_exportacion FOREIGN KEY (id_exportacion) REFERENCES exportaciones (id_exportacion) ON DELETE CASCADE,
    INDEX ix_documentos_exportacion (id_exportacion)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- contenedores · módulo de logística (se declara antes que envios)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contenedores (
    id_contenedor INT AUTO_INCREMENT PRIMARY KEY,
    codigo        VARCHAR(20)  NOT NULL UNIQUE,
    tipo          VARCHAR(10)  NOT NULL DEFAULT '20GP'
                  CHECK (tipo IN ('20GP', '40GP', '40HC', '20RF', '40RF', 'LCL')),
    capacidad_kg  DECIMAL(10, 2) NOT NULL,
    naviera       VARCHAR(100) NULL,
    disponible    BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT ck_contenedor_capacidad CHECK (capacidad_kg > 0),
    INDEX ix_contenedores_disponible (disponible)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- 9. envios
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS envios (
    id_envio          INT AUTO_INCREMENT PRIMARY KEY,
    id_exportacion    INT          NOT NULL,
    transportadora    VARCHAR(100) NOT NULL,
    numero_seguimiento VARCHAR(100) NOT NULL UNIQUE,
    fecha_salida      DATE         NULL,
    fecha_llegada     DATE         NULL,
    estado            VARCHAR(50)  NOT NULL DEFAULT 'Programado'
                      CHECK (estado IN ('Programado', 'En tránsito', 'En aduana',
                                        'En destino', 'Entregado', 'Demorado', 'Incidencia')),
    id_contenedor     INT          NULL,
    puerto_origen     VARCHAR(100) NULL,
    puerto_destino    VARCHAR(100) NULL,
    tipo_transporte   VARCHAR(20)  NOT NULL DEFAULT 'Marítimo',
    costo_flete       DECIMAL(12, 2) NULL,
    temperatura_c     DECIMAL(5, 2)  NULL,
    CONSTRAINT fk_envios_exportacion FOREIGN KEY (id_exportacion) REFERENCES exportaciones (id_exportacion) ON DELETE CASCADE,
    CONSTRAINT fk_envios_contenedor  FOREIGN KEY (id_contenedor)  REFERENCES contenedores (id_contenedor)  ON DELETE SET NULL,
    CONSTRAINT ck_envio_fechas CHECK (fecha_llegada IS NULL OR fecha_salida IS NULL
                                     OR fecha_llegada >= fecha_salida),
    INDEX ix_envios_exportacion (id_exportacion),
    INDEX ix_envios_estado      (estado)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Extensiones de los módulos del Sprint 2
-- ---------------------------------------------------------------------------

-- calidad_lote · HU-17
CREATE TABLE IF NOT EXISTS calidad_lote (
    id_calidad     INT AUTO_INCREMENT PRIMARY KEY,
    id_lote        INT             NOT NULL UNIQUE,
    humedad        DECIMAL(5, 2)   NULL CHECK (humedad BETWEEN 0 AND 100),
    puntaje_cata   DECIMAL(6, 2)   NULL CHECK (puntaje_cata BETWEEN 0 AND 100),
    actividad_agua DECIMAL(5, 2)   NULL,
    granulometria  DECIMAL(5, 2)   NULL,
    impurezas      DECIMAL(5, 2)   NULL,
    cafeina_pct    DECIMAL(5, 2)   NULL,
    grasa_pct      DECIMAL(5, 2)   NULL,
    prueba_metodos VARCHAR(200)    NULL,
    clasificacion  VARCHAR(50)     NULL,
    laboratorio    VARCHAR(150)    NULL,
    observaciones  TEXT            NULL,
    fecha_analisis DATE            NULL,
    aprobado_por   VARCHAR(100)    NULL,
    CONSTRAINT fk_calidad_lote FOREIGN KEY (id_lote) REFERENCES lotes (id_lote) ON DELETE CASCADE
) ENGINE=InnoDB;

-- certificaciones · cumplimiento normativo
CREATE TABLE IF NOT EXISTS certificaciones (
    id_certificacion      INT AUTO_INCREMENT PRIMARY KEY,
    id_lote               INT          NULL,
    id_finca              INT          NULL,
    tipo                  VARCHAR(50)  NOT NULL
                          CHECK (tipo IN ('EUDR', 'Orgánico', 'Fairtrade', 'Fitosanitario',
                                          'Rainforest Alliance', 'Otro')),
    entidad_emisora       VARCHAR(150) NULL,
    numero_certificado    VARCHAR(100) NULL,
    fecha_emision         DATE         NOT NULL,
    fecha_vencimiento     DATE         NULL,
    archivo               VARCHAR(300) NULL,
    lote_georreferenciado BOOLEAN      NOT NULL DEFAULT FALSE,
    notas                 TEXT         NULL,
    CONSTRAINT fk_cert_lote  FOREIGN KEY (id_lote)  REFERENCES lotes  (id_lote)  ON DELETE CASCADE,
    CONSTRAINT fk_cert_finca FOREIGN KEY (id_finca) REFERENCES fincas (id_finca) ON DELETE CASCADE,
    CONSTRAINT ck_cert_propietario CHECK (id_lote IS NOT NULL OR id_finca IS NOT NULL),
    CONSTRAINT ck_cert_vencimiento CHECK (fecha_vencimiento IS NULL
                                         OR fecha_vencimiento >= fecha_emision),
    INDEX ix_certificaciones_lote         (id_lote),
    INDEX ix_certificaciones_finca        (id_finca),
    INDEX ix_certificaciones_vencimiento (fecha_vencimiento)
) ENGINE=InnoDB;

-- eventos_trazabilidad · HU-06
CREATE TABLE IF NOT EXISTS eventos_trazabilidad (
    id_evento   INT AUTO_INCREMENT PRIMARY KEY,
    id_lote     INT          NOT NULL,
    etapa       VARCHAR(50)  NOT NULL
                CHECK (etapa IN ('Finca', 'Beneficio', 'Puerto origen',
                                 'Tránsito marítimo', 'Aduana UE', 'Cliente')),
    fecha       DATE         NOT NULL,
    ubicacion   VARCHAR(150) NULL,
    descripcion VARCHAR(300) NULL,
    documento   VARCHAR(300) NULL,
    id_envio    INT          NULL,
    CONSTRAINT fk_eventos_lote  FOREIGN KEY (id_lote)  REFERENCES lotes  (id_lote)  ON DELETE CASCADE,
    CONSTRAINT fk_eventos_envio FOREIGN KEY (id_envio) REFERENCES envios (id_envio) ON DELETE SET NULL,
    INDEX ix_eventos_lote  (id_lote),
    INDEX ix_eventos_etapa (etapa)
) ENGINE=InnoDB;

-- cotizaciones · HU-08
CREATE TABLE IF NOT EXISTS cotizaciones (
    id_cotizacion  INT AUTO_INCREMENT PRIMARY KEY,
    numero         VARCHAR(60)  NOT NULL UNIQUE,
    id_cliente     INT          NOT NULL,
    id_usuario     INT          NOT NULL,
    fecha          DATE         NOT NULL,
    validez_dias   INT          NOT NULL DEFAULT 15,
    moneda         VARCHAR(10)  NOT NULL DEFAULT 'EUR',
    incoterm       VARCHAR(20)  NOT NULL DEFAULT 'FOB',
    estado         VARCHAR(30)  NOT NULL DEFAULT 'Borrador'
                   CHECK (estado IN ('Borrador', 'Enviada', 'Aceptada', 'Rechazada', 'Vencida')),
    precio_kg      DECIMAL(12, 2) NOT NULL,
    cantidad_kg    DECIMAL(12, 2) NOT NULL,
    puerto_origen  VARCHAR(100) NULL,
    puerto_destino VARCHAR(100) NULL,
    observaciones  TEXT         NULL,
    id_exportacion INT          NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cotizaciones_cliente    FOREIGN KEY (id_cliente)    REFERENCES clientes      (id_cliente)    ON DELETE CASCADE,
    CONSTRAINT fk_cotizaciones_usuario    FOREIGN KEY (id_usuario)    REFERENCES usuarios      (id_usuario)    ON DELETE RESTRICT,
    CONSTRAINT fk_cotizaciones_exportacion FOREIGN KEY (id_exportacion) REFERENCES exportaciones (id_exportacion) ON DELETE SET NULL,
    CONSTRAINT ck_cotizacion_precio   CHECK (precio_kg > 0),
    CONSTRAINT ck_cotizacion_cantidad CHECK (cantidad_kg > 0),
    CONSTRAINT ck_cotizacion_validez  CHECK (validez_dias BETWEEN 1 AND 365),
    INDEX ix_cotizaciones_cliente (id_cliente),
    INDEX ix_cotizaciones_estado  (estado)
) ENGINE=InnoDB;

-- ===========================================================================
-- Extensiones de los Sprint 3 y 4
-- ===========================================================================

-- pagos · HU-14
CREATE TABLE IF NOT EXISTS pagos (
    id_pago        INT AUTO_INCREMENT PRIMARY KEY,
    id_exportacion INT          NOT NULL,
    id_usuario     INT          NOT NULL,
    fecha          DATE         NOT NULL,
    tipo           VARCHAR(50)  NOT NULL DEFAULT 'Anticipo'
                   CHECK (tipo IN ('Anticipo', 'Pago parcial', 'Pago final', 'Saldo', 'Reembolso')),
    metodo         VARCHAR(50)  NOT NULL DEFAULT 'Transferencia'
                   CHECK (metodo IN ('Transferencia', 'Carta de crédito', 'Cheque', 'Efectivo', 'Otro')),
    estado         VARCHAR(50)  NOT NULL DEFAULT 'Registrado'
                   CHECK (estado IN ('Registrado', 'Confirmado', 'Anulado')),
    valor          DECIMAL(14, 2) NOT NULL,
    moneda         VARCHAR(10)  NOT NULL DEFAULT 'EUR',
    referencia     VARCHAR(100) NULL,
    banco          VARCHAR(150) NULL,
    observaciones  TEXT         NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pagos_exportacion FOREIGN KEY (id_exportacion) REFERENCES exportaciones (id_exportacion) ON DELETE CASCADE,
    CONSTRAINT fk_pagos_usuario     FOREIGN KEY (id_usuario)     REFERENCES usuarios      (id_usuario)     ON DELETE RESTRICT,
    CONSTRAINT ck_pago_valor CHECK (valor > 0),
    INDEX ix_pagos_exportacion (id_exportacion),
    INDEX ix_pagos_estado      (estado),
    INDEX ix_pagos_fecha       (fecha)
) ENGINE=InnoDB;

-- notificaciones · HU-16
CREATE TABLE IF NOT EXISTS notificaciones (
    id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario      INT          NULL,
    rol_destino     VARCHAR(50)  NULL,
    tipo            VARCHAR(50)  NOT NULL DEFAULT 'Sistema'
                    CHECK (tipo IN ('Certificación', 'Envío', 'Pago', 'Pedido',
                                    'Sistema', 'Seguridad')),
    tono            VARCHAR(20)  NOT NULL DEFAULT 'azul',
    titulo          VARCHAR(200) NOT NULL,
    detalle         TEXT         NULL,
    enlace          VARCHAR(200) NULL,
    clave           VARCHAR(160) NULL UNIQUE,
    leida           BOOLEAN      NOT NULL DEFAULT FALSE,
    fecha           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notificaciones_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE,
    INDEX ix_notificaciones_usuario (id_usuario),
    INDEX ix_notificaciones_rol     (rol_destino),
    INDEX ix_notificaciones_leida   (leida),
    INDEX ix_notificaciones_fecha   (fecha)
) ENGINE=InnoDB;

-- auditoria · HU-21
CREATE TABLE IF NOT EXISTS auditoria (
    id_auditoria   INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario     INT          NULL,
    usuario_correo VARCHAR(150) NULL,
    accion         VARCHAR(100) NOT NULL,
    entidad        VARCHAR(80)  NULL,
    id_entidad     VARCHAR(50)  NULL,
    detalle        TEXT         NULL,
    metodo         VARCHAR(10)  NULL,
    ruta           VARCHAR(300) NULL,
    estado_http    INT          NULL,
    ip             VARCHAR(60)  NULL,
    fecha          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_auditoria_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE SET NULL,
    INDEX ix_auditoria_usuario (id_usuario),
    INDEX ix_auditoria_fecha   (fecha),
    INDEX ix_auditoria_entidad (entidad)
) ENGINE=InnoDB;

-- tipos_cambio · HU-19. `tasa` son unidades de la moneda por 1 EUR.
CREATE TABLE IF NOT EXISTS tipos_cambio (
    id_tipo_cambio INT AUTO_INCREMENT PRIMARY KEY,
    moneda         VARCHAR(10)    NOT NULL,
    tasa           DECIMAL(18, 6) NOT NULL,
    fecha          DATE           NOT NULL,
    fuente         VARCHAR(100)   NULL,
    created_at     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tipo_cambio_moneda_fecha UNIQUE (moneda, fecha),
    CONSTRAINT ck_tipo_cambio_tasa CHECK (tasa > 0),
    INDEX ix_tipos_cambio_fecha (fecha)
) ENGINE=InnoDB;

-- respaldos · HU-22
CREATE TABLE IF NOT EXISTS respaldos (
    id_respaldo  INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(200) NOT NULL,
    ruta         VARCHAR(400) NOT NULL,
    tamano_bytes INT          NOT NULL DEFAULT 0,
    checksum     VARCHAR(64)  NULL,
    tipo         VARCHAR(50)  NOT NULL DEFAULT 'Manual'
                 CHECK (tipo IN ('Manual', 'Automática')),
    estado       VARCHAR(50)  NOT NULL DEFAULT 'Completado'
                 CHECK (estado IN ('Completado', 'Fallido', 'Restaurado')),
    tablas       INT          NOT NULL DEFAULT 0,
    registros    INT          NOT NULL DEFAULT 0,
    detalle      TEXT         NULL,
    id_usuario   INT          NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_respaldos_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE SET NULL,
    INDEX ix_respaldos_fecha (created_at)
) ENGINE=InnoDB;

-- registros_integracion · HU-20
CREATE TABLE IF NOT EXISTS registros_integracion (
    id_registro INT AUTO_INCREMENT PRIMARY KEY,
    servicio    VARCHAR(60)  NOT NULL,
    accion      VARCHAR(100) NOT NULL,
    estado      VARCHAR(30)  NOT NULL DEFAULT 'ok',
    mensaje     TEXT         NULL,
    detalle     TEXT         NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_registros_integracion_servicio (servicio),
    INDEX ix_registros_integracion_fecha    (created_at)
) ENGINE=InnoDB;

-- ===========================================================================
-- Nota sobre el orden de las tablas
--
-- En PostgreSQL la tabla `envios` declara su clave foránea a `contenedores`
-- mediante un ALTER TABLE al final del script, porque `contenedores` se crea
-- después. En MySQL el orden es estrictamente topológico: `contenedores` se
-- declara antes que `envios` y no hace falta ese paso adicional.
-- ===========================================================================

-- solicitudes_pedido · solicitudes recibidas desde el portal de compradores
CREATE TABLE IF NOT EXISTS solicitudes_pedido (
    id_solicitud   INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente     INT           NOT NULL,
    id_usuario     INT           NOT NULL,
    id_producto    INT           NOT NULL,
    cantidad_kg    DECIMAL(12, 2) NOT NULL CHECK (cantidad_kg > 0),
    incoterm       VARCHAR(20)   NOT NULL DEFAULT 'FOB',
    puerto_destino VARCHAR(100)  NULL,
    observaciones  TEXT          NULL,
    estado         VARCHAR(30)   NOT NULL DEFAULT 'Pendiente',
    created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_solicitud_cliente FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente) ON DELETE CASCADE,
    CONSTRAINT fk_solicitud_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE RESTRICT,
    CONSTRAINT fk_solicitud_producto FOREIGN KEY (id_producto) REFERENCES productos (id_producto) ON DELETE RESTRICT,
    INDEX ix_solicitudes_pedido_cliente (id_cliente),
    INDEX ix_solicitudes_pedido_estado (estado)
) ENGINE=InnoDB;
