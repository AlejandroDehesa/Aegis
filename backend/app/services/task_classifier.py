import re
import unicodedata


TASK_TYPE_RESEARCH = "research"
TASK_TYPE_SUMMARY = "summary"
TASK_TYPE_COMPARISON = "comparison"
TASK_TYPE_ANALYSIS = "analysis"
TASK_TYPE_PLANNING = "planning"
TASK_TYPE_GENERAL = "general"


KEYWORDS_BY_TASK_TYPE: dict[str, tuple[str, ...]] = {
    TASK_TYPE_COMPARISON: (
        "compare",
        "comparison",
        "vs",
        "versus",
        "difference",
        "differences",
        "pros and cons",
        "better than",
        "comparar",
        "compara",
        "comparacion",
        "diferencia",
        "diferencias",
        "ventajas y desventajas",
    ),
    TASK_TYPE_PLANNING: (
        "plan",
        "roadmap",
        "step by step",
        "step-by-step",
        "implementation plan",
        "create a plan",
        "plan paso a paso",
        "paso a paso",
        "hoja de ruta",
        "plan de implementacion",
        "crear un plan",
        "crea un plan",
    ),
    TASK_TYPE_ANALYSIS: (
        "analyze",
        "analyse",
        "analysis",
        "risk analysis",
        "evaluate risks",
        "analiza",
        "analisis",
        "riesgo",
        "riesgos",
        "evalua riesgos",
        "evaluar riesgos",
    ),
    TASK_TYPE_RESEARCH: (
        "research",
        "investigate",
        "study",
        "explore",
        "find information",
        "look into",
        "investiga",
        "investigar",
        "investigacion",
        "opciones",
        "alternativas",
    ),
    TASK_TYPE_SUMMARY: (
        "summarize",
        "summary",
        "summarise",
        "brief",
        "recap",
        "tldr",
        "tl dr",
        "resume",
        "resumen",
        "resumir",
        "sintesis",
    ),
}

# Priority chosen to avoid obvious product regressions:
# comparison > planning > analysis > research > summary > general.
TASK_TYPE_PRIORITY = (
    TASK_TYPE_COMPARISON,
    TASK_TYPE_PLANNING,
    TASK_TYPE_ANALYSIS,
    TASK_TYPE_RESEARCH,
    TASK_TYPE_SUMMARY,
)


def _normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFD", lowered)
        if unicodedata.category(char) != "Mn"
    )
    normalized = re.sub(r"[^a-z0-9\s]", " ", without_accents)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def classify_task(title: str, description: str | None = None) -> str:
    content = _normalize_text(f"{title} {description or ''}")

    for task_type in TASK_TYPE_PRIORITY:
        keywords = KEYWORDS_BY_TASK_TYPE.get(task_type, ())
        if any(keyword in content for keyword in keywords):
            return task_type

    return TASK_TYPE_GENERAL
