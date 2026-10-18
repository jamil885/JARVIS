# ADR-0001 — Go como backend principal

**Estado:** Aceptada (decisión de arquitectura, migración gradual).

## Decisión

- **Go** será el lenguaje principal del servidor JARVIS: API, orquestación de tareas,
  registro de herramientas, políticas de acceso y comunicación con nodos.
- **Python** será un componente especializado opcional para procesamiento de IA,
  audio, visión, experimentación y bibliotecas que lo requieran.
- **C++** se reservará para interfaces nativas o módulos de rendimiento justificados
  mediante mediciones. No es una dependencia del arranque inicial.
- PostgreSQL/pgvector, React/TypeScript y la estrategia híbrida local/nube permanecen.

## Consecuencias

La API FastAPI actual se mantiene temporalmente como referencia funcional.
Su eliminación queda condicionada a una implementación equivalente en Go,
con migraciones, pruebas de contrato, autorización y pruebas de integración.
No se crearán microservicios por cada módulo: preferimos un monolito modular
con interfaces explícitas. Los modelos IA nunca ejecutan herramientas directamente:
las acciones requieren validación determinista de permisos.

## Estado de este PR

Incluye solo un servidor HTTP Go mínimo con pruebas de salud y CI.
`/api/v1/health/ready` devuelve **503** de forma deliberada mientras no exista
comprobación real de PostgreSQL. No implementa aún chat, memoria ni agentes.
