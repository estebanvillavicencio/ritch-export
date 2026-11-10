"""Agregador de rutas de la API."""

from fastapi import APIRouter

from app.api.routes import (
    auditoria,
    auth,
    catalogos,
    comercial,
    financiero,
    logistica,
    notificaciones,
    operacion,
    pedidos,
    panel,
    sistema,
    usuarios,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(catalogos.router)
api_router.include_router(operacion.router)
api_router.include_router(comercial.router)
api_router.include_router(pedidos.router)
api_router.include_router(logistica.router)
api_router.include_router(panel.router)
# Sprint 3
api_router.include_router(financiero.router)
api_router.include_router(notificaciones.router)
api_router.include_router(auditoria.router)
# Sprint 4
api_router.include_router(sistema.router)

__all__ = ["api_router"]
