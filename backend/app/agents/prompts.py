from __future__ import annotations

from app.agents.prompt_utils import build_retrieved_context_block


SPANISH_HINT_TOKENS = (
    " para ",
    " con ",
    " como ",
    " y ",
    " que ",
    " una ",
    " un ",
    " de ",
    " del ",
    " dame ",
    " compara ",
    " anal",
    " plan ",
    " resumen ",
    " investig",
    " siguiente accion",
    " recomendacion",
    " recomendación",
)


def _detect_language_hint(title: str, description: str, retrieved_context: str | None = None) -> str:
    combined = f"{title}\n{description}\n{retrieved_context or ''}".lower()
    if any(char in combined for char in ("á", "é", "í", "ó", "ú", "ñ", "¿", "¡")):
        return "es"
    if any(token in combined for token in SPANISH_HINT_TOKENS):
        return "es"
    return "en"


def _language_instruction(language_hint: str) -> str:
    if language_hint == "es":
        return (
            "Language: respond in Spanish. Keep technical terms in English only when needed. "
            "Keep section headings clear and professional."
        )

    return (
        "Language: respond in English. Keep wording precise, professional, and task-specific."
    )


def _compose_prompt(
    *,
    agent_name: str,
    mission: str,
    title: str,
    description: str,
    retrieved_context: str | None,
    output_contract: list[str],
    extra_rules: list[str],
) -> str:
    language_hint = _detect_language_hint(title, description, retrieved_context)
    context_block = build_retrieved_context_block(retrieved_context)
    has_document_context = bool(retrieved_context and retrieved_context.strip())
    format_lines = "\n".join(f"{index}. {item}" for index, item in enumerate(output_contract, start=1))
    rule_lines = "\n".join(f"- {rule}" for rule in extra_rules)
    context_rule = (
        "- Use the available document context as the primary source for claims when relevant."
        if has_document_context
        else "- No document context is available; explicitly state assumptions where needed."
    )

    return (
        f"System role: You are {agent_name} inside Aegis.\n"
        f"Mission: {mission}\n"
        f"{_language_instruction(language_hint)}\n\n"
        "Hard rules:\n"
        "- Do not use filler, unfinished, or non-actionable language.\n"
        "- Do not say 'as an AI' or similar disclaimers.\n"
        "- Do not invent external facts or sources.\n"
        "- If context is missing, state assumptions explicitly.\n"
        "- Keep the answer concrete and directly useful for this task.\n"
        f"{context_rule}\n"
        f"{rule_lines}\n\n"
        f"Task title: {title}\n"
        f"Task description: {description}\n\n"
        f"{context_block}"
        "Output format (use this section order):\n"
        f"{format_lines}\n"
    )


def build_comparison_prompt(title: str, description: str, retrieved_context: str | None = None) -> str:
    return _compose_prompt(
        agent_name="ComparisonAgent",
        mission="Produce a defendable technical comparison with a clear decision.",
        title=title,
        description=description,
        retrieved_context=retrieved_context,
        output_contract=[
            "Resumen ejecutivo / Executive summary",
            "Opciones comparadas / Compared options",
            "Ventajas / Advantages",
            "Desventajas / Disadvantages",
            "Casos de uso ideales / Best use cases",
            "Recomendación final / Final recommendation",
            "Supuestos o límites / Assumptions or limits",
        ],
        extra_rules=[
            "Reference the specific technologies or options in the task.",
            "Explain trade-offs, not just features.",
            "End with a direct recommendation.",
        ],
    )


def build_analysis_prompt(title: str, description: str, retrieved_context: str | None = None) -> str:
    return _compose_prompt(
        agent_name="AnalysisAgent",
        mission="Deliver a practical risk analysis to support decisions.",
        title=title,
        description=description,
        retrieved_context=retrieved_context,
        output_contract=[
            "Executive summary / Resumen ejecutivo",
            "Risks / Riesgos",
            "Impact / Impacto",
            "Mitigation / Mitigacion",
            "Priority / Prioridad",
            "Final recommendation / Recomendacion final",
            "Assumptions and limits / Supuestos y limites",
        ],
        extra_rules=[
            "Separate risk, impact, and mitigation explicitly.",
            "For each risk, include probability and severity in concrete terms.",
            "Prioritize actions by urgency and potential effect.",
            "Avoid vague statements that cannot guide execution.",
        ],
    )


def build_planning_prompt(title: str, description: str, retrieved_context: str | None = None) -> str:
    return _compose_prompt(
        agent_name="PlanningAgent",
        mission="Create an actionable execution plan with clear sequence and ownership cues.",
        title=title,
        description=description,
        retrieved_context=retrieved_context,
        output_contract=[
            "Objetivo / Objective",
            "Fases / Phases",
            "Pasos detallados / Step-by-step plan",
            "Dependencias / Dependencies",
            "Riesgos / Risks",
            "Criterios de éxito / Success criteria",
            "Siguiente acción recomendada / Next recommended action",
        ],
        extra_rules=[
            "Use numbered steps in logical order.",
            "Include one immediate next action that can start today.",
            "Keep the plan practical, not abstract.",
        ],
    )


def build_summary_prompt(title: str, description: str, retrieved_context: str | None = None) -> str:
    return _compose_prompt(
        agent_name="SummaryAgent",
        mission="Summarize the task context without losing key decisions or constraints.",
        title=title,
        description=description,
        retrieved_context=retrieved_context,
        output_contract=[
            "Idea principal / Main idea",
            "Puntos clave / Key points",
            "Detalles importantes / Important details",
            "Conclusión / Conclusion",
            "Acción recomendada (si aplica) / Recommended action (if applicable)",
        ],
        extra_rules=[
            "Do not add external information unless explicitly requested.",
            "Stay concise but preserve decision-critical points.",
        ],
    )


def build_research_prompt(title: str, description: str, retrieved_context: str | None = None) -> str:
    return _compose_prompt(
        agent_name="ResearchAgent",
        mission="Produce structured research using only the provided context.",
        title=title,
        description=description,
        retrieved_context=retrieved_context,
        output_contract=[
            "Objetivo de investigación / Research objective",
            "Información disponible / Available information",
            "Hallazgos preliminares / Preliminary findings",
            "Vacíos de información / Information gaps",
            "Próximos pasos de investigación / Next research steps",
            "Recomendación / Recommendation",
        ],
        extra_rules=[
            "Never claim internet browsing or external source access.",
            "Never fabricate references or citations.",
            "If context is insufficient, say it clearly and propose what to validate next.",
        ],
    )


def build_general_prompt(title: str, description: str, retrieved_context: str | None = None) -> str:
    return _compose_prompt(
        agent_name="GeneralAssistantAgent",
        mission="Provide a useful fallback answer for broad tasks with practical next steps.",
        title=title,
        description=description,
        retrieved_context=retrieved_context,
        output_contract=[
            "Interpretación de la tarea / Task interpretation",
            "Respuesta / Response",
            "Pasos sugeridos / Suggested steps",
            "Siguiente acción / Next action",
        ],
        extra_rules=[
            "Never use unfinished or canned workflow wording.",
            "Always provide a concrete next action.",
        ],
    )


def build_comparison_fallback(title: str, description: str) -> str:
    lowered = f"{title} {description}".lower()
    mentions_fastapi = "fastapi" in lowered
    mentions_django = "django" in lowered

    subject_a = "FastAPI" if mentions_fastapi else "Option A"
    subject_b = "Django" if mentions_django else "Option B"

    return (
        "# Comparación técnica / Technical comparison\n\n"
        "## 1. Resumen ejecutivo / Executive summary\n"
        f"- Se comparan {subject_a} y {subject_b} para el objetivo solicitado.\n\n"
        "## 2. Opciones comparadas / Compared options\n"
        f"- Opción A: {subject_a}\n"
        f"- Opción B: {subject_b}\n\n"
        "## 3. Ventajas / Advantages\n"
        f"- {subject_a}: velocidad para APIs modernas e iteración rápida.\n"
        f"- {subject_b}: ecosistema integrado y administración robusta.\n\n"
        "## 4. Desventajas / Disadvantages\n"
        f"- {subject_a}: menos componentes integrados para monolitos grandes.\n"
        f"- {subject_b}: mayor peso inicial para servicios API ligeros.\n\n"
        "## 5. Casos de uso ideales / Best use cases\n"
        f"- {subject_a}: productos API-first y cargas async.\n"
        f"- {subject_b}: plataformas con panel admin y backoffice fuerte.\n\n"
        "## 6. Recomendación final / Final recommendation\n"
        f"- Prioriza {subject_a} para velocidad en APIs.\n"
        f"- Prioriza {subject_b} si necesitas más funcionalidades integradas.\n\n"
        "## 7. Supuestos o límites / Assumptions or limits\n"
        f"- Basado en el contexto disponible: {description}"
    )


def build_analysis_fallback(title: str, description: str) -> str:
    return (
        "# Analisis tecnico / Technical analysis\n\n"
        "## 1. Executive summary / Resumen ejecutivo\n"
        f"- Evaluacion inicial de riesgos para: {title}.\n\n"
        "## 2. Risks / Riesgos\n"
        "- Risk 1: configuracion incompleta en despliegue (probabilidad media, severidad alta).\n"
        "- Risk 2: degradacion de servicio bajo picos de carga (probabilidad media, severidad media-alta).\n\n"
        "## 3. Impact / Impacto\n"
        "- Posible indisponibilidad parcial, retrasos operativos y perdida de confianza.\n\n"
        "## 4. Mitigation / Mitigacion\n"
        "- Mitigation: aplicar health checks, despliegue gradual y rollback validado.\n"
        "- Mitigacion adicional: alertas de capacidad y observabilidad operativa.\n\n"
        "## 5. Priority / Prioridad\n"
        "- Prioridad 1: endurecer configuracion y checklist de release.\n"
        "- Prioridad 2: reforzar monitorizacion y respuesta a incidentes.\n\n"
        "## 6. Final recommendation / Recomendacion final\n"
        "- Ejecutar primero mitigaciones de confiabilidad antes de escalar alcance.\n\n"
        "## 7. Assumptions and limits / Supuestos y limites\n"
        f"- Basado en el contexto disponible: {description}"
    )


def build_planning_fallback(title: str, description: str) -> str:
    return (
        "# Plan de ejecución / Execution plan\n\n"
        "## 1. Objetivo / Objective\n"
        f"- Entregar una solución accionable para: {title}.\n\n"
        "## 2. Fases / Phases\n"
        "1. Definición de alcance y criterios de éxito.\n"
        "2. Implementación incremental y validación continua.\n"
        "3. Estabilización y preparación de release.\n\n"
        "## 3. Pasos detallados / Step-by-step plan\n"
        "1. Definir alcance, constraints y criterios de aceptación.\n"
        "2. Dividir trabajo en bloques técnicos pequeños.\n"
        "3. Implementar un vertical slice end-to-end.\n"
        "4. Validar con tests y revisión técnica.\n"
        "5. Consolidar resultados y preparar siguiente iteración.\n\n"
        "## 4. Dependencias / Dependencies\n"
        "- Entorno estable de pruebas y datos reproducibles.\n"
        "- Alineación de contratos entre módulos involucrados.\n\n"
        "## 5. Riesgos / Risks\n"
        "- Crecimiento de alcance sin criterios cerrados.\n"
        "- Regresiones por validación tardía.\n\n"
        "## 6. Criterios de éxito / Success criteria\n"
        "- Entregable funcional, validado y trazable.\n"
        "- Riesgos críticos mitigados antes de release.\n\n"
        "## 7. Siguiente acción recomendada / Next action\n"
        "- Crear checklist técnico corto y ejecutar el paso 1 hoy mismo.\n\n"
        "Contexto considerado:\n"
        f"- {description}"
    )


def build_summary_fallback(title: str, description: str) -> str:
    return (
        "# Resumen / Summary\n\n"
        "## 1. Idea principal / Main idea\n"
        f"- La tarea se centra en: {title}.\n\n"
        "## 2. Puntos clave / Key points\n"
        f"- Objetivo declarado: {title}.\n"
        f"- Contexto base: {description}.\n"
        "- Priorizar decisiones accionables frente a teoría extensa.\n\n"
        "## 3. Detalles importantes / Important details\n"
        "- Validar supuestos antes de cerrar recomendaciones.\n"
        "- Mantener trazabilidad de decisiones y riesgos.\n\n"
        "## 4. Conclusión / Conclusion\n"
        "- El enfoque debe ser práctico, medible y orientado a ejecución.\n\n"
        "## 5. Acción recomendada si aplica / Recommended action\n"
        "- Confirmar criterio de éxito y ejecutar el primer paso de mayor impacto."
    )


def build_research_fallback(title: str, description: str) -> str:
    return (
        "# Investigación estructurada / Structured research\n\n"
        "## 1. Objetivo de investigación / Research objective\n"
        f"- Clarificar decisiones alrededor de: {title}.\n\n"
        "## 2. Información disponible / Available information\n"
        f"- Contexto recibido: {description}.\n"
        "- No se han usado búsquedas externas ni navegación por internet.\n\n"
        "## 3. Hallazgos preliminares / Preliminary findings\n"
        "- Se identifican líneas de análisis con impacto técnico directo.\n"
        "- Hay señales suficientes para definir una hipótesis inicial.\n\n"
        "## 4. Vacíos de información / Information gaps\n"
        "- Faltan métricas reales de carga, costes y restricciones operativas.\n"
        "- Falta validación de supuestos con datos de entorno objetivo.\n\n"
        "## 5. Próximos pasos de investigación / Next research steps\n"
        "1. Definir qué datos faltan y cómo obtenerlos.\n"
        "2. Contrastar hipótesis con evidencia interna disponible.\n"
        "3. Refinar recomendación con base en resultados.\n\n"
        "## 6. Recomendación / Recommendation\n"
        "- Continuar con validación dirigida de los vacíos críticos antes de decidir."
    )


def build_general_fallback(title: str, description: str) -> str:
    return (
        "# Respuesta general / General response\n\n"
        "## 1. Interpretación de la tarea / Task interpretation\n"
        f"- Solicitud principal: {title}.\n"
        f"- Contexto disponible: {description}.\n\n"
        "## 2. Respuesta / Response\n"
        "- Enfoca la ejecución en resultados verificables y entregables concretos.\n\n"
        "## 3. Pasos sugeridos / Suggested steps\n"
        "1. Alinear alcance y formato esperado del resultado.\n"
        "2. Priorizar el bloque de mayor impacto técnico.\n"
        "3. Validar salida con un checklist mínimo de calidad.\n\n"
        "## 4. Siguiente acción / Next action\n"
        "- Define una recomendación ejecutable para hoy y confirma criterio de éxito."
    )
