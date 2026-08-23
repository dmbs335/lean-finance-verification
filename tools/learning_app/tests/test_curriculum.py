from __future__ import annotations

import unittest
from pathlib import Path

from tools.learning_app.check_curriculum import (
    REQUIRED_COVERAGE_IDS,
    load_curriculum,
    validate_curriculum,
)

ROOT = Path(__file__).resolve().parents[3]


class LearningAppCurriculumTests(unittest.TestCase):
    def test_repository_curriculum_is_complete(self) -> None:
        summary = validate_curriculum(ROOT)
        self.assertGreaterEqual(summary["lesson_count"], 24)
        self.assertGreaterEqual(summary["coverage_count"], len(REQUIRED_COVERAGE_IDS))
        self.assertGreater(summary["source_count"], 60)
        self.assertGreater(summary["minutes"], 600)

    def test_every_path_has_a_distinct_ordered_lesson_sequence(self) -> None:
        curriculum = load_curriculum(ROOT)
        known = {lesson["id"] for lesson in curriculum["lessons"]}
        for path in curriculum["paths"]:
            lesson_ids = path["lessonIds"]
            self.assertTrue(lesson_ids, path["id"])
            self.assertEqual(len(lesson_ids), len(set(lesson_ids)), path["id"])
            self.assertTrue(set(lesson_ids).issubset(known), path["id"])

    def test_every_lesson_links_source_and_states_assurance_boundary(self) -> None:
        curriculum = load_curriculum(ROOT)
        for lesson in curriculum["lessons"]:
            with self.subTest(lesson=lesson["id"]):
                self.assertTrue(lesson["sources"])
                self.assertTrue(lesson["assurance"]["proves"])
                self.assertTrue(lesson["assurance"]["notProves"])
                self.assertGreaterEqual(len(lesson["quiz"]), 2)

    def test_all_project_coverage_ids_are_represented(self) -> None:
        curriculum = load_curriculum(ROOT)
        represented = {
            area
            for lesson in curriculum["lessons"]
            for area in lesson["covers"]
        }
        self.assertTrue(REQUIRED_COVERAGE_IDS.issubset(represented))


if __name__ == "__main__":
    unittest.main()
