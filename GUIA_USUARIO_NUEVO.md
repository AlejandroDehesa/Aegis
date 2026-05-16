# Guia de Usuario Nuevo - Aegis

## 1) Que es Aegis (en 30 segundos)

Aegis es una plataforma para **ejecutar tareas con agentes de IA** de forma trazable.

No es un chat clasico.  
La idea central es:

1. Crear tarea
2. Clasificar y seleccionar agente
3. Ejecutar
4. Guardar resultado y traza
5. Valorar calidad
6. Revisar insights

---

## 2) Primer acceso

### Opcion A: usuario demo

- Email: `demo@aegis.local`
- Password: `Demo12345!`

### Opcion B: crear cuenta nueva

1. En la pantalla de login, pulsa `Register`.
2. Escribe email y password.
3. Pulsa `Create account`.
4. Entraras automaticamente.

---

## 3) Selector de idioma (Espanol / English)

Tienes selector de idioma en 2 sitios:

1. Pantalla de auth (antes de entrar).
2. Sidebar dentro de la app (una vez logueado).

El idioma queda guardado en tu navegador.

---

## 4) Mapa rapido de la web

Las secciones principales son:

1. `Dashboard` (`/`)
2. `Tasks` (`/tasks`)
3. `Task Detail` (`/tasks/:taskId`)
4. `Documents` (`/documents`)
5. `Agents` (`/agents`)
6. `Insights` (`/insights`)

---

## 5) Flujo de trabajo recomendado (usuario nuevo)

## Paso 1: entrar

1. Abre `http://localhost:5173`.
2. Login o Register.
3. Verifica que ves sidebar y menu.

## Paso 2: crear una tarea

1. Ve a `Tasks`.
2. En `Create Task`, completa:
   - `Title`
   - `Description`
3. Pulsa `Create task`.

Consejo: puedes usar el boton de plantilla demo.

## Paso 3: ejecutar la tarea

1. En la lista de tareas, pulsa `Execute`.
2. Veras estados:
   - `pending`
   - `processing`
   - `completed` o `failed`
3. La lista se refresca automaticamente mientras corre.

## Paso 4: revisar detalle y traza

1. Pulsa `Open detail`.
2. En `Task Detail` revisa:
   - metadatos de ejecucion
   - resultado final
   - execution trace (paso a paso)
   - contexto debug (si aplica)

## Paso 5: valorar calidad del resultado

1. En `Result Evaluation`, elige rating 1-5.
2. Escribe comentario opcional.
3. Pulsa `Save evaluation`.

Esto cierra el loop de calidad de producto.

## Paso 6: usar documentos para enriquecer contexto

1. Ve a `Documents`.
2. Sube texto o archivo (`.txt`, `.md`, `.csv`, `.json`).
3. Vuelve a `Tasks` y ejecuta una tarea de nuevo.
4. Compara resultado y traza.

## Paso 7: revisar calidad operativa

1. Ve a `Insights`.
2. Mira:
   - metricas globales por usuario
   - distribuciones (estado, tipo, agente, rating)
   - quality queue (fallidas o mal valoradas)
   - strong results (bien valoradas)

---

## 6) Como entender cada vista

## Dashboard

Sirve para orientarte rapido:

1. KPIs de tareas/documentos/agentes/ratings
2. Demo flow guiado
3. Tareas recientes

## Tasks

Es tu centro operativo diario:

1. Crear tareas
2. Filtrar tareas por status/task_type/agent/rating
3. Ejecutar rapido
4. Entrar al detalle

## Task Detail

Es la vista de validacion de calidad:

1. Estado y tiempos
2. Resultado consolidado
3. Traza de ejecucion por pasos
4. Evaluacion de salida (rating + comentario)

## Documents

Es la capa de contexto:

1. Ingesta de informacion
2. Biblioteca documental
3. Soporte para flujo RAG

## Agents

Catalogo de capacidades disponibles:

1. Nombre del agente
2. Descripcion
3. Tipos de tarea soportados

## Insights

Vista de control de calidad:

1. Total de tareas
2. Fallos y low-rated
3. Distribuciones operativas
4. Cola de revision prioritaria

---

## 7) Estados y mensajes que veras

Estados tipicos en UI:

1. `loading`
2. `empty`
3. `error`
4. `success`

Estados de tarea:

1. `pending`
2. `processing`
3. `completed`
4. `failed`

---

## 8) Flujo diario sugerido (practico)

1. Entra a Dashboard para contexto general.
2. Crea 1-2 tareas en Tasks.
3. Ejecuta y abre detalle.
4. Valora cada salida.
5. Sube 1 documento y repite ejecucion.
6. Cierra en Insights para detectar mejoras.

Este flujo te da una rutina clara de uso real.

---

## 9) Checklist de demo (5-7 min)

1. Login
2. Crear tarea
3. Ejecutar
4. Abrir detalle y traza
5. Valorar resultado
6. Subir documento
7. Re-ejecutar tarea
8. Mostrar Insights

---

## 10) Problemas comunes y solucion rapida

## No puedo entrar

1. Revisa email/password.
2. Prueba usuario demo.
3. Si no va, reinicia stack:
   - `docker compose up --build -d`

## No veo cambios en frontend

1. Recarga fuerte (`Ctrl + F5`).
2. Reconstruye frontend:
   - `docker compose up --build -d frontend`

## La tarea tarda en cambiar de estado

1. Espera unos segundos (polling activo).
2. Pulsa `Refresh` en Tasks.
3. Revisa salud backend:
   - `http://localhost:8000/api/v1/health`

---

## 11) Buenas practicas de uso

1. Escribe titulos de tarea claros.
2. Incluye contexto suficiente en descripcion.
3. Usa feedback siempre despues de ejecutar.
4. Usa Documents para casos con contexto externo.
5. Revisa Insights para priorizar mejoras.

---

## 12) Resumen final

Si eres nuevo, piensa Aegis como un flujo:

`Task -> Execute -> Detail/Trace -> Feedback -> Insights -> Improve`

Con eso ya puedes usar la plataforma de punta a punta con criterio profesional.
