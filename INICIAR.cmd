@echo off
REM ===================================================================
REM  RiTech SAS - INICIAR
REM
REM  Doble clic en este archivo para levantar la aplicacion y abrirla
REM  en el navegador. Se puede usar todas las veces que haga falta.
REM
REM  La direccion que se abre es http://localhost:8000, que es la unica
REM  que no depende de internet ni de un enlace temporal. Los enlaces de
REM  trycloudflare.com caducan solos: no sirven para presentar ni para
REM  compartir, porque dejan de existir en cuanto se apaga la maquina.
REM ===================================================================

REM Las pausas usan `ping` y no `timeout`: `timeout` falla cuando la
REM entrada estandar esta redirigida y deja un error en pantalla.

setlocal
cd /d "%~dp0"

echo.
echo   RiTech SAS - Levantando la aplicacion...
echo.

rem --- Se busca un Python que funcione ------------------------------------
set "PYTHON="
where python >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON (
    if exist "C:\Users\esteb\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
        set "PYTHON=C:\Users\esteb\AppData\Local\Python\pythoncore-3.14-64\python.exe"
    )
)
if not defined PYTHON (
    echo   [ERROR] No se encontro Python en este equipo.
    echo.
    echo   Se puede instalar desde https://www.python.org/downloads/
    echo   Marcando "Add python.exe to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

rem --- Se comprueba si ya esta encendida ----------------------------------
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if %errorlevel%==0 (
    echo   Ya estaba encendida. Abriendo el navegador...
    start "" "http://localhost:8000/#/login"
    echo.
    echo   Para cerrar la aplicacion: doble clic en APAGAR.cmd
    echo.
    ping -n 5 127.0.0.1 >nul
    exit /b 0
)

rem --- Se siembran los datos y se levanta en segundo plano -----------------
echo   Cargando datos de ejemplo...
pushd backend
"%PYTHON%" -m app.seed --reset >nul 2>&1
popd

echo   Encendiendo la aplicacion...
powershell -NoProfile -Command "Start-Process -FilePath '%PYTHON%' -ArgumentList '-m','uvicorn','app.main:app','--port','8000' -WorkingDirectory '%~dp0backend' -WindowStyle Minimized"

echo   Esperando a que responda...
set /a INTENTOS=0
:esperar
ping -n 3 127.0.0.1 >nul
set /a INTENTOS+=1
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if %errorlevel%==0 goto listo
if %INTENTOS% lss 20 goto esperar

echo.
echo   [ERROR] La aplicacion no arranco.
echo.
echo   Para ver que paso, abrila a mano desde una terminal:
echo     cd "%~dp0backend"
echo     %PYTHON% -m uvicorn app.main:app --port 8000
echo.
pause
exit /b 1

:listo
echo   Listo. Abriendo el navegador...
start "" "http://localhost:8000/#/login"
echo.
echo   ------------------------------------------------------------
echo   Administrador   andres.villavicencio@ritch.com   RiTech2026*
echo   Administrador   juan.iguia@ritch.com             RiTech2026*
echo   Comercial       juan.araujo@ritch.com             RiTech2026*
echo   Logistica       dario.paz@ritch.com               RiTech2026*
echo   Cliente UE      comprador@cafe-rotterdam.nl       ClienteUE2026*
echo   ------------------------------------------------------------
echo.
echo   Para cerrar la aplicacion: doble clic en APAGAR.cmd
echo.
ping -n 9 127.0.0.1 >nul
endlocal
