"""Pruebas de los Sprint 3 y 4.

Sprint 3 — pagos y cartera (HU-14), notificaciones (HU-16) y auditoría (HU-21).
Sprint 4 — multimoneda (HU-19), integraciones (HU-20) y respaldos (HU-22).
"""

from __future__ import annotations

from pathlib import Path

from app.models import Rol, Usuario
from app.security import hash_password
from tests.conftest import CONTRASENA


# --------------------------------------------------------------------------- #
# Utilidades                                                                   #
# --------------------------------------------------------------------------- #
def _login(cliente, correo: str) -> dict[str, str]:
    r = cliente.post(
        "/api/auth/login",
        json={"correo": correo, "contrasena": CONTRASENA},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _crear_exportacion(
    cliente, datos, *, kg: str = "100", precio: str = "10", id_cliente: int | None = None
) -> dict:
    """Crea un lote y un contrato de 1.000 EUR (100 kg × 10 EUR)."""
    cab = datos["_cab"]
    lote = cliente.post(
        "/api/lotes",
        headers=cab,
        json={
            "id_finca": datos["finca"].id_finca,
            "id_producto": datos["producto_cafe"].id_producto,
            "cantidad_kg": kg,
            "fecha_cosecha": datos["hoy"].isoformat(),
        },
    )
    assert lote.status_code == 201, lote.text

    r = cliente.post(
        "/api/exportaciones",
        headers=cab,
        json={
            "id_cliente": id_cliente or datos["cliente"].id_cliente,
            "fecha": datos["hoy"].isoformat(),
            "moneda": "EUR",
            "puerto_origen": "Cartagena",
            "puerto_destino": "Rotterdam",
            "detalles": [
                {
                    "id_lote": lote.json()["id_lote"],
                    "cantidad_kg": kg,
                    "precio_kg": precio,
                }
            ],
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def _pago(id_exportacion: int, datos, valor: str, **extra) -> dict:
    cuerpo = {
        "id_exportacion": id_exportacion,
        "fecha": datos["hoy"].isoformat(),
        "tipo": "Anticipo",
        "metodo": "Transferencia",
        "valor": valor,
        "moneda": "EUR",
        "referencia": "RF-TEST-001",
    }
    cuerpo.update(extra)
    return cuerpo


# --------------------------------------------------------------------------- #
# Financiero · HU-14                                                           #
# --------------------------------------------------------------------------- #
class TestFinanciero:
    def test_registra_pago_y_actualiza_la_cartera(self, cliente, datos):
        exp = _crear_exportacion(cliente, datos)

        r = cliente.post("/api/pagos", headers=datos["_cab"], json=_pago(exp["id_exportacion"], datos, "300.00"))
        assert r.status_code == 201, r.text
        pago = r.json()
        assert pago["valor"] == "300.00"
        assert pago["estado"] == "Registrado"
        assert pago["numero_contrato"] == exp["numero_contrato"]
        assert pago["cliente"] == "Café Rotterdam BV"

        listado = cliente.get("/api/pagos", headers=datos["_cab"]).json()
        assert listado["total"] == 1

        resumen = cliente.get("/api/financiero/resumen", headers=datos["_cab"]).json()
        assert resumen["total_contratado"] == 1000.0
        assert resumen["total_cobrado"] == 300.0
        assert resumen["total_pendiente"] == 700.0
        assert resumen["contratos_con_saldo"] == 1

    def test_rechaza_sobrecobro(self, cliente, datos):
        exp = _crear_exportacion(cliente, datos)
        assert cliente.post(
            "/api/pagos", headers=datos["_cab"], json=_pago(exp["id_exportacion"], datos, "300.00")
        ).status_code == 201

        r = cliente.post(
            "/api/pagos", headers=datos["_cab"], json=_pago(exp["id_exportacion"], datos, "800.00")
        )
        assert r.status_code == 400
        assert "supera el saldo" in r.json()["detail"]

    def test_anular_pago_lo_saca_de_la_cartera(self, cliente, datos):
        exp = _crear_exportacion(cliente, datos)
        pago = cliente.post(
            "/api/pagos", headers=datos["_cab"], json=_pago(exp["id_exportacion"], datos, "250.00")
        ).json()

        r = cliente.post(f"/api/pagos/{pago['id_pago']}/anular", headers=datos["_cab"])
        assert r.status_code == 200
        assert r.json()["estado"] == "Anulado"

        resumen = cliente.get("/api/financiero/resumen", headers=datos["_cab"]).json()
        assert resumen["total_cobrado"] == 0.0
        assert resumen["total_pendiente"] == 1000.0
        assert resumen["pagos_anulados"] == 1

        # Un pago anulado no se modifica ni se vuelve a anular.
        assert cliente.post(
            f"/api/pagos/{pago['id_pago']}/anular", headers=datos["_cab"]
        ).status_code == 409

    def test_pago_confirmado_no_se_elimina(self, cliente, datos):
        exp = _crear_exportacion(cliente, datos)
        pago = cliente.post(
            "/api/pagos", headers=datos["_cab"], json=_pago(exp["id_exportacion"], datos, "100.00")
        ).json()
        cliente.patch(
            f"/api/pagos/{pago['id_pago']}",
            headers=datos["_cab"],
            json={"estado": "Confirmado"},
        )
        r = cliente.delete(f"/api/pagos/{pago['id_pago']}", headers=datos["_cab"])
        assert r.status_code == 409
        assert "anúlalo" in r.json()["detail"]

    def test_solo_finanzas_registra_pagos(self, cliente, datos):
        exp = _crear_exportacion(cliente, datos)
        cab_logistica = _login(cliente, "logistica@ritch.com")
        r = cliente.post(
            "/api/pagos",
            headers=cab_logistica,
            json=_pago(exp["id_exportacion"], datos, "100.00"),
        )
        assert r.status_code == 403

    def test_pago_en_otra_moneda_se_consolida_en_eur(self, cliente, datos):
        exp = _crear_exportacion(cliente, datos)
        # Sin tabla de tipos, el servicio usa el respaldo local: 1 EUR = 1,09 USD.
        r = cliente.post(
            "/api/pagos",
            headers=datos["_cab"],
            json=_pago(exp["id_exportacion"], datos, "109.00", moneda="USD"),
        )
        assert r.status_code == 201, r.text

        resumen = cliente.get("/api/financiero/resumen", headers=datos["_cab"]).json()
        assert resumen["total_cobrado"] == 100.0
        assert resumen["total_pendiente"] == 900.0

    def test_cliente_europeo_solo_ve_su_propia_cartera(self, cliente, datos, db):
        # Dos contratos de 1.000 EUR con sendos anticipos de 300 EUR: uno del
        # cliente del portal y otro de otra empresa. El resumen del portal debe
        # ignorar por completo el segundo, incluso en los contadores globales.
        propio = _crear_exportacion(cliente, datos)
        ajeno = _crear_exportacion(
            cliente, datos, id_cliente=datos["otro_cliente"].id_cliente
        )
        for exp in (propio, ajeno):
            assert cliente.post(
                "/api/pagos", headers=datos["_cab"], json=_pago(exp["id_exportacion"], datos, "300.00")
            ).status_code == 201

        portal = Usuario(
            nombre="Comprador Rotterdam",
            correo="portal@cafe-rotterdam.nl",
            contrasena_hash=hash_password(CONTRASENA),
            rol=Rol.CLIENTE_EU,
            id_cliente=datos["cliente"].id_cliente,
        )
        db.add(portal)
        db.commit()

        cab_portal = _login(cliente, "portal@cafe-rotterdam.nl")
        resumen = cliente.get("/api/financiero/resumen", headers=cab_portal).json()
        assert resumen["total_contratado"] == 1000.0
        assert resumen["total_cobrado"] == 300.0
        assert resumen["total_pendiente"] == 700.0
        assert resumen["total_anticipos"] == 300.0
        assert resumen["pagos_registrados"] == 1
        assert resumen["pagos_confirmados"] == 0
        assert resumen["contratos_con_saldo"] == 1
        assert len(resumen["por_exportacion"]) == 1
        assert resumen["por_exportacion"][0]["id_exportacion"] == propio["id_exportacion"]

        # El listado de pagos también respeta la frontera entre importadores.
        listado = cliente.get("/api/pagos", headers=cab_portal).json()
        assert listado["total"] == 1
        assert listado["items"][0]["id_exportacion"] == propio["id_exportacion"]


# --------------------------------------------------------------------------- #
# Notificaciones · HU-16                                                       #
# --------------------------------------------------------------------------- #
class TestNotificaciones:
    def test_bandeja_marca_leidas(self, cliente, datos):
        cab = datos["_cab"]
        r = cliente.post(
            "/api/notificaciones",
            headers=cab,
            json={
                "titulo": "Aviso de prueba",
                "detalle": "Contenido de la prueba.",
                "tipo": "Sistema",
                "tono": "azul",
            },
        )
        assert r.status_code == 201, r.text
        aviso = r.json()
        assert aviso["leida"] is False

        contador = cliente.get("/api/notificaciones/contador", headers=cab).json()
        assert contador["total"] == 1
        assert contador["no_leidas"] == 1

        leida = cliente.post(f"/api/notificaciones/{aviso['id_notificacion']}/leer", headers=cab)
        assert leida.status_code == 200
        assert leida.json()["leida"] is True

        assert cliente.get("/api/notificaciones/contador", headers=cab).json()["no_leidas"] == 0

    def test_clave_hace_idempotente_el_aviso(self, cliente, datos):
        cab = datos["_cab"]
        cuerpo = {
            "titulo": "Vencimiento de certificación",
            "clave": "prueba-clave-unica",
            "tipo": "Certificación",
            "tono": "gold",
        }
        primero = cliente.post("/api/notificaciones", headers=cab, json=cuerpo)
        segundo = cliente.post("/api/notificaciones", headers=cab, json=cuerpo)
        assert primero.status_code == segundo.status_code == 201
        assert primero.json()["id_notificacion"] == segundo.json()["id_notificacion"]

        avisos = cliente.get("/api/notificaciones?limite=200", headers=cab).json()
        assert sum(1 for a in avisos if a["clave"] == "prueba-clave-unica") == 1

    def test_marcar_todas(self, cliente, datos):
        cab = datos["_cab"]
        for titulo in ("Primer aviso", "Segundo aviso"):
            assert cliente.post(
                "/api/notificaciones", headers=cab, json={"titulo": titulo}
            ).status_code == 201

        r = cliente.post("/api/notificaciones/leer-todas", headers=cab)
        assert r.status_code == 200
        assert "2 notificación" in r.json()["mensaje"]
        assert cliente.get("/api/notificaciones/contador", headers=cab).json()["no_leidas"] == 0


# --------------------------------------------------------------------------- #
# Auditoría · HU-21                                                            #
# --------------------------------------------------------------------------- #
class TestAuditoria:
    def test_el_login_deja_rastro(self, cliente, datos):
        filas = cliente.get(
            "/api/auditoria", headers=datos["_cab"], params={"q": "Iniciar sesión"}
        ).json()
        assert filas["total"] >= 1
        assert any(f["accion"] == "Iniciar sesión" for f in filas["items"])
        assert all(f["usuario_correo"] == "admin@ritch.com" for f in filas["items"])

    def test_un_pago_queda_auditado(self, cliente, datos):
        exp = _crear_exportacion(cliente, datos)
        pago = cliente.post(
            "/api/pagos", headers=datos["_cab"], json=_pago(exp["id_exportacion"], datos, "150.00")
        ).json()

        filas = cliente.get(
            "/api/auditoria", headers=datos["_cab"], params={"accion": "Registrar pago"}
        ).json()
        assert filas["total"] == 1
        fila = filas["items"][0]
        assert fila["entidad"] == "pagos"
        assert fila["id_entidad"] == str(pago["id_pago"])
        assert fila["metodo"] == "POST"

        detalle = cliente.get(
            f"/api/auditoria/{fila['id_auditoria']}", headers=datos["_cab"]
        )
        assert detalle.status_code == 200
        assert detalle.json()["accion"] == "Registrar pago"

    def test_solo_el_administrador_consulta_el_rastro(self, cliente, datos):
        cab_logistica = _login(cliente, "logistica@ritch.com")
        assert cliente.get("/api/auditoria", headers=cab_logistica).status_code == 403


# --------------------------------------------------------------------------- #
# Multimoneda · HU-19                                                          #
# --------------------------------------------------------------------------- #
class TestMultimoneda:
    def test_convierte_con_la_tasa_vigente(self, cliente, datos):
        cab = datos["_cab"]
        r = cliente.post(
            "/api/tipos-cambio",
            headers=cab,
            json={
                "moneda": "USD",
                "tasa": "1.25",
                "fecha": datos["hoy"].isoformat(),
                "fuente": "Prueba",
            },
        )
        assert r.status_code == 201, r.text
        assert float(r.json()["tasa"]) == 1.25

        conversion = cliente.get(
            "/api/monedas/convertir",
            headers=cab,
            params={"valor": "100", "desde": "EUR", "hasta": "USD"},
        )
        assert conversion.status_code == 200
        cuerpo = conversion.json()
        assert cuerpo["resultado"] == 125.0
        assert cuerpo["tasa"] == 1.25

    def test_actualizar_tasas_es_idempotente(self, cliente, datos):
        cab = datos["_cab"]
        # Una carga manual previa del mismo día no debe duplicar la fila.
        cliente.post(
            "/api/tipos-cambio",
            headers=cab,
            json={"moneda": "USD", "tasa": "1.25", "fecha": datos["hoy"].isoformat()},
        )

        r = cliente.post("/api/tipos-cambio/actualizar", headers=cab)
        assert r.status_code == 200, r.text
        resultado = r.json()
        assert resultado["modo"] == "respaldo local"
        assert resultado["actualizados"] >= 2
        assert float(resultado["tasas"]["USD"]) == 1.09

        tipos = cliente.get("/api/tipos-cambio", headers=cab).json()
        assert sum(1 for t in tipos if t["moneda"] == "USD") == 1
        assert float(next(t for t in tipos if t["moneda"] == "USD")["tasa"]) == 1.09

    def test_moneda_desconocida_devuelve_400(self, cliente, datos):
        r = cliente.get(
            "/api/monedas/convertir",
            headers=datos["_cab"],
            params={"valor": "10", "desde": "EUR", "hasta": "XXX"},
        )
        assert r.status_code == 400


# --------------------------------------------------------------------------- #
# Integraciones · HU-20                                                        #
# --------------------------------------------------------------------------- #
class TestIntegraciones:
    def test_estado_de_los_servicios(self, cliente, datos):
        r = cliente.get("/api/integraciones", headers=datos["_cab"])
        assert r.status_code == 200
        servicios = {i["servicio"]: i for i in r.json()}
        assert {"Tipos de cambio", "Correo", "Seguimiento navieras", "Almacenamiento documental"} <= set(servicios)
        assert servicios["Correo"]["estado"] == "simulado"

    def test_correo_simulado_deja_bitacora(self, cliente, datos):
        cab = datos["_cab"]
        r = cliente.post(
            "/api/integraciones/correo",
            headers=cab,
            json={"destinatario": "compras@ritch.com", "asunto": "Prueba"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["estado"] == "simulado"
        assert "compras@ritch.com" in r.json()["mensaje"]

        bitacora = cliente.get("/api/integraciones/bitacora", headers=cab).json()
        assert any(f["servicio"] == "Correo" for f in bitacora)

    def test_correo_invalido_se_rechaza(self, cliente, datos):
        r = cliente.post(
            "/api/integraciones/correo",
            headers=datos["_cab"],
            json={"destinatario": "sin-arroba"},
        )
        assert r.status_code == 422

    def test_seguimiento_sin_envio_deja_error(self, cliente, datos):
        r = cliente.post(
            "/api/integraciones/seguimiento/NO-EXISTE", headers=datos["_cab"]
        )
        assert r.status_code == 200
        assert r.json()["estado"] == "error"
        assert "No hay un envío" in r.json()["mensaje"]

    def test_bitacora_solo_para_administradores(self, cliente, datos):
        cab_logistica = _login(cliente, "logistica@ritch.com")
        assert cliente.get("/api/integraciones/bitacora", headers=cab_logistica).status_code == 403
        # El estado de las integraciones sí es visible para el personal interno.
        assert cliente.get("/api/integraciones", headers=cab_logistica).status_code == 200


# --------------------------------------------------------------------------- #
# Respaldos · HU-22                                                            #
# --------------------------------------------------------------------------- #
class TestRespaldos:
    def test_crea_verifica_y_descarga(self, cliente, datos):
        cab = datos["_cab"]
        r = cliente.post("/api/respaldos", headers=cab)
        assert r.status_code == 201, r.text
        respaldo = r.json()
        assert respaldo["nombre"].startswith("ritch-")
        assert respaldo["tipo"] == "Manual"
        assert respaldo["estado"] == "Completado"
        assert respaldo["tablas"] > 0
        assert respaldo["registros"] >= 4
        assert len(respaldo["checksum"]) == 64
        assert Path(respaldo["ruta"]).is_file()

        verificacion = cliente.post(
            f"/api/respaldos/{respaldo['id_respaldo']}/verificar", headers=cab
        )
        assert verificacion.status_code == 200
        assert verificacion.json()["existe"] is True
        assert verificacion.json()["integro"] is True

        listado = cliente.get("/api/respaldos", headers=cab).json()
        assert any(x["id_respaldo"] == respaldo["id_respaldo"] for x in listado)

        descarga = cliente.get(
            f"/api/respaldos/{respaldo['id_respaldo']}/descargar", headers=cab
        )
        assert descarga.status_code == 200
        assert descarga.headers["content-type"].startswith("application/json")
        assert b"RiTech SAS" in descarga.content

    def test_un_archivo_borrado_no_es_integro(self, cliente, datos):
        cab = datos["_cab"]
        respaldo = cliente.post("/api/respaldos", headers=cab).json()
        Path(respaldo["ruta"]).unlink()

        verificacion = cliente.post(
            f"/api/respaldos/{respaldo['id_respaldo']}/verificar", headers=cab
        ).json()
        assert verificacion["existe"] is False
        assert verificacion["integro"] is False

    def test_solo_el_administrador_respalda(self, cliente, datos):
        cab_logistica = _login(cliente, "logistica@ritch.com")
        assert cliente.post("/api/respaldos", headers=cab_logistica).status_code == 403
        assert cliente.get("/api/respaldos", headers=cab_logistica).status_code == 403
