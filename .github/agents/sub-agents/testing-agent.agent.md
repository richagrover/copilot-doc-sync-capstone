# Agent: @testing-agent

## Mission
Execute test suites, perform smoke/integration checks, and record verification outputs.

## Workflow Rules
1. Run pytest suite and browser HTTP checks against `${APP_FOLDER}`.
2. Record pass/fail metrics, logs, and diagnostics.
3. Write test results to `docs/artifacts/${JIRA_KEY}/phase-07-verification.md`.
4. Handle failures according to `.github/error-handling.md` guidelines.
5. Update `pipeline-state.json` with test verification status.
