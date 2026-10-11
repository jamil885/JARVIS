# J.A.R.V.I.S. — Sprint 0 starter (pre-MVP)

Este repositorio es un **andamiaje ejecutable**, NO una versión funcional completa de JARVIS.
Basado en JARVIS-SRS v1.0, SAD, SEC, DATA y API v1.0. Cumple parcialmente la preparación del Sprint 0.

## Incluye
- API FastAPI con `GET /api/v1/health/live`, `GET /api/v1/health/ready`.
- Contrato de errores JSON, `X-Request-ID`, OpenAPI autogenerado.
- Ejemplo aislado de evaluación **deny-by-default** (no es un Policy Engine completo).
- PostgreSQL + pgvector mediante Docker Compose, accesible solo en localhost.
- Pruebas automatizadas y flujo CI de ejemplo.

## Requisitos
Windows 11 + WSL2 Ubuntu (recomendado), Python 3.11+ y Docker compatible con WSL2.

## Instalación local en Ubuntu/WSL2
```bash
cd infrastructure
cp .env.example .env
# EDITAR .env: establecer contraseña aleatoria fuerte
# El archivo .env es local y está excluido de Git.
docker compose up -d
cd ../services/api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Definir la variable de conexión para la misma contraseña de infraestructura:
```bash
export JARVIS_DATABASE_URL='postgresql://jarvis:TU_CLAVE@127.0.0.1:5432/jarvis'
uvicorn jarvis_api.main:app --host 127.0.0.1 --port 8000
```
> Si la contraseña tiene caracteres especiales, hay que codificarlos para la URL o usar otro mecanismo de configuración seguro. No compartas contraseñas ni las guardes en capturas de pantalla.

En otra terminal:
```bash
curl http://127.0.0.1:8000/api/v1/health/live
curl http://127.0.0.1:8000/api/v1/health/ready
```
Consultar OpenAPI: http://127.0.0.1:8000/docs

## Pruebas
```bash
cd services/api
python -m pytest -q
python -m ruff check jarvis_api tests
```

## Seguridad / limitaciones
- SOLO entorno de desarrollo en localhost. NO desplegar públicamente: todavía no existe autenticación de usuario, rate limiting, permisos persistentes, migraciones ni TLS.
- `ready` comprueba conexión SQL; **no** equivale a validación de todo el ecosistema.
- No implementa chat, agentes, memoria, comandos de Windows ni IoT.
- El ejemplo `policy.evaluate` no es aún el control obligatorio integrado en un Tool Gateway.
- Antes de exponer rutas protegidas, implementar identidad, autorizaciones, pruebas negativas y auditoría según JARVIS-SEC.

## Próximo incremento
Diseñar migración SQL (`users`, `sessions`, `messages`, `audit_events`), autenticación local, rutas `/sessions`, adaptador `MockModelProvider`, mensajes persistentes, pruebas de reinicio y streaming.
