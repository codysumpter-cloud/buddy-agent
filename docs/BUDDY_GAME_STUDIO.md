# Buddy Game Studio

Buddy Game Studio turns VS Code into a lightweight development cockpit for Godot or Unity projects while keeping the game engine as the runtime/editor source of truth.

This is intentionally conservative: it writes reviewable VS Code workspace files, indexes project structure, and surfaces diagnostics. It does **not** auto-launch Godot, Unity, shell commands, external agents, build uploads, or account-connected services.

## Why this exists

Game engines are great at scenes, inspectors, animation, prefabs, tilemaps, imports, exports, and play mode. VS Code is great at code, Git, docs, tasks, search, debugging, and agent-assisted review.

Buddy Game Studio connects those strengths without pretending VS Code should replace the engine.

## Reference app patterns

Buddy Game Studio follows the useful parts of agentic game-builder apps without copying their whole stack.

- **BloxBot pattern**: a desktop UI talks to an agent sidecar, and the agent reaches the creative tool through a structured MCP-style bridge. That is the right shape for Godot, Unity, browser, file, art, calendar, and message adapters.
- **Stud pattern**: a UI talks to a local bridge, the bridge queues tool work, and the creative app reports results back. That is the right shape for live feedback, undo-aware edits, and user-visible progress.

Buddy's first implementation in this PR is not a replacement for existing Buddy browser, automation, iOS, or workspace runtime work. It is the safer local contract underneath those surfaces: manifests, drafts, receipts, reviewable files, and explicit approval boundaries that existing and future adapters can plug into.

## Existing browser and workspace surfaces

Browser/workspace work is **not** greenfield. The relevant surface area already spans multiple repos:

### `codysumpter-cloud/buddy-agent`

- `docs/BUDDY_FEATURE_PARITY.md` tracks Browser/web tooling as part of the parity surface.
- `skills/native/hermes-bookmark-research-digest/` handles approved, read-only browser/API research digests.
- `skills/native/signed-in-safari-social-automation/` documents explicit-approval, signed-in Safari workflows on macOS.

### `codysumpter-cloud/buddy-brain`

- `docs/BROWSER_AUTOMATION_PROFILE.md` defines browser automation as an opt-in, isolated delegated profile, not the default chat path.
- `skills/browser-automation/README.md` tells operators when browser/UI automation is appropriate and keeps it scoped.
- `skills/workspace-dispatch/SKILL.md` defines a mission orchestration loop with independent worker tasks, machine-checkable exit criteria, retries, and reporting.
- `docs/UNIFIED_OPERATOR_APP.md` maps browser-first surfaces, workstation-first surfaces, and shared companion surfaces so the user can move from browser planning to local execution without guessing ownership.

### `codysumpter-cloud/prismtek-apps`

- `apps/bemore-ios-native/BeMoreAgentShell/Views/BuddyAgentBrowserView.swift` already implements the guarded in-app Agent Browser using `WKWebView`, Buddy/Lil' Buddy Orchestrator/Worker UI, tool chips, approval cards, and a receipt timeline.
- `apps/bemore-ios-native/BeMoreAgentShell/WebBrowserService.swift` provides a Safari-backed browser open path through `SFSafariViewController`.
- `apps/bemore-ios-native/BeMoreAgentShell/BeMoreWorkspaceRuntime.swift` already models action receipts, artifacts, built-in Web Browser/GitHub Search capabilities, workspace reads/writes, skill installs, sandbox-style commands, and `.bemore` artifact persistence.
- `docs/BUDDY_ACTION_LOOP_V1.md` defines the guarded Agent Browser MVP, minimum two-agent Orchestrator/Worker loop, safe browser/draft actions, approval risk classes, receipts, and the future bridge to `buddy-agent` endpoints.
- `docs/BUDDY_CAPABILITY_SURFACES.md` defines product ownership for Buddy Workshop, installed skills/apps, config forms, receipt/artifact rendering, and product adapters calling the shared Buddy Runtime.

The playground's browser folder is therefore a **receipt/draft bridge** for existing agent-browser work, not a claim that browser automation still needs to be invented. Existing agent-browser/browser skills should write notes, plans, artifacts, and secret-free receipts here when running through Buddy Game Studio.

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

Use the two workspaces this way:

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
- `Buddy: Initialize Playground`
- `Buddy: Playground Status`
- `Buddy: Draft Code Task`
- `Buddy: Draft Art Request`

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
- `Buddy: Initialize Playground`
- `Buddy: Playground Status`
- `Buddy: Draft Code Task`
- `Buddy: Draft Art Request`

Set `UNITY_EDITOR` before running Unity tasks:

```bash
export UNITY_EDITOR="/Applications/Unity/Hub/Editor/<version>/Unity.app/Contents/MacOS/Unity"
```

## Adapter surfaces

The playground is designed to sit underneath richer app surfaces, including surfaces that already exist elsewhere in Buddy Brain, Prismtek Apps, and Buddy/Hermes skills:

| Surface | First safe behavior in this PR | Adapter integration behavior |
| --- | --- | --- |
| Browser / agent-browser | research notes, web-task plans, and receipts | existing browser adapters write secret-free receipts and use approval gates for account actions |
| Files | local generated files | project patch application with diffs or promotion into app-visible `.bemore` artifacts |
| Code | code tasks and snippets | sandboxed execution and test repair loop |
| Art | prompts and asset briefs | image generation job queue/gallery |
| Email | saved drafts | provider connector after approval |
| Messages | saved drafts | chat/SMS connector after approval |
| Calendar | saved event JSON | calendar connector after approval |
| Workspace dispatch | local task drafts and receipts | Buddy Brain worker orchestration with machine-checkable exit criteria |

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
