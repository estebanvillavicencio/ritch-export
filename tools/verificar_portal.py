"""Comprueba en el servidor real que un cliente ve lo suyo y nada más.

    python tools/verificar_portal.py

Las pruebas de `backend/tests/` ya cubren el portal, pero corren contra una base
de datos de pruebas con dos empresas y un pedido cada una. Esta hace lo mismo
contra la base de desarrollo, que tiene los datos de ejemplo reales, y además
entra por la API como lo haría el navegador.

Sale con código 1 si algo se rompe, para poder pegarlo en un paso de compilación.
"""

from __future__ import annotations

import sys

import httpx

BASE = "http://localhost:8000"
ADMIN = ("andres.villavicencio@ritch.com", "RiTech2026*")
COMPRADOR = ("comprador@cafe-rotterdam.nl", "ClienteUE2026*")

falla = 0


def revisar(etiqueta: str, condicion: bool, detalle: str = "") -> None:
    global falla
    if not condicion:
        falla += 1
    marca = "ok  " if condicion else "FALLA"
    sufijo = f"   {detalle}" if detalle else ""
    print(f"    {marca} {etiqueta}{sufijo}")


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=30) as c:
        # El administrador, para tener la foto completa de qué hay en la base.
        r = c.post("/api/auth/login",
                   json={"correo": ADMIN[0], "contrasena": ADMIN[1]})
        if r.status_code != 200:
            print("  No se pudo entrar como administrador. ¿Está el servidor?")
            return 1
        c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"

        total_export = c.get("/api/exportaciones", params={"tamano": 100}).json()["total"]
        total_envios = c.get("/api/envios", params={"tamano": 100}).json()["total"]
        print(f"\n  La base de desarrollo tiene {total_export} exportaciones "
              f"y {total_envios} envíos, de varias empresas.\n")

        # El comprador entra por su cuenta.
        c2 = httpx.Client(base_url=BASE, timeout=30)
        r = c2.post("/api/auth/login",
                    json={"correo": COMPRADOR[0], "contrasena": COMPRADOR[1]})
        if r.status_code != 200:
            print("  No se pudo entrar como comprador. Crea la cuenta con:")
            print("    python tools/crear_cuenta_comprador.py")
            return 1
        sesion = r.json()
        c2.headers["Authorization"] = f"Bearer {sesion['access_token']}"
        usuario = sesion["usuario"]
        print(f"  Entró {usuario['nombre']} · rol {usuario['rol']} · "
              f"empresa {usuario.get('nombre_cliente')}\n")

        print("  Lo que sí puede ver:")
        r = c2.get("/api/exportaciones", params={"tamano": 100})
        propias = r.json()
        revisar("sus exportaciones", r.status_code == 200,
                f"HTTP {r.status_code} · {propias['total']} de {total_export}")
        # `cliente` viene anidado como objeto, así que se compara por nombre.
        empresas = {
            (x.get("cliente") or {}).get("nombre_empresa")
            for x in propias.get("items", [])
        }
        empresas.discard(None)
        revisar("solo de su empresa", len(empresas) <= 1,
                f"empresas: {sorted(empresas)}")

        r = c2.get("/api/envios", params={"tamano": 100})
        revisar("sus envíos", r.status_code == 200,
                f"HTTP {r.status_code} · {r.json().get('total')} de {total_envios}")

        r = c2.get("/api/productos")
        revisar("el catálogo", r.status_code == 200, f"HTTP {r.status_code}")

        print("\n  Lo que no puede ver:")
        for etiqueta, ruta in [
            ("el panel general", "/api/panel"),
            ("los indicadores de la empresa", "/api/reportes/kpis"),
            ("las cotizaciones de otros", "/api/cotizaciones"),
            ("la lista de clientes", "/api/clientes"),
            ("los lotes", "/api/lotes"),
        ]:
            r = c2.get(ruta)
            revisar(f"no accede a {etiqueta}", r.status_code in (403, 404),
                    f"HTTP {r.status_code}")

        # Y que no pueda escribir nada.
        r = c2.post("/api/envios", json={"id_exportacion": 1, "transportadora": "X",
                                         "numero_seguimiento": "HACK-1"})
        revisar("no crea envíos", r.status_code in (403, 404), f"HTTP {r.status_code}")
        r = c2.post("/api/usuarios", json={"nombre": "Intruso", "correo": "i@x.com",
                                            "contrasena": "ClavePortal2026*",
                                            "rol": "Administrador"})
        revisar("no crea usuarios", r.status_code in (403, 404), f"HTTP {r.status_code}")

    print()
    if falla:
        print(f"  {falla} comprobación(es) fallaron.")
        return 1
    print("  El portal se comporta como debe: el comprador ve lo suyo y nada más.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
