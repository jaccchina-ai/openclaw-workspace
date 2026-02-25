# Feature Requests

User-requested capabilities and system improvements.

**Categories**: new_feature | enhancement | automation | integration | ui_improvement
**Areas**: frontend | backend | infra | tests | docs | config | data | external_api
**Statuses**: pending | in_progress | implemented | rejected | promoted

## Status Definitions

| Status | Meaning |
|--------|---------|
| `pending` | Not yet evaluated |
| `in_progress` | Being implemented |
| `implemented` | Feature completed |
| `rejected` | Decided not to implement (reason in Resolution) |
| `promoted` | Integrated into system documentation |

## Entry Format

```markdown
## [FEAT-YYYYMMDD-XXX] capability_name

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Requested Capability
What the user wanted to do

### User Context
Why they needed it, what problem they're solving

### Complexity Estimate
simple | medium | complex

### Suggested Implementation
How this could be built, what it might extend

### Metadata
- Frequency: first_time | recurring
- Related Features: existing_feature_name
- See Also: FEAT-20250110-001 (if related)

---

```

## ID Generation

Format: `FEAT-YYYYMMDD-XXX`
- `FEAT`: Feature request type
- `YYYYMMDD`: Current date
- `XXX`: Sequential number or random 3 chars (e.g., `001`, `A7B`)

## Resolution

When a feature request is addressed:

1. Change `**Status**: pending` → `**Status**: implemented` or `rejected`
2. Add resolution block:

```markdown
### Resolution
- **Status Changed**: ISO-8601 timestamp
- **Implemented/Rejected**: Date of decision
- **Notes**: Brief description of implementation or reason for rejection
- **Related Work**: PR #42, commit abc123 (if applicable)
```

## Promotion

When a feature request reveals a broader need:

1. **Promote to AGENTS.md**: If it suggests new automation or workflow
2. **Promote to TOOLS.md**: If it's about tool capabilities
3. **Update entry**: Change `**Status**: pending` → `**Status**: promoted`

---

