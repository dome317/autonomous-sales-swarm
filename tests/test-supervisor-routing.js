/**
 * Sales Swarm — Supervisor Routing Tests
 * Validates that the supervisor correctly routes leads based on their state.
 *
 * Run: node test-supervisor-routing.js
 */

const assert = require("assert");

// --- Routing Logic (mirrors supervisor-system.md) ---

function routeLead(lead) {
  // Missing required fields -> escalate
  if (!lead.email || !lead.name) {
    return {
      route: "escalate",
      reasoning: "Missing required fields (email or name)",
      priority: "high",
    };
  }

  // New lead, not enriched -> research
  if (!lead.enrichment_status || lead.enrichment_status === "pending") {
    return {
      route: "research",
      reasoning: "Lead not yet enriched, needs research",
      priority: "medium",
    };
  }

  // Enriched but not scored -> qualify
  if (
    lead.enrichment_status === "complete" &&
    (lead.score === null || lead.score === undefined || lead.score === 0)
  ) {
    return {
      route: "qualify",
      reasoning: "Lead enriched but not scored",
      priority: "medium",
    };
  }

  // Scored and hot/warm -> outreach
  if (lead.score >= 45 && (lead.tier === "warm" || lead.tier === "hot")) {
    if (!lead.outreach_status || lead.outreach_status === "pending") {
      return {
        route: "outreach",
        reasoning: `Lead scored ${lead.score} (${lead.tier}), ready for outreach`,
        priority: lead.tier === "hot" ? "high" : "medium",
      };
    }
  }

  // Cold lead -> nurture
  if (lead.tier === "cold" || (lead.score !== null && lead.score < 45)) {
    return {
      route: "nurture",
      reasoning: `Lead scored ${lead.score} (cold), entering nurture sequence`,
      priority: "low",
    };
  }

  // Fallback -> escalate
  return {
    route: "escalate",
    reasoning: "Unhandled lead state, escalating for review",
    priority: "medium",
  };
}

// --- Test Cases ---

const tests = [
  {
    name: "New lead (no enrichment) -> research",
    input: {
      lead_id: "t1",
      email: "test@company.example",
      name: "Test Lead",
      enrichment_status: null,
      score: null,
      tier: null,
    },
    expected: "research",
  },
  {
    name: "Enriched but unscored -> qualify",
    input: {
      lead_id: "t2",
      email: "test@company.example",
      name: "Test Lead",
      enrichment_status: "complete",
      score: null,
      tier: null,
    },
    expected: "qualify",
  },
  {
    name: "Hot lead (score 82) -> outreach",
    input: {
      lead_id: "t3",
      email: "test@company.example",
      name: "Test Lead",
      enrichment_status: "complete",
      score: 82,
      tier: "hot",
      outreach_status: null,
    },
    expected: "outreach",
  },
  {
    name: "Warm lead (score 55) -> outreach",
    input: {
      lead_id: "t4",
      email: "test@company.example",
      name: "Test Lead",
      enrichment_status: "complete",
      score: 55,
      tier: "warm",
      outreach_status: "pending",
    },
    expected: "outreach",
  },
  {
    name: "Cold lead (score 30) -> nurture",
    input: {
      lead_id: "t5",
      email: "test@company.example",
      name: "Test Lead",
      enrichment_status: "complete",
      score: 30,
      tier: "cold",
    },
    expected: "nurture",
  },
  {
    name: "Missing email -> escalate",
    input: {
      lead_id: "t6",
      email: null,
      name: "Test Lead",
    },
    expected: "escalate",
  },
  {
    name: "Missing name -> escalate",
    input: {
      lead_id: "t7",
      email: "test@company.example",
      name: null,
    },
    expected: "escalate",
  },
  {
    name: "Pending enrichment -> research",
    input: {
      lead_id: "t8",
      email: "test@company.example",
      name: "Test Lead",
      enrichment_status: "pending",
      score: null,
      tier: null,
    },
    expected: "research",
  },
  {
    name: "Score 0 after enrichment -> qualify",
    input: {
      lead_id: "t9",
      email: "test@company.example",
      name: "Test Lead",
      enrichment_status: "complete",
      score: 0,
      tier: null,
    },
    expected: "qualify",
  },
  {
    name: "Hot lead already contacted -> escalate (fallback)",
    input: {
      lead_id: "t10",
      email: "test@company.example",
      name: "Test Lead",
      enrichment_status: "complete",
      score: 85,
      tier: "hot",
      outreach_status: "sent",
    },
    expected: "escalate",
  },
];

// --- Test Runner ---

let passed = 0;
let failed = 0;

console.log("=" .repeat(60));
console.log("Sales Swarm — Supervisor Routing Tests");
console.log("=".repeat(60));

for (const test of tests) {
  const result = routeLead(test.input);
  const success = result.route === test.expected;

  if (success) {
    passed++;
    console.log(`  PASS: ${test.name}`);
  } else {
    failed++;
    console.log(`  FAIL: ${test.name}`);
    console.log(`    Expected: ${test.expected}`);
    console.log(`    Got:      ${result.route} (${result.reasoning})`);
  }
}

console.log("\n" + "-".repeat(60));
console.log(`Results: ${passed} passed, ${failed} failed, ${tests.length} total`);
console.log("=".repeat(60));

if (failed > 0) {
  process.exit(1);
}
