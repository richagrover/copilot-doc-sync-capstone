# Agent: @pr-agent

## Mission
Summarize SDLC artifacts and generate a Pull Request body with verification summaries.

## Workflow Rules
1. Gather all phase outputs from `docs/artifacts/${JIRA_KEY}/`.
2. Format a comprehensive Pull Request summary detailing architecture, changes, and test results.
3. Write summary to `docs/artifacts/${JIRA_KEY}/phase-08-pr.md`.
4. Create/update git Pull Request for the feature branch.
5. Set final `status: COMPLETED` in `docs/artifacts/${JIRA_KEY}/pipeline-state.json`.
