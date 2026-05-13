# iBeMore Companion Spec

Buddy should become a persistent companion layer, not only a chat page. The user can keep Buddy visible as a small animated pet, open chat from it, and use Buddy as a friendly helper across supported surfaces.

## Product intent

The phone, desktop, website, or HUD is the environment. Buddy is the animated friend that lives inside that environment.

## Surfaces

| Surface | Purpose |
| --- | --- |
| Desktop companion | Small floating Buddy pet window. |
| Chat drawer | Opens when the user clicks or taps Buddy. |
| Conversation mode | Optional live conversation experience. |
| Browser bridge | Approved website context bridge. |
| iBeMore iOS app | Buddy home, chat, care, training, widgets, and shortcuts. |
| App widgets | Lightweight Buddy status and quick entries. |

## Architecture

```text
Buddy companion shell
  Buddy renderer
  chat drawer
  conversation status
  consent prompts

Surface bridges
  desktop bridge
  browser bridge
  iOS bridge
  widget bridge

Buddy Agent runtime
  model router
  tools
  memory
  app bridge
  policy
  event log
```

## Buddy states

Companion states:

- idle
- listening
- thinking
- watching
- acting
- happy
- sleepy
- needs_attention

The default Buddy template guarantees the base render states:

- idle
- happy
- thinking
- sleepy

## First demo target

A first companion demo should prove:

1. Buddy appears as a floating pet window.
2. Clicking Buddy opens chat.
3. `buddy generate` creates a render-safe default Buddy template.
4. The renderer can switch between idle, happy, thinking, and sleepy.
5. Extra context bridges require user consent.

## Implementation phases

### Phase 1: Floating shell

Add the desktop companion window, Buddy sprite renderer, click-to-chat behavior, and local template loading.

### Phase 2: Conversation mode

Add push-to-talk first, then optional live conversation mode.

### Phase 3: Context bridges

Add approved context bridges for desktop, browser, and iOS handoff flows.

### Phase 4: iBeMore

Add iOS Buddy home, care, training, chat, conversation mode, widgets, shortcuts, and appearance sync.

### Phase 5: Approved helper actions

Add allowlisted helpers with clear confirmation and event logs.
