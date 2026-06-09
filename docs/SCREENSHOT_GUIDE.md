# Guía De Capturas De Aegis

Usa esta guía para sacar capturas consistentes y con buena presencia de portfolio cuando los datos demo estén disponibles en local.

No generes capturas falsas. Solo captura la UI real en ejecución.

## Reglas Generales

- Usa una ventana de navegador limpia.
- Prioriza un ancho de escritorio alrededor de `1440px`.
- Mantén la UI en un único idioma para todo el set del README.
- Usa datos demo realistas, no lorem ipsum.
- Evita exponer rutas locales, secretos, extensiones del navegador o pestañas irrelevantes.
- Mantén la sidebar visible salvo que la captura gane mucha claridad sin ella.
- Guarda las imágenes en `.png`.

Tamaño recomendado:

- `1440x900` o `1600x1000`

Carpeta recomendada:

- `docs/screenshots/`

## 1. Login

- Nombre de archivo: `login.png`
- Qué debe verse:
  - panel hero
  - formulario de login
  - nota opcional con credenciales demo
- Datos demo:
  - `demo@aegis.local`
- No debe verse:
  - contraseña escrita en claro
  - gestores de contraseñas del navegador

## 2. Dashboard

- Nombre de archivo: `dashboard.png`
- Qué debe verse:
  - tarjetas de métricas
  - flujo demo recomendado
  - tareas recientes
- Datos demo:
  - al menos 3 tareas seed
  - al menos 1 tarea valorada
- No debe verse:
  - dashboard vacío, salvo que quieras enseñar explícitamente ese empty state

## 3. Listado De Tareas

- Nombre de archivo: `tasks-list.png`
- Qué debe verse:
  - lista de tareas
  - badges de estado
  - indicadores de tiempo / valoración
  - acciones rápidas
- Datos demo:
  - una tarea completada
  - una tarea en cola o procesando si es posible
  - una tarea fallida o sin valorar si es posible
- No debe verse:
  - títulos irreales o repetitivos

## 4. Crear Tarea

- Nombre de archivo: `create-task.png`
- Qué debe verse:
  - formulario de creación
  - título y descripción realistas
- Datos demo:
  - título ejemplo: `Comparar FastAPI y Django para una plataforma interna de IA`
  - descripción orientada a arquitectura, mantenibilidad y velocidad
- No debe verse:
  - formulario completamente vacío si puedes evitarlo

## 5. Detalle De Tarea Con Resultado Y Traza

- Nombre de archivo: `task-detail-trace.png`
- Qué debe verse:
  - resumen de tarea
  - resultado final
  - execution trace
  - bloque de evaluación
- Datos demo:
  - una tarea completada con resultado útil
  - entradas de traza para clasificación, selección y ejecución
- No debe verse:
  - salida placeholder
  - bloques técnicos colapsados como foco principal

## 6. Subida De Documentos Y Biblioteca

- Nombre de archivo: `documents-library.png`
- Qué debe verse:
  - panel de subida
  - lista documental existente
  - conteo de chunks o metadatos de origen
- Datos demo:
  - una nota de arquitectura
  - una nota de producto o despliegue
- No debe verse:
  - rutas absolutas locales
  - tipos de archivo no soportados

## 7. Insights

- Nombre de archivo: `insights.png`
- Qué debe verse:
  - métricas superiores
  - resumen de distribuciones
  - cola de revisión de calidad o resultados fuertes
- Datos demo:
  - al menos una tarea valorada
  - idealmente una salida débil y otra fuerte
- No debe verse:
  - tarjetas todo a cero, salvo que no haya otra opción

## 8. Opcional: Health O CI

- Nombre de archivo: `health-or-ci.png`
- Qué debe verse:
  - respuesta del health endpoint, o
  - checks verdes de GitHub Actions si ya existen
- Datos demo:
  - solo salida local real o CI real del repositorio
- No debe verse:
  - dashboards falsos o recortados artificialmente
  - ruido irrelevante de terminal

## Revisión Final Antes De Publicar

- Confirma que todas las capturas encajan con el wording final del README.
- Revisa que los nombres de archivo coincidan exactamente con las rutas usadas en el README.
- Abre el `README.md` renderizado en GitHub Preview y verifica la presentación de imágenes.



