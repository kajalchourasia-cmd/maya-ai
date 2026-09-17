from __future__ import annotations

import unittest

from app.schemas.state_lifecycle import PlanLifecycle, ReviewState
from app.services.capstone_flows import run_all_capstone_stories, run_capstone_story


class CapstoneFlowTests(unittest.TestCase):
    def test_plan_story_requires_explicit_review_and_save(self):
        result = run_capstone_story("plan-save")
        self.assertTrue(result.passed)
        self.assertEqual(result.plan_status, PlanLifecycle.SAVED)
        self.assertIn("explicit user review", result.causal_chain)

    def test_record_story_selectively_stales_without_regeneration(self):
        result = run_capstone_story("record-continuity")
        self.assertTrue(result.passed)
        self.assertEqual(result.plan_status, PlanLifecycle.STALE)
        self.assertIn("stale plan", result.causal_chain)

    def test_urgent_story_is_zero_generation_and_truthfully_simulated(self):
        result = run_capstone_story("urgent-review")
        self.assertTrue(result.passed)
        self.assertEqual(result.review_state, ReviewState.QUEUED)
        self.assertEqual(result.ordinary_generation_calls, 0)
        self.assertEqual(result.external_transmissions, 0)

    def test_all_three_stories_repeat_from_reset_three_times(self):
        results = run_all_capstone_stories()
        self.assertEqual(len(results), 9)
        self.assertTrue(all(result.passed for result in results))
        self.assertEqual({result.run for result in results}, {1, 2, 3})


if __name__ == "__main__":
    unittest.main()
