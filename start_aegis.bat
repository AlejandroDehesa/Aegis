@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

if /I "%~1"=="--help" goto :help
if /I "%~1"=="/?" goto :help

echo [Aegis] Preparando arranque...

where docker >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker no esta instalado o no esta en PATH.
  exit /b 1
)

docker compose version >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Docker Compose no esta disponible.
  exit /b 1
)

call :ensure_docker_daemon
if errorlevel 1 (
  exit /b 1
)

if not exist ".env" (
  if exist ".env.example" (
    copy /Y ".env.example" ".env" >nul
    echo [Aegis] .env local creado desde .env.example
  ) else (
    echo [ERROR] Falta .env y .env.example
    exit /b 1
  )
)

if not exist "frontend\.env" (
  if exist "frontend\.env.example" (
    copy /Y "frontend\.env.example" "frontend\.env" >nul
    echo [Aegis] frontend\.env creado desde frontend\.env.example
  ) else (
    echo [ERROR] Falta frontend\.env y frontend\.env.example
    exit /b 1
  )
)

echo [Aegis] Levantando servicios (db, backend, frontend)...
docker compose --env-file .env up --build -d
if errorlevel 1 (
  echo [WARN] Primer intento de docker compose fallo. Reintentando con --remove-orphans...
  docker compose --env-file .env up --build -d --remove-orphans
  if errorlevel 1 (
    echo [WARN] Compose devolvio error otra vez. Verificando disponibilidad real de servicios...
  )
)

if /I "%~1"=="--seed" (
  echo [Aegis] Cargando datos demo...
  docker compose --env-file .env run --rm backend python -m scripts.seed_demo_data
  if errorlevel 1 (
    echo [WARN] No se pudo cargar seed demo. El sistema sigue levantado.
  )
)

set "SERVICES_OK=1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$url='http://localhost:8000/api/v1/health'; $ok=$false; for($i=1;$i -le 45;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 4; if($r.StatusCode -ge 200 -and $r.StatusCode -lt 500){ $ok=$true; break } } catch {}; Start-Sleep -Seconds 2 }; if($ok){ exit 0 } else { exit 1 }" >nul 2>nul
if errorlevel 1 (
  echo [WARN] Backend health no respondio a tiempo: http://localhost:8000/api/v1/health
  set "SERVICES_OK=0"
) else (
  echo [Aegis] Backend health OK.
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$url='http://localhost:5173'; $ok=$false; for($i=1;$i -le 45;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 4; if($r.StatusCode -ge 200 -and $r.StatusCode -lt 500){ $ok=$true; break } } catch {}; Start-Sleep -Seconds 2 }; if($ok){ exit 0 } else { exit 1 }" >nul 2>nul
if errorlevel 1 (
  echo [WARN] Frontend no respondio a tiempo: http://localhost:5173
  set "SERVICES_OK=0"
) else (
  echo [Aegis] Frontend OK.
)

if /I not "%SERVICES_OK%"=="1" (
  echo [ERROR] Los servicios no quedaron listos a tiempo.
  echo         Revisa estado con: docker compose --env-file .env ps
  echo         Revisa logs con:   docker compose --env-file .env logs --no-color --tail 100
  exit /b 1
)

echo.
echo [Aegis] Listo para demo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo Health:   http://localhost:8000/api/v1/health
echo.
setlocal DisableDelayedExpansion
echo Credenciales demo (si usaste --seed):
echo   email: demo@aegis.local
echo   pass:  Demo12345!
endlocal
echo.

start "" "http://localhost:5173"
exit /b 0

:ensure_docker_daemon
set "DOCKER_CHECK_LOG=%TEMP%\aegis_docker_check_%RANDOM%.log"
docker info >"%DOCKER_CHECK_LOG%" 2>&1
if not errorlevel 1 (
  del /q "%DOCKER_CHECK_LOG%" >nul 2>nul
  echo [Aegis] Docker daemon OK.
  exit /b 0
)

findstr /I /C:"must be run with elevated privileges" /C:"open //./pipe/docker_engine" /C:"Acceso denegado" "%DOCKER_CHECK_LOG%" >nul
if not errorlevel 1 (
  del /q "%DOCKER_CHECK_LOG%" >nul 2>nul
  echo [ERROR] Docker esta instalado, pero Windows denego acceso al daemon.
  echo         Solucion habitual:
  echo         1^) Abre PowerShell como Administrador y ejecuta de nuevo este .bat
  echo         2^) Agrega tu usuario al grupo docker-users:
  echo            net localgroup docker-users %%USERNAME%% /add
  echo         3^) Cierra sesion o reinicia Windows para aplicar cambios
  exit /b 1
)

findstr /I /C:".docker\config.json" /C:"Error loading config file" "%DOCKER_CHECK_LOG%" >nul
if not errorlevel 1 (
  del /q "%DOCKER_CHECK_LOG%" >nul 2>nul
  echo [ERROR] Docker no puede leer C:\Users\%%USERNAME%%\.docker\config.json por permisos.
  echo         Abre PowerShell como Administrador y corrige permisos de esa carpeta.
  echo         Luego reintenta este script.
  exit /b 1
)

del /q "%DOCKER_CHECK_LOG%" >nul 2>nul
echo [Aegis] Docker daemon no responde. Intentando iniciar Docker Desktop...
if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
  start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
) else (
  echo [WARN] No se encontro Docker Desktop.exe en la ruta esperada.
)

set /a DTRY=1
set /a DMAX=45

:wait_docker
docker info --format "{{.ServerVersion}}" >nul 2>nul
if not errorlevel 1 (
  echo [Aegis] Docker daemon listo.
  exit /b 0
)

if !DTRY! GEQ !DMAX! (
  echo [ERROR] Docker daemon sigue no disponible.
  echo         Abre Docker Desktop manualmente y espera que diga "Engine running".
  echo         Luego vuelve a ejecutar este script.
  exit /b 1
)

echo [Aegis] Esperando Docker daemon... intento !DTRY!/!DMAX!
set /a DTRY+=1
timeout /t 2 /nobreak >nul
goto :wait_docker

:help
echo.
echo Uso:
echo   start_aegis.bat
echo   start_aegis.bat --seed
echo.
echo Opciones:
echo   --seed   Ejecuta seed demo despues de levantar contenedores.
echo.
exit /b 0
