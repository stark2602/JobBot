# .cursor/rules

Drop this `rules/` folder into `.cursor/rules/` at the root of your repo.
Cursor automatically loads every `.mdc` file here as project rules.

## Files

| File | Scope | Always applied? |
|---|---|---|
| `000-general.mdc` | Repo-wide engineering standards, layout, style | Yes |
| `100-agent-core.mdc` | Building the agent runtime (planner/executor/memory/guardrails) | Only when editing `src/agent/**` |
| `110-agent-skills.mdc` | Skill/plugin contract for specialized capabilities | Only when editing `src/skills/**` |
| `120-agent-safety.mdc` | Guardrails, prompt-injection defense, least privilege | Only when editing `src/agent/**` or `src/skills/**` |
| `200-testing.mdc` | Unit/integration/e2e + agent behavior eval harness | Yes |
| `300-devops.mdc` | CI/CD, containers, environments, observability, release | Only when editing `infra/**` or CI configs |
| `400-security.mdc` | Secrets, dependency, and infra security | Yes |

## How the frontmatter works

- `alwaysApply: true` → rule is injected into every Cursor chat/edit in this
  repo, regardless of which file you're touching.
- `globs:` → rule is auto-attached only when you're working on a matching
  file path (Cursor scopes it for you — no manual toggling needed).
- `description:` → shown to Cursor and to you in the rules picker; keep it
  a one-line, precise summary — this is what makes rules discoverable.

## Adapting this to your stack

These rules assume:
- Python **or** TypeScript/Node (both style sections are included — delete
  whichever you don't use in `000-general.mdc`).
- Docker + docker-compose for local/integration environments.
- A CI system with job-based stages (GitHub Actions assumed; swap paths in
  `300-devops.mdc`'s frontmatter `globs` if you use GitLab CI/CircleCI).
- No specific agent framework — the rules describe a from-scratch runtime
  (planner/executor/memory/guardrails) so they apply whether you're using
  the Anthropic API directly, OpenAI, or a local model.

## Suggested next steps

1. Scaffold `/src/agent`, `/src/skills`, `/src/tools`, `/src/eval`,
   `/src/observability` per `000-general.mdc`'s layout.
2. Implement the five core components in `100-agent-core.mdc` before
   writing any skill.
3. Write your first skill following `110-agent-skills.mdc`'s manifest
   contract, with its eval dataset from day one (`200-testing.mdc`).
4. Stand up the CI pipeline stages in `300-devops.mdc` early — even a
   skeleton pipeline that just runs lint+unit tests catches drift immediately.
