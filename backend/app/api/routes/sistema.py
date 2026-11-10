"""Sistema: integraciones, multimoneda y copias de seguridad.

HU-19 · tipos de cambio y conversión.
HU-20 · estado de los servicios externos y bitácora.
HU-22 · respaldos verificables.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Respaldo, Rol, TipoCambio, Usuario
from app.schemas import (
    ActualizacionTiposCambio,
    ConversionMoneda,
    EnvioCorreo,
    IntegracionEstado,
    Mensaje,
    RegistroIntegracionRead,
    RespaldoRead,
    RespaldoVerificacion,
    ResultadoIntegracion,
    TipoCambioCreate,
    TipoCambioRead,
)
from app.services import auditoria, integraciones, monedas, respaldos

router = APIRouter(tags=["Sistema"], dependencies=[Depends(get_current_user)])

_roles_internos = require_roles(
    Rol.ADMINISTRADOR, Rol.COMERCIAL, Rol.FINANCIERO, Rol.LOGISTICA, Rol.CALIDAD
)
_roles_admin = require_roles(Rol.ADMINISTRADOR)


# --------------------------------------------------------------------------- #
# integraciones · HU-20
# --------------------------------------------------------------------------- #
@router.get(
    "/integraciones",
    response_model=list[IntegracionEstado],
    summary="Estado de las integraciones",
)
def estado_integraciones(
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_internos),
) -> list[IntegracionEstado]:
    return integraciones.estado(db)


@router.post(
    "/integraciones/correo",
    response_model=ResultadoIntegracion,
    summary="Probar el envío de correo",
)
def probar_correo(
    datos: EnvioCorreo,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_admin),
) -> ResultadoIntegracion:
    resultado = integraciones.probar_correo(db, datos)
    auditoria.registrar(
        db,
        usuario,
        "Probar integración de correo",
        entidad="integraciones",
        detalle=f"Destinatario: {datos.destinatario}",
        metodo="POST",
        ruta="/api/integraciones/correo",
        estado_http=200,
    )
    db.commit()
    return resultado


@router.post(
    "/integraciones/seguimiento/{numero}",
    response_model=ResultadoIntegracion,
    summary="Consultar el seguimiento de un envío",
)
def consultar_seguimiento(
    numero: str,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_internos),
) -> ResultadoIntegracion:
    resultado = integraciones.consultar_seguimiento(db, numero)
    db.commit()
    return resultado


@router.get(
    "/integraciones/bitacora",
    response_model=list[RegistroIntegracionRead],
    summary="Bitácora de integraciones",
)
def bitacora(
    limite: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_admin),
) -> list[RegistroIntegracionRead]:
    return [
        RegistroIntegracionRead.model_validate(r)
        for r in integraciones.bitacora(db, limite=limite)
    ]


# --------------------------------------------------------------------------- #
# tipos de cambio · HU-19
# --------------------------------------------------------------------------- #
@router.get(
    "/tipos-cambio",
    response_model=list[TipoCambioRead],
    summary="Listar los tipos de cambio vigentes",
)
def listar_tipos(
    db: Session = Depends(get_db),
    _u: Usuario = Depends(get_current_user),
) -> list[TipoCambioRead]:
    return [TipoCambioRead.model_validate(t) for t in monedas.listar(db)]


@router.post(
    "/tipos-cambio",
    response_model=TipoCambioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un tipo de cambio",
)
def crear_tipo(
    datos: TipoCambioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_admin),
) -> TipoCambioRead:
    moneda = monedas.normalizar(datos.moneda)
    existente = db.scalar(
        select(TipoCambio).where(
            TipoCambio.moneda == moneda, TipoCambio.fecha == datos.fecha
        )
    )
    if existente is not None:
        existente.tasa = datos.tasa
        existente.fuente = datos.fuente or existente.fuente
        fila = existente
    else:
        fila = TipoCambio(
            moneda=moneda,
            tasa=datos.tasa,
            fecha=datos.fecha,
            fuente=datos.fuente or "Carga manual",
        )
        db.add(fila)
    auditoria.registrar(
        db,
        usuario,
        "Registrar tipo de cambio",
        entidad="tipos_cambio",
        detalle=f"{moneda} · 1 EUR = {datos.tasa} {moneda}",
        metodo="POST",
        ruta="/api/tipos-cambio",
        estado_http=201,
    )
    db.commit()
    db.refresh(fila)
    return TipoCambioRead.model_validate(fila)


@router.post(
    "/tipos-cambio/actualizar",
    response_model=ActualizacionTiposCambio,
    summary="Actualizar las tasas del día",
)
def actualizar_tipos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_admin),
) -> ActualizacionTiposCambio:
    resultado = monedas.actualizar(db)
    auditoria.registrar(
        db,
        usuario,
        "Actualizar tipos de cambio",
        entidad="tipos_cambio",
        detalle=f"{resultado['actualizados']} monedas · {resultado['fuente']}",
        metodo="POST",
        ruta="/api/tipos-cambio/actualizar",
        estado_http=200,
    )
    db.commit()
    return ActualizacionTiposCambio(**resultado)


@router.get(
    "/monedas/convertir",
    response_model=ConversionMoneda,
    summary="Convertir un importe entre monedas",
)
def convertir(
    valor: Decimal = Query(gt=0),
    desde: str = "EUR",
    hasta: str = "USD",
    fecha: date | None = None,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(get_current_user),
) -> ConversionMoneda:
    try:
        origen = monedas.normalizar(desde)
        destino = monedas.normalizar(hasta)
        resultado = monedas.convertir(db, valor, origen, destino, fecha)
        tasa = monedas.convertir(db, Decimal("1"), origen, destino, fecha)
    except monedas.ErrorMoneda as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return ConversionMoneda(
        valor=float(valor),
        desde=origen,
        hasta=destino,
        resultado=round(float(resultado), 2),
        tasa=round(float(tasa), 6),
        fecha=fecha or date.today(),
    )


# --------------------------------------------------------------------------- #
# respaldos · HU-22
# --------------------------------------------------------------------------- #
@router.get("/respaldos", response_model=list[RespaldoRead], summary="Listar respaldos")
def listar_respaldos(
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_admin),
) -> list[RespaldoRead]:
    return [RespaldoRead.model_validate(r) for r in respaldos.listar(db)]


@router.post(
    "/respaldos",
    response_model=RespaldoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una copia de seguridad",
)
def crear_respaldo(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(_roles_admin),
) -> RespaldoRead:
    try:
        respaldo = respaldos.crear(db, usuario)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo escribir el respaldo: {exc}",
        ) from exc
    auditoria.registrar(
        db,
        usuario,
        "Crear respaldo",
        entidad="respaldos",
        id_entidad=respaldo.id_respaldo,
        detalle=f"{respaldo.nombre} · {respaldo.registros} registros",
        metodo="POST",
        ruta="/api/respaldos",
        estado_http=201,
    )
    db.commit()
    db.refresh(respaldo)
    return RespaldoRead.model_validate(respaldo)


@router.post(
    "/respaldos/{id_respaldo}/verificar",
    response_model=RespaldoVerificacion,
    summary="Verificar la integridad de una copia",
)
def verificar_respaldo(
    id_respaldo: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_admin),
) -> RespaldoVerificacion:
    respaldo = db.get(Respaldo, id_respaldo)
    if respaldo is None:
        raise HTTPException(status_code=404, detail="Respaldo no encontrado")
    return RespaldoVerificacion(**respaldos.verificar(respaldo))


@router.get(
    "/respaldos/{id_respaldo}/descargar",
    summary="Descargar una copia de seguridad",
)
def descargar_respaldo(
    id_respaldo: int,
    db: Session = Depends(get_db),
    _u: Usuario = Depends(_roles_admin),
) -> FileResponse:
    respaldo = db.get(Respaldo, id_respaldo)
    if respaldo is None:
        raise HTTPException(status_code=404, detail="Respaldo no encontrado")
    try:
        ruta = respaldos.ruta_de(respaldo)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(ruta, media_type="application/json", filename=respaldo.nombre)
