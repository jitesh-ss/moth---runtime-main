"""Reproducible World sources for disposable Runtime 5.0 Surface instances."""

from __future__ import annotations

import json


SURFACE_SOURCE = """\
Operation "realize-semantic-result" selects kernel primitive "REALIZE_SEMANTIC_RESULT".
Instruction "realize-semantic-result" selects operation "realize-semantic-result" accepts "Realize the verified semantic result.".
"""


def _quoted(value: object) -> str:
    return json.dumps(json.dumps(value, separators=(",", ":")))


def _factor_source(
    *,
    values: list[tuple[str, str]],
    domains: dict[str, list[str]],
    templates: dict[str, dict],
    programs: dict[str, list[dict]],
    fields: list[str],
) -> str:
    schema = {
        "type": "object",
        "properties": {name: {"type": "string"} for name in fields},
        "required": fields,
        "additionalProperties": False,
    }
    lines = ['Scalar type "symbol" selects kernel type "STRING".']
    lines += [
        f'Value "{name}" has type "symbol" and canonical JSON {_quoted(value)}.'
        for name, value in values
    ]
    lines.append(f'Structured schema "inputs" is canonical JSON Schema {_quoted(schema)}.')
    lines += [
        f'Schema field "{name}" in schema "inputs" has type "symbol" and is required.'
        for name in fields
    ]
    lines += [
        f'Finite domain "{name}" is canonical value JSON {_quoted(items)}.'
        for name, items in domains.items()
    ]
    lines += [
        f'Factor template "{name}" is canonical table JSON {_quoted(table)}.'
        for name, table in templates.items()
    ]
    lines += [
        f'Factor program "{name}" is canonical instruction JSON {_quoted(steps)}.'
        for name, steps in programs.items()
    ]
    lines += [
        'Operation "factor-settle" selects kernel primitive "FACTOR_SETTLEMENT".',
        'Output schema "answer-json" selects kernel schema "ANSWER_WITH_PROOF".',
        'Instruction "factor-settle" selects operation "factor-settle" accepts "Settle {PROGRAM} with {BINDINGS} using {SCHEMA}.".',
    ]
    return "\n".join(lines) + "\n"


def decision_source() -> str:
    values = [
        ("yes", "true"),
        ("no", "false"),
        ("proposed", "PROPOSED"),
        ("backup", "BACKUP"),
        ("none", "NONE"),
        ("reason-none", "NONE"),
        ("reason-resource", "RESOURCE"),
        ("reason-permission", "PERMISSION"),
        ("reason-deadline", "DEADLINE"),
    ]
    fields = [
        "proposed-resource",
        "proposed-permission",
        "proposed-deadline",
        "backup-resource",
        "backup-permission",
        "backup-deadline",
    ]
    validity_rows = []
    diagnosis_rows = []
    for resource in ("no", "yes"):
        for permission in ("no", "yes"):
            for deadline in ("no", "yes"):
                valid = "yes" if resource == permission == deadline == "yes" else "no"
                validity_rows.append([resource, permission, deadline, valid])
                reason = (
                    "reason-resource"
                    if resource == "no"
                    else "reason-permission"
                    if permission == "no"
                    else "reason-deadline"
                    if deadline == "no"
                    else "reason-none"
                )
                diagnosis_rows.append([resource, permission, deadline, reason])
    templates = {
        "validity": {
            "ports": [
                {"name": key, "domain": "boolean"}
                for key in ("resource", "permission", "deadline", "valid")
            ],
            "allowed_tuples": validity_rows,
        },
        "selection": {
            "ports": [
                {"name": "proposed-valid", "domain": "boolean"},
                {"name": "backup-valid", "domain": "boolean"},
                {"name": "selected", "domain": "selection"},
            ],
            "allowed_tuples": [
                ["yes", "yes", "proposed"],
                ["yes", "no", "proposed"],
                ["no", "yes", "backup"],
                ["no", "no", "none"],
            ],
        },
        "diagnosis": {
            "ports": [
                {"name": key, "domain": "boolean"}
                for key in ("resource", "permission", "deadline")
            ]
            + [{"name": "reason", "domain": "failure-reason"}],
            "allowed_tuples": diagnosis_rows,
        },
    }
    steps: list[dict] = []
    for field in fields:
        steps.append({"opcode": "CREATE_VARIABLE", "instance": field, "domain": "boolean"})
    for name, domain in (
        ("proposed-valid", "boolean"),
        ("backup-valid", "boolean"),
        ("selected-plan", "selection"),
        ("failure-reason", "failure-reason"),
    ):
        steps.append({"opcode": "CREATE_VARIABLE", "instance": name, "domain": domain})
    for candidate in ("proposed", "backup"):
        factor = f"{candidate}-validity"
        steps.append({"opcode": "INSTANTIATE_FACTOR", "instance": factor, "template": "validity"})
        for port in ("resource", "permission", "deadline"):
            steps.append(
                {
                    "opcode": "BIND_PORT",
                    "factor": factor,
                    "port": port,
                    "variable": f"{candidate}-{port}",
                }
            )
        steps.append(
            {
                "opcode": "BIND_PORT",
                "factor": factor,
                "port": "valid",
                "variable": f"{candidate}-valid",
            }
        )
    steps.append({"opcode": "INSTANTIATE_FACTOR", "instance": "selection", "template": "selection"})
    for port, variable in (
        ("proposed-valid", "proposed-valid"),
        ("backup-valid", "backup-valid"),
        ("selected", "selected-plan"),
    ):
        steps.append({"opcode": "BIND_PORT", "factor": "selection", "port": port, "variable": variable})
    steps.append({"opcode": "INSTANTIATE_FACTOR", "instance": "diagnosis", "template": "diagnosis"})
    for port in ("resource", "permission", "deadline"):
        steps.append(
            {
                "opcode": "BIND_PORT",
                "factor": "diagnosis",
                "port": port,
                "variable": f"proposed-{port}",
            }
        )
    steps.append(
        {
            "opcode": "BIND_PORT",
            "factor": "diagnosis",
            "port": "reason",
            "variable": "failure-reason",
        }
    )
    for field in fields:
        steps.append({"opcode": "CLAMP_FROM_PROMPT", "variable": field, "field": field})
    for ordinal, variable in enumerate(
        ("proposed-valid", "backup-valid", "selected-plan", "failure-reason")
    ):
        steps.append(
            {"opcode": "EXPOSE_OUTPUT", "variable": variable, "ordinal": ordinal, "label": variable}
        )
    source = _factor_source(
        values=values,
        domains={
            "boolean": ["no", "yes"],
            "selection": ["proposed", "backup", "none"],
            "failure-reason": ["reason-none", "reason-resource", "reason-permission", "reason-deadline"],
        },
        templates=templates,
        programs={"validate-and-select": steps},
        fields=fields,
    )
    entities = [
        "direct-courier",
        "backup-courier",
        "cold-storage",
        "road-permit",
        "delivery-deadline",
        "deployment-engineer",
        "backup-engineer",
        "server-access",
        "production-approval",
        "deployment-deadline",
    ]
    return source + "\n".join(
        [
            'Directional relation "satisfies" maps Entity to Entity and is multi-valued.',
            *[f'Entity "{name}" is declared.' for name in entities],
        ]
    ) + "\n"


def semantic_contract(domain: str) -> dict:
    if domain == "delivery":
        definition = {
            "domain": ["delivery", "courier", "carrier"],
            "entities": [
                ("proposed", "direct-courier", "PROPOSED", ["direct courier", "proposed courier", "direct carrier", "proposed carrier", "direct plan", "proposed plan"]),
                ("backup", "backup-courier", "BACKUP", ["backup courier", "alternative courier", "backup carrier", "alternative carrier", "backup plan", "alternative plan"]),
                ("resource", "cold-storage", "RESOURCE", ["cold storage", "refrigeration", "refrigerated storage", "cold-chain equipment"]),
                ("permission", "road-permit", "PERMISSION", ["road permit", "delivery authorization", "delivery permission", "permission", "authorization"]),
                ("deadline", "delivery-deadline", "DEADLINE", ["delivery deadline"]),
            ],
            "deadline_frames": ["{SUBJECT} can meet the deadline", "{SUBJECT} can arrive before the deadline", "{SUBJECT} can arrive on time"],
            "deadline_negative": ["{SUBJECT} cannot meet the deadline", "{SUBJECT} cannot arrive before the deadline", "{SUBJECT} cannot arrive on time"],
        }
    elif domain == "deployment":
        definition = {
            "domain": ["deployment", "engineer", "production"],
            "entities": [
                ("proposed", "deployment-engineer", "PROPOSED", ["deployment engineer", "proposed engineer", "primary engineer", "proposed plan"]),
                ("backup", "backup-engineer", "BACKUP", ["backup engineer", "alternative engineer", "alternate engineer", "backup plan", "alternative plan"]),
                ("resource", "server-access", "RESOURCE", ["server access", "production access", "system access"]),
                ("permission", "production-approval", "PERMISSION", ["production approval", "deployment approval", "production permission", "approval", "authorization"]),
                ("deadline", "deployment-deadline", "DEADLINE", ["deployment deadline"]),
            ],
            "deadline_frames": ["{SUBJECT} can meet the deadline", "{SUBJECT} can finish before the deadline", "{SUBJECT} can complete on time"],
            "deadline_negative": ["{SUBJECT} cannot meet the deadline", "{SUBJECT} cannot finish before the deadline", "{SUBJECT} cannot complete on time"],
        }
    else:
        raise ValueError(f"unsupported domain: {domain}")
    frames = [
        {"template": "{SUBJECT} has {OBJECT}", "polarity": "POSITIVE"},
        {"template": "{SUBJECT} possesses {OBJECT}", "polarity": "POSITIVE"},
        {"template": "{SUBJECT} lacks {OBJECT}", "polarity": "NEGATIVE"},
        {"template": "{SUBJECT} does not have {OBJECT}", "polarity": "NEGATIVE"},
        {"template": "{SUBJECT} has no {OBJECT}", "polarity": "NEGATIVE"},
        {"template": "{SUBJECT} is without {OBJECT}", "polarity": "NEGATIVE"},
        {"template": "{SUBJECT} is unavailable to {OBJECT}", "polarity": "NEGATIVE"},
        {"template": "{SUBJECT} is authorized", "polarity": "POSITIVE", "object": "permission"},
        {"template": "{SUBJECT} has authorization", "polarity": "POSITIVE", "object": "permission"},
        {"template": "{SUBJECT} is not authorized", "polarity": "NEGATIVE", "object": "permission"},
        {"template": "{SUBJECT} lacks authorization", "polarity": "NEGATIVE", "object": "permission"},
    ]
    frames += [
        {"template": value, "polarity": "POSITIVE", "object": "deadline"}
        for value in definition["deadline_frames"]
    ]
    frames += [
        {"template": value, "polarity": "NEGATIVE", "object": "deadline"}
        for value in definition["deadline_negative"]
    ]
    projections = []
    for subject_role, prefix in (("PROPOSED", "proposed"), ("BACKUP", "backup")):
        for object_role, suffix in (
            ("RESOURCE", "resource"),
            ("PERMISSION", "permission"),
            ("DEADLINE", "deadline"),
        ):
            projections.append(
                {
                    "subject_role": subject_role,
                    "predicate": "satisfies",
                    "object_role": object_role,
                    "field": f"{prefix}-{suffix}",
                    "positive_value": "yes",
                    "negative_value": "no",
                }
            )
    return {
        "schema": "moth-semantic-contract/5.0",
        "language": "en",
        "domain": {"id": domain, "surfaces": definition["domain"]},
        "entities": [
            {"key": key, "entity": entity, "role": role, "surfaces": surfaces}
            for key, entity, role, surfaces in definition["entities"]
        ],
        "predicates": [
            {
                "id": "satisfies",
                "relation": "satisfies",
                "subject_roles": ["PROPOSED", "BACKUP"],
                "object_roles": ["RESOURCE", "PERMISSION", "DEADLINE"],
                "frames": frames,
            }
        ],
        "pronouns": {"surfaces": ["it"], "policy": "MOST_RECENT_UNAMBIGUOUS"},
        "intents": [
            {
                "id": "validate-and-select",
                "surfaces": [
                    "validate the proposed plan and select a replacement",
                    "can the proposed plan be used and which plan should replace it",
                    "review the proposed option and choose a replacement",
                    "is the proposed plan valid and what should we use instead",
                ],
                "instruction": "factor-settle",
                "slots": {"PROGRAM": "validate-and-select", "SCHEMA": "answer-json"},
                "projections": projections,
            }
        ],
        "transformations": ["external-paraphrase", "internal-relation-form"],
    }


def semantic_source(*domains: str) -> str:
    rows = [decision_source()]
    for domain in domains:
        rows.append(
            f'Semantic contract "{domain}-en" is canonical semantic JSON {_quoted(semantic_contract(domain))}.'
        )
    return "\n".join(rows) + "\n"

