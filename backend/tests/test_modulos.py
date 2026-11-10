"""Pruebas de los módulos del Sprint 2.

Cubren el modelo de datos de nueve tablas, las reglas de negocio (inventario,
cadena de estados, certificaciones) y el control de acceso por rol.
"""

from __future__ import annotations

from datetime import timedelta
import pytest
from app.models import EstadoExportacion
from app.services.reglas import puede_transicionar, progreso
from tests.conftest import CONTRASENA
from tests.datos import sembrar_minimo

# --------------------------------------------------------------------------- #
# Utilidades                                                                   #
# --------------------------------------------------------------------------- #
def crear_lote(cliente, datos, kg="1000"):
    """Crea un lote de café y devuelve su representación."""
    r = cliente.post(
        "/api/lotes",
        headers=datos["_cab"],
        json={
            "id_finca": datos["finca"].id_finca,
            "id_producto": datos["producto_cafe"].id_producto,
            "cantidad_kg": kg,
            "fecha_cosecha": datos["hoy"].isoformat(),
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


# --------------------------------------------------------------------------- #
# Autenticación y roles · HU-01, HU-02, RR-004                              #
# --------------------------------------------------------------------------- #
class TestAutenticacion:
    def test_salud(self, cliente):
        assert cliente.get("/api/salud").json()["estado"] == "ok"

    def test_login_devuelve_token_y_rol(self, cliente, datos):
        r = cliente.post(
            "/api/auth/login",
            json={"correo": "admin@ritch.com", "contrasena": CONTRASENA},
        )
        assert r.status_code == 200
        cuerpo = r.json()
        assert cuerpo["usuario"]["rol"] == "Administrador"
        assert cuerpo["access_token"]

    def test_login_rechaza_contrasena_incorrecta(self, cliente, datos):
        r = cliente.post(
            "/api/auth/login",
            json={"correo": "admin@ritch.com", "contrasena": "incorrecta"},
        )
        assert r.status_code == 401

    def test_no_revela_si_el_correo_existe(self, cliente, datos):
        r = cliente.post(
            "/api/auth/login",
            json={"correo": "nadie@ritch.com", "contrasena": CONTRASENA},
        )
        assert r.status_code == 401
        assert r.json()["detail"] == "Correo o contraseña incorrectos"

    def test_sin_token_no_hay_acceso(self, cliente, datos):
        assert cliente.get("/api/lotes").status_code == 401

    def test_usuario_inactivo_no_entra(self, cliente, datos):
        datos["logistica"].estado = "inactivo"
        datos["_db"].commit()
        r = cliente.post(
            "/api/auth/login",
            json={"correo": "logistica@ritch.com", "contrasena": CONTRASENA},
        )
        assert r.status_code == 403


class TestRoles:
    def _login(self, cliente, correo):
        r = cliente.post(
            "/api/auth/login", json={"correo": correo, "contrasena": CONTRASENA}
        )
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def test_calidad_no_administra_usuarios(self, cliente, datos):
        cab = self._login(cliente, "calidad@ritch.com")
        assert cliente.get("/api/usuarios", headers=cab).status_code == 403

    def test_logistica_no_registra_fincas(self, cliente, datos):
        cab = self._login(cliente, "logistica@ritch.com")
        r = cliente.post(
            "/api/fincas",
            headers=cab,
            json={
                "nombre": "F",
                "ubicacion": "U",
                "departamento": "D",
                "propietario": "P",
            },
        )
        assert r.status_code == 403

    def test_logistica_gestiona_envios(self, cliente, datos):
        cab = self._login(cliente, "logistica@ritch.com")
        assert cliente.get("/api/envios", headers=cab).status_code == 200

    def test_calidad_consulta_lotes(self, cliente, datos):
        cab = self._login(cliente, "calidad@ritch.com")
        assert cliente.get("/api/lotes", headers=cab).status_code == 200


# --------------------------------------------------------------------------- #
# Módulo de productores, fincas y lotes · HU-04, HU-05, HU-06                 #
# --------------------------------------------------------------------------- #
class TestFincas:
    def test_crea_finca(self, cliente, datos):
        r = cliente.post(
            "/api/fincas",
            headers=datos["_cab"],
            json={
                "nombre": "Finca Nueva",
                "ubicacion": "Vereda X",
                "departamento": "Huila",
                "propietario": "Dueño",
                "latitud": "2.317778",
                "longitud": "-75.723611",
            },
        )
        assert r.status_code == 201
        assert r.json()["latitud"] is not None


class TestLotes:
    def test_codigo_lote_automatico(self, cliente, datos):
        lote = crear_lote(cliente, datos, kg="5000")
        assert lote["codigo_lote"].startswith("CO-HUI-")
        assert float(lote["disponible_kg"]) == 5000.0

    def test_codigo_duplicado_rechazado(self, cliente, datos):
        lote = crear_lote(cliente, datos)
        r = cliente.post(
            "/api/lotes",
            headers=datos["_cab"],
            json={
                "id_finca": datos["finca"].id_finca,
                "id_producto": datos["producto_cafe"].id_producto,
                "cantidad_kg": "100",
                "fecha_cosecha": datos["hoy"].isoformat(),
                "codigo_lote": lote["codigo_lote"],
            },
        )
        assert r.status_code == 409

    def test_fecha_cosecha_futura_rechazada(self, cliente, datos):
        cab = datos["_cab"]
        r = cliente.post(
            "/api/lotes",
            headers=cab,
            json={
                "id_finca": datos["finca"].id_finca,
                "id_producto": 1,
                "cantidad_kg": "100",
                "fecha_cosecha": "2099-01-01",
            },
        )
        assert r.status_code == 422

    def test_finca_inexistente(self, cliente, datos):
        r = cliente.post(
            "/api/lotes",
            headers=datos["_cab"],
            json={
                "id_finca": 9999,
                "id_producto": 1,
                "cantidad_kg": "100",
                "fecha_cosecha": datos["hoy"].isoformat(),
            },
        )
        assert r.status_code == 404

    def test_crea_evento_finca_automatico(self, cliente, datos):
        lote = crear_lote(cliente, datos)
        r = cliente.get(f"/api/lotes/{lote['id_lote']}/trazabilidad", headers=datos["_cab"])
        etapas = r.json()["etapas"]
        assert etapas[0]["etapa"] == "Finca"
        assert etapas[0]["estado"] == "done"
        assert etapas[1]["estado"] == "current"

    def test_no_reduce_lote_bajo_lo_comprometido(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos, kg="1000")
        # Se compromete todo el lote en una exportación.
        r = cliente.post(
            "/api/exportaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "fecha": datos["hoy"].isoformat(),
                "detalles": [
                    {
                        "id_lote": lote["id_lote"],
                        "cantidad_kg": "800",
                        "precio_kg": "7000",
                    }
                ],
            },
        )
        assert r.status_code == 201
        r = cliente.patch(
            f"/api/lotes/{lote['id_lote']}",
            headers=cab,
            json={"cantidad_kg": "500"},
        )
        assert r.status_code == 400
        assert "comprometidos" in r.json()["detail"]

    def test_retirar_lote_comprometido_falla(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos, kg="1000")
        cliente.post(
            "/api/exportaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "fecha": datos["hoy"].isoformat(),
                "detalles": [
                    {"id_lote": lote["id_lote"], "cantidad_kg": "800", "precio_kg": "7000"}
                ],
            },
        )
        r = cliente.delete(f"/api/lotes/{lote['id_lote']}", headers=cab)
        assert r.status_code == 409

    def test_inventario_refleja_compromisos(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos, kg="1000")
        cliente.post(
            "/api/exportaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "fecha": datos["hoy"].isoformat(),
                "detalles": [
                    {"id_lote": lote["id_lote"], "cantidad_kg": "600", "precio_kg": "7000"}
                ],
            },
        )
        r = cliente.get("/api/lotes/inventario", headers=cab).json()
        assert r["kilos_totales"] == 1000
        assert r["kilos_disponibles"] == 400
        assert r["kilos_comprometidos"] == 600


class TestTrazabilidad:
    def test_registra_hito_y_avanza_etapa(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        r = cliente.post(
            f"/api/lotes/{lote['id_lote']}/trazabilidad",
            headers=cab,
            json={"etapa": "Beneficio", "fecha": datos["hoy"].isoformat(), "ubicacion": "Beneficio"},
        )
        assert r.status_code == 201
        etapas = cliente.get(
            f"/api/lotes/{lote['id_lote']}/trazabilidad", headers=cab
        ).json()["etapas"]
        assert [e["etapa"] for e in etapas] == [
            "Finca", "Beneficio", "Puerto origen",
            "Tránsito marítimo", "Aduana UE", "Cliente",
        ]
        assert etapas[1]["estado"] == "done"
        assert etapas[2]["estado"] == "current"


# --------------------------------------------------------------------------- #
# Módulo de calidad · HU-17                                                    #
# --------------------------------------------------------------------------- #
class TestCalidad:
    def test_registra_calidad_y_actualiza_estado(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        r = cliente.put(
            f"/api/lotes/{lote['id_lote']}/calidad",
            headers=cab,
            json={"id_lote": lote["id_lote"], "humedad": "10.5", "puntaje_cata": "86.5"},
        )
        assert r.status_code == 200
        assert float(r.json()["puntaje_cata"]) == 86.5
        # Special (>=85) con responsable de aprobación → Aprobado
        assert cliente.get(f"/api/lotes/{lote['id_lote']}", headers=cab).json()["estado_calidad"] == "Aprobado"

    def test_humedad_fuera_de_rango(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        r = cliente.put(
            f"/api/lotes/{lote['id_lote']}/calidad",
            headers=cab,
            json={"id_lote": lote["id_lote"], "humedad": "18"},
        )
        assert r.status_code == 422

    def test_actualiza_calidad_existente(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        cliente.put(
            f"/api/lotes/{lote['id_lote']}/calidad",
            headers=cab,
            json={"id_lote": lote["id_lote"], "humedad": "11", "puntaje_cata": "82"},
        )
        r = cliente.put(
            f"/api/lotes/{lote['id_lote']}/calidad",
            headers=cab,
            json={"id_lote": lote["id_lote"], "humedad": "10", "puntaje_cata": "88"},
        )
        assert r.status_code == 200
        assert float(r.json()["puntaje_cata"]) == 88.0

    def test_sin_calidad_devuelve_404(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        assert cliente.get(f"/api/lotes/{lote['id_lote']}/calidad", headers=cab).status_code == 404


# --------------------------------------------------------------------------- #
# Certificaciones · Informe §6.4                                               #
# --------------------------------------------------------------------------- #
class TestCertificaciones:
    def test_registra_y_deriva_estado(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        r = cliente.post(
            "/api/certificaciones",
            headers=cab,
            json={
                "id_lote": lote["id_lote"],
                "tipo": "EUDR",
                "fecha_emision": datos["hoy"].isoformat(),
                "fecha_vencimiento": (datos["hoy"] + timedelta(days=400)).isoformat(),
                "lote_georreferenciado": True,
            },
        )
        assert r.status_code == 201
        assert r.json()["estado"] == "Vigente"

    def test_vencimiento_anterior_a_emision(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        r = cliente.post(
            "/api/certificaciones",
            headers=cab,
            json={
                "id_lote": lote["id_lote"],
                "tipo": "Orgánico",
                "fecha_emision": "2026-01-10",
                "fecha_vencimiento": "2025-01-10",
            },
        )
        assert r.status_code == 422

    def test_requiere_lote_o_finca(self, cliente, datos):
        r = cliente.post(
            "/api/certificaciones",
            headers=datos["_cab"],
            json={"tipo": "Fairtrade", "fecha_emision": "2026-01-10"},
        )
        assert r.status_code == 422


# --------------------------------------------------------------------------- #
# Módulo comercial · HU-03, HU-08, HU-09, HU-10                               #
# --------------------------------------------------------------------------- #
class TestComercial:
    def test_lista_clientes_devuelve_registro_completo(self, cliente, datos):
        r = cliente.get("/api/clientes", headers=datos["_cab"])
        assert r.status_code == 200
        primero = r.json()["items"][0]
        # La tabla necesita `activo` para pintar la columna de estado.
        assert "activo" in primero
        assert "vat" in primero

    def test_crea_cotizacion_con_numero_y_total(self, cliente, datos):
        r = cliente.post(
            "/api/cotizaciones",
            headers=datos["_cab"],
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "cantidad_kg": "5000",
                "precio_kg": "8000",
                "incoterm": "FOB",
                "fecha": datos["hoy"].isoformat(),
            },
        )
        assert r.status_code == 201
        cuerpo = r.json()
        assert cuerpo["numero"].startswith("QT-")
        assert float(cuerpo["valor_total"]) == 40_000_000.0

    def test_incoterm_invalido(self, cliente, datos):
        r = cliente.post(
            "/api/cotizaciones",
            headers=datos["_cab"],
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "cantidad_kg": "100",
                "precio_kg": "100",
                "incoterm": "XXX",
                "fecha": datos["hoy"].isoformat(),
            },
        )
        assert r.status_code == 422

    def test_acepta_cotizacion_y_genera_contrato(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos, kg="10000")
        cot = cliente.post(
            "/api/cotizaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "cantidad_kg": "5000",
                "precio_kg": "8000",
                "incoterm": "CIF",
                "fecha": datos["hoy"].isoformat(),
            },
        ).json()
        cliente.patch(f"/api/cotizaciones/{cot['id_cotizacion']}", headers=cab, json={"estado": "Enviada"})
        r = cliente.post(
            f"/api/cotizaciones/{cot['id_cotizacion']}/aceptar",
            headers=cab,
            json={"lotes": [lote["codigo_lote"]], "cantidad_default": "5000"},
        )
        assert r.status_code == 201
        exportacion = r.json()
        assert exportacion["numero_contrato"].startswith("CT-")
        assert exportacion["estado"] == "Pedido recibido"
        assert len(exportacion["detalles"]) == 1

    def test_no_convierte_dos_veces(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos, kg="10000")
        cot = cliente.post(
            "/api/cotizaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "cantidad_kg": "1000",
                "precio_kg": "8000",
                "incoterm": "FOB",
                "fecha": datos["hoy"].isoformat(),
            },
        ).json()
        cliente.patch(f"/api/cotizaciones/{cot['id_cotizacion']}", headers=cab, json={"estado": "Enviada"})
        cuerpo = {"lotes": [lote["codigo_lote"]], "cantidad_default": "1000"}
        assert cliente.post(f"/api/cotizaciones/{cot['id_cotizacion']}/aceptar", headers=cab, json=cuerpo).status_code == 201
        assert cliente.post(f"/api/cotizaciones/{cot['id_cotizacion']}/aceptar", headers=cab, json=cuerpo).status_code == 409

    def test_no_pide_mas_de_lo_disponible(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos, kg="1000")
        r = cliente.post(
            "/api/exportaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "fecha": datos["hoy"].isoformat(),
                "detalles": [
                    {"id_lote": lote["id_lote"], "cantidad_kg": "5000", "precio_kg": "7000"}
                ],
            },
        )
        assert r.status_code == 400
        assert "disponibles" in r.json()["detail"]

    def test_rechaza_lote_repetido(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos, kg="1000")
        r = cliente.post(
            "/api/exportaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "fecha": datos["hoy"].isoformat(),
                "detalles": [
                    {"id_lote": lote["id_lote"], "cantidad_kg": "100", "precio_kg": "7000"},
                    {"id_lote": lote["id_lote"], "cantidad_kg": "200", "precio_kg": "7000"},
                ],
            },
        )
        assert r.status_code == 422

    def test_documento_borrador_no_se_autoriza(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        exp = cliente.post(
            "/api/exportaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "fecha": datos["hoy"].isoformat(),
                "detalles": [
                    {"id_lote": lote["id_lote"], "cantidad_kg": "100", "precio_kg": "7000"}
                ],
            },
        ).json()
        doc = cliente.post(
            f"/api/exportaciones/{exp['id_exportacion']}/documentos",
            headers=cab,
            json={
                "tipo_documento": "Factura comercial",
                "numero_documento": "FC-1",
                "fecha_emision": datos["hoy"].isoformat(),
            },
        ).json()
        assert cliente.post(f"/api/documentos/{doc['id_documento']}/autorizar", headers=cab).status_code == 400
        cliente.patch(
            f"/api/documentos/{doc['id_documento']}", headers=cab, json={"estado": "Validado"}
        )
        assert cliente.post(f"/api/documentos/{doc['id_documento']}/autorizar", headers=cab).status_code == 200

    def test_numero_documento_duplicado(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        exp = cliente.post(
            "/api/exportaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "fecha": datos["hoy"].isoformat(),
                "detalles": [
                    {"id_lote": lote["id_lote"], "cantidad_kg": "100", "precio_kg": "7000"}
                ],
            },
        ).json()
        cuerpo = {
            "tipo_documento": "Packing list",
            "numero_documento": "PL-DUP",
            "fecha_emision": datos["hoy"].isoformat(),
        }
        assert cliente.post(
            f"/api/exportaciones/{exp['id_exportacion']}/documentos", headers=cab, json=cuerpo
        ).status_code == 201
        assert cliente.post(
            f"/api/exportaciones/{exp['id_exportacion']}/documentos", headers=cab, json=cuerpo
        ).status_code == 409


# --------------------------------------------------------------------------- #
# Cadena de estados · Informe §6.9                                             #
# --------------------------------------------------------------------------- #
class TestCadenaEstados:
    def test_reglas_de_transicion(self):
        # avanzar un paso
        assert puede_transicionar(
            EstadoExportacion.PEDIDO_RECIBIDO, EstadoExportacion.EN_PREPARACION
        )
        # saltar varios pasos no
        assert not puede_transicionar(
            EstadoExportacion.PEDIDO_RECIBIDO, EstadoExportacion.EN_PUERTO
        )
        # retroceder un paso sí
        assert puede_transicionar(
            EstadoExportacion.EN_PREPARACION, EstadoExportacion.PEDIDO_RECIBIDO
        )
        # anular antes de producir
        assert puede_transicionar(
            EstadoExportacion.PEDIDO_RECIBIDO, EstadoExportacion.ANULADO
        )
        # no anular tras entregar
        assert not puede_transicionar(
            EstadoExportacion.ENTREGADO, EstadoExportacion.ANULADO
        )
        # desde anulado no se sale
        assert not puede_transicionar(
            EstadoExportacion.ANULADO, EstadoExportacion.EN_PREPARACION
        )

    def test_progreso(self):
        assert progreso(EstadoExportacion.PEDIDO_RECIBIDO) == 14
        assert progreso(EstadoExportacion.ENTREGADO) == 100
        assert progreso(EstadoExportacion.ANULADO) == 0

    def test_api_rechaza_salto_de_estado(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        exp = cliente.post(
            "/api/exportaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "fecha": datos["hoy"].isoformat(),
                "detalles": [
                    {"id_lote": lote["id_lote"], "cantidad_kg": "100", "precio_kg": "7000"}
                ],
            },
        ).json()
        r = cliente.patch(
            f"/api/exportaciones/{exp['id_exportacion']}", headers=cab, json={"estado": "En puerto"}
        )
        assert r.status_code == 400
        assert "Transición no permitida" in r.json()["detail"]

    def test_avance_valido_persiste(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        exp = cliente.post(
            "/api/exportaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "fecha": datos["hoy"].isoformat(),
                "detalles": [
                    {"id_lote": lote["id_lote"], "cantidad_kg": "100", "precio_kg": "7000"}
                ],
            },
        ).json()
        r = cliente.patch(
            f"/api/exportaciones/{exp['id_exportacion']}",
            headers=cab,
            json={"estado": "En preparación"},
        )
        assert r.status_code == 200
        assert r.json()["estado"] == "En preparación"

    def test_anular_libera_inventario(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos, kg="1000")
        exp = cliente.post(
            "/api/exportaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "fecha": datos["hoy"].isoformat(),
                "detalles": [
                    {"id_lote": lote["id_lote"], "cantidad_kg": "600", "precio_kg": "7000"}
                ],
            },
        ).json()
        assert cliente.get("/api/lotes/inventario", headers=cab).json()["kilos_disponibles"] == 400
        cliente.patch(
            f"/api/exportaciones/{exp['id_exportacion']}", headers=cab, json={"estado": "Anulado"}
        )
        assert cliente.get("/api/lotes/inventario", headers=cab).json()["kilos_disponibles"] == 1000


# --------------------------------------------------------------------------- #
# Módulo de logística · HU-11, HU-12, HU-13                                    #
# --------------------------------------------------------------------------- #
class TestLogistica:
    def _exportacion(self, cliente, datos, cab, kg="1000"):
        lote = crear_lote(cliente, datos, kg=kg)
        return cliente.post(
            "/api/exportaciones",
            headers=cab,
            json={
                "id_cliente": datos["cliente"].id_cliente,
                "fecha": datos["hoy"].isoformat(),
                "puerto_origen": "Cartagena",
                "puerto_destino": "Rotterdam",
                "detalles": [
                    {"id_lote": lote["id_lote"], "cantidad_kg": kg, "precio_kg": "7000"}
                ],
            },
        ).json()

    def test_crea_envio(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        exp = self._exportacion(cliente, datos, cab)
        r = cliente.post(
            "/api/envios",
            headers=cab,
            json={
                "id_exportacion": exp["id_exportacion"],
                "transportadora": "Maersk",
                "numero_seguimiento": "MAEU-1",
                "fecha_salida": datos["hoy"].isoformat(),
                "fecha_llegada": (datos["hoy"] + timedelta(days=20)).isoformat(),
                "estado": "En tránsito",
                "puerto_origen": "Cartagena",
                "puerto_destino": "Rotterdam",
            },
        )
        assert r.status_code == 201

    def test_sincroniza_estado_de_exportacion(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        exp = self._exportacion(cliente, datos, cab)
        cliente.post(
            "/api/envios",
            headers=cab,
            json={
                "id_exportacion": exp["id_exportacion"],
                "transportadora": "Maersk",
                "numero_seguimiento": "MAEU-2",
                "fecha_salida": datos["hoy"].isoformat(),
                "estado": "En tránsito",
            },
        )
        # En tránsito lleva la exportación a «En puerto».
        assert cliente.get(
            f"/api/exportaciones/{exp['id_exportacion']}", headers=cab
        ).json()["estado"] == "En puerto"

    def test_llegada_antes_de_salida(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        exp = self._exportacion(cliente, datos, cab)
        r = cliente.post(
            "/api/envios",
            headers=cab,
            json={
                "id_exportacion": exp["id_exportacion"],
                "transportadora": "CMA CGM",
                "numero_seguimiento": "X-1",
                "fecha_salida": "2026-10-20",
                "fecha_llegada": "2026-09-01",
            },
        )
        assert r.status_code == 422

    def test_seguimiento_requiere_llegada_para_entregado(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        exp = self._exportacion(cliente, datos, cab)
        r = cliente.post(
            "/api/envios",
            headers=cab,
            json={
                "id_exportacion": exp["id_exportacion"],
                "transportadora": "CMA CGM",
                "numero_seguimiento": "X-2",
                "estado": "Entregado",
            },
        )
        assert r.status_code == 422

    def test_contenedor_sobrecargado_rechazado(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        exp = self._exportacion(cliente, datos, cab, kg="1000")
        r = cliente.post(
            "/api/envios",
            headers=cab,
            json={
                "id_exportacion": exp["id_exportacion"],
                "transportadora": "CMA CGM",
                "numero_seguimiento": "X-3",
                "id_contenedor": datos["contenedor"].id_contenedor,
                "puerto_origen": "Cartagena",
                "puerto_destino": "Rotterdam",
            },
        )
        assert r.status_code == 201, r.text  # 1000 kg caben en 26 400 kg
        # Un envío entregado no puede anularse
        cliente.patch(
            f"/api/envios/{r.json()['id_envio']}",
            headers=cab,
            json={"estado": "Entregado", "fecha_llegada": datos["hoy"].isoformat()},
        )
        assert cliente.delete(f"/api/envios/{r.json()['id_envio']}", headers=cab).status_code == 409

    def test_linea_tiempo_seis_etapas(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        exp = self._exportacion(cliente, datos, cab)
        envio = cliente.post(
            "/api/envios",
            headers=cab,
            json={
                "id_exportacion": exp["id_exportacion"],
                "transportadora": "Maersk",
                "numero_seguimiento": "MAEU-3",
                "fecha_salida": datos["hoy"].isoformat(),
                "fecha_llegada": (datos["hoy"] + timedelta(days=20)).isoformat(),
                "estado": "En tránsito",
                "puerto_origen": "Cartagena",
                "puerto_destino": "Rotterdam",
            },
        ).json()
        etapas = cliente.get(
            f"/api/envios/{envio['id_envio']}/trazabilidad", headers=cab
        ).json()
        assert [e["etapa"] for e in etapas] == [
            "Finca", "Beneficio", "Puerto origen",
            "Tránsito marítimo", "Aduana UE", "Cliente",
        ]
        assert sum(1 for e in etapas if e["estado"] == "done") >= 2
        assert sum(1 for e in etapas if e["estado"] == "current") == 1

    def test_envio_entregado_completa_la_linea(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        exp = self._exportacion(cliente, datos, cab)
        envio = cliente.post(
            "/api/envios",
            headers=cab,
            json={
                "id_exportacion": exp["id_exportacion"],
                "transportadora": "Maersk",
                "numero_seguimiento": "MAEU-4",
                "fecha_salida": datos["hoy"].isoformat(),
                "fecha_llegada": (datos["hoy"] + timedelta(days=20)).isoformat(),
                "estado": "En tránsito",
            },
        ).json()
        cliente.patch(
            f"/api/envios/{envio['id_envio']}",
            headers=cab,
            json={"estado": "Entregado", "fecha_llegada": (datos["hoy"] + timedelta(days=20)).isoformat()},
        )
        etapas = cliente.get(
            f"/api/envios/{envio['id_envio']}/trazabilidad", headers=cab
        ).json()
        assert all(e["estado"] == "done" for e in etapas)
        assert cliente.get(
            f"/api/exportaciones/{exp['id_exportacion']}", headers=cab
        ).json()["estado"] == "Entregado"


# --------------------------------------------------------------------------- #
# Panel y KPIs · HU-15                                                         #
# --------------------------------------------------------------------------- #
class TestPanel:
    def test_panel_trae_las_cuatro_tarjetas(self, cliente, datos):
        r = cliente.get("/api/panel", headers=datos["_cab"])
        assert r.status_code == 200
        cuerpo = r.json()
        assert len(cuerpo["tarjetas"]) == 4
        assert len(cuerpo["cumplimiento"]) == 3
        assert "pedidos_recientes" in cuerpo

    def test_kpis_desglosan_cafe_y_cacao(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote_cafe = crear_lote(cliente, datos, kg="1000")
        # Un lote de cacao
        r = cliente.post(
            "/api/lotes",
            headers=cab,
            json={
                "id_finca": datos["finca"].id_finca,
                "id_producto": datos["producto_cacao"].id_producto,
                "cantidad_kg": "700",
                "fecha_cosecha": datos["hoy"].isoformat(),
            },
        )
        assert r.status_code == 201
        lote_cacao = r.json()

        for lote, precio in ((lote_cafe, "7000"), (lote_cacao, "6000")):
            cliente.post(
                "/api/exportaciones",
                headers=cab,
                json={
                    "id_cliente": datos["cliente"].id_cliente,
                    "fecha": datos["hoy"].isoformat(),
                    "detalles": [
                        {
                            "id_lote": lote["id_lote"],
                            "cantidad_kg": lote["cantidad_kg"],
                            "precio_kg": precio,
                        }
                    ],
                },
            )

        kpis = cliente.get("/api/reportes/kpis", headers=cab).json()
        assert float(kpis["kilos_cafe"]) == 1000.0
        assert float(kpis["kilos_cacao"]) == 700.0
        assert float(kpis["volumen_total_kg"]) == 1700.0
        assert kpis["pedidos"] == 2
        assert kpis["por_pais"][0]["pais"] == "Países Bajos"
        assert len(kpis["por_producto"]) == 2

    def test_cumplimiento_eudr_exige_georreferenciacion(self, cliente, datos):
        cab = datos["_cab"]
        datos["_cab"] = cab
        lote = crear_lote(cliente, datos)
        cliente.post(
            "/api/certificaciones",
            headers=cab,
            json={
                "id_lote": lote["id_lote"],
                "tipo": "EUDR",
                "fecha_emision": datos["hoy"].isoformat(),
                "fecha_vencimiento": datos["manana"].isoformat(),
                "lote_georreferenciado": False,
            },
        )
        barras = {c["normativa"]: c for c in cliente.get("/api/panel", headers=cab).json()["cumplimiento"]}
        assert barras["EUDR"]["porcentaje"] == 0

        # Al georreferenciarla, sube.
        from app.models import Certificacion

        cert = cliente.get("/api/certificaciones", headers=cab).json()["items"][0]
        from app.database import SessionLocal

        with SessionLocal() as db:
            db.get(Certificacion, cert["id_certificacion"]).lote_georreferenciado = True
            db.commit()
        barras = {c["normativa"]: c for c in cliente.get("/api/panel", headers=cab).json()["cumplimiento"]}
        assert barras["EUDR"]["porcentaje"] == 100
