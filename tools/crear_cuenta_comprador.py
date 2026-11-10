"""Crea la cuenta de acceso de un cliente europeo, para las pruebas en vivo.

    python tools/crear_cuenta_comprador.py

Abre la aplicación ya levantada (uvicorn en el 8000), entra como administrador y
crea una cuenta con el rol «Cliente europeo» atada a una de las empresas
importadoras. Sirve para probar el portal a mano, no para la entrega: la cuenta
que se crea es de prueba y la contraseña se imprime en pantalla.

No siembra nada: si el servidor no está corriendo, lo dice y termina. Tampoco
borra lo que ya hay, así que se puede volver a correr sin miedo; si el correo ya
existe, reactiva la cuenta y le pone la contraseña de este script.
"""

from __future__ import annotations

import sys

import httpx

BASE = "http://localhost:8000"

ADMIN = ("andres.villavicencio@ritch.com", "RiTech2026*")

#: Correo, contraseña, empresa a la que pertenece y a nombre de quién se crea.
COMPRADOR = (
    "comprador@cafe-rotterdam.nl",
    "ClienteUE2026*",
    "Café Rotterdam BV",
    "Sanne de Vries",
)


def main() -> int:
    correo, clave, empresa, contacto = COMPRADOR

    try:
        with httpx.Client(base_url=BASE, timeout=30) as c:
            r = c.post("/api/auth/login",
                       json={"correo": ADMIN[0], "contrasena": ADMIN[1]})
            if r.status_code != 200:
                print(f"  No se pudo entrar como administrador (HTTP {r.status_code}).")
                print("  ¿Levantaste el servidor?  cd backend; uvicorn app.main:app --port 8000")
                return 1
            c.headers["Authorization"] = f"Bearer {r.json()['access_token']}"

            # La empresa tiene que existir en el catálogo de clientes.
            r = c.get("/api/clientes", params={"q": empresa})
            if r.status_code != 200 or not r.json().get("items"):
                print(f"  No se encontró la empresa «{empresa}».")
                print("  Revisa el nombre con:  curl 'localhost:8000/api/clientes'")
                return 1
            id_cliente = r.json()["items"][0]["id_cliente"]

            # Si la cuenta ya existe de una corrida anterior, se reactiva.
            r = c.get("/api/usuarios", params={"q": correo})
            existente = next(
                (u for u in r.json().get("items", []) if u["correo"] == correo), None
            )
            if existente:
                c.patch(f"/api/usuarios/{existente['id_usuario']}",
                        json={"estado": "activo", "contrasena": clave,
                              "id_cliente": id_cliente, "rol": "Cliente europeo"})
                print(f"  La cuenta ya existía; se reactivó y se le puso la contraseña.")
            else:
                r = c.post("/api/usuarios", json={
                    "nombre": contacto,
                    "correo": correo,
                    "contrasena": clave,
                    "rol": "Cliente europeo",
                    "id_cliente": id_cliente,
                })
                if r.status_code != 201:
                    print(f"  No se pudo crear la cuenta (HTTP {r.status_code}):")
                    print(f"  {r.text[:200]}")
                    return 1

            print(f"\n  Cuenta de comprador lista")
            print(f"    empresa   {empresa}")
            print(f"    correo    {correo}")
            print(f"    clave     {clave}")
            print(f"\n  Entra en {BASE}/#/login y elige el rol «Cliente europeo».")
    except httpx.ConnectError:
        print("  No hay servidor en el puerto 8000. Levántalo primero:")
        print("    cd backend")
        print("    python -m app.seed --reset")
        print("    uvicorn app.main:app --port 8000")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
