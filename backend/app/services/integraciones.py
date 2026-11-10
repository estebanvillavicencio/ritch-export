"""HU-20 · integraciones con servicios externos.

El proyecto no puede depender de internet durante la demostración, así que cada
integración tiene dos caminos:

* el servicio real, cuando está configurado y hay red;
* un modo simulado determinista que deja el mismo rastro en la bitácora.

Todas las ejecuciones quedan en ``registros_integracion`` para que el
administrador pueda revisar qué se intentó, cuándo y con qué resultado.
"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Envio, RegistroIntegracion
from app.schemas.sprint3 import EnvioCorreo, IntegracionEstado, ResultadoIntegracion

SERVICIOS = {
    "Tipos de cambio": "Tasas EUR/USD/COP para el portal multimoneda.",
    "Correo": "Avisos de vencimientos, pagos y cambios de estado.",
    "Seguimiento navieras": "Consulta del estado de un contenedor por número.",
    "Almacenamiento documental": "Archivos de facturas, BL y certificados.",
}


def _ultimo(db: Session, servicio: str) -> RegistroIntegracion | None:
    return db.scalar(
        select(RegistroIntegracion)
        .where(RegistroIntegracion.servicio == servicio)
        .order_by(RegistroIntegracion.created_at.desc(), RegistroIntegracion.id_registro.desc())
    )


def estado(db: Session) -> list[IntegracionEstado]:
    """Estado de cada integración, con su última ejecución."""
    resultado: list[IntegracionEstado] = []
    for servicio, descripcion in SERVICIOS.items():
        ultimo = _ultimo(db, servicio)
        if servicio == "Tipos de cambio":
            configurado = True
            detalle = (
                "Consultando el proveedor público."
                if settings.integraciones_red
                else "Modo local: se usan tasas de respaldo."
            )
            estado_servicio = "operativo"
        elif servicio == "Correo":
            configurado = bool(settings.integraciones_red)
            detalle = "Modo simulado: los envíos quedan en la bitácora."
            estado_servicio = "simulado" if not configurado else "operativo"
        elif servicio == "Seguimiento navieras":
            configurado = False
            detalle = "Consulta el envío registrado en RiTech; no llama a la naviera."
            estado_servicio = "simulado"
        else:
            configurado = bool(settings.upload_dir)
            detalle = f"Directorio de archivos: {settings.upload_dir}"
            estado_servicio = "operativo" if configurado else "sin configurar"

        resultado.append(
            IntegracionEstado(
                servicio=servicio,
                descripcion=descripcion,
                estado=estado_servicio,
                configurado=configurado,
                detalle=detalle,
                ultima_ejecucion=ultimo.created_at if ultimo else None,
            )
        )
    return resultado


def _registrar(
    db: Session,
    servicio: str,
    accion: str,
    estado: str,
    mensaje: str,
    detalle: dict | None = None,
) -> RegistroIntegracion:
    registro = RegistroIntegracion(
        servicio=servicio,
        accion=accion,
        estado=estado,
        mensaje=mensaje,
        detalle=json.dumps(detalle, ensure_ascii=False, default=str) if detalle else None,
    )
    db.add(registro)
    db.flush()
    return registro


def probar_correo(db: Session, datos: EnvioCorreo) -> ResultadoIntegracion:
    modo = "servicio" if settings.integraciones_red else "simulado"
    mensaje = (
        f"Correo encolado para {datos.destinatario}."
        if settings.integraciones_red
        else f"Correo simulado para {datos.destinatario}; no salió de la red local."
    )
    _registrar(
        db,
        "Correo",
        "Prueba de envío",
        "ok" if settings.integraciones_red else "simulado",
        mensaje,
        {"destinatario": datos.destinatario, "asunto": datos.asunto, "modo": modo},
    )
    return ResultadoIntegracion(
        servicio="Correo",
        accion="Prueba de envío",
        estado="ok" if settings.integraciones_red else "simulado",
        mensaje=mensaje,
        detalle={"destinatario": datos.destinatario, "modo": modo},
        ejecutado_en=datetime.now(),
    )


def consultar_seguimiento(db: Session, numero: str) -> ResultadoIntegracion:
    envio = db.scalar(
        select(Envio).where(Envio.numero_seguimiento == numero.strip())
    )
    if envio is None:
        mensaje = f"No hay un envío registrado con el número {numero}."
        _registrar(db, "Seguimiento navieras", "Consultar", "error", mensaje)
        return ResultadoIntegracion(
            servicio="Seguimiento navieras",
            accion="Consultar",
            estado="error",
            mensaje=mensaje,
            ejecutado_en=datetime.now(),
        )

    detalle = {
        "numero_seguimiento": envio.numero_seguimiento,
        "transportadora": envio.transportadora,
        "estado": envio.estado.value,
        "puerto_origen": envio.puerto_origen,
        "puerto_destino": envio.puerto_destino,
        "fecha_salida": envio.fecha_salida,
        "fecha_llegada": envio.fecha_llegada,
    }
    mensaje = (
        f"{envio.transportadora}: el envío {envio.numero_seguimiento} está "
        f"«{envio.estado.value}»."
    )
    _registrar(
        db,
        "Seguimiento navieras",
        "Consultar",
        "simulado",
        mensaje,
        detalle,
    )
    return ResultadoIntegracion(
        servicio="Seguimiento navieras",
        accion="Consultar",
        estado="simulado",
        mensaje=mensaje,
        detalle=detalle,
        ejecutado_en=datetime.now(),
    )


def bitacora(db: Session, limite: int = 50) -> list[RegistroIntegracion]:
    return db.scalars(
        select(RegistroIntegracion)
        .order_by(RegistroIntegracion.created_at.desc(), RegistroIntegracion.id_registro.desc())
        .limit(limite)
    ).all()
