# GitHub setup

Recommended repository name:

```text
llm-evalops-lab
```

## Create and push with GitHub CLI

From the project directory:

```bash
git init
git add .
git commit -m "Initial LLM EvalOps lab"
gh repo create llm-evalops-lab --private --source=. --remote=origin --push
```

Use `--public` instead of `--private` if you want an open source repository.

## Repository secrets

For real OpenAI runs in GitHub Actions, add repository secrets:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`

The included CI workflow does not require those secrets because it uses deterministic tests only.

## Branch protection recommendation

Require the `ci` workflow to pass before merge to `main`.
