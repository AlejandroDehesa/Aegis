from __future__ import annotations

import re
import unittest

from app.services.task_classifier import classify_task


def _slugify(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered or "case"


class TaskClassifierMultilingualRegressionTests(unittest.TestCase):
    def test_spanish_comparison_task_is_not_classified_as_general(self) -> None:
        task_type = classify_task(
            title="Compara FastAPI y Django",
            description=(
                "Compara FastAPI y Django para crear una API backend moderna. "
                "Dame ventajas, desventajas y recomendacion final."
            ),
        )
        self.assertEqual(task_type, "comparison")
        self.assertNotEqual(task_type, "general")

    def test_analysis_task_is_classified_as_analysis(self) -> None:
        task_type = classify_task(
            title="Riesgos Railway",
            description="Analiza los riesgos de desplegar backend con Docker y PostgreSQL.",
        )
        self.assertEqual(task_type, "analysis")

    def test_planning_task_is_classified_as_planning(self) -> None:
        task_type = classify_task(
            title="Plan plataforma agentes",
            description=(
                "Crea un plan paso a paso para construir una plataforma de agentes IA "
                "con clasificacion, seleccion de agente, ejecucion y trazabilidad."
            ),
        )
        self.assertEqual(task_type, "planning")


CLASSIFIER_CASES: list[tuple[str, str, str, str]] = [
    ("comparison", "Compara React y Angular", "", "spanish"),
    ("comparison", "Comparar React y Angular", "Necesito decidir stack frontend.", "spanish"),
    ("comparison", "Dime diferencias entre PostgreSQL y MySQL", "", "spanish"),
    ("comparison", "Ventajas y desventajas de Docker", "Quiero una recomendacion.", "spanish"),
    ("comparison", "Comparacion de FastAPI vs Django", "Incluye casos de uso.", "spanish"),
    ("comparison", "Que es mejor entre Redis y PostgreSQL", "Para una API", "spanish"),
    ("comparison", "Compare FastAPI and Django", "Include recommendation", "english"),
    ("comparison", "FastAPI vs Django comparison", "Include pros and cons", "english"),
    ("comparison", "Difference between PostgreSQL and MySQL", "Need tradeoffs", "english"),
    ("comparison", "Better than analysis: Flask versus FastAPI", "", "english"),
    ("comparison", "COMPARISON OF NODE AND GO", "", "english"),
    ("comparison", "Compare kafka vs rabbitmq for workers", "", "english"),
    ("summary", "Hazme un resumen de este texto", "", "spanish"),
    ("summary", "Resume las ventajas de FastAPI", "", "spanish"),
    ("summary", "Necesito un resumen ejecutivo", "Corto y claro", "spanish"),
    ("summary", "Sintesis de arquitectura backend", "", "spanish"),
    ("summary", "Summary of deployment notes", "", "english"),
    ("summary", "Summarize this document", "", "english"),
    ("summary", "TLDR for this RFC", "", "english"),
    ("summary", "Brief recap of sprint risks", "", "english"),
    ("research", "Investiga mejores opciones para desplegar backend", "", "spanish"),
    ("research", "Investigacion sobre monitoreo para APIs", "", "spanish"),
    ("research", "Explora alternativas de hosting para FastAPI", "", "spanish"),
    ("research", "Research backend deployment options", "", "english"),
    ("research", "Investigate cloud cost controls", "", "english"),
    ("research", "Look into observability options", "", "english"),
    ("analysis", "Analiza los riesgos de usar Railway", "", "spanish"),
    ("analysis", "Analisis de riesgos de despliegue", "", "spanish"),
    ("analysis", "Evalua riesgos de migrar base de datos", "", "spanish"),
    ("analysis", "Analiza impacto de latencia en UX", "", "spanish"),
    ("analysis", "Analyze the risks of Docker deployment", "", "english"),
    ("analysis", "Risk analysis for API throttling", "", "english"),
    ("analysis", "Evaluate risks in release pipeline", "", "english"),
    ("planning", "Crea un plan paso a paso para construir una API", "", "spanish"),
    ("planning", "Plan de implementacion para autenticacion JWT", "", "spanish"),
    ("planning", "Hoja de ruta para modularizar servicios", "", "spanish"),
    ("planning", "Crear un plan de pruebas por fases", "", "spanish"),
    ("planning", "Create a step-by-step plan", "", "english"),
    ("planning", "Roadmap for production hardening", "", "english"),
    ("planning", "Implementation plan for task orchestration", "", "english"),
    ("general", "Ayudame con una tarea general", "", "spanish"),
    ("general", "Necesito ayuda con algo", "", "spanish"),
    ("general", "Quiero soporte general", "", "spanish"),
    ("general", "Help me with a general task", "", "english"),
    ("general", "I need generic assistance", "", "english"),
]


def _build_case_test(
    expected_type: str,
    title: str,
    description: str,
) -> callable:
    def _test(self: TaskClassifierMultilingualRegressionTests) -> None:
        task_type = classify_task(title=title, description=description)
        self.assertEqual(
            task_type,
            expected_type,
            msg=f"Unexpected classification for title='{title}' description='{description}'",
        )
        if expected_type != "general":
            self.assertNotEqual(task_type, "general")

    return _test


for case_index, (expected_type, title, description, language) in enumerate(CLASSIFIER_CASES, start=1):
    method_name = (
        f"test_classifier_case_{case_index:03d}_{language}_"
        f"{_slugify(title)[:56]}_returns_{expected_type}"
    )
    setattr(
        TaskClassifierMultilingualRegressionTests,
        method_name,
        _build_case_test(expected_type, title, description),
    )


TITLE_DESCRIPTION_CONFLICT_CASES: list[tuple[str, str, str]] = [
    (
        "comparison",
        "Necesito ayuda",
        "Comparar Postgres y MySQL con ventajas y desventajas",
    ),
    (
        "analysis",
        "Necesito ayuda",
        "Analiza riesgos operativos de desplegar con Railway",
    ),
    (
        "planning",
        "Necesito ayuda",
        "Crea un plan paso a paso para publicar una API",
    ),
    (
        "research",
        "Necesito ayuda",
        "Investiga opciones de monitorizacion para backend",
    ),
    (
        "summary",
        "Necesito ayuda",
        "Resume este documento de arquitectura",
    ),
]


def _build_title_description_case_test(
    expected_type: str,
    title: str,
    description: str,
) -> callable:
    def _test(self: TaskClassifierMultilingualRegressionTests) -> None:
        task_type = classify_task(title=title, description=description)
        self.assertEqual(task_type, expected_type)

    return _test


for case_index, (expected_type, title, description) in enumerate(TITLE_DESCRIPTION_CONFLICT_CASES, start=1):
    method_name = (
        f"test_title_description_case_{case_index:03d}_"
        f"{_slugify(description)[:56]}_returns_{expected_type}"
    )
    setattr(
        TaskClassifierMultilingualRegressionTests,
        method_name,
        _build_title_description_case_test(expected_type, title, description),
    )


if __name__ == "__main__":
    unittest.main()
