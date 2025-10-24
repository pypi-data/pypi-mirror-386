[ \]; exec /usr/bin/env uv run -q claudebook run $0 "$@"; ]: #

```yaml
mcp:
  github:
    command: uv run --quiet examples/_support/github.py
  buildkite:
    command: uv run --quiet examples/_support/buildkite.py
```

# Diagnose PR failure

## 1. Get the context URLs

Use the GitHub MCP tools to get the failing context information.

Note there might be more than one failing context!

## 2. Get the logs

For each URL, use the Buildkite MCP to get the logs.
Find the relevant failure information (you may want to use agents for this).

## 3. Analyze the logs

Analyze the logs to understand the failure.

Report to the user.
