"""Módulo Comercial: cotizaciones, exportaciones y documentos.

HU-03 (clientes UE) · HU-08 (cotizaciones y contratos) · HU-09 (pedidos)
HU-10 (documentación) · HU-11 (gestión aduanera).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import (
    Cliente,
    Cotizacion,
    DetalleExportacion,
    DocumentoExportacion,
    EstadoCotizacion,
    EstadoDocumento,
    EstadoExportacion,
    Exportacion,
    Lote,
    Rol,
    Usuario,
)
from app.schemas import (
    CotizacionConversion,
    CotizacionCreate,
    CotizacionRead,
    CotizacionUpdate,
    DocumentoBase,
    DocumentoRead,
    DocumentoUpdate,
    ExportacionCreate,
    ExportacionRead,
    ExportacionUpdate,
    Mensaje,
    Paginado,
)
from app.services import auditoria, notificaciones
from app.services.reglas import (
    generar_numero_contrato,
    generar_numero_cotizacion,
    puede_transicionar,
    recalcular_disponibles,
    verificar_disponibilidad,
)

router = APIRouter(tags=["Comercial"], dependencies=[Depends(get_current_user)])

#: Roles que pueden LEER las exportaciones. El cliente europeo entra aquí, pero
#: `_cargar_exportacion` y `listar_exportaciones` le recortan la respuesta a su
#: propia empresa.
_roles_lectura = require_roles(
    Rol.ADMINISTRADOR, Rol.COMERCIAL, Rol.LOGISTICA, Rol.FINANCIERO, Rol.CLIENTE_EU
)

#: Todo lo demás del módulo comercial es interno de RiTech. El cliente europeo no
#: entra: no puede crear ni cambiar cotizaciones, exportaciones ni documentos.
#: Es lo que impide que una cuenta de comprador convierta el portal en un panel de
#: escritura.
_roles_comercial = require_roles(
    Rol.ADMINISTRADOR, Rol.COMERCIAL, Rol.LOGISTICA, Rol.FINANCIERO
)
_roles_ventas = require_roles(Rol.ADMINISTRADOR, Rol.COMERCIAL)


def _es_cliente(usuario: Usuario) -> bool:
    return usuario.rol == Rol.CLIENTE_EU


def _cargar_exportacion(
    db: Session, id_exportacion: int, usuario: Usuario | None = None
) -> Exportacion:
    """Carga una exportación y, si quien pregunta es un cliente, se cernea.

    Sin empresa asignada no se le muestra nada; con empresa, solo puede abrir las
    exportaciones de esa empresa. Un 404 y no un 403, para no confirmar que el
    pedido existe en otra cuenta.
    """
    exportacion = db.scalar(
        select(Exportacion)
        .options(
            selectinload(Exportacion.cliente),
            selectinload(Exportacion.detalles),
            selectinload(Exportacion.documentos),
            selectinload(Exportacion.envios),
        )
        .where(Exportacion.id_exportacion == id_exportacion)
    )
    if exportacion is None:
        raise HTTPException(status_code=404, detail="Exportación no encontrada")
    if usuario is not None and _es_cliente(usuario):
        if usuario.id_cliente is None or exportacion.id_cliente != usuario.id_cliente:
            raise HTTPException(status_code=404, detail="Exportación no encontrada")
    return exportacion


# --------------------------------------------------------------------------- #
# cotizaciones · HU-08
# --------------------------------------------------------------------------- #
@router.get("/cotizaciones", response_model=Paginado[CotizacionRead], summary="Listar cotizaciones")
def listar_cotizaciones(
    id_cliente: int | None = None,
    estado: EstadoCotizacion | None = None,
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_comercial),
) -> Paginado[CotizacionRead]:
    consulta = select(Cotizacion).options(selectinload(Cotizacion.cliente))
    if id_cliente:
        consulta = consulta.where(Cotizacion.id_cliente == id_cliente)
    if estado:
        consulta = consulta.where(Cotizacion.estado == estado.value)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Cotizacion.fecha.desc(), Cotizacion.id_cotizacion.desc())
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    ).all()
    return Paginado[CotizacionRead](
        items=[CotizacionRead.model_validate(c) for c in filas],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


@router.post(
    "/cotizaciones",
    response_model=CotizacionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cotización",
)
def crear_cotizacion(
    datos: CotizacionCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_ventas),
) -> CotizacionRead:
    """HU-08 · Generar cotizaciones en distintas monedas e Incoterms."""
    if db.get(Cliente, datos.id_cliente) is None:
        raise HTTPException(status_code=404, detail="El cliente indicado no existe")

    numero = (datos.numero or "").strip() or generar_numero_cotizacion(db)
    if db.scalar(select(Cotizacion).where(Cotizacion.numero == numero)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La cotización {numero} ya existe",
        )

    cotizacion = Cotizacion(
        **datos.model_dump(exclude={"numero"}), numero=numero, id_usuario=usuario.id_usuario
    )
    db.add(cotizacion)
    db.commit()
    db.refresh(cotizacion)
    return CotizacionRead.model_validate(cotizacion)


@router.post(
    "/cotizaciones/{id_cotizacion}/aceptar",
    response_model=ExportacionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Aceptar cotización y generar la exportación",
)
def aceptar_cotizacion(
    id_cotizacion: int,
    body: CotizacionConversion,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_ventas),
) -> ExportacionRead:
    """Convierte una cotización aceptada en un contrato de exportación.

    Los lotes se eligen en el momento de la conversión indicando sus códigos
    y la cantidad de kilos a asignar.
    """
    cotizacion = db.get(Cotizacion, id_cotizacion)
    if cotizacion is None:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    if cotizacion.estado not in (EstadoCotizacion.ENVIADA, EstadoCotizacion.ACEPTADA):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solo una cotización enviada o aceptada puede convertirse en "
                f"exportación (estado actual: {cotizacion.estado.value})"
            ),
        )
    if cotizacion.id_exportacion is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La cotización {cotizacion.numero} ya fue convertida",
        )

    lotes = db.scalars(
        select(Lote).where(Lote.codigo_lote.in_(body.lotes))
    ).all()
    faltantes = set(body.lotes) - {l.codigo_lote for l in lotes}
    if faltantes:
        raise HTTPException(
            status_code=404,
            detail=f"Lotes no encontrados: {', '.join(sorted(faltantes))}",
        )

    detalles = []
    total = Decimal("0")
    for lote in sorted(lotes, key=lambda l: l.codigo_lote):
        cantidad = body.cantidad_por_lote.get(lote.codigo_lote, body.cantidad_default)
        try:
            verificar_disponibilidad(db, lote.id_lote, cantidad)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        detalles.append(
            DetalleExportacion(
                id_lote=lote.id_lote, cantidad_kg=cantidad, precio_kg=cotizacion.precio_kg
            )
        )
        total += cantidad

    exportacion = Exportacion(
        id_cliente=cotizacion.id_cliente,
        id_usuario=usuario.id_usuario,
        fecha=cotizacion.fecha,
        estado=EstadoExportacion.PEDIDO_RECIBIDO,
        moneda=cotizacion.moneda,
        numero_contrato=generar_numero_contrato(db),
        incoterm=cotizacion.incoterm,
        puerto_origen=cotizacion.puerto_origen,
        puerto_destino=cotizacion.puerto_destino,
        valor_total=total * cotizacion.precio_kg,
        detalles=detalles,
    )
    db.add(exportacion)
    cotizacion.estado = EstadoCotizacion.ACEPTADA
    db.flush()
    cotizacion.id_exportacion = exportacion.id_exportacion

    db.commit()
    return ExportacionRead.model_validate(_cargar_exportacion(db, exportacion.id_exportacion))


@router.patch(
    "/cotizaciones/{id_cotizacion}", response_model=CotizacionRead, summary="Modificar cotización"
)
def actualizar_cotizacion(
    id_cotizacion: int,
    datos: CotizacionUpdate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_ventas),
) -> CotizacionRead:
    cotizacion = db.get(Cotizacion, id_cotizacion)
    if cotizacion is None:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    if cotizacion.id_exportacion is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La cotización ya se convirtió en exportación y no admite cambios",
        )

    cambios = datos.model_dump(exclude_unset=True)
    if "estado" in cambios and cambios["estado"] == EstadoCotizacion.ACEPTADA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usa el endpoint /aceptar para convertir la cotización en exportación",
        )
    for campo, valor in cambios.items():
        setattr(cotizacion, campo, valor)

    db.commit()
    db.refresh(cotizacion)
    return CotizacionRead.model_validate(cotizacion)


# --------------------------------------------------------------------------- #
# exportaciones
# --------------------------------------------------------------------------- #
@router.get("/exportaciones", response_model=Paginado[ExportacionRead], summary="Listar exportaciones")
def listar_exportaciones(
    id_cliente: int | None = None,
    estado: EstadoExportacion | None = None,
    q: str | None = Query(default=None, description="Busca por número de contrato"),
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    u: Usuario = Depends(_roles_lectura),
) -> Paginado[ExportacionRead]:
    consulta = select(Exportacion).options(
        selectinload(Exportacion.cliente),
        selectinload(Exportacion.detalles),
        selectinload(Exportacion.documentos),
        selectinload(Exportacion.envios),
    )
    # HU-10 · El cliente europeo solo ve lo suyo. Va antes que cualquier filtro
    # que venga en la URL, para que no se pueda ampliar con ?id_cliente=.
    if u.rol == Rol.CLIENTE_EU:
        if u.id_cliente is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Tu cuenta no tiene empresa asignada, así que no hay pedidos "
                    "que mostrar. Pídele al administrador que la asocie a tu "
                    "empresa en la pantalla de usuarios."
                ),
            )
        consulta = consulta.where(Exportacion.id_cliente == u.id_cliente)
    elif id_cliente:
        consulta = consulta.where(Exportacion.id_cliente == id_cliente)
    if estado:
        consulta = consulta.where(Exportacion.estado == estado.value)
    if q:
        consulta = consulta.where(Exportacion.numero_contrato.ilike(f"%{q}%"))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Exportacion.fecha.desc(), Exportacion.id_exportacion.desc())
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    ).all()
    return Paginado[ExportacionRead](
        items=[ExportacionRead.model_validate(e) for e in filas],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


@router.post(
    "/exportaciones",
    response_model=ExportacionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar exportación / pedido",
)
def crear_exportacion(
    datos: ExportacionCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_ventas),
) -> ExportacionRead:
    """HU-09 · Crear un pedido indicando producto, cantidad, calidad e Incoterm.

    La operación descuenta el inventario de los lotes indicados.
    """
    if db.get(Cliente, datos.id_cliente) is None:
        raise HTTPException(status_code=404, detail="El cliente indicado no existe")

    for detalle in datos.detalles:
        try:
            verificar_disponibilidad(db, detalle.id_lote, detalle.cantidad_kg)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    id_usuario = datos.id_usuario or usuario.id_usuario
    detalles = [
        DetalleExportacion(
            id_lote=d.id_lote, cantidad_kg=d.cantidad_kg, precio_kg=d.precio_kg
        )
        for d in datos.detalles
    ]
    valor_total = sum((d.cantidad_kg * d.precio_kg for d in detalles), start=0)

    exportacion = Exportacion(
        id_cliente=datos.id_cliente,
        id_usuario=id_usuario,
        fecha=datos.fecha,
        moneda=datos.moneda,
        incoterm=datos.incoterm,
        puerto_origen=datos.puerto_origen,
        puerto_destino=datos.puerto_destino,
        observaciones=datos.observaciones,
        estado=EstadoExportacion.PEDIDO_RECIBIDO,
        numero_contrato=generar_numero_contrato(db),
        valor_total=valor_total,
        detalles=detalles,
    )
    db.add(exportacion)
    db.flush()
    recalcular_disponibles(db)
    db.commit()
    return ExportacionRead.model_validate(_cargar_exportacion(db, exportacion.id_exportacion))


@router.get("/exportaciones/{id_exportacion}", response_model=ExportacionRead, summary="Ver exportación")
def obtener_exportacion(
    id_exportacion: int,
    db: Session = Depends(get_db),
    u: Usuario = Depends(_roles_lectura),
) -> ExportacionRead:
    return ExportacionRead.model_validate(
        _cargar_exportacion(db, id_exportacion, u)
    )


@router.patch(
    "/exportaciones/{id_exportacion}",
    response_model=ExportacionRead,
    summary="Actualizar exportación / cambiar estado",
)
def actualizar_exportacion(
    id_exportacion: int,
    datos: ExportacionUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_comercial),
) -> ExportacionRead:
    """Informe §6.9 · Cadena de estados del seguimiento.

    Solo se admiten transiciones válidas: avanzar un paso, retroceder uno o
    anular antes de la producción.
    """
    exportacion = _cargar_exportacion(db, id_exportacion)
    estado_anterior = exportacion.estado
    cambios = datos.model_dump(exclude_unset=True)

    if "estado" in cambios and cambios["estado"] is not None:
        nuevo = cambios.pop("estado")
        if not puede_transicionar(exportacion.estado, nuevo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Transición no permitida: {exportacion.estado.value} → {nuevo.value}. "
                    "La cadena de estados solo admite avanzar o retroceder un paso."
                ),
            )
        exportacion.estado = nuevo

    if "detalles" in cambios and cambios["detalles"] is not None:
        if exportacion.estado not in (
            EstadoExportacion.PEDIDO_RECIBIDO,
            EstadoExportacion.EN_PREPARACION,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Los lotes solo pueden modificarse antes de entrar en producción",
            )
        nuevos = cambios.pop("detalles")
        ids = [d.id_lote for d in nuevos]
        if len(ids) != len(set(ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un lote no puede repetirse dentro de la misma exportación",
            )
        for d in nuevos:
            try:
                verificar_disponibilidad(db, d.id_lote, d.cantidad_kg)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
                ) from exc
        exportacion.detalles.clear()
        db.flush()
        for d in nuevos:
            exportacion.detalles.append(
                DetalleExportacion(
                    id_lote=d.id_lote, cantidad_kg=d.cantidad_kg, precio_kg=d.precio_kg
                )
            )
        db.flush()
        exportacion.valor_total = sum(
            (d.cantidad_kg * d.precio_kg for d in exportacion.detalles), start=0
        )

    for campo, valor in cambios.items():
        setattr(exportacion, campo, valor)

    db.flush()
    recalcular_disponibles(db)

    # HU-21 y HU-16 · el cambio de estado de un pedido es un hecho crítico:
    # deja rastro y avisa al área comercial.
    if exportacion.estado != estado_anterior:
        notificaciones.notificar_cambio_estado(
            db,
            exportacion,
            estado_anterior.value,
            exportacion.estado.value,
            usuario,
        )
        auditoria.registrar(
            db,
            usuario,
            "Cambiar estado de exportación",
            entidad="exportaciones",
            id_entidad=exportacion.id_exportacion,
            detalle=f"{estado_anterior.value} → {exportacion.estado.value}",
            metodo="PATCH",
            ruta=f"/api/exportaciones/{id_exportacion}",
            estado_http=200,
        )
    else:
        auditoria.registrar(
            db,
            usuario,
            "Modificar exportación",
            entidad="exportaciones",
            id_entidad=exportacion.id_exportacion,
            detalle="Campos actualizados: " + ", ".join(sorted(datos.model_dump(exclude_unset=True))),
            metodo="PATCH",
            ruta=f"/api/exportaciones/{id_exportacion}",
            estado_http=200,
        )

    db.commit()
    return ExportacionRead.model_validate(_cargar_exportacion(db, id_exportacion))


# --------------------------------------------------------------------------- #
# documentos · HU-10
# --------------------------------------------------------------------------- #
@router.get(
    "/exportaciones/{id_exportacion}/documentos",
    response_model=list[DocumentoRead],
    summary="Listar documentos",
)
def listar_documentos(
    id_exportacion: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_comercial),
) -> list[DocumentoRead]:
    docs = db.scalars(
        select(DocumentoExportacion)
        .where(DocumentoExportacion.id_exportacion == id_exportacion)
        .order_by(DocumentoExportacion.fecha_emision.desc())
    ).all()
    return [DocumentoRead.model_validate(d) for d in docs]


@router.post(
    "/exportaciones/{id_exportacion}/documentos",
    response_model=DocumentoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar documento de exportación",
)
def crear_documento(
    id_exportacion: int,
    datos: DocumentoBase,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_comercial),
) -> DocumentoRead:
    """HU-10 · Factura comercial, packing list, certificado de origen, BL y AWB.

    La exportación se toma de la ruta, así que el cuerpo solo lleva el documento.
    """
    if db.get(Exportacion, id_exportacion) is None:
        raise HTTPException(status_code=404, detail="Exportación no encontrada")

    duplicado = db.scalar(
        select(DocumentoExportacion).where(
            DocumentoExportacion.numero_documento == datos.numero_documento
        )
    )
    if duplicado is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El documento {datos.numero_documento} ya está registrado",
        )

    documento = DocumentoExportacion(**datos.model_dump(), id_exportacion=id_exportacion)
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return DocumentoRead.model_validate(documento)


@router.patch(
    "/documentos/{id_documento}", response_model=DocumentoRead, summary="Modificar documento"
)
def actualizar_documento(
    id_documento: int,
    datos: DocumentoUpdate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_comercial),
) -> DocumentoRead:
    documento = db.get(DocumentoExportacion, id_documento)
    if documento is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(documento, campo, valor)
    db.commit()
    db.refresh(documento)
    return DocumentoRead.model_validate(documento)


@router.post(
    "/documentos/{id_documento}/autorizar",
    response_model=Mensaje,
    summary="Autorizar documento para el portal del cliente",
)
def autorizar_documento(
    id_documento: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_comercial),
) -> Mensaje:
    """Informe §8 · El cliente solo descarga los documentos autorizados."""
    documento = db.get(DocumentoExportacion, id_documento)
    if documento is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    if documento.estado == EstadoDocumento.BORRADOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emite el documento antes de autorizarlo para el cliente",
        )
    documento.autorizado_cliente = not documento.autorizado_cliente
    db.commit()
    estado = "autorizado" if documento.autorizado_cliente else "retirado"
    return Mensaje(mensaje=f"Documento {documento.numero_documento} {estado}", id=id_documento)
