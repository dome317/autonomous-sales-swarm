"""
Sales Swarm — Lead Scoring Model
Weighted scoring logic for B2B company leads.

Usage:
    python lead_scoring_model.py              # Run with sample data
    python lead_scoring_model.py --export-js  # Export n8n-compatible JS function
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


CONFIG_PATH = Path(__file__).parent / "scoring-config.json"


def load_config() -> dict[str, Any]:
    """Load scoring configuration from JSON file."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def score_practice_size(team_size: int, config: dict[str, Any]) -> int:
    """Score based on number of team members."""
    ranges = config["criteria"]["practice_size"]["ranges"]
    for r in ranges:
        if r["min"] <= team_size <= r["max"]:
            return r["score"]
    return 30  # default: solo business


def score_pain_match(pain_level: int, config: dict[str, Any]) -> int:
    """Score based on pain match level (0-3)."""
    ranges = config["criteria"]["pain_match"]["ranges"]
    for r in ranges:
        if r["min"] <= pain_level <= r["max"]:
            return r["score"]
    return 10


def score_digitalization(digital_level: int, config: dict[str, Any]) -> int:
    """Score based on digitalization readiness (0-3)."""
    ranges = config["criteria"]["digitalization_readiness"]["ranges"]
    for r in ranges:
        if r["min"] <= digital_level <= r["max"]:
            return r["score"]
    return 20


def score_region_fit(reference_count: int, config: dict[str, Any]) -> int:
    """Score based on number of reference customers in region."""
    ranges = config["criteria"]["region_fit"]["ranges"]
    for r in ranges:
        if r["min"] <= reference_count <= r["max"]:
            return r["score"]
    return 40


def score_source_quality(source: str, config: dict[str, Any]) -> int:
    """Score based on lead acquisition source."""
    values = config["criteria"]["source_quality"]["values"]
    return values.get(source, 20)


def compute_total_score(scores: dict[str, int], config: dict[str, Any]) -> float:
    """Compute weighted total score."""
    weights = config["weights"]
    total = 0.0
    for criterion, weight in weights.items():
        raw = scores.get(criterion, 0)
        total += raw * weight
    return round(total, 2)


def determine_tier(score: float, config: dict[str, Any]) -> str:
    """Determine lead tier based on total score."""
    thresholds = config["thresholds"]
    if score >= thresholds["hot"]:
        return "hot"
    if score >= thresholds["warm"]:
        return "warm"
    return "cold"


def score_lead(lead: dict[str, Any]) -> dict[str, Any]:
    """Score a lead and return full scoring breakdown."""
    config = load_config()

    scores = {
        "practice_size": score_practice_size(
            lead.get("team_size", 1), config
        ),
        "pain_match": score_pain_match(
            lead.get("pain_level", 0), config
        ),
        "digitalization_readiness": score_digitalization(
            lead.get("digital_level", 0), config
        ),
        "region_fit": score_region_fit(
            lead.get("reference_count", 0), config
        ),
        "source_quality": score_source_quality(
            lead.get("source", "cold_outreach"), config
        ),
    }

    weights = config["weights"]
    scoring_detail = {}
    for criterion, raw in scores.items():
        weighted = round(raw * weights[criterion], 2)
        scoring_detail[criterion] = {"raw": raw, "weighted": weighted}

    total = compute_total_score(scores, config)
    tier = determine_tier(total, config)

    return {
        "scoring": scoring_detail,
        "total_score": total,
        "tier": tier,
    }


def export_n8n_js() -> str:
    """Export the scoring logic as an n8n-compatible JavaScript function."""
    config = load_config()
    return f"""// Sales Swarm — Lead Scoring (n8n Code Node)
// Auto-generated from scoring-config.json

const config = {json.dumps(config, indent=2)};

const lead = $input.first().json;

function scoreRange(value, ranges) {{
  for (const r of ranges) {{
    if (value >= r.min && value <= r.max) return r.score;
  }}
  return ranges[0].score;
}}

const scores = {{
  practice_size: scoreRange(lead.team_size || 1, config.criteria.practice_size.ranges),
  pain_match: scoreRange(lead.pain_level || 0, config.criteria.pain_match.ranges),
  digitalization_readiness: scoreRange(lead.digital_level || 0, config.criteria.digitalization_readiness.ranges),
  region_fit: scoreRange(lead.reference_count || 0, config.criteria.region_fit.ranges),
  source_quality: config.criteria.source_quality.values[lead.source] || 20,
}};

let total = 0;
const detail = {{}};
for (const [key, raw] of Object.entries(scores)) {{
  const weighted = Math.round(raw * config.weights[key] * 100) / 100;
  detail[key] = {{ raw, weighted }};
  total += raw * config.weights[key];
}}
total = Math.round(total * 100) / 100;

const tier = total >= config.thresholds.hot ? 'hot'
           : total >= config.thresholds.warm ? 'warm'
           : 'cold';

return {{
  json: {{
    scoring: detail,
    total_score: total,
    tier: tier,
  }}
}};
"""


def main() -> None:
    if "--export-js" in sys.argv:
        print(export_n8n_js())
        return

    sample_leads = [
        {
            "name": "TechStart GmbH",
            "team_size": 5,
            "pain_level": 2,
            "digital_level": 1,
            "reference_count": 3,
            "source": "website_form",
        },
        {
            "name": "Solo Consulting Mueller",
            "team_size": 1,
            "pain_level": 1,
            "digital_level": 0,
            "reference_count": 0,
            "source": "cold_outreach",
        },
        {
            "name": "Enterprise Solutions GmbH",
            "team_size": 12,
            "pain_level": 3,
            "digital_level": 2,
            "reference_count": 6,
            "source": "referral",
        },
    ]

    print("=" * 60)
    print("Sales Swarm — Lead Scoring Model Test")
    print("=" * 60)

    for lead in sample_leads:
        result = score_lead(lead)
        print(f"\n--- {lead['name']} ---")
        print(f"  Team Size: {lead['team_size']}")
        print(f"  Source: {lead['source']}")
        for criterion, detail in result["scoring"].items():
            print(f"  {criterion}: {detail['raw']} (weighted: {detail['weighted']})")
        print(f"  TOTAL: {result['total_score']}")
        print(f"  TIER: {result['tier'].upper()}")


if __name__ == "__main__":
    main()
