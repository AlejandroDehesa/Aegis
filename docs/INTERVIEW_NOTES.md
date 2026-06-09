# Notas De Entrevista De Aegis

## Qué Es Aegis

Aegis es un proyecto backend-first de orquestación de tareas con IA construido para demostrar un flujo completo, no una respuesta aislada de chat.

La historia principal es:

- entrada estructurada de tareas
- clasificación
- selección de agente
- ejecución
- traza persistida
- feedback
- insights

Eso lo convierte en una pieza de portfolio más fuerte que un CRUD simple o una UI de chatbot.

## Cómo Explico La Arquitectura

### Backend

- FastAPI expone endpoints para auth, tasks, documents, insights, agents y health.
- Los servicios encapsulan preocupaciones de orquestación como clasificación, routing, ejecución y contexto documental.
- Los modelos SQLAlchemy persisten tareas, documentos y metadatos de ejecución.
- Los schemas Pydantic definen el contrato API y la capa de validación.

### Frontend

- React + Vite ofrece el flujo autenticado del producto.
- Las vistas principales son dashboard, tasks, task detail, documents e insights.
- Los componentes compartidos gestionan estados async, layout, feedback y render de traza.

### Flujo de datos

```txt
usuario crea tarea
  -> backend clasifica solicitud
  -> selecciona agente
  -> ejecuta tarea
  -> persiste resultado + traza
  -> usuario revisa salida
  -> usuario envía feedback
  -> insights agrega señales de calidad
```

## Por Qué No Es Solo Un CRUD

Un CRUD almacena registros. Aegis hace más que eso:

- enruta trabajo por tipo de tarea
- sigue el estado de ejecución a lo largo del tiempo
- almacena trazabilidad paso a paso
- soporta revisión ligera de calidad
- usa contexto documental para enriquecer futuras ejecuciones

Esa combinación crea una historia de flujo, no solo formularios y tablas.

## Por Qué FastAPI

- experiencia de desarrollo limpia
- velocidad alta de iteración
- buen encaje con contratos tipados request/response
- fácil de estructurar por servicios y routers
- muy adecuado para un portfolio con peso backend

## Por Qué React + Vite

- arranque rápido sin complicar el frontend
- gran velocidad de iteración para pantallas de producto
- permite centrar la UI en el flujo y no en la ceremonia del framework
- suficiente flexibilidad para páginas con estado como tareas, revisión de traza e insights

## Por Qué Cookies HttpOnly En La Sesión Web

- reducen la exposición del token de sesión a JavaScript en navegador
- encajan mejor con un modelo de auth más realista que guardar JWT en `localStorage`
- fortalecen la narrativa de seguridad del proyecto

Se mantiene compatibilidad Bearer para tests y uso manual de API, pero el flujo web es cookie-based.

## Por Qué Alembic

- los cambios de esquema deben ser explícitos y revisables
- el historial de migraciones es más razonable que DDL en runtime
- es el paso correcto para salir de atajos de demo y acercarse a higiene profesional de repositorio

## Por Qué Aún No Hay Celery

- el objetivo actual es un MVP sólido de portfolio, no una plataforma distribuida de jobs
- `BackgroundTasks` basta para demostrar transiciones de estado y trazabilidad
- meter Celery o Redis ahora mismo aumentaría la complejidad operativa más de lo que aporta a la demo

Si el proyecto evolucionara hacia una carga más cercana a producción, una cola durable sería el siguiente paso lógico.

## Por Qué El Rate Limiting Sigue Siendo In-Memory

- era suficiente para demos locales y un scope de portfolio monoinstancia
- mantiene la implementación simple y fácil de explicar
- también sirve como ejemplo honesto de limitación que revisaría antes de múltiples réplicas

## Cómo Explico RAG De Forma Honesta

- el usuario puede subir documentos
- los documentos se trocean y quedan almacenados para retrieval
- futuras tareas pueden usar ese contexto durante la ejecución

Puntos importantes de honestidad:

- esto es un flujo RAG de nivel MVP
- no se presenta como un sistema de retrieval profundamente evaluado
- no finge navegar por internet ni inventar fuentes externas

## Tradeoffs Que Tomé

- mantuve una arquitectura por capas, pero sin sobre-ingeniería
- prioricé trazabilidad y claridad del flujo sobre complejidad de agentes autónomos
- endurecí auth, configuración y documentación antes de perseguir infraestructura avanzada
- acepté rate limiting in-memory y background no durable como tradeoffs razonables de portfolio

## Qué Aprendí Construyéndolo

- `completed` no significa necesariamente `útil` si no hay quality checks
- la traza de ejecución cambia mucho la capacidad de depurar y revisar el sistema
- documentar limitaciones con honestidad fortalece el proyecto en una entrevista
- la documentación, la demo y la estrategia de tests pesan casi tanto como el código en un portfolio

## Qué Mejoraría Antes De Producción

- ejecución en background durable
- rate limiting distribuido
- observabilidad y alerting más fuertes
- cobertura E2E de navegador
- evaluación RAG y monitorización de retrieval más profundas
- validación real de despliegue con daemon/runtime disponibles

## Pitch Corto De Entrevista

> "Aegis es un proyecto backend-first de orquestación de tareas con IA. En lugar de quedarse en prompt y respuesta, muestra clasificación, enrutamiento, traza de ejecución, feedback e insights dentro de un flujo de producto real."

## Pitch Largo De Entrevista

> "Construí Aegis para demostrar cómo se ve un flujo asistido por IA cuando lo tratas como software de producto. Una persona crea una tarea estructurada, el backend la clasifica, selecciona una ruta de ejecución, persiste resultado y traza, y después la UI soporta feedback e insights. No se vende como completamente production-ready, pero sí como un proyecto endurecido lo suficiente para ser una pieza seria de portfolio."


