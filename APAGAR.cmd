@echo off
REM ===================================================================
REM  RiTech SAS - APAGAR
REM
REM  Doble clic para cerrar la aplicacion y liberar el puerto 8000.
REM ===================================================================

REM Las pausas usan `ping` y no `timeout`: `timeout` falla cuando la
REM entrada estandar esta redirigida y deja un error en pantalla.

setlocal
cd /d "%~dp0"

set "PYTHON="
where python >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON (
    if exist "C:\Users\esteb\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
        set "PYTHON=C:\Users\esteb\AppData\Local\Python\pythoncore-3.14-64\python.exe"
    )
)

echo.
echo   RiTech SAS - Apagando...

rem --- El vigilante, si esta corriendo ------------------------------------
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*vigilante.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" 2>nul

rem --- El tunel, si esta corriendo -----------------------------------------
taskkill /IM cloudflared.exe /F >nul 2>&1

rem --- La aplicacion -------------------------------------------------------
if defined PYTHON "%PYTHON%" tools\bajar.py >nul 2>&1

powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if %errorlevel%==0 (
    echo   [aviso] Algo sigue escuchando en el puerto 8000.
) else (
    echo   Todo apagado. El puerto 8000 quedo libre.
)
echo.
ping -n 4 127.0.0.1 >nul
endlocal
