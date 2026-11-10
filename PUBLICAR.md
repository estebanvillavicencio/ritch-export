# Publicar la aplicación en un enlace que no se caiga

El enlace que se estaba usando sale de un **túnel temporal de Cloudflare**: Cloudflare
lo prestaba sin cuenta y sin garantía de disponibilidad, por diseño. Cuando la
computadora se apaga, se reinicia o se corta la red, ese enlace deja de existir y
no hay forma de recuperarlo. No es un error del proyecto: es que ese servicio no
sirve para dejar algo publicado.

Para tener un enlace de verdad hay que **alojar la aplicación en algún servicio**,
y eso significa abrir una cuenta. Eso no lo puede hacer nadie por vos, porque
hace falta tu usuario, tu correo y tu contraseña. Lo que sí está todo listo para
que sean unos minutos.

El proyecto quedó preparado con todo lo que el servicio necesita:

| Archivo | Para qué |
|---|---|
| `requirements.txt` (raíz) | Lo que el servicio instala |
| `render.yaml` | La configuración del servicio, en un solo archivo |
| `Procfile` | Para servicios tipo Railway o Heroku |
| `runtime.txt` | La versión de Python |
| `wsgi.py` | Para servicios que usan WSGI, como PythonAnywhere |
| `.gitignore` | Para que no se suban la base de datos ni los secretos |

---

## Opción 1 · Render (recomendada, con git)

Es la que menos pasos tiene. Necesitás una cuenta de GitHub (que ya tenés, con
GitHub Desktop) y una de Render.

**1. Publicar el código en GitHub**

El repositorio todavía no existe. Desde GitHub Desktop: *File → Add local
repository*, apuntá a la carpeta `ritch-export`, y después *Publish repository*.
Dejalo privado o público, da igual para esto.

Si preferís la línea de comandos:

```powershell
cd "C:\Users\esteb\OneDrive\Documentos\Proyecto predeterminado\ritch-export"
git init
git add -A
git commit -m "RiTech SAS · Sprint 2"
git remote add origin https://github.com/TU_USUARIO/ritch-export.git
git push -u origin main
```

**2. Crear el servicio**

1. Entrá a [render.com](https://render.com) y creá la cuenta con GitHub.
2. *New → Blueprint*, elegí el repositorio.
3. Render lee `render.yaml` solo y arma el servicio con los valores de ahí.
4. Le das *Apply* y en dos o tres minutos te da una dirección tipo
   `https://ritch-export.onrender.com`.

Eso es todo. No hay que configurar variables a mano: la clave de las sesiones se
genera sola.

**Lo que hay que saber antes**

- **El plan gratis apaga el servicio a los 15 minutos sin visitas.** Cuando alguien
  entre, tarda medio minuto en volver a arrancar. Para un trabajo que se abre un
  rato está bien; para un enlace que se mande a un profesor con días de diferencia,
  no.
- **El disco es temporal.** La base de datos se borra en cada reinicio. Por eso la
  aplicación ahora **siembra los datos de ejemplo sola cuando encuentra la base
  vacía** (`backend/app/sembrar_si_esta_vacia.py`): se abre, tiene lotes, clientes
  y cuentas, y sirve para la demostración. Lo que alguien cargue a mano después se
  pierde en el reinicio siguiente.
- **La clave de las sesiones no está en el repositorio**, se genera en Render. Con
  esto nadie puede fabricar un token por conocer el código.

---

## Opción 2 · PythonAnywhere (si no querés usar git)

Necesitás una cuenta en [pythonanywhere.com](https://pythonanywhere.com) y el plan
gratis. Tiene la ventaja de que **el disco no es temporal**: la base de datos se
queda.

**1. Subir el proyecto**

En la pestaña *Files*, subí la carpeta `ritch-export` (se puede comprimir en un
zip y subirlo entero, que es más rápido).

**2. Crear la aplicación web**

1. Pestaña *Web*, *Add a domain manual*.
2. Framework: **Flask**, porque ahí es donde se apunta el archivo WSGI.
3. Ruta al código: `/home/TU_USUARIO/ritch-export/wsgi.py`
4. Variable de aplicación: `application`

**3. Consola**

```bash
cd ~/ritch-export
python3 -m venv ~/venvs/ritch && ~/venvs/ritch/bin/activate
pip install -r requirements.txt
python -c "import sys; sys.path.insert(0,'backend'); from app.seed import sembrar; from app.database import SessionLocal; init_db(); db=SessionLocal(); sembrar(db, reset=False)"
```

**4. Configuración**

En *Configuration files*, en el archivo de la aplicación, poner:

```
RITECH_JWT_SECRET = <una cadena larga y aleatoria>
RITECH_DB_URL = sqlite:////home/TU_USUARIO/ritch-export/ritch_dev.db
```

Para inventar la clave: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

---

## Antes de publicarlo: dos cosas que importan

**1. Las cuentas de demostración usan contraseñas aleatorias en Render.** La
pantalla pública no muestra accesos rápidos. Render genera por separado
`RITECH_DEMO_PASSWORD` y `RITECH_BUYER_PASSWORD`; consúltalas en el panel del
servicio si necesitas iniciar sesión. Mantén el repositorio de GitHub privado para
que las credenciales locales y los documentos del proyecto no queden expuestos.

**2. Si usás PostgreSQL de verdad, cambiá `RITECH_DB_URL`.** El requisito RR-003
pide PostgreSQL, y con el plan gratis de Render eso no está disponible. Se
consigue gratis en varios servicios (Neon, Supabase, Aiven) y ahí la variable
queda así:

```
RITECH_DB_URL = postgresql+psycopg://usuario:clave@host:5432/ritch
```

Con PostgreSQL los datos sí sobreviven a los reinicios, y el proyecto queda como lo
pide el informe. Es el paso que más vale la pena.

---

## Y para presentar en el salón

Nada de esto hace falta. En la computadora:

```
http://localhost:8000
```

No depende de internet, no cambia nunca y arranca al instante. Para la
demostración en clase, esa es la dirección. El enlace de internet sirve para
mandárselo a alguien que esté en otro lado.
