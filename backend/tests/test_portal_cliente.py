"""Portal del cliente europeo (HU-10) y control de acceso por rol.

El portal tiene una sola garantía que importa: una cuenta con el rol «Cliente
europeo» ve las exportaciones y los envíos de su propia empresa, y nada más. Las
pruebas de aquí son la red que sostiene esa garantía, porque un filtro mal
colocado se rompe en silencio: la API sigue respondiendo 200 y lo único que
cambia es que un cliente ve los pedidos de la competencia.

Se comprueban las dos caras:

  · lo que el cliente PUEDE ver (sus datos, el catálogo);
  · lo que NO puede (los de otros, el panel general, y escribir cualquier cosa).
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import (
    Envio,
    EstadoEnvio,
    EstadoExportacion,
    Exportacion,
    Rol,
    Usuario,
)
from app.security import hash_password
from tests.datos import CONTRASENA

# --------------------------------------------------------------------------- #
# Utilidades                                                                     #
# --------------------------------------------------------------------------- #


def _crear_exportacion(db: Session, cliente, numero: str) -> Exportacion:
    """Exportación mínima, la que el cliente debería ver en su portal."""
    exportacion = Exportacion(
        id_cliente=cliente.id_cliente,
        id_usuario=1,
        numero_contrato=numero,
        incoterm="FOB",
        puerto_origen="Cartagena",
        puerto_destino=cliente.puerto_destino,
        estado=EstadoExportacion.EN_TRANSITO,
        fecha=date.today(),
    )
    db.add(exportacion)
    db.flush()
    return exportacion


def _crear_envio(db: Session, exportacion: Exportacion, seguimiento: str) -> Envio:
    envio = Envio(
        id_exportacion=exportacion.id_exportacion,
        transportadora="Maersk",
        numero_seguimiento=seguimiento,
        estado=EstadoEnvio.EN_TRANSITO,
    )
    db.add(envio)
    db.flush()
    return envio


def _crear_cuenta_cliente(
    db: Session, cliente: TestClient, cab: dict, correo: str, id_cliente: int | None
) -> int:
    """Crea la cuenta por la API, como lo haría el administrador."""
    r = cliente.post(
        "/api/usuarios",
        headers=cab,
        json={
            "nombre": "Comprador de Prueba",
            "correo": correo,
            "contrasena": "ClavePortal2026*",
            "rol": Rol.CLIENTE_EU.value,
            "id_cliente": id_cliente,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id_usuario"]


@pytest.fixture
def portal(datos: dict, cliente: TestClient) -> dict:
    """Dos clientes europeos, un pedido y un envío para cada uno.

    Devuelve las cabeceras de autenticación de cada cuenta, ya listas para
    probar lo que ve una y lo que ve la otra.
    """
    db: Session = datos["_db"]
    cab: dict = datos["_cab"]

    propio = datos["cliente"]
    otro = datos["otro_cliente"]

    e1 = _crear_exportacion(db, propio, "CTR-PRIO-001")
    _crear_envio(db, e1, "MSKU-PRIO-001")
    e2 = _crear_exportacion(db, otro, "CTR-OTRO-001")
    _crear_envio(db, e2, "MSKU-OTRO-001")
    db.commit()

    id_propio = _crear_cuenta_cliente(
        db, cliente, cab, "comprador.propio@ritch.com", propio.id_cliente
    )
    id_otro = _crear_cuenta_cliente(
        db, cliente, cab, "comprador.otro@ritch.com", otro.id_cliente
    )

    def _cabecera(correo: str) -> dict:
        r = cliente.post(
            "/api/auth/login", json={"correo": correo, "contrasena": "ClavePortal2026*"}
        )
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return {
        "id_propio": id_propio,
        "id_otro": id_otro,
        "exportacion_propia": e1.id_exportacion,
        "exportacion_ajena": e2.id_exportacion,
        "cab_propio": _cabecera("comprador.propio@ritch.com"),
        "cab_otro": _cabecera("comprador.otro@ritch.com"),
        "id_cliente_propio": propio.id_cliente,
        "id_cliente_otro": otro.id_cliente,
    }


# --------------------------------------------------------------------------- #
# Crear la cuenta                                                                #
# --------------------------------------------------------------------------- #
def test_cliente_necesita_empresa(datos: dict, cliente: TestClient) -> None:
    """Sin empresa no hay portal: la API lo rechaza al crear la cuenta."""
    r = cliente.post(
        "/api/usuarios",
        headers=datos["_cab"],
        json={
            "nombre": "Comprador",
            "correo": "sin.empresa@ritch.com",
            "contrasena": "ClavePortal2026*",
            "rol": Rol.CLIENTE_EU.value,
        },
    )
    assert r.status_code == 422
    assert "Cliente europeo" in r.json()["detail"]


def test_cliente_no_puede_apuntar_a_una_empresa_inexistente(
    datos: dict, cliente: TestClient
) -> None:
    r = cliente.post(
        "/api/usuarios",
        headers=datos["_cab"],
        json={
            "nombre": "Comprador",
            "correo": "empresa.falsa@ritch.com",
            "contrasena": "ClavePortal2026*",
            "rol": Rol.CLIENTE_EU.value,
            "id_cliente": 9999,
        },
    )
    assert r.status_code == 422


def test_usuario_interno_no_guarda_empresa(datos: dict, cliente: TestClient) -> None:
    """Un comercial no se ata a una empresa: el dato se descarta."""
    r = cliente.post(
        "/api/usuarios",
        headers=datos["_cab"],
        json={
            "nombre": "Comercial Prueba",
            "correo": "comercial@ritch.com",
            "contrasena": "ClavePortal2026*",
            "rol": Rol.COMERCIAL.value,
            "id_cliente": datos["cliente"].id_cliente,
        },
    )
    assert r.status_code == 201
    assert r.json()["id_cliente"] is None


def test_cuenta_de_cliente_devuelve_el_nombre_de_su_empresa(
    datos: dict, cliente: TestClient
) -> None:
    """La pantalla de usuarios puede decir de quién es la cuenta."""
    _crear_cuenta_cliente(
        datos["_db"], cliente, datos["_cab"], "con.nombre@ritch.com",
        datos["cliente"].id_cliente,
    )
    r = cliente.get(
        "/api/usuarios", headers=datos["_cab"], params={"q": "con.nombre"}
    )
    assert r.status_code == 200
    assert r.json()["items"][0]["nombre_cliente"] == "Café Rotterdam BV"


# --------------------------------------------------------------------------- #
# El cliente ve lo suyo, y solo lo suyo                                         #
# --------------------------------------------------------------------------- #
def test_cliente_ve_su_empresa_en_la_lista(portal: dict, cliente: TestClient) -> None:
    r = cliente.get("/api/exportaciones", headers=portal["cab_propio"])
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["numero_contrato"] == "CTR-PRIO-001"


def test_no_puede_ampliar_el_filtro_por_url(portal: dict, cliente: TestClient) -> None:
    """`?id_cliente=` es un filtro normal; para un cliente no puede servir de lupa."""
    r = cliente.get(
        "/api/exportaciones",
        headers=portal["cab_propio"],
        params={"id_cliente": portal["id_cliente_otro"]},
    )
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["numero_contrato"] == "CTR-PRIO-001"


def test_no_puede_abrir_el_pedido_de_otro(portal: dict, cliente: TestClient) -> None:
    """Un 404, no un 403: tampoco se le confirma que ese pedido existe."""
    r = cliente.get(
        f"/api/exportaciones/{portal['exportacion_ajena']}",
        headers=portal["cab_propio"],
    )
    assert r.status_code == 404


def test_cada_cliente_ve_su_propio_envio(portal: dict, cliente: TestClient) -> None:
    r = cliente.get("/api/envios", headers=portal["cab_propio"])
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["numero_seguimiento"] == "MSKU-PRIO-001"

    r2 = cliente.get("/api/envios", headers=portal["cab_otro"])
    assert r2.json()["items"][0]["numero_seguimiento"] == "MSKU-OTRO-001"


def test_no_puede_ver_la_trazabilidad_de_un_envio_ajeno(
    portal: dict, cliente: TestClient
) -> None:
    r = cliente.get("/api/envios", headers=portal["cab_otro"])
    ajeno = r.json()["items"][0]["id_envio"]
    r2 = cliente.get(
        f"/api/envios/{ajeno}/trazabilidad", headers=portal["cab_propio"]
    )
    assert r2.status_code == 404


# --------------------------------------------------------------------------- #
# Lo que el cliente no puede ver ni tocar                                        #
# --------------------------------------------------------------------------- #
def test_no_entra_al_panel_general(portal: dict, cliente: TestClient) -> None:
    """Los indicadores son de la empresa, no del cliente."""
    assert cliente.get("/api/panel", headers=portal["cab_propio"]).status_code == 403
    assert (
        cliente.get("/api/reportes/kpis", headers=portal["cab_propio"]).status_code
        == 403
    )


def test_no_ve_las_cotizaciones_de_otros(portal: dict, cliente: TestClient) -> None:
    assert (
        cliente.get("/api/cotizaciones", headers=portal["cab_propio"]).status_code
        == 403
    )


def test_no_ve_la_lista_de_clientes(portal: dict, cliente: TestClient) -> None:
    assert cliente.get("/api/clientes", headers=portal["cab_propio"]).status_code == 403


def test_solo_lectura_no_escribe(portal: dict, cliente: TestClient) -> None:
    """El portal es de consulta: ninguna escritura le sale al cliente."""
    propias = {"headers": portal["cab_propio"]}
    id_exportacion = portal["exportacion_propia"]

    casos = [
        ("post", "/api/cotizaciones", {"id_cliente": 1, "producto": "Café"}),
        ("post", f"/api/exportaciones/{id_exportacion}/documentos", {"tipo": "Factura"}),
        ("patch", f"/api/exportaciones/{id_exportacion}", {"estado": "Anulada"}),
        ("post", "/api/envios", {"id_exportacion": id_exportacion,
                                  "transportadora": "Maersk",
                                  "numero_seguimiento": "HACK-001"}),
        ("post", "/api/usuarios", {"nombre": "Intruso", "correo": "i@x.com",
                                    "contrasena": "ClavePortal2026*",
                                    "rol": "Administrador"}),
    ]
    for metodo, ruta, cuerpo in casos:
        r = cliente.request(metodo.upper(), ruta, json=cuerpo, **propias)
        assert r.status_code in (403, 404), f"{metodo.upper()} {ruta} devolvió {r.status_code}"


def test_cliente_sin_empresa_no_ve_nada(datos: dict, cliente: TestClient) -> None:
    """Una cuenta huérfana se rechaza al crearla, pero si queda alguna debe fallar
    al leer, no devolver la lista completa."""
    db: Session = datos["_db"]
    huerfano = Usuario(
        nombre="Huerfano",
        correo="huerfano@ritch.com",
        contrasena_hash=hash_password(CONTRASENA),
        rol=Rol.CLIENTE_EU,
    )
    db.add(huerfano)
    db.commit()
    r = cliente.post(
        "/api/auth/login", json={"correo": "huerfano@ritch.com", "contrasena": CONTRASENA}
    )
    cab = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = cliente.get("/api/exportaciones", headers=cab)
    assert r.status_code == 403
    assert "empresa" in r.json()["detail"]


# --------------------------------------------------------------------------- #
# El personal de RiTech sigue viendo todo                                        #
# --------------------------------------------------------------------------- #
def test_administrador_no_pierde_ningun_dato(portal: dict, cliente: TestClient) -> None:
    """El filtro es solo para el cliente: internamente no cambia nada."""
    r = cliente.post(
        "/api/auth/login",
        json={"correo": "admin@ritch.com", "contrasena": CONTRASENA},
    )
    cab = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert cliente.get("/api/exportaciones", headers=cab).json()["total"] == 2
    assert cliente.get("/api/envios", headers=cab).json()["total"] == 2
    assert cliente.get("/api/panel", headers=cab).status_code == 200
