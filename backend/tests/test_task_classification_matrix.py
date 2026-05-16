from __future__ import annotations

import unittest

from app.services.task_classifier import classify_task


class TaskClassificationMatrixTests(unittest.TestCase):
    def test_classifier_detects_spanish_comparison(self) -> None:
        task_type = classify_task(
            title="Compara FastAPI y Django",
            description="Dame ventajas, desventajas y recomendación final.",
        )
        self.assertEqual(task_type, "comparison")

    def test_classifier_detects_spanish_summary(self) -> None:
        task_type = classify_task(
            title="Hazme un resumen de este texto",
            description="Resume los puntos principales.",
        )
        self.assertEqual(task_type, "summary")

    def test_classifier_detects_spanish_research(self) -> None:
        task_type = classify_task(
            title="Investiga opciones para desplegar un backend",
            description="Quiero alternativas y criterios.",
        )
        self.assertEqual(task_type, "research")

    def test_classifier_detects_spanish_analysis(self) -> None:
        task_type = classify_task(
            title="Analiza los riesgos de usar Railway",
            description="Incluye impacto y mitigaciones.",
        )
        self.assertEqual(task_type, "analysis")

    def test_classifier_detects_spanish_planning(self) -> None:
        task_type = classify_task(
            title="Crea un plan paso a paso para construir una API",
            description="Divídelo por fases.",
        )
        self.assertEqual(task_type, "planning")

    def test_classifier_detects_english_comparison(self) -> None:
        task_type = classify_task(
            title="Compare FastAPI and Django",
            description="Include pros, cons and recommendation.",
        )
        self.assertEqual(task_type, "comparison")

    def test_classifier_does_not_default_obvious_tasks_to_general(self) -> None:
        obvious_cases = [
            ("Dime diferencias entre PostgreSQL y MySQL", "comparison"),
            ("Resume las ventajas de FastAPI", "summary"),
            ("Analiza riesgos de despliegue", "analysis"),
            ("Crea un plan de implementación", "planning"),
        ]

        for title, _ in obvious_cases:
            with self.subTest(title=title):
                detected = classify_task(title=title, description="")
                self.assertNotEqual(detected, "general")

    def test_classifier_handles_title_and_description_together(self) -> None:
        task_type = classify_task(
            title="Necesito ayuda",
            description="Comparar React y Angular para una decisión técnica.",
        )
        self.assertEqual(task_type, "comparison")

    def test_classifier_handles_case_insensitive_keywords(self) -> None:
        task_type = classify_task(
            title="COMPARE fastapi and django",
            description="Need recommendation.",
        )
        self.assertEqual(task_type, "comparison")

    def test_classifier_handles_accents_and_spanish_variants(self) -> None:
        task_type = classify_task(
            title="Análisis de riesgos de despliegue",
            description="Evalúa riesgos técnicos y operativos.",
        )
        self.assertEqual(task_type, "analysis")


if __name__ == "__main__":
    unittest.main()
