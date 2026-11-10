"""Panel general e indicadores (Informe §6.10 · HU-15 · HU-16)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Rol, Usuario
from app.schemas import DashboardRead, KpiResumen
from app.services import indicadores

router = APIRouter(tags=["Panel y reportes"], dependencies=[Depends(get_current_user)])

#: El panel y los indicadores son de la empresa: lotes disponibles, kilos
#: exportados, cumplimiento normativo de toda la operación. El cliente europeo
#: no entra aquí aunque tenga una sesión válida; lo que puede ver son sus
#: exportaciones y sus envíos, que ya vienen recortados por empresa.
#:
#: Sin este cierre, una cuenta de comprador veía los indicadores globales de
#: RiTech por el solo hecho de estar logueada.
_roles_internos = require_roles(
    Rol.ADMINISTRADOR, Rol.COMERCIAL, Rol.LOGISTICA, Rol.CALIDAD, Rol.FINANCIERO
)


@router.get(
    "/panel",
    response_model=DashboardRead,
    summary="Datos del panel general",
)
def panel(db: Session = Depends(get_db), _u: Usuario = Depends(_roles_internos)) -> DashboardRead:
    """Reúne las tarjetas KPI, las barras de cumplimiento, los pedidos
    recientes, la ficha de lote, la línea de tiempo del envío destacado y
    las alertas. Es la fuente única de la pantalla principal.
    """
    db.commit()  # consolida los ajustes de disponibilidad antes de leer
    return DashboardRead(
        tarjetas=indicadores.tarjetas_kpi(db),
        cumplimiento=indicadores.cumplimiento_normativo(db),
        pedidos_recientes=indicadores.pedidos_recientes(db),
        ficha_lote=indicadores.ficha_lote(db),
        envio_destacado=indicadores.envio_destacado(db),
        alertas=indicadores.alertas(db),
    )


@router.get("/reportes/kpis", response_model=KpiResumen, summary="Indicadores gerenciales")
def kpis(db: Session = Depends(get_db), _u: Usuario = Depends(_roles_internos)) -> KpiResumen:
    """HU-15 · Volumen exportado, café, cacao, ingresos, países de destino,
    clientes, pedidos, envíos activos, tiempo promedio de entrega, estado de
    los contratos y pagos pendientes."""
    db.commit()
    return indicadores.calcular_kpis(db)
