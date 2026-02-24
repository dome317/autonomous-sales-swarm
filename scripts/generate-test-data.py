"""
Sales Swarm — Test Data Generator
Generates realistic B2B company leads for testing.

Usage: python scripts/generate-test-data.py [count]
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path


FIRST_NAMES = [
    "Markus", "Julia", "Thomas", "Anna", "Stefan",
    "Lisa", "Michael", "Sandra", "Peter", "Carla",
    "Andreas", "Katharina", "Christian", "Maria", "Jan",
]

LAST_NAMES = [
    "Schneider", "Hartmann", "Mueller", "Weber", "Braun",
    "Engel", "Richter", "Klein", "Hoffmann", "Schwarz",
    "Becker", "Fischer", "Wagner", "Schmidt", "Koch",
]

CITIES = [
    ("Berlin", "Berlin"),
    ("Munich", "Bavaria"),
    ("Hamburg", "Hamburg"),
    ("Cologne", "North Rhine-Westphalia"),
    ("Frankfurt", "Hesse"),
    ("Stuttgart", "Baden-Wuerttemberg"),
    ("Duesseldorf", "North Rhine-Westphalia"),
    ("Dresden", "Saxony"),
    ("Hanover", "Lower Saxony"),
    ("Nuremberg", "Bavaria"),
]

COMPANY_TYPES = [
    "Solo Business",
    "Small Team",
    "Enterprise",
    "Specialist Firm",
    "Agency",
]

SOURCES = ["website_form", "referral", "event", "cold_outreach"]

FOCUS_AREAS = [
    "Marketing", "Sales", "Operations", "Finance", "Technology",
    "HR", "Customer Success", "Product", "Analytics",
]


def generate_lead(idx: int) -> dict:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    city, state = random.choice(CITIES)
    company_type = random.choice(COMPANY_TYPES)

    team_size_map = {
        "Solo Business": random.randint(1, 1),
        "Small Team": random.randint(2, 4),
        "Enterprise": random.randint(6, 15),
        "Specialist Firm": random.randint(2, 5),
        "Agency": random.randint(2, 6),
    }
    team_size = team_size_map.get(company_type, 2)

    company_templates = [
        f"{last} Consulting",
        f"{last} & Partners GmbH",
        f"{city} {random.choice(FOCUS_AREAS)} Solutions" if company_type == "Enterprise" else f"{last} Services",
        f"{random.choice(FOCUS_AREAS)} Hub {city}",
    ]

    return {
        "lead_id": f"gen-{idx:04d}",
        "name": f"{first} {last}",
        "email": f"{last.lower()}@{last.lower()}-{city.lower()}.example",
        "company": random.choice(company_templates),
        "website": f"https://{last.lower()}-{city.lower()}.example"
        if random.random() > 0.2 else None,
        "phone": f"+49 {random.randint(30, 89)} {random.randint(1000000, 9999999)}",
        "source": random.choice(SOURCES),
        "team_size": team_size,
        "pain_level": random.randint(0, 3),
        "digital_level": random.randint(0, 3),
        "reference_count": random.randint(0, 6),
        "company_type": company_type,
        "focus_areas": random.sample(
            FOCUS_AREAS, k=random.randint(1, 3)
        ),
        "city": city,
        "state": state,
        "notes": f"Generated test lead #{idx}",
    }


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    leads = [generate_lead(i + 1) for i in range(count)]

    output_path = Path(__file__).parent.parent / "tests" / "generated-leads.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    print(f"Generated {count} test leads -> {output_path}")


if __name__ == "__main__":
    main()
