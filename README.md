<p align="center">
  <img src="assets/buddy-agent-mascot.svg" alt="Buddy Agent animated ASCII mascot" width="280">
</p>

<h1 align="center">Buddy Agent</h1>

<p align="center"><strong>Native Buddy runtime for the Prismtek / Hermes ecosystem.</strong></p>

<p align="center">
  <a href="#ascii-buddy"><strong>ASCII Buddy</strong></a>
  &nbsp;•&nbsp;
  <a href="#pixel-buddy"><strong>Pixel Buddy</strong></a>
</p>

<details open id="ascii-buddy">
<summary><strong>View ASCII Buddy mascot</strong></summary>

<p align="center">
  <img src="assets/buddy-agent-mascot.svg" alt="Animated ASCII Buddy mascot" width="280">
</p>

</details>

<details id="pixel-buddy">
<summary><strong>View Pixel Buddy mascot</strong></summary>

<p align="center">
  <img src="assets/default-buddy.svg" alt="Default pixel Buddy mascot" width="220">
</p>

</details>

<p align="center">
  <img src="assets/badges/runtime.svg" alt="Runtime: runnable alpha"><br>
  <img src="assets/badges/version.svg" alt="Version: 0.1.0 alpha"><br>
  <img src="assets/badges/license.svg" alt="License: Prismtek Source Available">
</p>

<p align="center">
  <a href="https://github.com/codysumpter-cloud/buddy-agent/archive/refs/heads/main.zip"><img src="assets/badges/download.svg" alt="Download Source ZIP"></a><br>
  <a href="https://github.com/codysumpter-cloud/buddy-agent"><img src="assets/badges/repository.svg" alt="View Repository"></a><br>
  <a href="https://github.com/codysumpter-cloud/buddy-agent/issues"><img src="assets/badges/roadmap.svg" alt="View Roadmap"></a>
</p>

## Install

```bash
git clone https://github.com/codysumpter-cloud/buddy-agent.git
cd buddy-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
buddy doctor
buddy smoke
buddy alpha
```

## Alpha Runtime

```bash
buddy chat "hello buddy"
buddy remember "Buddy can keep local notes"
buddy recall "local"
buddy skill --skill caps "buddy alpha"
```

The Alpha Runtime wires local chat routing, persistent memory, built-in skills, Buddy template validation, and companion permission policy into one runnable path.

## Generate a Buddy

```bash
buddy generate --output my-buddy
```

Generated Buddies support pixel and ASCII render modes, idle/happy/thinking/sleepy states, and a centered 64x64 frame contract.

## Buddy Game Studio

Use VS Code as a dev cockpit for Godot or Unity while the game engine stays the source of truth for scenes, inspectors, prefabs, animation, imports, exports, and play mode.

```bash
buddy game-studio doctor ./my-game
buddy game-studio detect ./my-game
buddy game-studio init ./my-game godot
buddy game-studio init ./my-game unity
buddy game-studio index ./my-game
```

`buddy game-studio init` writes a reviewable `.vscode/` scaffold with recommended extensions, settings, tasks, launch config, and workspace notes. Existing files are skipped by default. `buddy game-studio index` creates compact JSON project context while ignoring engine caches such as `.godot`, `Library`, `Temp`, `Obj`, `Build`, `Logs`, `.vscode`, `node_modules`, and `.git`.

See [`docs/BUDDY_GAME_STUDIO.md`](docs/BUDDY_GAME_STUDIO.md) for the full workflow and guardrails.

## Version Tracker

| Track | Status |
| --- | --- |
| Runtime | <img src="assets/status-dot.svg" width="12" alt="online"> runnable alpha |
| Package | `0.1.0` alpha scaffold |
| CLI | `buddy` |
| Memory | persistent JSON-backed local memory |
| Appearance | pixel and ASCII Buddy modes |
| Companion | consent-first contracts started |
| iBeMore | typed app bridge contracts started |
| Game Studio | VS Code + Godot/Unity cockpit scaffold |

## Development

```bash
ruff check .
mypy src
pytest
buddy --help
buddy doctor
buddy smoke
buddy alpha
buddy generate --output my-buddy
buddy game-studio doctor .
buddy game-studio index .
```
