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

## Incremento: sesiones y mensajes persistentes (PR de desarrollo)

Este incremento agrega rutas para crear/consultar sesiones y añadir/listar mensajes humanos.
**Todavía no genera respuestas mediante un LLM** y su token compartido es solo para
desarrollo local de un único usuario. No exponerlo a Internet.

Desde la raíz del repositorio en Ubuntu:

```bash
cd infrastructure
cp -n .env.example .env
# Ajustar JARVIS_DB_PASSWORD en infrastructure/.env
docker compose up -d
cd ..
docker compose -f infrastructure/compose.yaml exec -T postgres psql -U jarvis -d jarvis < infrastructure/migrations/0001_sessions_messages.sql
cd services/api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
export JARVIS_DATABASE_URL='postgresql://jarvis:TU_CLAVE@127.0.0.1:5432/jarvis'
export JARVIS_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn jarvis_api.main:app --host 127.0.0.1 --port 8000
```

En otra terminal, usando **el mismo token** (no imprimirlo en logs):

```bash
export JARVIS_API_TOKEN='PEGA_AQUI_EL_TOKEN_DE_LA_PRIMERA_TERMINAL'
curl -sS -X POST http://127.0.0.1:8000/api/v1/sessions \
  -H "Authorization: Bearer $JARVIS_API_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Primera conversación"}'
```

La respuesta contiene el `id` de sesión. Para añadir un mensaje, sustituye
`SESSION_UUID` por ese ID y genera `client_message_id` con `python -c 'import uuid; print(uuid.uuid4())'`:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/sessions/SESSION_UUID/messages \
  -H "Authorization: Bearer $JARVIS_API_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"client_message_id":"MESSAGE_UUID","content":"Hola JARVIS"}'
curl -sS -H "Authorization: Bearer $JARVIS_API_TOKEN" \
  http://127.0.0.1:8000/api/v1/sessions/SESSION_UUID/messages
```

Los reintentos con el mismo `client_message_id` y contenido devuelven el mensaje existente.
Reutilizarlo con contenido distinto produce 409. Este primer esquema no maneja aún
propietarios, usuarios múltiples, roles avanzados ni límites de recursos completos.
