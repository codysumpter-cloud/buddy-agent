# Buddy Appearance Spec

Buddy Agent separates two visual roles:

1. **App icon**: the pocket-pet device mark used for repo/app branding.
2. **Default Buddy**: the actual pet-like animated companion that lives inside the app.

The phone, web app, HUD, or terminal is the device. A Buddy is the living companion inside that device.

## Default assets

| Role | Asset |
| --- | --- |
| GitHub README mascot | `assets/buddy-agent-mascot.svg` |
| App icon | `assets/buddy-app-icon.svg` |
| Default Buddy | `assets/default-buddy.svg` |

## Required render modes

Every Buddy template must support:

- `pixel`
- `ascii`

## Required animation states

Every Buddy template must define these states:

- `idle`
- `happy`
- `thinking`
- `sleepy`

## Required frame format

| Setting | Value |
| --- | --- |
| Canvas | `64x64` |
| Placement | centered |
| Padding | equal padding on all sides |
| Recommended raster export | indexed-color PNG |
| Background | transparent for app sprites |
| Outline | dark navy / high contrast |

## Customization options

Generated Buddies should keep the same frame contract while allowing users to customize:

- palette
- ears / antennae / silhouette accents
- top tuft
- face
- belly charm
- accessory
- idle animation
- ASCII style

## Generator

```bash
buddy generate --output my-buddy
```

The command writes:

- `buddy.json`
- `ascii_frames.json`

The manifest records the asset roles, render modes, states, palette, and frame rules needed by the app renderer.

## Guardrails

Generated Buddies should be pet-like companions, not device-shaped characters. Do not give generated Buddy creatures screen bodies, gamepad controls, or a silhouette that reads as an existing copyrighted character.
