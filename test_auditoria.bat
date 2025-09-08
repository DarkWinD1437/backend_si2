@echo off
echo ========================================
echo PRUEBAS DE AUDITORIA BASICA
echo ========================================
echo.

echo 1. Probando LOGIN EXITOSO...
curl -X POST http://127.0.0.1:8000/api/token/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@example.com\",\"password\":\"admin123\"}" ^
  --silent --show-error > token_response.json

echo.
echo Respuesta guardada en token_response.json
type token_response.json
echo.

echo 2. Probando LOGIN FALLIDO...
curl -X POST http://127.0.0.1:8000/api/token/ ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@example.com\",\"password\":\"password_incorrecto\"}" ^
  --silent --show-error

echo.
echo.
echo 3. Extrayendo token para siguiente solicitud...
for /f "tokens=2 delims=:" %%a in ('findstr "access" token_response.json') do (
    set "token_part=%%a"
)
set "token=%token_part:~2,-2%"
echo Token extraido: %token:~0,50%...

echo.
echo 4. Consultando logs de auditoria...
curl -X GET http://127.0.0.1:8000/api/auditoria/logs/ ^
  -H "Authorization: Bearer %token%" ^
  --silent --show-error

echo.
echo.
echo ========================================
echo PRUEBAS COMPLETADAS
echo ========================================
echo.
echo Para ver los logs de auditoria en el admin:
echo http://127.0.0.1:8000/admin/auditoria/auditorialog/
echo Usuario: admin@example.com
echo Password: admin123
echo.
pause
