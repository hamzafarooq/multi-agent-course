"""Evaluation harness for the multi-layer security pipeline.

Loads test scenarios from JSON, runs each query through the
validate_input pipeline, and reports pass/fail statistics.
"""

import asyncio
import json
import os
import re
import logging
from pathlib import Path
from typing import Any, Dict

from cs_agent.security.blocker import evaluate_prompt
from cs_agent.security.sanitizer import sanitize_input

logger = logging.getLogger(__name__)

_EVAL_DIR = Path(__file__).resolve().parent


class SimpleEvaluator:
    """Run JSON-driven security evaluation scenarios."""

    def __init__(
        self,
        scenarios_file: str | None = None,
        config_file: str | None = None,
    ):
        scenarios_file = scenarios_file or str(_EVAL_DIR / "test_scenarios.json")
        config_file = config_file or str(_EVAL_DIR / "test_config.json")

        with open(scenarios_file, "r") as f:
            self.scenarios = json.load(f)

        with open(config_file, "r") as f:
            self.config = json.load(f)

        self.results: Dict[str, Any] = {
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "details": [],
        }

    async def evaluate_query(
        self, query: str, expected_outcome: str, test_name: str
    ) -> Dict[str, Any]:
        """Evaluate a single query against the security pipeline."""
        print(f"\nTesting: {test_name}")
        print(f"Query: {query}")
        print(f"Expected outcome: {expected_outcome}")

        try:
            # Layer 1: sanitize_input
            try:
                sanitized = sanitize_input(query)
            except ValueError:
                actual_outcome = "BLOCKED"
                return self._build_result(
                    test_name, query, expected_outcome, actual_outcome, "Blocked by sanitizer"
                )

            # Layer 2: SecurityBlocker regex
            blocker_status = evaluate_prompt(sanitized)
            if blocker_status == "BLOCKED":
                actual_outcome = "BLOCKED"
                return self._build_result(
                    test_name, query, expected_outcome, actual_outcome, "Blocked by SecurityBlocker"
                )

            actual_outcome = "PASSED"
            return self._build_result(
                test_name, query, expected_outcome, actual_outcome, "Passed all checks"
            )

        except Exception as e:
            logger.error("Evaluation error for %s: %s", test_name, e)
            return {
                "name": test_name,
                "query": query,
                "expected_outcome": expected_outcome,
                "actual_outcome": "ERROR",
                "response": f"Error: {str(e)}",
                "passed": False,
            }

    @staticmethod
    def _build_result(
        name: str, query: str, expected: str, actual: str, response: str
    ) -> Dict[str, Any]:
        return {
            "name": name,
            "query": query,
            "expected_outcome": expected,
            "actual_outcome": actual,
            "response": response,
            "passed": actual == expected,
        }

    async def run_evaluation(self) -> Dict[str, Any]:
        """Run all test scenarios and produce a summary report."""
        print("Starting evaluation...")

        all_scenarios = []
        all_scenarios.extend(
            [{"category": "malicious", **s} for s in self.scenarios["malicious_queries"]]
        )
        all_scenarios.extend(
            [{"category": "legitimate", **s} for s in self.scenarios["legitimate_queries"]]
        )

        total = len(all_scenarios)
        passed = 0

        for scenario in all_scenarios:
            result = await self.evaluate_query(
                query=scenario["query"],
                expected_outcome=scenario["expected_outcome"],
                test_name=f"{scenario['category']}_{scenario['name']}",
            )

            if result["passed"]:
                passed += 1
                print("  PASS")
            else:
                print("  FAIL")
                print(f"  Expected: {result['expected_outcome']}")
                print(f"  Actual:   {result['actual_outcome']}")

            self.results["details"].append(result)

        self.results["summary"]["total"] = total
        self.results["summary"]["passed"] = passed
        self.results["summary"]["failed"] = total - passed

        if "save_results_to" in self.config:
            out_path = _EVAL_DIR / self.config["save_results_to"]
            with open(out_path, "w") as f:
                json.dump(self.results, f, indent=2)
            print(f"\nResults saved to {out_path}")

        print("\n===== EVALUATION SUMMARY =====")
        print(f"Total tests: {total}")
        print(f"Passed: {passed} ({passed / total * 100:.1f}%)")
        print(f"Failed: {total - passed} ({(total - passed) / total * 100:.1f}%)")

        return self.results


async def main():
    evaluator = SimpleEvaluator()
    await evaluator.run_evaluation()


if __name__ == "__main__":
    asyncio.run(main())
