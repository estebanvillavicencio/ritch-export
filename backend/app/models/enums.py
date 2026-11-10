"""Catálogos y dominios de valores compartidos por todo el sistema.

Todos los dominios se persisten como VARCHAR + CHECK (``native_enum=False``)
para que el mismo modelo funcione sobre PostgreSQL, MySQL y SQLite.
"""

from __future__ import annotations

from enum import Enum

from sqlalchemy import Enum as SAEnum


def enum_col(enum_cls: type[Enum], length: int = 50):
    """Columna VARCHAR + CHECK portable entre PostgreSQL, MySQL y SQLite.

    ``native_enum=False`` evita tipos ENUM nativos, que no son portables y
    complican las migraciones. ``values_callable`` hace que se guarde el
    *valor* del enumerado (p. ej. «En tránsito») y no su nombre interno.
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        values_callable=lambda cls: [m.value for m in cls],
        validate_strings=True,
    )


class Rol(str, Enum):
    """RR-004 · Roles de usuario soportados por el sistema."""

    ADMINISTRADOR = "Administrador"
    COMERCIAL = "Comercial"
    LOGISTICA = "Logística"
    CALIDAD = "Calidad"
    FINANCIERO = "Financiero"
    CLIENTE_EU = "Cliente europeo"


class TipoProducto(str, Enum):
    """Café o cacao (doc. base de datos · tabla `productos`)."""

    CAFE = "Café"
    CACAO = "Cacao"


class EstadoExportacion(str, Enum):
    """Cadena de estados del módulo de seguimiento (Informe §6.9)."""

    PEDIDO_RECIBIDO = "Pedido recibido"
    EN_PREPARACION = "En preparación"
    EN_PRODUCCION = "En producción"
    EN_PUERTO = "En puerto"
    EN_TRANSITO = "En tránsito"
    EN_DESTINO = "En destino"
    ENTREGADO = "Entregado"
    ANULADO = "Anulado"


#: Orden de la cadena de estados; se usa para el progreso y las transiciones.
ORDEN_EXPORTACION: tuple[EstadoExportacion, ...] = (
    EstadoExportacion.PEDIDO_RECIBIDO,
    EstadoExportacion.EN_PREPARACION,
    EstadoExportacion.EN_PRODUCCION,
    EstadoExportacion.EN_PUERTO,
    EstadoExportacion.EN_TRANSITO,
    EstadoExportacion.EN_DESTINO,
    EstadoExportacion.ENTREGADO,
)


class EstadoEnvio(str, Enum):
    """Estados del envío (módulo de logística · doc. base de datos `envios`)."""

    PROGRAMADO = "Programado"
    EN_TRANSITO = "En tránsito"
    EN_ADUANA = "En aduana"
    EN_DESTINO = "En destino"
    ENTREGADO = "Entregado"
    DEMORADO = "Demorado"
    INCIDENCIA = "Incidencia"


class EstadoCalidad(str, Enum):
    """Clasificación de calidad de un lote (doc. `lotes.estado_calidad`)."""

    PENDIENTE = "Pendiente"
    EN_ANALISIS = "En análisis"
    APROBADO = "Aprobado"
    APROBADO_CON_RESERVA = "Aprobado con reserva"
    RECHAZADO = "Rechazado"


class EstadoCertificacion(str, Enum):
    VIGENTE = "Vigente"
    POR_RENOVAR = "Por renovar"
    VENCIDA = "Vencida"
    PENDIENTE = "Pendiente"


class TipoCertificacion(str, Enum):
    """Certificaciones controladas por el módulo de cumplimiento (Informe §6.4)."""

    EUDR = "EUDR"
    ORGANICO = "Orgánico"
    FAIRTRADE = "Fairtrade"
    FITOSANITARIO = "Fitosanitario"
    RAINFOREST_ALLIANCE = "Rainforest Alliance"
    OTRO = "Otro"


class TipoDocumento(str, Enum):
    """Documentos de exportación (Informe §6.7)."""

    FACTURA_COMERCIAL = "Factura comercial"
    PACKING_LIST = "Packing list"
    CERTIFICADO_ORIGEN = "Certificado de origen"
    BL = "BL"
    AWB = "AWB"
    CERTIFICADO = "Certificado"
    ADUANA = "Documento aduanero"


class EstadoDocumento(str, Enum):
    BORRADOR = "Borrador"
    EMITIDO = "Emitido"
    VALIDADO = "Validado"
    ANULADO = "Anulado"


class EstadoCotizacion(str, Enum):
    """HU-08 · Cotizaciones y contratos en diferentes monedas."""

    BORRADOR = "Borrador"
    ENVIADA = "Enviada"
    ACEPTADA = "Aceptada"
    RECHAZADA = "Rechazada"
    VENCIDA = "Vencida"


class Moneda(str, Enum):
    """Multimoneda (HU-19)."""

    EUR = "EUR"
    USD = "USD"
    COP = "COP"


class TipoPago(str, Enum):
    """HU-14 · naturaleza del pago de una exportación."""

    ANTICIPO = "Anticipo"
    PAGO_PARCIAL = "Pago parcial"
    PAGO_FINAL = "Pago final"
    SALDO = "Saldo"
    REEMBOLSO = "Reembolso"


class MetodoPago(str, Enum):
    """HU-14 · medio por el que entra o sale el dinero."""

    TRANSFERENCIA = "Transferencia"
    CARTA_CREDITO = "Carta de crédito"
    CHEQUE = "Cheque"
    EFECTIVO = "Efectivo"
    OTRO = "Otro"


class EstadoPago(str, Enum):
    """HU-14 · ciclo de vida de un pago."""

    REGISTRADO = "Registrado"
    CONFIRMADO = "Confirmado"
    ANULADO = "Anulado"


class TipoNotificacion(str, Enum):
    """HU-16 · origen del aviso."""

    CERTIFICACION = "Certificación"
    ENVIO = "Envío"
    PAGO = "Pago"
    PEDIDO = "Pedido"
    SISTEMA = "Sistema"
    SEGURIDAD = "Seguridad"


class TipoRespaldo(str, Enum):
    """HU-22 · cómo se originó la copia de seguridad."""

    MANUAL = "Manual"
    AUTOMATICO = "Automática"


class EstadoRespaldo(str, Enum):
    """HU-22 · resultado de la copia de seguridad."""

    COMPLETADO = "Completado"
    FALLIDO = "Fallido"
    RESTAURADO = "Restaurado"


class EtapaTrazabilidad(str, Enum):
    """Recorrido de un lote: HU-06 · de la finca al destino.

    Las seis primeras etapas corresponden a la línea de tiempo del mockup
    (Finca · Beneficio · Puerto origen · Tránsito marítimo · Aduana UE · Cliente).
    """

    FINCA = "Finca"
    BENEFICIO = "Beneficio"
    PUERTO_ORIGEN = "Puerto origen"
    TRANSITO_MARITIMO = "Tránsito marítimo"
    ADUANA_UE = "Aduana UE"
    CLIENTE = "Cliente"


#: Etapas en orden, tal como aparecen en la línea de tiempo del panel.
ORDEN_TRAZABILIDAD: tuple[EtapaTrazabilidad, ...] = (
    EtapaTrazabilidad.FINCA,
    EtapaTrazabilidad.BENEFICIO,
    EtapaTrazabilidad.PUERTO_ORIGEN,
    EtapaTrazabilidad.TRANSITO_MARITIMO,
    EtapaTrazabilidad.ADUANA_UE,
    EtapaTrazabilidad.CLIENTE,
)


class PaisUE(str, Enum):
    """Países de destino de la Unión Europea (RR-005 · escalabilidad)."""

    ALEMANIA = "Alemania"
    PAISES_BAJOS = "Países Bajos"
    ITALIA = "Italia"
    SUECIA = "Suecia"
    FRANCIA = "Francia"
    BÉLGICA = "Bélgica"
    PORTUGAL = "Portugal"
    POLONIA = "Polonia"


class PuertoUE(str, Enum):
    ROTTERDAM = "Rotterdam"
    HAMBURGO = "Hamburgo"
    TRIESTE = "Trieste"
    GÖTEBORG = "Gotemburgo"
    AMBERES = "Amberes"
    LEHAVRE = "Le Havre"
    LISBOA = "Lisboa"
    GDANSK = "Gdansk"


class PuertoOrigen(str, Enum):
    """Puertos de salida en Colombia (principal origen de café y cacao)."""

    CARTAGENA = "Cartagena"
    BARRANQUILLA = "Barranquilla"
    BUENAVENTURA = "Buenaventura"
    SANTA_MARTA = "Santa Marta"
    CUCUTA = "Cúcuta"
