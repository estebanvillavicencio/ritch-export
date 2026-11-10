"""Módulo de Productores, Lotes y Trazabilidad (HU-04, HU-05, HU-06) y Calidad (HU-17)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import (
    CalidadLote,
    Certificacion,
    EstadoCalidad,
    EstadoCertificacion,
    EstadoExportacion,
    EtapaTrazabilidad,
    EventoTrazabilidad,
    Finca,
    Lote,
    ORDEN_TRAZABILIDAD,
    Producto,
    Rol,
    TipoCertificacion,
    Usuario,
)
from app.schemas import (
    CalidadCreate,
    CalidadRead,
    CalidadUpdate,
    CertificacionCreate,
    CertificacionRead,
    EventoBase,
    EventoRead,
    LoteCreate,
    LoteDetallado,
    LoteRead,
    LoteUpdate,
    Mensaje,
    Paginado,
    ResumenInventario,
    TrazabilidadRead,
)
from app.services import indicadores
from app.services.reglas import (
    estado_certificacion,
    generar_codigo_lote,
    recalcular_disponibles,
)

router = APIRouter(tags=["Productores, lotes y calidad"], dependencies=[Depends(get_current_user)])

_roles_productores = require_roles(Rol.ADMINISTRADOR, Rol.COMERCIAL, Rol.CALIDAD, Rol.LOGISTICA)
_roles_calidad = require_roles(Rol.ADMINISTRADOR, Rol.CALIDAD)


# --------------------------------------------------------------------------- #
# lotes · HU-05
# --------------------------------------------------------------------------- #
@router.get("/lotes", response_model=Paginado[LoteRead], summary="Listar lotes")
def listar_lotes(
    q: str | None = Query(default=None, description="Busca por código de lote"),
    id_finca: int | None = None,
    id_producto: int | None = None,
    estado_calidad: EstadoCalidad | None = None,
    tipo: str | None = Query(default=None, description="Café | Cacao"),
    solo_disponibles: bool = Query(default=False, description="Solo lotes con saldo"),
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_productores),
) -> Paginado[LoteRead]:
    recalcular_disponibles(db)
    db.commit()

    consulta = select(Lote).join(Finca).join(Producto)
    if q:
        consulta = consulta.where(Lote.codigo_lote.ilike(f"%{q}%"))
    if id_finca:
        consulta = consulta.where(Lote.id_finca == id_finca)
    if id_producto:
        consulta = consulta.where(Lote.id_producto == id_producto)
    if estado_calidad:
        consulta = consulta.where(Lote.estado_calidad == estado_calidad.value)
    if tipo:
        consulta = consulta.where(Producto.tipo == tipo)
    if solo_disponibles:
        consulta = consulta.where(Lote.disponible_kg > 0)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.scalars(
        consulta.order_by(Lote.fecha_cosecha.desc(), Lote.id_lote.desc())
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    ).all()
    return Paginado[LoteRead](
        items=[LoteRead.model_validate(l) for l in filas],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


@router.post(
    "/lotes",
    response_model=LoteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar lote",
)
def crear_lote(
    datos: LoteCreate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_productores),
) -> LoteRead:
    """HU-05 · Registrar un lote de café o cacao para controlar el inventario.

    Si no se envía ``codigo_lote`` se genera uno correlativo con el formato
    ``CO-HUI-AAAA-NNNN``. El primer evento de trazabilidad («Finca») se crea
    automáticamente.
    """
    if db.get(Finca, datos.id_finca) is None:
        raise HTTPException(status_code=404, detail="La finca indicada no existe")
    if db.get(Producto, datos.id_producto) is None:
        raise HTTPException(status_code=404, detail="El producto indicado no existe")

    codigo = (datos.codigo_lote or "").strip() or generar_codigo_lote(db)
    if db.scalar(select(Lote).where(Lote.codigo_lote == codigo)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El código de lote {codigo} ya está registrado",
        )

    lote = Lote(
        **datos.model_dump(exclude={"codigo_lote"}),
        codigo_lote=codigo,
        disponible_kg=datos.cantidad_kg,
    )
    db.add(lote)
    db.flush()

    finca = db.get(Finca, datos.id_finca)
    db.add(
        EventoTrazabilidad(
            id_lote=lote.id_lote,
            etapa=EtapaTrazabilidad.FINCA,
            fecha=lote.fecha_cosecha,
           ubicacion=f"{finca.ubicacion}, {finca.departamento}",
            descripcion=f"Lote cosechado en {finca.nombre}",
        )
    )
    db.commit()
    db.refresh(lote)
    return LoteRead.model_validate(lote)


@router.get("/lotes/inventario", response_model=ResumenInventario, summary="Resumen de inventario")
def inventario(
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_productores),
) -> ResumenInventario:
    """HU-05 · Control de inventario disponible para exportación."""
    resumen = indicadores.inventario(db)
    db.commit()
    return resumen


@router.get("/lotes/{id_lote}", response_model=LoteDetallado, summary="Ver lote")
def obtener_lote(
    id_lote: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_productores),
) -> LoteDetallado:
    lote = db.scalar(
        select(Lote)
        .options(
            selectinload(Lote.finca),
            selectinload(Lote.producto),
            selectinload(Lote.calidad),
            selectinload(Lote.certificaciones),
        )
        .where(Lote.id_lote == id_lote)
    )
    if lote is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    from app.schemas.catalogos import CertificacionResumida

    return LoteDetallado(
        **LoteRead.model_validate(lote).model_dump(),
        finca_nombre=lote.finca.nombre,
        finca_ubicacion=lote.finca.ubicacion,
        finca_departamento=lote.finca.departamento,
        finca_propietario=lote.finca.propietario,
        finca_asociacion=lote.finca.asociacion,
        producto_nombre=lote.producto.nombre,
        producto_tipo=lote.producto.tipo.value,
        certificaciones=[
            CertificacionResumida(
                tipo=c.tipo,
                estado=estado_certificacion(c).value,
                fecha_vencimiento=c.fecha_vencimiento,
            )
            for c in lote.certificaciones
        ],
        calidad=CalidadRead.model_validate(lote.calidad) if lote.calidad else None,
    )


@router.patch("/lotes/{id_lote}", response_model=LoteRead, summary="Modificar lote")
def actualizar_lote(
    id_lote: int,
    datos: LoteUpdate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_productores),
) -> LoteRead:
    lote = db.get(Lote, id_lote)
    if lote is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    cambios = datos.model_dump(exclude_unset=True)
    # La cantidad total de un lote no se reduce por debajo de lo ya comprometido.
    nueva_cantidad = cambios.get("cantidad_kg")
    if nueva_cantidad is not None and nueva_cantidad < lote.consumo_kg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No puedes reducir el lote a {nueva_cantidad} kg: ya hay "
                f"{lote.consumo_kg} kg comprometidos en exportaciones"
            ),
        )

    for campo, valor in cambios.items():
        setattr(lote, campo, valor)

    db.flush()
    recalcular_disponibles(db)
    db.commit()
    db.refresh(lote)
    return LoteRead.model_validate(lote)


@router.delete("/lotes/{id_lote}", response_model=Mensaje, summary="Retirar lote")
def retirar_lote(
    id_lote: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(require_roles(Rol.ADMINISTRADOR, Rol.CALIDAD)),
) -> Mensaje:
    """Un lote con historial de trazabilidad no se borra; se marca como
    rechazado para que deje de ofrecerse como exportable."""
    lote = db.get(Lote, id_lote)
    if lote is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if lote.consumo_kg > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El lote {lote.codigo_lote} ya está comprometido en "
                f"{lote.consumo_kg} kg de exportación; no se puede retirar"
            ),
        )
    lote.estado_calidad = EstadoCalidad.RECHAZADO
    lote.disponible_kg = 0
    db.commit()
    return Mensaje(
        mensaje=f"Lote {lote.codigo_lote} retirado del inventario exportable",
        id=lote.id_lote,
    )


# --------------------------------------------------------------------------- #
# calidad_lote · HU-17
# --------------------------------------------------------------------------- #
@router.put("/lotes/{id_lote}/calidad", response_model=CalidadRead, summary="Registrar calidad")
def registrar_calidad(
    id_lote: int,
    datos: CalidadCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_calidad),
) -> CalidadRead:
    """HU-17 · Registrar resultados de catación y laboratorio.

    Guardar la calidad actualiza automáticamente el estado de calidad del lote.
    """
    lote = db.get(Lote, id_lote)
    if lote is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    calidad = db.scalar(select(CalidadLote).where(CalidadLote.id_lote == id_lote))
    campos = datos.model_dump(exclude={"id_lote"})
    if calidad is None:
        calidad = CalidadLote(**campos, id_lote=id_lote)
        db.add(calidad)
    else:
        for campo, valor in campos.items():
            setattr(calidad, campo, valor)

    lote.estado_calidad = _estado_por_resultados(
        puntaje=datos.puntaje_cata,
        humedad=datos.humedad,
        aprobado_por=usuario.nombre,
    )
    db.commit()
    db.refresh(calidad)
    return CalidadRead.model_validate(calidad)


def _estado_por_resultados(puntaje, humedad, aprobado_por: str | None) -> EstadoCalidad:
    """Deriva el estado de calidad a partir de la catación y la humedad.

    · Special  (≥ 85 puntos) con responsable de aprobación → Aprobado
    · Excelente (80–84.99) con humedad ≤ 12 %                → Aprobado
    · 60–79.99                                               → Con reserva
    · resto                                                  → Rechazado
    """
    if puntaje is None and humedad is None:
        return EstadoCalidad.EN_ANALISIS

    if puntaje is not None:
        puntos = Decimal(str(puntaje))
        if puntos >= 85 and aprobado_por:
            return EstadoCalidad.APROBADO
        if puntos >= 80 and humedad is not None and Decimal(str(humedad)) <= 12:
            return EstadoCalidad.APROBADO
        if puntos >= 60:
            return EstadoCalidad.APROBADO_CON_RESERVA
    return EstadoCalidad.RECHAZADO


@router.get("/lotes/{id_lote}/calidad", response_model=CalidadRead, summary="Ver calidad")
def ver_calidad(
    id_lote: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_productores),
) -> CalidadRead:
    calidad = db.scalar(select(CalidadLote).where(CalidadLote.id_lote == id_lote))
    if calidad is None:
        raise HTTPException(status_code=404, detail="Este lote aún no tiene calidad registrada")
    return CalidadRead.model_validate(calidad)


# --------------------------------------------------------------------------- #
# certificaciones · Informe §6.4
# --------------------------------------------------------------------------- #
@router.get(
    "/certificaciones",
    response_model=Paginado[CertificacionRead],
    summary="Listar certificaciones",
)
def listar_certificaciones(
    id_lote: int | None = None,
    id_finca: int | None = None,
    tipo: TipoCertificacion | None = None,
    solo_por_vencer: bool = Query(
        default=False, description="Vencidas o que vencen en menos de 45 días"
    ),
    pagina: int = Query(default=1, ge=1),
    tamano: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_productores),
) -> Paginado[CertificacionRead]:
    consulta = select(Certificacion)
    if id_lote:
        consulta = consulta.where(Certificacion.id_lote == id_lote)
    if id_finca:
        consulta = consulta.where(Certificacion.id_finca == id_finca)
    if tipo:
        consulta = consulta.where(Certificacion.tipo == tipo.value)
    if solo_por_vencer:
        limite = date.today() + timedelta(days=45)
        consulta = consulta.where(
            Certificacion.fecha_vencimiento.isnot(None),
            Certificacion.fecha_vencimiento <= limite,
        )

    certs = db.scalars(consulta.order_by(Certificacion.fecha_vencimiento)).all()
    items = []
    for c in certs:
        cert = CertificacionRead.model_validate(c)
        cert.estado = estado_certificacion(c).value
        cert.dias_para_vencer = c.dias_para_vencer
        items.append(cert)

    inicio = (pagina - 1) * tamano
    return Paginado[CertificacionRead](
        items=items[inicio : inicio + tamano],
        total=len(items),
        pagina=pagina,
        tamano=tamano,
    )


@router.post(
    "/certificaciones",
    response_model=CertificacionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar certificación",
)
def crear_certificacion(
    datos: CertificacionCreate,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(require_roles(Rol.ADMINISTRADOR, Rol.CALIDAD, Rol.COMERCIAL)),
) -> CertificacionRead:
    """Informe §6.4 · EUDR, orgánico, Fairtrade y fitosanitario.

    Para el cumplimiento del EUDR la certificación debe tener el lote
    georreferenciado.
    """
    if datos.id_lote and db.get(Lote, datos.id_lote) is None:
        raise HTTPException(status_code=404, detail="El lote indicado no existe")
    if datos.id_finca and db.get(Finca, datos.id_finca) is None:
        raise HTTPException(status_code=404, detail="La finca indicada no existe")

    cert = Certificacion(**datos.model_dump())
    db.add(cert)
    db.commit()
    db.refresh(cert)

    respuesta = CertificacionRead.model_validate(cert)
    respuesta.estado = estado_certificacion(cert).value
    respuesta.dias_para_vencer = cert.dias_para_vencer
    return respuesta


@router.delete(
    "/certificaciones/{id_certificacion}",
    response_model=Mensaje,
    summary="Anular certificación",
)
def anular_certificacion(
    id_certificacion: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(require_roles(Rol.ADMINISTRADOR, Rol.CALIDAD)),
) -> Mensaje:
    cert = db.get(Certificacion, id_certificacion)
    if cert is None:
        raise HTTPException(status_code=404, detail="Certificación no encontrada")
    db.delete(cert)
    db.commit()
    return Mensaje(
        mensaje=f"Certificación {cert.tipo.value} retirada", id=cert.id_certificacion
    )


# --------------------------------------------------------------------------- #
# trazabilidad · HU-06
# --------------------------------------------------------------------------- #
@router.get("/lotes/{id_lote}/trazabilidad", response_model=TrazabilidadRead, summary="Trazabilidad")
def ver_trazabilidad(
    id_lote: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_productores),
) -> TrazabilidadRead:
    """HU-06 · Recorrido del lote desde la finca hasta el destino."""
    lote = db.get(Lote, id_lote)
    if lote is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    eventos = db.scalars(
        select(EventoTrazabilidad)
        .where(EventoTrazabilidad.id_lote == id_lote)
        .order_by(EventoTrazabilidad.fecha, EventoTrazabilidad.id_evento)
    ).all()
    por_etapa: dict[str, EventoTrazabilidad] = {}
    for evento in eventos:
        por_etapa.setdefault(evento.etapa.value, evento)

    from app.schemas.operacion import EtapaTrazabilidadEstado

    # Todas las etapas con evento registrado quedan «done»; la primera sin
    # evento es la etapa «current» (donde está el lote ahora mismo).
    primera_pendiente = next(
        (i for i, e in enumerate(ORDEN_TRAZABILIDAD) if e.value not in por_etapa), None
    )

    etapas = []
    for i, etapa in enumerate(ORDEN_TRAZABILIDAD):
        evento = por_etapa.get(etapa.value)
        if evento is not None:
            estado = "done"
        elif i == primera_pendiente:
            estado = "current"
        else:
            estado = "pending"
        etapas.append(
            EtapaTrazabilidadEstado(
                etapa=etapa,
                fecha=evento.fecha if evento else None,
                ubicacion=evento.ubicacion if evento else None,
                descripcion=evento.descripcion if evento else None,
                estado=estado,
            )
        )

    return TrazabilidadRead(id_lote=lote.id_lote, codigo_lote=lote.codigo_lote, etapas=etapas)


@router.post(
    "/lotes/{id_lote}/trazabilidad",
    response_model=EventoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar hito de trazabilidad",
)
def registrar_evento(
    id_lote: int,
    datos: EventoBase,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_productores),
) -> EventoRead:
    """HU-06 · Añade un hito al recorrido del lote.

    El lote se toma de la ruta, por eso el cuerpo no lo incluye.
    """
    if db.get(Lote, id_lote) is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    evento = EventoTrazabilidad(**datos.model_dump(), id_lote=id_lote)
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return EventoRead.model_validate(evento)
