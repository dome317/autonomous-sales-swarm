"""
Sales Swarm — Scoring Accuracy Tests
Validates that the scoring model produces expected tiers for test leads.

Run: python test-scoring-accuracy.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent dir so we can import scoring module
sys.path.insert(0, str(Path(__file__).parent.parent / "scoring"))
from lead_scoring_model import score_lead  # noqa: E402


TEST_LEADS_PATH = Path(__file__).parent / "test-leads.json"


def load_test_leads() -> list[dict]:
    with open(TEST_LEADS_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_scoring_accuracy() -> tuple[int, int, list[str]]:
    """Test each lead and check if the computed tier matches expected."""
    leads = load_test_leads()
    passed = 0
    failed = 0
    failures: list[str] = []

    for lead in leads:
        result = score_lead(lead)
        expected_tier = lead.get("expected_tier")

        if expected_tier is None:
            continue

        actual_tier = result["tier"]
        total_score = result["total_score"]

        if actual_tier == expected_tier:
            passed += 1
            print(f"  PASS: {lead['company']}")
            print(f"    Score: {total_score}, Tier: {actual_tier}")
        else:
            failed += 1
            msg = (
                f"  FAIL: {lead['company']}\n"
                f"    Expected: {expected_tier}, Got: {actual_tier}\n"
                f"    Score: {total_score}\n"
                f"    Breakdown: {json.dumps(result['scoring'], indent=6)}"
            )
            print(msg)
            failures.append(msg)

    return passed, failed, failures


def test_score_boundaries():
    """Test edge cases at tier boundaries."""
    print("\n--- Boundary Tests ---")
    passed = 0
    failed = 0

    # Exactly at hot threshold (75)
    lead_hot_boundary = {
        "team_size": 8,       # 100 * 0.25 = 25
        "pain_level": 2,      # 70 * 0.30 = 21
        "digital_level": 2,   # 75 * 0.20 = 15
        "reference_count": 3,  # 90 * 0.15 = 13.5
        "source": "cold_outreach",  # 20 * 0.10 = 2
    }
    # Expected: 25 + 21 + 15 + 13.5 + 2 = 76.5 -> hot
    result = score_lead(lead_hot_boundary)
    if result["tier"] == "hot":
        print(f"  PASS: Boundary hot (score={result['total_score']})")
        passed += 1
    else:
        print(f"  FAIL: Boundary hot expected 'hot', got '{result['tier']}' (score={result['total_score']})")
        failed += 1

    # Just below warm threshold
    lead_cold_boundary = {
        "team_size": 1,       # 30 * 0.25 = 7.5
        "pain_level": 1,      # 40 * 0.30 = 12
        "digital_level": 1,   # 50 * 0.20 = 10
        "reference_count": 0,  # 40 * 0.15 = 6
        "source": "cold_outreach",  # 20 * 0.10 = 2
    }
    # Expected: 7.5 + 12 + 10 + 6 + 2 = 37.5 -> cold
    result = score_lead(lead_cold_boundary)
    if result["tier"] == "cold":
        print(f"  PASS: Boundary cold (score={result['total_score']})")
        passed += 1
    else:
        print(f"  FAIL: Boundary cold expected 'cold', got '{result['tier']}' (score={result['total_score']})")
        failed += 1

    # Maximum possible score
    lead_max = {
        "team_size": 10,
        "pain_level": 3,
        "digital_level": 3,
        "reference_count": 10,
        "source": "referral",
    }
    result = score_lead(lead_max)
    if result["tier"] == "hot" and result["total_score"] >= 95:
        print(f"  PASS: Maximum score (score={result['total_score']})")
        passed += 1
    else:
        print(f"  FAIL: Maximum expected 'hot' >=95, got '{result['tier']}' score={result['total_score']}")
        failed += 1

    # Minimum possible score
    lead_min = {
        "team_size": 1,
        "pain_level": 0,
        "digital_level": 0,
        "reference_count": 0,
        "source": "cold_outreach",
    }
    result = score_lead(lead_min)
    if result["tier"] == "cold" and result["total_score"] < 30:
        print(f"  PASS: Minimum score (score={result['total_score']})")
        passed += 1
    else:
        print(f"  FAIL: Minimum expected 'cold' <30, got '{result['tier']}' score={result['total_score']}")
        failed += 1

    return passed, failed


def main():
    print("=" * 60)
    print("Sales Swarm — Scoring Accuracy Tests")
    print("=" * 60)

    print("\n--- Lead Tier Tests ---")
    p1, f1, _ = test_scoring_accuracy()

    p2, f2 = test_score_boundaries()

    total_passed = p1 + p2
    total_failed = f1 + f2
    total = total_passed + total_failed

    print("\n" + "-" * 60)
    print(f"Results: {total_passed} passed, {total_failed} failed, {total} total")
    print("=" * 60)

    if total_failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
