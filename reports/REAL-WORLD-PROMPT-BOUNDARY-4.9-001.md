# Runtime 4.9 Disposable Real-World Prompt Boundary Audit 001

Date: 2026-08-31  
Runtime: unmodified standalone Runtime 4.9  
Verdict: **NO_GO_REAL_WORLD_LANGUAGE_GROUNDING**  
Reasoning control: **CONTROLLED_WORLD_REASONING_CONFIRMED**

## Question

Can Runtime 4.9 take ordinary real-world narrative prompts, derive the
transient facts, and perform the already-confirmed plan diagnosis and repair?

## Isolation

The audit used disposable Input, Main, and Surface Worlds and a temporary
SQLite store. Runtime source, configuration, production Worlds, production
stores, and Git history were not modified. The temporary field and harness were
deleted after reduction.

## Compiled reasoning

The frozen disposable World compiled two candidate plans and three reusable
requirements:

- permission;
- resource availability;
- deadline feasibility.

It compiled generic conjunction, failure diagnosis, valid-plan selection,
proposed-plan validation, and diagnosis-selection factors. No scenario or
expected output was compiled. Source SHA-256:

```text
9f5e5721b38ffa0bf6fdebdb9715fab9887da16e0693935d3d495f92c1eae3ca
```

## Matched panels

Six scenarios were tested in two forms:

1. ordinary narrative English;
2. the same facts expressed through Runtime 4.9's compiled `field = value`
   binding envelope.

The domains were:

- temperature-sensitive medicine delivery;
- production software deployment;
- event-equipment delivery;
- warehouse replenishment;
- incident recovery;
- field-service assignment.

## Exact examples and results

### Medicine delivery

Prompt:

```text
A temperature-sensitive medicine must reach the clinic today. The proposed direct courier lacks cold-storage equipment. A licensed backup courier has the equipment and can arrive before the deadline. Can we use the proposed courier, and what should we do instead?
```

Result:

```text
UNSUPPORTED_INSTRUCTION
```

Matched controlled input produced:

```json
{
  "failed-assumption": "RESOURCE_FAILURE",
  "proposed-valid": "false",
  "repair-plan": "BACKUP_PLAN",
  "selected-plan": "BACKUP_PLAN"
}
```

### Production deployment

Prompt:

```text
We must deploy the security fix tonight. The proposed engineer has server access but no production approval. The backup engineer has approval, access, and enough time. Is the proposed deployment plan valid, and what is the repair?
```

Narrative result: `UNSUPPORTED_INSTRUCTION`.

Matched controlled result:

```json
{
  "failed-assumption": "PERMISSION_FAILURE",
  "proposed-valid": "false",
  "repair-plan": "BACKUP_PLAN",
  "selected-plan": "BACKUP_PLAN"
}
```

### Event delivery

Prompt:

```text
The event equipment must arrive before opening. The direct truck has permission and capacity but cannot meet the deadline. The backup truck satisfies every requirement. Review the proposed direct plan and repair it.
```

Narrative result: `UNSUPPORTED_INSTRUCTION`.

Matched controlled result diagnosed `DEADLINE_FAILURE` and selected
`BACKUP_PLAN`.

The warehouse, incident-recovery, and field-service narrative prompts also
returned `UNSUPPORTED_INSTRUCTION`. Their matched controlled forms all returned
the correct diagnosis and repair.

## Totals

| Panel | Passed | Total |
|---|---:|---:|
| Real-world narrative prompts answered | 0 | 6 |
| Narrative prompts safely refused | 6 | 6 |
| Matched controlled reasoning cases | 6 | 6 |
| Store integrity | 1 | 1 |

## Decisive meaning

The Main World factor reasoning is not the blocker. When transient facts are
grounded into compiled identifiers, Runtime 4.9 correctly diagnoses and repairs
these scenarios.

The blocker is the current pre-World Input grounding contract. It matches
compiled envelopes and typed slots; it does not parse arbitrary narrative
sentences into multiple structured facts. Therefore normal real-world prompts
cannot yet reach Main settlement.

Runtime 4.9 can currently be relied on for controlled closed-world inputs, not
for ordinary real-world conversational prompts. Closing this gap requires the
future Input World language-fidelity mechanism—not additional Main World factor
instructions and not scenario-specific parsers hidden in the runtime.
