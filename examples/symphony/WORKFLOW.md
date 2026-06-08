---
tracker:
  kind: local-json
  path: examples/symphony/issues.json
workspace:
  root: .buddy/workspaces
hooks:
  after_create: echo ready
agent:
  max_turns: 20
codex:
  command: codex app-server
---
Implement {{ issue.identifier }}: {{ issue.title }}.

Priority: {{ issue.priority }}

{{ issue.body }}
