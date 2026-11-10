"""Punto de entrada de la API de RiTech SAS.

Uso:

    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import settings
from app.database import init_db

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(name)s  %(message)s"
)
logger = logging.getLogger("ritch")

#: Carpeta del frontend que se sirve como aplicación web.
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # init_db() crea las tablas que faltan, pero no altera las que ya existen.
    # Sin esto, añadir una columna al modelo y arrancar con una base de una
    # corrida anterior falla en el primer INSERT, con un error del motor que no
    # señala el código.
    from app.migraciones import aplicar

    aplicar()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.backup_dir).mkdir(parents=True, exist_ok=True)
    logger.info("Esquema verificado · %s", settings.db_url.split("://")[0])

    _avisos_de_despliegue()
    _sembrar_si_hace_falta()
    _respaldo_automatico()
    yield
    logger.info("Api detenida")


def _respaldo_automatico() -> None:
    """HU-22 · deja una copia de seguridad si pasaron las horas configuradas.

    Se hace al arrancar y no con un programador de tareas: el sistema se
    reinicia con frecuencia en la demostración y así la copia ocurre sin que
    nadie tenga que acordarse de pulsar el botón.
    """
    from app.database import SessionLocal
    from app.services import respaldos

    try:
        with SessionLocal() as db:
            creado = respaldos.automatico_si_hace_falta(db)
        if creado is not None:
            logger.info("Respaldo automático creado · %s", creado.nombre)
    except Exception as exc:  # noqa: BLE001 — un fallo de respaldo no impide arrancar
        logger.warning("No se pudo crear el respaldo automático: %s", exc)


def _sembrar_si_hace_falta() -> None:
    """Carga los datos de ejemplo cuando la base está vacía.

    En los servicios gratuitos el disco es temporal, así que la base se borra
    en cada reinicio. Sembrar aquí deja el sistema con datos aunque se haya
    reiniciado hace un minuto, que es lo que hace falta para que el enlace
    compartido abra con algo que mirar.
    """
    from app.database import SessionLocal
    from app.sembrar_si_esta_vacia import sembrar_si_esta_vacia

    with SessionLocal() as db:
        sembrar_si_esta_vacia(db)


def _avisos_de_despliegue() -> None:
    """Deja en el registro lo que hay que arreglar antes de publicar esto."""
    if settings.jwt_secret == "cambia-esta-clave-en-produccion":
        logger.warning(
            "ATENCION · La clave de las sesiones es la de ejemplo. Cualquiera "
            "que conozca el codigo puede fabricar un token y entrar como "
            "administrador. Antes de publicar la aplicacion hay que poner "
            "RITECH_JWT_SECRET en el archivo .env."
        )
    if not settings.db_url.startswith(("postgresql", "sqlite")):
        logger.warning("ATENCION · RITECH_DB_URL tiene un valor raro: %s",
                       settings.db_url)
    if settings.db_url.startswith("sqlite"):
        logger.info(
            "La base es SQLite. En un hosting con disco temporal se perdera en "
            "cada reinicio; los datos de ejemplo se vuelven a sembrar solos, "
            "pero lo que se cargue despues no."
        )


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description=(
        "API del sistema de gestión de exportaciones de café y cacao hacia la "
        "Unión Europea de RiTech SAS.\n\n"
        "Sprint 2: productores, fincas y lotes · calidad · comercial · logística.\n\n"
        "Sprint 3: pagos y cartera (HU-14) · notificaciones (HU-16) · auditoría "
        "(HU-21).\n\n"
        "Sprint 4: multimoneda (HU-19) · integraciones (HU-20) · copias de "
        "seguridad (HU-22).\n\n"
        "Metodología: Scrum. Base de datos: PostgreSQL (RR-003)."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/api/salud", tags=["Sistema"], summary="Comprobar el estado del servicio")
def salud() -> dict:
    return {"estado": "ok", "empresa": settings.company, "version": app.version}


@app.exception_handler(ValueError)
async def valor_invalido(request: Request, exc: ValueError) -> JSONResponse:
    """Las reglas de negocio lanzan ``ValueError``; se devuelven como 400."""
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# --- Frontend ------------------------------------------------------------- #
# Los archivos estáticos se sirven sin caché, a propósito. La aplicación es un
# SPA de módulos ES sin paso de compilación, así que el navegador no tiene forma
# de invalidar lo que ya descargó: si se edita un `.js` y se recarga, sigue
# ejecutando la versión anterior y parece que el arreglo no sirva. Con
# `no-store` siempre se pide el archivo, que es lo que uno espera al trabajar
# encima. En una aplicación de producción esto se cambiaría por el nombre con
# versión dentro del index.html; aquí pesa más no confundirse.
#
# Va como middleware y no como `headers=` en el montaje porque no todas las
# versiones de Starlette lo aceptan en StaticFiles.
SIN_CACHEC = {
    "Cache-Control": "no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


@app.middleware("http")
async def sin_cache_en_el_frontend(request: Request, call_next):
    """Agrega `no-store` a lo que se sirve del frontend, y solo a eso.

    La API sí lleva su propia caché y no se toca: las respuestas de la API se
    generan en el momento y no tiene sentido forbidding.
    """
    respuesta = await call_next(request)
    ruta = request.url.path
    if ruta.startswith(("/js/", "/css/")) or ruta in ("/", "/portal", "/index.html"):
        for clave, valor in SIN_CACHEC.items():
            respuesta.headers[clave] = valor
    return respuesta


if FRONTEND_DIR.is_dir():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

    @app.get("/", include_in_schema=False)
    def raiz() -> FileResponse:
        """Aplicación interna de RiTech SAS."""
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/portal", include_in_schema=False)
    def portal() -> FileResponse:
        """Portal especializado para clientes europeos (Informe §8)."""
        return FileResponse(FRONTEND_DIR / "portal.html")
