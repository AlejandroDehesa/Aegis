# Guion De Demo De Aegis (3-5 min)

Objetivo: enseñar Aegis como un flujo trazable de ejecución de tareas, no como una simple respuesta de chat.

## Antes De Empezar

Comprobaciones rápidas:

- `docker compose ps` muestra servicios saludables
- frontend disponible en `http://localhost:5173`
- backend health disponible en `http://localhost:8000/api/v1/health`
- usuario demo preparado:
  - email: `demo@aegis.local`
  - password: `Demo12345!`

Frase sugerida de apertura:

> "Aegis es una demo backend-first de orquestación de tareas con IA. La idea no es solo generar texto, sino enseñar un flujo completo con trazabilidad, persistencia y revisión."

## 1. Login (20-30s)

Abre `http://localhost:5173/login` e inicia sesión.

Qué decir:

- "La sesión web usa un flujo de autenticación propio de producto, así que puedo moverme por tareas, documentos e Insights como usuario autenticado."

Qué enseñar:

- pantalla de login
- credenciales demo opcionales
- transición al shell principal de la app

## 2. Dashboard (20-30s)

Aterriza en el dashboard y fija el contexto.

Qué decir:

- "Esta vista me da el recorrido principal de la demo: tareas, ejecución, revisión, contexto documental e Insights."

Qué enseñar:

- tarjetas de métricas
- tareas recientes
- flujo recomendado de navegación

## 3. Crear Una Tarea (40-60s)

Ve a `Tareas` y crea una solicitud realista.

Ejemplo recomendado:

- título: `Comparar FastAPI y Django para una plataforma interna de IA`
- descripción: `Haz una comparativa práctica para un producto de orquestación con IA: arquitectura, mantenibilidad, rendimiento y velocidad de implementación. Termina con una recomendación.`

Qué decir:

- "Aquí parto de una tarea estructurada, no de un prompt genérico. Eso le da al backend contexto suficiente para clasificar, enrutar y persistir el flujo."

## 4. Ejecutar La Tarea (40-60s)

Lanza la tarea desde la lista o desde el detalle.

Qué enseñar:

- cambio de estado
- control rápido de ejecución
- refresco automático mientras la tarea está en cola o procesando

Qué decir:

- "Lo importante aquí no es solo la respuesta final. El sistema sigue el estado de ejecución y deja la corrida lista para revisión."

## 5. Abrir El Detalle Y La Traza (60-90s)

Abre el detalle de una tarea completada.

Qué enseñar:

- resumen de tarea
- resultado final
- execution trace
- bloque de evaluación

Qué remarcar:

- `task_type`
- `agent_name`
- timestamps y duración
- pasos de traza como clasificación, selección y ejecución

Frase sugerida:

> "Aquí es donde Aegis deja de ser una simple demo de texto. Puedo inspeccionar qué ocurrió durante la ejecución, no solo lo que devolvió el modelo."

## 6. Enviar Feedback (20-30s)

Valora la salida y, si quieres, añade un comentario corto.

Qué decir:

- "La valoración es ligera a propósito, pero genera una señal de calidad que luego puedo agregar en Insights."

## 7. Enseñar Documentos / Contexto De Recuperación (30-45s)

Abre `Documentos`.

Qué enseñar:

- formulario de subida
- biblioteca documental existente
- ingestión por archivo o por texto

Qué decir:

- "Aegis puede ingerir contexto de apoyo para que futuras tareas se ejecuten con información recuperada y no solo con el prompt."

Mantén la explicación honesta:

- no afirmar evaluación semántica profunda si no existe
- no afirmar navegación por internet

## 8. Enseñar Insights (30-45s)

Abre `Insights`.

Qué enseñar:

- métricas superiores
- resumen de distribuciones
- cola de revisión de calidad
- bloque de resultados fuertes

Qué decir:

- "Aquí se cierra el ciclo. El sistema no solo ejecuta trabajo; también enseña corridas débiles y fuertes para poder revisarlas."

## 9. Cierre (15-20s)

Cierre sugerido:

> "Aegis es un MVP técnico para portfolio y entrevistas. Demuestra un flujo full-stack backend-first con entrada de tareas, enrutamiento, trazabilidad, feedback y revisión operativa."

Frase opcional de continuación:

> "Si esto evolucionara hacia producción, el siguiente paso sería reforzar observabilidad, usar una cola durable y validar mejor el runtime real."

## Checklist De Demo

- login funciona
- dashboard carga
- la tarea se crea
- la tarea se ejecuta
- el detalle enseña resultado y traza
- el feedback se guarda
- la biblioteca documental está visible
- Insights refleja señales de calidad



