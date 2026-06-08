# Buddy Game Studio

Buddy Game Studio turns VS Code into a lightweight development cockpit for Godot or Unity projects while keeping the game engine as the runtime/editor source of truth.

This is intentionally conservative: it writes reviewable VS Code workspace files, indexes project structure, and surfaces diagnostics. It does **not** auto-launch Godot, Unity, shell commands, external agents, build uploads, or account-connected services.

## Why this exists

Game engines are great at scenes, inspectors, animation, prefabs, tilemaps, imports, exports, and play mode. VS Code is great at code, Git, docs, tasks, search, debugging, and agent-assisted review.

Buddy Game Studio connects those strengths without pretending VS Code should replace the engine.

## Commands

```bash
buddy game-studio doctor [project-path]
buddy game-studio detect [project-path]
buddy game-studio init [project-path] [auto|godot|unity]
buddy game-studio index [project-path]
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

The index ignores engine caches and generated folders such as `.godot`, `Library`, `Temp`, `Obj`, `Build`, `Logs`, `.vscode`, `node_modules`, and `.git`.

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

Prefer small changes:

1. index project
2. ask for a specific edit plan
3. edit scripts or docs first
4. only modify scenes/prefabs with explicit review
5. run engine smoke tests manually or through VS Code tasks

## Future extensions

Good next slices:

- `buddy game-studio prompt` to create a safe edit brief from the project index
- Godot scene template generation
- Unity assembly/test layout helpers
- pixel sprite state manifest generation
- PR-ready game change receipts
- optional integration with Buddy worker/orchestrator sessions
