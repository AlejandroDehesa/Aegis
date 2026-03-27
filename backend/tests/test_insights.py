from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from app.api.v1.insights import read_insights_overview

from .helpers import FakeExecuteResult, build_user


class InsightsTests(unittest.TestCase):
    def test_read_insights_overview_aggregates_metrics(self) -> None:
        db = MagicMock()
        user = build_user()

        db.scalar.side_effect = [
            12,  # total tasks
            4,   # unrated tasks
            2,   # failed tasks
            1,   # low-rated tasks
        ]
        db.execute.side_effect = [
            FakeExecuteResult(rows=[("completed", 8), ("failed", 2), ("processing", 2)]),
            FakeExecuteResult(rows=[("research", 5), ("comparison", 4), ("summary", 3)]),
            FakeExecuteResult(rows=[("ResearchAgent", 5), ("ComparisonAgent", 4), ("SummaryAgent", 3)]),
            FakeExecuteResult(rows=[(1, 1), (2, 2), (4, 3), (5, 2)]),
        ]

        overview = read_insights_overview(current_user=user, db=db)

        self.assertEqual(overview.total_tasks, 12)
        self.assertEqual(overview.tasks_by_status["completed"], 8)
        self.assertEqual(overview.tasks_by_task_type["research"], 5)
        self.assertEqual(overview.tasks_by_agent_name["ResearchAgent"], 5)
        self.assertEqual(overview.feedback_rating_distribution["5"], 2)
        self.assertEqual(overview.unrated_tasks, 4)
        self.assertEqual(overview.failed_tasks, 2)
        self.assertEqual(overview.low_rated_tasks, 1)


if __name__ == "__main__":
    unittest.main()
