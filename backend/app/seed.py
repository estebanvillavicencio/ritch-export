"""Carga de datos iniciales (semilla) para desarrollo y demostración.

Uso:

    python -m app.seed            # crea lo que falte
    python -m app.seed --reset    # borra y vuelve a crear

Los datos reproducen el escenario del mockup: la finca La Esperanza en Huila,
el lote CO-HUI-2026-0912 y los cuatro importadores europeos del panel.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.config import settings
from app.models import (
    CalidadLote,
    Certificacion,
    Cliente,
    Contenedor,
    Cotizacion,
    DetalleExportacion,
    DocumentoExportacion,
    Envio,
    EstadoCalidad,
    EstadoCotizacion,
    EstadoDocumento,
    EstadoEnvio,
    EstadoExportacion,
    EstadoPago,
    EtapaTrazabilidad,
    EventoTrazabilidad,
    Exportacion,
    Finca,
    Lote,
    MetodoPago,
    Notificacion,
    Pago,
    Producto,
    RegistroIntegracion,
    Respaldo,
    Rol,
    TipoCambio,
    TipoCertificacion,
    TipoDocumento,
    TipoNotificacion,
    TipoPago,
    TipoProducto,
    Usuario,
)
from app.security import hash_password
from app.services.reglas import (
    generar_codigo_lote,
    generar_numero_contrato,
    recalcular_disponibles,
)

CONTRASENA_DEMO = settings.demo_password

#: Usuarios del equipo. Son los cuatro del sprint y nada más: no hay cuentas
#: de relleno, así que la lista de la pantalla de acceso, la que imprime este
#: script y la que aparece en el documento son las mismas.
EQUIPO = [
    ("Andres Esteban Villavicencio Ojeda", "andres.villavicencio@ritch.com", Rol.ADMINISTRADOR),
    ("Juan Sebastian Rios Inagua", "juan.iguia@ritch.com", Rol.ADMINISTRADOR),
    ("Juan Camilo Araujo Portilla", "juan.araujo@ritch.com", Rol.COMERCIAL),
    ("Dario Sebastian Paz Cabrera", "dario.paz@ritch.com", Rol.LOGISTICA),
]

#: (correo, contraseña) de la cuenta de demostración de un cliente europeo.
#: Va aparte de `EQUIPO` porque no es del equipo: es el contacto de una de las
#: empresas importadoras, y sirve para mostrar el portal (HU-10).
COMPRADOR = ("comprador@cafe-rotterdam.nl", settings.buyer_password)

CLIENTES = [
    ("Löwe Kaffee GmbH", "Alemania", "Speicherstraße 88, 20457 Hamburg", "info@lowekaffee.de", "+49 40 5550 1120", "DE8145092", "Hamburgo", "Katharina Löwe"),
    ("Torrefazione Adriatica", "Italia", "Via del Porto 14, 34121 Trieste", "acquisti@torrefazadri.it", "+39 040 631 442", "IT00998810442", "Trieste", "Marco Benassi"),
    ("Café Rotterdam BV", "Países Bajos", "Waalhaven Zuidzijde 12, 3088 HH Rotterdam", "inkoop@caferotterdam.nl", "+31 10 495 2200", "NL809123456B01", "Rotterdam", "Sanne de Vries"),
    ("Nordic Cacao AB", "Suecia", "Kvarnbergsgatan 2, 411 05 Göteborg", "import@nordiccacao.se", "+46 31 774 6100", "SE556677889901", "Gotemburgo", "Erik Lundqvist"),
    ("Cacao & Co. Handels GmbH", "Austria", "Schottenring 18, 1020 Wien", "einkauf@cacao-co.at", "+43 1 515 330", "ATFN12345Z", "Hamburgo", "Julia Brandt"),
]

PRODUCTOS = [
    ("Café pergamino Huila", TipoProducto.CAFE, "Café arábigo de altura, proceso lavado", "Caturra · Castillo", "7850.00"),
    ("Café verde Colombia Premium", TipoProducto.CAFE, "Café trillado y descafeinado en origen", "Castillo Colombia", "9250.00"),
    ("Cacao fino de aroma", TipoProducto.CACAO, "Cacao fermentado y secado al sol", "Criollo · Forastero", "6450.00"),
    ("Cacao orgánico en grano", TipoProducto.CACAO, "Grano de cacao para industria del chocolate", "Nacional", "7180.00"),
]

FINCAS = [
    # (nombre, ubicación, departamento, propietario, productor, asociación,
    #  altura msnm, superficie ha, capacidad kg, latitud, longitud)
    ("Finca La Esperanza", "Vereda El Cedro, Pitalito", "Huila", "María Peralta", "Andrés Quintero", "Asociación Cafetera del Sur", 1720, 6.5, 14000, "2.317778", "-75.723611"),
    ("Finca El Mirador", "Vereda San Agustín, Garzón", "Huila", "Jorge Eduardo Ramírez", "Luz Marina Díaz", "Asociación Cafetera del Sur", 1850, 4.2, 9000, "2.312444", "-75.645833"),
    ("Finca La Palmera", "Corregimiento Moaña, Apartadó", "Antioquia", "Hernán Londoño Ruiz", "Unión de Cafeteros de Urabá", "Coopcafé Urabá", 1250, 18.0, 32000, "7.585833", "-76.532222"),
    ("Finca San José", "Vereda La Colonia, Carmen de Viboral", "Antioquia", "Gloria Sánchez Montoya", "Asociación de Cafeteros de Carmen", "Coopcafé Urabá", 1480, 9.8, 21000, "6.253056", "-75.371389"),
    ("Finca Cacao Alto", "Vereda Juan XIII, Tibú", "Norte de Santander", "Asociación de Cacaoteros del Catatumbo", "Productores de Cacao del Catatumbo", "Asociación Cacaotera del Catatumbo", 640, 12.5, 18000, "8.647222", "-72.869722"),
    ("Finca El Cacao", "Palenque, Bolívar", "Bolívar", "Rosa Hernández Padilla", "Palmicultores de Palenque", "ASOPALEN", 380, 7.3, 11000, "10.442778", "-74.799444"),
]

LOTES = [
    # finca_idx, producto_idx, kg, dias_atras_cosecha, altura, estado
    (0, 0, Decimal("12000"), 12, 1720, EstadoCalidad.APROBADO),
    (0, 2, Decimal("5400"), 25, 1680, EstadoCalidad.APROBADO),
    (1, 0, Decimal("8500"), 34, 1850, EstadoCalidad.APROBADO_CON_RESERVA),
    (2, 1, Decimal("22000"), 48, 1250, EstadoCalidad.APROBADO),
    (2, 3, Decimal("9500"), 52, 1220, EstadoCalidad.EN_ANALISIS),
    (3, 0, Decimal("14500"), 61, 1480, EstadoCalidad.APROBADO),
    (4, 2, Decimal("18000"), 70, 640, EstadoCalidad.APROBADO),
    (4, 3, Decimal("8200"), 74, 700, EstadoCalidad.PENDIENTE),
    (5, 2, Decimal("11000"), 88, 380, EstadoCalidad.RECHAZADO),
]

#: Certificaciones por lote (índice de lote, tipo, entidad, días desde emisión,
#: días hasta vencimiento, georreferenciado)
CERTIFICACIONES = [
    (0, TipoCertificacion.EUDR, "Rainforest Alliance", 400, 330, True),
    (0, TipoCertificacion.ORGANICO, "Control Union Certification", 380, 350, True),
    (0, TipoCertificacion.FAIRTRADE, "FLOCERT", 300, 30, True),
    (1, TipoCertificacion.EUDR, "Rainforest Alliance", 380, 20, True),
    (1, TipoCertificacion.ORGANICO, "Control Union Certification", 200, 165, True),
    (2, TipoCertificacion.ORGANICO, "Control Union Certification", 500, 40, True),
    (3, TipoCertificacion.FAIRTRADE, "FLOCERT", 150, 215, True),
    (4, TipoCertificacion.EUDR, "Preferred by Nature", 90, 275, False),
    (5, TipoCertificacion.ORGANICO, "Control Union Certification", 250, 115, True),
    (6, TipoCertificacion.EUDR, "Rainforest Alliance", 120, 245, True),
    (7, TipoCertificacion.FAIRTRADE, "FLOCERT", 45, 60, True),
]

CALIDADES = [
    (0, "10.5", "86.5", "0.58", "17.0", "0.03", "1.35", "SCA", "Special"),
    (1, "9.8", "83.0", "0.61", "16.5", "0.05", "1.48", "SCA", "Excelente"),
    (2, "12.8", "78.5", "0.66", "15.0", "0.09", "1.52", "SCA", "Estándar"),
    (3, "10.9", "85.0", "0.55", "18.0", "0.02", "1.30", "SCA", "Special"),
    (4, "11.4", None, "0.60", "16.0", "0.04", None, "Laboratorio Andino", None),
    (5, "11.2", "84.0", "0.57", "17.5", "0.03", "1.40", "SCA", "Excelente"),
    (6, "8.9", "80.5", "0.64", "14.0", "0.11", "54.20", "CAOBISCO", "Grano fino"),
    (7, "9.4", None, None, None, None, "52.80", "CAOBISCO", None),
    (8, "14.2", "58.0", "0.78", "12.0", "0.31", "49.10", "CAOBISCO", "Rechazado"),
]

CONTENEDORES = [
    ("CNT-2026-0417", "40HC", "26400", "Maersk", True),
    ("CNT-2026-0418", "20GP", "28200", "Maersk", True),
    ("CNT-2026-0419", "40HC", "26400", "Hapag-Lloyd", True),
    ("CNT-2026-0420", "40RF", "27200", "MSC", False),
    ("CNT-2026-0421", "20GP", "28200", "CMA CGM", True),
]


def _p(*args) -> str | None:
    return None if args[0] is None else str(args[0])


def sembrar(db: Session, reset: bool = False) -> None:
    """Inserta los datos iniciales. Es idempotente salvo que ``reset``."""
    if reset:
        print("  borrando datos existentes…")
        for modelo in (
            RegistroIntegracion,
            Notificacion,
            Pago,
            TipoCambio,
            Respaldo,
            Cotizacion,
            DocumentoExportacion,
            Envio,
            DetalleExportacion,
            Exportacion,
            EventoTrazabilidad,
            CalidadLote,
            Certificacion,
            Lote,
            Contenedor,
            Finca,
            Producto,
            Cliente,
            Usuario,
        ):
            db.query(modelo).delete()
        db.commit()

    if db.scalar(select(func.count(Usuario.id_usuario))):
        print("  la base ya contiene usuarios; no se siembra nada nuevo")
        return

    hoy = date.today()

    # --- usuarios -------------------------------------------------------- #
    usuarios: list[Usuario] = []
    for nombre, correo, rol in EQUIPO:
        usuario = Usuario(
            nombre=nombre, correo=correo, contrasena_hash=hash_password(CONTRASENA_DEMO), rol=rol
        )
        db.add(usuario)
        usuarios.append(usuario)
    # Se buscan por correo y no por posición: si mañana entra o sale alguien,
    # estas variables no se corren en silencio.
    por_correo = {u.correo: u for u in usuarios}
    admin = por_correo["andres.villavicencio@ritch.com"]
    comercial = por_correo["juan.araujo@ritch.com"]
    logistica = por_correo["dario.paz@ritch.com"]
    # No hay nadie del equipo con el rol de Calidad, así que la catación queda
    # registrada por el administrador, que sí está permitido en ese módulo.
    calidad = admin
    db.flush()
    print(f"  {len(usuarios)} usuarios")

    # --- clientes -------------------------------------------------------- #
    clientes: list[Cliente] = []
    for empresa, pais, direccion, correo, tel, vat, puerto, contacto in CLIENTES:
        cliente = Cliente(
            nombre_empresa=empresa,
            pais=pais,
            direccion=direccion,
            correo=correo,
            telefono=tel,
            contacto=contacto,
            vat=vat,
            moneda_preferida="EUR",
            puerto_destino=puerto,
        )
        db.add(cliente)
        clientes.append(cliente)
    db.flush()
    print(f"  {len(clientes)} clientes")

    # --- cuenta de un cliente europeo (HU-10) ----------------------------- #
    # Se crea aquí y no aparte, porque `python -m app.seed --reset` borra la base
    # y la pantalla de acceso anuncia esta cuenta: si no estuviera en la semilla,
    # quedaríaListed pero no funcionaría después de cada reinicio.
    # Se usa el contacto que ya figura en la fila del cliente, así que no hay
    # ningún nombre inventado.
    comprador = Usuario(
        nombre=CLIENTES[2][7],
        correo=COMPRADOR[0],
        contrasena_hash=hash_password(COMPRADOR[1]),
        rol=Rol.CLIENTE_EU,
        id_cliente=clientes[2].id_cliente,
    )
    db.add(comprador)
    db.flush()
    usuarios.append(comprador)

    # --- productos ------------------------------------------------------- #
    productos: list[Producto] = []
    for nombre, tipo, descripcion, variedad, precio in PRODUCTOS:
        producto = Producto(
            nombre=nombre,
            tipo=tipo,
            descripcion=descripcion,
            variedad=variedad,
            precio_referencia_eur=Decimal(precio),
        )
        db.add(producto)
        productos.append(producto)
    db.flush()
    print(f"  {len(productos)} productos")

    # --- fincas ---------------------------------------------------------- #
    fincas: list[Finca] = []
    for (nombre, ubicacion, depto, propietario, productor, asociacion, altura, sup, cap, lat, lon) in FINCAS:
        finca = Finca(
            nombre=nombre,
            ubicacion=ubicacion,
            departamento=depto,
            propietario=propietario,
            productor=productor,
            asociacion=asociacion,
            altura_msnm=altura,
            superficie_ha=Decimal(sup),
            capacidad_produccion_kg=Decimal(cap),
            latitud=Decimal(lat),
            longitud=Decimal(lon),
        )
        db.add(finca)
        fincas.append(finca)
    db.flush()
    print(f"  {len(fincas)} fincas")

    # --- lotes ----------------------------------------------------------- #
    lotes: list[Lote] = []
    for finca_i, producto_i, kg, dias, altura, estado in LOTES:
        cosecha = hoy - timedelta(days=dias)
        lote = Lote(
            codigo_lote=generar_codigo_lote(db),
            id_finca=fincas[finca_i].id_finca,
            id_producto=productos[producto_i].id_producto,
            cantidad_kg=kg,
            disponible_kg=kg,
            fecha_cosecha=cosecha,
            estado_calidad=estado,
            variedad=productos[producto_i].variedad,
            altura_msnm=altura,
        )
        db.add(lote)
        # El correlativo se consulta en la base, así que el lote debe quedar
        # insertado antes de generar el siguiente código.
        db.flush()
        lotes.append(lote)
    db.flush()
    print(f"  {len(lotes)} lotes (primer código: {lotes[0].codigo_lote})")

    # --- eventos de trazabilidad ----------------------------------------- #
    for lote in lotes:
        finca = fincas[[f.id_finca for f in fincas].index(lote.id_finca)]
        db.add(
            EventoTrazabilidad(
                id_lote=lote.id_lote,
                etapa=EtapaTrazabilidad.FINCA,
                fecha=lote.fecha_cosecha,
                ubicacion=f"{finca.ubicacion}, {finca.departamento}",
                descripcion=f"Cosecha registrada en {finca.nombre}",
            )
        )
        db.add(
            EventoTrazabilidad(
                id_lote=lote.id_lote,
                etapa=EtapaTrazabilidad.BENEFICIO,
                fecha=lote.fecha_cosecha + timedelta(days=20),
                ubicacion=f"Beneficio {finca.nombre.replace('Finca ', '')}",
                descripcion="Beneficio y secado completados",
            )
        )
    db.flush()

    # --- certificaciones ------------------------------------------------- #
    for lote_i, tipo, entidad, emision, vence, geo in CERTIFICACIONES:
        db.add(
            Certificacion(
                id_lote=lotes[lote_i].id_lote,
                tipo=tipo,
                entidad_emisora=entidad,
                numero_certificado=f"{tipo.value[:3].upper()}-{hoy.year}-{lote_i + 100:04d}",
                fecha_emision=hoy - timedelta(days=emision),
                fecha_vencimiento=hoy + timedelta(days=vence),
                lote_georreferenciado=geo,
            )
        )
    db.flush()
    print(f"  {len(CERTIFICACIONES)} certificaciones")

    # --- calidad --------------------------------------------------------- #
    for (lote_i, hum, cat, aw, gran, imp, cafeina, metodo, clasif) in CALIDADES:
        db.add(
            CalidadLote(
                id_lote=lotes[lote_i].id_lote,
                humedad=Decimal(hum) if hum else None,
                puntaje_cata=Decimal(cat) if cat else None,
                actividad_agua=Decimal(aw) if aw else None,
                granulometria=Decimal(gran) if gran else None,
                impurezas=Decimal(imp) if imp else None,
                cafeina_pct=Decimal(cafeina) if cafeina else None,
                prueba_metodos=metodo,
                clasificacion=clasif,
                laboratorio="Laboratorio Andino de Cafés" if metodo == "SCA" else "CAOBISCO",
                fecha_analisis=hoy - timedelta(days=30),
                aprobado_por=calidad.nombre if cat and Decimal(cat) >= 80 else None,
            )
        )
    db.flush()
    print(f"  {len(CALIDADES)} registros de calidad")

    # --- contenedores ---------------------------------------------------- #
    contenedores: list[Contenedor] = []
    for codigo, tipo, capacidad, naviera, disp in CONTENEDORES:
        c = Contenedor(
            codigo=codigo,
            tipo=tipo,
            capacidad_kg=Decimal(capacidad),
            naviera=naviera,
            disponible=disp,
        )
        db.add(c)
        contenedores.append(c)
    db.flush()
    print(f"  {len(contenedores)} contenedores")

    # --- cotizaciones ---------------------------------------------------- #
    cotizaciones = [
        Cotizacion(
            numero="QT-2026-0001",
            id_cliente=clientes[2].id_cliente,
            id_usuario=comercial.id_usuario,
            fecha=hoy - timedelta(days=9),
            validez_dias=15,
            moneda="EUR",
            incoterm="CIF",
            estado=EstadoCotizacion.ENVIADA,
            precio_kg=Decimal("9250.00"),
            cantidad_kg=Decimal("22000"),
            puerto_origen="Cartagena",
            puerto_destino="Rotterdam",
            observaciones="Café verde Colombia Premium, calidad Special.",
        ),
        Cotizacion(
            numero="QT-2026-0002",
            id_cliente=clientes[0].id_cliente,
            id_usuario=comercial.id_usuario,
            fecha=hoy - timedelta(days=5),
            validez_dias=21,
            moneda="EUR",
            incoterm="FOB",
            estado=EstadoCotizacion.ENVIADA,
            precio_kg=Decimal("7850.00"),
            cantidad_kg=Decimal("12000"),
            puerto_origen="Cartagena",
            puerto_destino="Hamburgo",
            observaciones="Café pergamino Huila, catación 86.5.",
        ),
        Cotizacion(
            numero="QT-2026-0003",
            id_cliente=clientes[3].id_cliente,
            id_usuario=comercial.id_usuario,
            fecha=hoy - timedelta(days=2),
            moneda="USD",
            incoterm="CFR",
            estado=EstadoCotizacion.BORRADOR,
            precio_kg=Decimal("7180.00"),
            cantidad_kg=Decimal("9000"),
            puerto_origen="Cartagena",
            puerto_destino="Gotemburgo",
        ),
    ]
    db.add_all(cotizaciones)
    db.flush()
    print(f"  {len(cotizaciones)} cotizaciones")

    # --- exportaciones y su detalle -------------------------------------- #
    # (cliente, usuario, dias_atras, estado, puerto_destino, incoterm,
    #  [(lote, kg, precio)], documentos, envios)
    escenarios = [
        (
            clientes[2], logistica, 38, EstadoExportacion.EN_TRANSITO, "Rotterdam", "CIF",
            [(3, Decimal("22000"), Decimal("9250.00"))],
            [
                ("Factura comercial", "FC-2026-0141", 36, EstadoDocumento.VALIDADO, True),
                ("Packing list", "PL-2026-0141", 36, EstadoDocumento.VALIDADO, True),
                ("Certificado de origen", "CO-2026-0141", 34, EstadoDocumento.EMITIDO, True),
                ("BL", "MAEU-4471288", 32, EstadoDocumento.VALIDADO, True),
            ],
            [
                dict(
                    transportadora="Maersk", numero_seguimiento="MAEU-4471288",
                    fecha_salida=hoy - timedelta(days=32), fecha_llegada=hoy + timedelta(days=3),
                    estado=EstadoEnvio.EN_ADUANA, id_contenedor=contenedores[0],
                    puerto_origen="Cartagena", puerto_destino="Rotterdam",
                    tipo_transporte="Marítimo", costo_flete=Decimal("4850.00"),
                )
            ],
        ),
        (
            clientes[0], logistica, 52, EstadoExportacion.ENTREGADO, "Hamburgo", "FOB",
            [(0, Decimal("12000"), Decimal("7850.00"))],
            [
                ("Factura comercial", "FC-2026-0118", 50, EstadoDocumento.VALIDADO, True),
                ("Packing list", "PL-2026-0118", 50, EstadoDocumento.VALIDADO, True),
                ("Certificado de origen", "CO-2026-0118", 48, EstadoDocumento.VALIDADO, True),
                ("BL", "HLCU-882301", 46, EstadoDocumento.VALIDADO, True),
            ],
            [
                dict(
                    transportadora="Hapag-Lloyd", numero_seguimiento="HLCU-882301",
                    fecha_salida=hoy - timedelta(days=46),
                    fecha_llegada=hoy - timedelta(days=14),
                    estado=EstadoEnvio.ENTREGADO, id_contenedor=contenedores[2],
                    puerto_origen="Cartagena", puerto_destino="Hamburgo",
                    tipo_transporte="Marítimo", costo_flete=Decimal("5120.00"),
                )
            ],
        ),
        (
            clientes[1], logistica, 26, EstadoExportacion.EN_PREPARACION, "Trieste", "CFR",
            [(2, Decimal("8000"), Decimal("7680.00"))],
            [
                ("Factura comercial", "FC-2026-0155", 24, EstadoDocumento.EMITIDO, False),
                ("Packing list", "PL-2026-0155", 24, EstadoDocumento.BORRADOR, False),
            ],
            [],
        ),
        (
            clientes[3], comercial, 12, EstadoExportacion.PEDIDO_RECIBIDO, "Gotemburgo", "CFR",
            [(6, Decimal("9000"), Decimal("6450.00"))],
            [],
            [],
        ),
        (
            clientes[4], comercial, 70, EstadoExportacion.EN_DESTINO, "Hamburgo", "DAP",
            [(7, Decimal("8000"), Decimal("7180.00"))],
            [
                ("Factura comercial", "FC-2026-0092", 66, EstadoDocumento.VALIDADO, True),
                ("AWB", "AWB-180-33412-90", 64, EstadoDocumento.EMITIDO, False),
            ],
            [
                dict(
                    transportadora="CMA CGM", numero_seguimiento="CMAU-3390127",
                    fecha_salida=hoy - timedelta(days=48),
                    fecha_llegada=hoy - timedelta(days=2),
                    estado=EstadoEnvio.ENTREGADO, id_contenedor=contenedores[3],
                    puerto_origen="Cartagena", puerto_destino="Hamburgo",
                    tipo_transporte="Marítimo", costo_flete=Decimal("4390.00"),
                )
            ],
        ),
        (
            clientes[2], comercial, 8, EstadoExportacion.EN_PRODUCCION, "Rotterdam", "CIF",
            [(5, Decimal("14500"), Decimal("7800.00"))],
            [("Factura comercial", "FC-2026-0160", 6, EstadoDocumento.BORRADOR, False)],
            [],
        ),
    ]

    exportaciones_creadas: list[Exportacion] = []
    for (cliente, usuario, dias, estado, destino, incoterm, detalles, docs, envios) in escenarios:
        fecha = hoy - timedelta(days=dias)
        total = sum((kg * precio for _, kg, precio in detalles), Decimal("0"))
        exportacion = Exportacion(
            id_cliente=cliente.id_cliente,
            id_usuario=usuario.id_usuario,
            fecha=fecha,
            estado=estado,
            moneda="EUR",
            numero_contrato=generar_numero_contrato(db),
            incoterm=incoterm,
            puerto_origen="Cartagena",
            puerto_destino=destino,
            valor_total=total,
        )
        db.add(exportacion)
        db.flush()
        exportaciones_creadas.append(exportacion)
        for lote_i, kg, precio in detalles:
            db.add(
                DetalleExportacion(
                    id_exportacion=exportacion.id_exportacion,
                    id_lote=lotes[lote_i].id_lote,
                    cantidad_kg=kg,
                    precio_kg=precio,
                )
            )
        db.flush()
        for tipo_doc, numero_doc, dias_emision, estado_doc, autorizado in docs:
            db.add(
                DocumentoExportacion(
                    id_exportacion=exportacion.id_exportacion,
                    tipo_documento=TipoDocumento(tipo_doc),
                    numero_documento=numero_doc,
                    fecha_emision=hoy - timedelta(days=dias_emision),
                    estado=estado_doc,
                    autorizado_cliente=autorizado,
                )
            )
        for datos_envio in envios:
            # Los escenarios guardan el objeto Contenedor; la columna es la FK.
            contenedor = datos_envio.pop("id_contenedor", None)
            if contenedor is not None:
                datos_envio["id_contenedor"] = contenedor.id_contenedor
            datos_envio["id_exportacion"] = exportacion.id_exportacion
            db.add(Envio(**datos_envio))
        db.flush()
    print(f"  {len(escenarios)} exportaciones con detalle, documentos y envíos")

    # --- pagos · HU-14 --------------------------------------------------- #
    # Anticipos y saldos coherentes con la cartera de cada contrato.
    pagos_demo = [
        (0, TipoPago.ANTICIPO, MetodoPago.TRANSFERENCIA, EstadoPago.CONFIRMADO, "0.30", 30),
        (1, TipoPago.PAGO_FINAL, MetodoPago.CARTA_CREDITO, EstadoPago.CONFIRMADO, "1.00", 40),
        (2, TipoPago.ANTICIPO, MetodoPago.TRANSFERENCIA, EstadoPago.REGISTRADO, "0.20", 20),
        (4, TipoPago.PAGO_PARCIAL, MetodoPago.TRANSFERENCIA, EstadoPago.CONFIRMADO, "0.50", 45),
        (5, TipoPago.ANTICIPO, MetodoPago.CARTA_CREDITO, EstadoPago.REGISTRADO, "0.10", 6),
    ]
    for indice, tipo, metodo, estado, fraccion, dias in pagos_demo:
        exportacion = exportaciones_creadas[indice]
        valor = (Decimal(exportacion.valor_total) * Decimal(fraccion)).quantize(Decimal("0.01"))
        db.add(
            Pago(
                id_exportacion=exportacion.id_exportacion,
                id_usuario=comercial.id_usuario,
                fecha=hoy - timedelta(days=dias),
                tipo=tipo,
                metodo=metodo,
                estado=estado,
                valor=valor,
                moneda=exportacion.moneda,
                referencia=f"RF-{exportacion.id_exportacion:04d}-{tipo.value[:3].upper()}",
                banco="Bancolombia" if metodo == MetodoPago.TRANSFERENCIA else "Banco de Bogotá",
                observaciones="Pago de demostración de la semilla.",
            )
        )
    db.flush()
    print(f"  {len(pagos_demo)} pagos")

    # --- notificaciones · HU-16 ------------------------------------------ #
    db.add_all(
        [
            Notificacion(
                tipo=TipoNotificacion.PAGO,
                tono="verde",
                titulo="Anticipo confirmado · Café Rotterdam BV",
                detalle="Se confirmó el 30 % del contrato en tránsito a Rotterdam.",
                enlace="#/financiero",
                rol_destino=Rol.FINANCIERO.value,
                clave="seed-pago-anticipo-rotterdam",
            ),
            Notificacion(
                tipo=TipoNotificacion.CERTIFICACION,
                tono="gold",
                titulo="Certificación Fairtrade por renovar",
                detalle="El lote de Café Rotterdam BV renueva en menos de 45 días.",
                enlace="#/lotes",
                rol_destino=Rol.ADMINISTRADOR.value,
                clave="seed-certificacion-por-renovar",
            ),
            Notificacion(
                tipo=TipoNotificacion.SISTEMA,
                tono="azul",
                titulo="Sprints 3 y 4 disponibles",
                detalle="Pagos, notificaciones, auditoría, multimoneda, integraciones y respaldos.",
                enlace="#/panel",
                clave="seed-sprints-3-4",
            ),
        ]
    )

    # --- tipos de cambio · HU-19 ----------------------------------------- #
    db.add_all(
        [
            TipoCambio(moneda="USD", tasa=Decimal("1.09"), fecha=hoy, fuente="Respaldo local RiTech"),
            TipoCambio(moneda="COP", tasa=Decimal("4300"), fecha=hoy, fuente="Respaldo local RiTech"),
            TipoCambio(
                moneda="USD",
                tasa=Decimal("1.08"),
                fecha=hoy - timedelta(days=30),
                fuente="Respaldo local RiTech",
            ),
        ]
    )

    # --- bitácora de integraciones · HU-20 -------------------------------- #
    db.add_all(
        [
            RegistroIntegracion(
                servicio="Tipos de cambio",
                accion="Actualizar tasas",
                estado="simulado",
                mensaje="Tasas de respaldo cargadas por la semilla.",
                detalle='{"modo": "respaldo local"}',
            ),
            RegistroIntegracion(
                servicio="Correo",
                accion="Prueba de envío",
                estado="simulado",
                mensaje="Correo de bienvenida simulado para el equipo comercial.",
                detalle='{"destinatario": "juan.araujo@ritch.com"}',
            ),
        ]
    )
    db.flush()
    print("  tipos de cambio, notificaciones y bitácora de integraciones")

    recalcular_disponibles(db)
    db.commit()
    print("  datos sembrados correctamente")


def main() -> None:
    parser = argparse.ArgumentParser(description="Siembra los datos iniciales de RiTech SAS")
    parser.add_argument(
        "--reset", action="store_true", help="Borra los datos existentes antes de sembrar"
    )
    args = parser.parse_args()

    print("RiTech SAS · siembra de datos")
    init_db()
    with SessionLocal() as db:
        sembrar(db, reset=args.reset)
    print("\nEquipo — credencial configurada mediante RITECH_DEMO_PASSWORD")
    for _nombre, correo, rol in EQUIPO:
        print(f"  {rol.value:<16} {correo}")
    print("\nCliente europeo (portal) — credencial configurada mediante RITECH_BUYER_PASSWORD")
    print(f"  {'Cliente europeo':<16} {COMPRADOR[0]}")


if __name__ == "__main__":
    main()
