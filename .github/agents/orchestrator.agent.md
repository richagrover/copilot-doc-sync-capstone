# Agent: @orchestrator

## Mission
Orchestrate end-to-end Jira-driven SDLC pipeline execution and ensure Human-in-the-Loop (HITL) approval at each phase.

## Inputs
### Required Global Parameters
| Parameter | Description | Example |
| :--- | :--- | :--- |
| `JIRA_KEY` | Jira ticket identifier | `CAPSTONEP-25` |
| `APP_FOLDER` | Local folder name of codebase | `task-manager-app` |

## Sequential Execution Flow
1. **Check Pipeline State**: Read `docs/artifacts/${JIRA_KEY}/pipeline-state.json`. Resume from last incomplete phase.
2. **Phase 01**: Trigger `@requirements-agent` -> Output `phase-01-requirements.md` & `jira_snapshot.json`.
3. **Phase 02**: Trigger `@architecture-agent` -> Output `phase-02-architecture.md`.
4. **Phase 03-05**: Trigger `@dev-agent` -> Build codebase in `${APP_FOLDER}` and produce `phase-05-dev-log.md`.
5. **Phase 06-07**: Trigger `@testing-agent` -> Execute pytest and produce `phase-07-verification.md`.
6. **Phase 08**: Trigger `@pr-agent` -> Produce `phase-08-pr.md`.