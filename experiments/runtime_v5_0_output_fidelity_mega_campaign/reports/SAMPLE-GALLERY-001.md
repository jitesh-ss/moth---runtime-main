# Sample gallery 001

All samples below realize the same Runtime decision: proposed invalid, backup
valid, select `BACKUP`, failure reason `RESOURCE`.

## Compact prose

Use the backup plan. The proposed plan is invalid, the backup plan is valid, and
the failure reason is resource.

## Detailed prose

Recommendation

Use the backup plan.

Assessment

The proposed plan is invalid. The backup plan is valid. The recorded failure
reason is resource.

Next step

Proceed with the backup plan after confirming execution readiness.

## Formal tone

The assessment concludes that the backup plan should be used: the proposed plan
is invalid, the backup plan is valid, and the recorded failure reason is
resource.

## Conversational tone

Go with the backup plan. The proposed plan is invalid, the backup plan is valid,
and the issue on record is resource.

## Markdown bullets

- Proposed plan: invalid
- Backup plan: valid
- Selection: BACKUP
- Failure reason: RESOURCE

## Markdown table

| Field | Value |
|---|---|
| Proposed plan | invalid |
| Backup plan | valid |
| Selection | BACKUP |
| Failure reason | RESOURCE |

## Explanation plus JSON

Use the backup plan; the complete verified decision follows.

```json
{
  "backup-valid": "true",
  "failure-reason": "RESOURCE",
  "proposed-valid": "false",
  "selected-plan": "BACKUP"
}
```

## Action plan

1. Record the proposed plan as invalid.
2. Record the backup plan as valid.
3. Record the failure reason as RESOURCE.
4. Select BACKUP for execution.
