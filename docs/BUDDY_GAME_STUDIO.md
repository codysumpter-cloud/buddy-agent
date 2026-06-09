# Buddy Game Studio

Buddy Game Studio turns VS Code into a lightweight development cockpit for Godot or Unity projects while keeping the game engine as the runtime/editor source of truth.

This is intentionally conservative: it writes reviewable VS Code workspace files, indexes project structure, and surfaces diagnostics. It does **not** auto-launch Godot, Unity, shell commands, external agents, build uploads, or account-connected services.

## Why this exists

Game engines are great at scenes, inspectors, animation, prefabs, tilemaps, imports, exports, and play mode. VS Code is great at code, Git, docs, tasks, search, debugging, and agent-assisted review.

Buddy Game Studio connects those strengths without pretending VS Code should replace the engine.

## Existing browser and workspace surfaces

Browser/workspace work is **not** greenfield. The relevant surface area already spans multiple repos:

- `buddy-agent`: local runtime, app-chat seam, Game Studio, `.buddy/playground`, integrations, and product-spine validation.
- `buddy-brain`: browser automation policy, workspace dispatch, and operator ownership boundaries.
- `prismtek-apps`: guarded Agent Browser, `.bemore` workspace runtime, action receipts, artifacts, and product-facing capability surfaces.

The playground's browser folder is therefore a **receipt/draft bridge** for existing agent-browser work, not a claim that browser automation still needs to be invented.

## Commands

```bash
buddy game-studio doctor [project-path]
buddy game-studio detect [project-path]
buddy game-studio init [project-path] [auto|godot|unity]
buddy game-studio index [project-path]

buddy-workspace init [project-path]
buddy-workspace status [project-path]
buddy-workspace code-task [project-path] [title] [body]
buddy-workspace art-request [project-path] [title] [body]
buddy-workspace browser-note [project-path] [title] [body]
buddy-workspace draft-email [project-path] [title] [body]
buddy-workspace draft-message [project-path] [title] [body]
buddy-workspace draft-calendar [project-path] [title] [body]
buddy-workspace file-note [project-path] [title] [body]

buddy-product-spine summary
buddy-product-spine json
buddy-product-spine validate
```

### `doctor`

Inspects the project and local toolchain:

- detects Godot or Unity markers
- checks whether `godot`, `godot4`, or `UNITY_EDITOR` are available
- summarizes indexed file counts

```bash
buddy game-studio doctor ./my-game
```

### `detect`

Prints the detected engine:

```bash
buddy game-studio detect ./my-game
```

Detection uses local file markers only. It does not execute engine binaries.

### `init`

Writes a `.vscode/` scaffold for the selected engine:

```bash
buddy game-studio init ./my-godot-game godot
buddy game-studio init ./my-unity-game unity
buddy game-studio init ./my-game auto
```

Generated files:

- `.vscode/extensions.json`
- `.vscode/settings.json`
- `.vscode/tasks.json`
- `.vscode/launch.json`
- `.vscode/BUDDY_GAME_STUDIO.md`

Existing files are skipped by default, so the command is safe to run against an existing project.

### `index`

Builds a compact JSON project index for docs, review prompts, and guarded agent context:

```bash
buddy game-studio index ./my-game
```

The index ignores engine caches and generated folders such as `.buddy`, `.godot`, `Library`, `Temp`, `Obj`, `Build`, `Logs`, `.vscode`, `node_modules`, and `.git`.

## Buddy Playground workspace

`buddy-workspace init` creates `.buddy/playground/`, Buddy's local sandbox inside the project.

```text
.buddy/playground/
├── manifest.json
├── permissions.json
├── README.md
├── browser/research_notes/
├── art/requests/
├── code/tasks/
├── files/
├── outbox/email_drafts/
├── outbox/message_drafts/
├── outbox/calendar_drafts/
└── receipts/
```

Buddy can use this playground to:

- create local files
- draft code tasks
- store browser/agent-browser notes and receipts
- write image/art generation briefs
- draft emails, messages, and calendar events for review
- keep receipts and task context

The important split is **draft vs action**. Drafts are allowed locally. External side effects require an approved adapter and user confirmation.

## Relationship to `.bemore` workspace runtime

`prismtek-apps` already has the app-side `.bemore` runtime. This PR intentionally does **not** replace that runtime.

| Workspace | Owner | Purpose |
| --- | --- | --- |
| `.bemore/` | `prismtek-apps` app runtime | Canonical app artifacts, skills, receipts, memory/session state, and user-visible persisted runtime records. |
| `.buddy/playground/` | `buddy-agent` local/project workspace | Reviewable local drafts, game/project work items, browser receipts, art/code requests, and pre-adapter handoff notes. |

The bridge direction is: app/runtime receipts from `.bemore` can inform Buddy's local project context, and Buddy's `.buddy/playground` drafts can be promoted into app-visible artifacts only after an explicit adapter/approval step.

## Godot workflow

Use Godot for:

- scenes
- nodes
- inspectors
- animation
- tilemaps
- imports
- exports

Use VS Code for:

- GDScript or C# editing
- docs
- Git
- tasks
- project indexing
- guarded Buddy prompts
- Buddy Playground drafts and receipts

Generated tasks include:

- `Godot: Run Game`
- `Godot: Headless Smoke`
- `Buddy: Index Game Project`

## Unity workflow

Use Unity for:

- scenes
- prefabs
- inspectors
- animator
- play mode
- package/build settings

Use VS Code for:

- C# editing
- debugging
- docs
- Git
- EditMode tests
- project indexing
- guarded Buddy prompts
- Buddy Playground drafts and receipts

Generated tasks include:

- `Unity: EditMode Tests`
- `Unity: Open Project`
- `Buddy: Index Game Project`

Set `UNITY_EDITOR` before running Unity tasks:

```bash
export UNITY_EDITOR="/Applications/Unity/Hub/Editor/<version>/Unity.app/Contents/MacOS/Unity"
```

## Guardrails

Do not let automated tools rewrite imported/cache folders.

Review diffs carefully for:

- `.tscn`
- `.unity`
- prefab or scene metadata
- project settings
- generated imports
- `.buddy/playground/outbox/*` drafts before using external adapters
- `.buddy/playground/browser/*` receipts before treating browser work as verified
- cross-workspace promotion from `.buddy/playground` into `.bemore` app artifacts

Prefer small changes:

1. initialize playground
2. index project
3. draft a specific code/art/browser/message/calendar item
4. review the draft, receipt, or patch
5. apply only the approved change
6. promote approved work to `.bemore` or external adapters only through a receipt-backed path
7. run engine smoke tests manually or through VS Code tasks

## Next integration slices

Good next slices:

- `buddy workspace` alias inside the main CLI
- wire existing agent-browser/browser skills to write standardized playground receipts
- define a `.bemore` ↔ `.buddy/playground` promotion/export contract
- image generation job queue and gallery manifest
- Godot scene template generation
- Unity assembly/test layout helpers
- pixel sprite state manifest generation
- PR-ready game change receipts
- optional integration with Buddy Brain workspace-dispatch Orchestrator/Worker sessions
