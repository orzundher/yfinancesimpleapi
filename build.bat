@echo off
echo ====================================
echo   YFinance API - Docker Compose
echo ====================================
echo.

echo Deteniendo contenedores existentes...
docker compose down

echo.
echo Construyendo y levantando servicios...
docker compose up --build -d

echo.
echo ====================================
echo   Servicios iniciados correctamente
echo ====================================
echo.
echo API disponible en: http://localhost:3010
echo Documentacion: http://localhost:3010/docs
echo.
echo Comandos utiles:
echo   docker compose logs -f       - Ver logs en tiempo real
echo   docker compose stop          - Detener servicios
echo   docker compose down          - Detener y eliminar contenedores
echo   docker compose restart       - Reiniciar servicios
echo.

pause
