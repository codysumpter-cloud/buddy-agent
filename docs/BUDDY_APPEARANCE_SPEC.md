# Buddy Appearance Spec

Buddy Agent separates two visual roles:

1. **App icon**: the pocket-pet device mark used for repo/app branding.
2. **Default Buddy**: the actual pet-like animated companion that lives inside the app.

The phone, web app, HUD, or terminal is the device. A Buddy is the living companion inside that device.

## Default assets

| Role | Asset |
| --- | --- |
| GitHub README ASCII mascot | `assets/buddy-agent-mascot.svg` |
| App icon | `assets/buddy-app-icon.svg` |
| Default pixel Buddy | `assets/default-buddy.svg` |
| Default generated manifest | `templates/default-buddy/buddy.json` |
| Default ASCII frames | `templates/default-buddy/ascii_frames.json` |

## Canonical Default Buddy style

The default Buddy should match the attached mint pixel-pet reference:

- round mint/cyan body;
- deep navy pixel outline;
- heart-shaped antler/ear nubs;
- small top tuft;
- large soft face panel;
- tiny dot eyes with small highlights;
- small friendly smile;
- plus/blush cheek marks;
- tiny side arms;
- tiny rounded feet;
- gold heart belly charm;
- asymmetric cyan and white highlight clusters;
- transparent background for app/runtime assets.

The style should feel like a crisp Tamagotchi/Pokémon-inspired pixel companion. It should not look like a phone, screen, gamepad, robot monitor, generic app icon, or a 3D/painterly mascot.

## Required render modes

Every Buddy template must support:

- `pixel`
- `ascii`

The default README intentionally shows both because they serve different surfaces:

- **ASCII Buddy**: terminal/docs mascot, lightweight, animated state cycle.
- **Pixel Buddy**: app/game companion, sprite-friendly default avatar.

## Required animation states

Every Buddy template must define these states in this exact order:

1. `idle`
2. `happy`
3. `thinking`
4. `sleepy`

ASCII and pixel renderers should cycle through the same order:

```text
idle -> happy -> thinking -> sleepy -> repeat
```

Default timing:

| Setting | Value |
| --- | --- |
| Frame duration | `900ms` |
| Loop | `true` |
| Reduced motion | Show `idle` only |

## Required frame format

| Setting | Value |
| --- | --- |
| Canvas | `64x64` |
| Placement | centered |
| Padding | equal padding on all sides |
| Recommended raster export | indexed-color PNG |
| Background | transparent for app sprites |
| Outline | deep navy / high contrast |
| Edge style | crisp pixels, no blur/antialias-heavy rendering |

## Pixel rendering rules

Use crisp pixel clusters and a limited palette. Shading should be readable at small sizes and should not depend on smooth gradients.

Preferred palette roles:

| Role | Example |
| --- | --- |
| Outline | `#08165c` |
| Cyan shadow | `#56d6d2` |
| Mint body | `#8ee9df` |
| Face panel | `#cffff2` |
| Highlight | `#effff9` |
| Gold heart | `#ffd45e` |
| Warm heart shadow | `#f69c45` |
| Eye highlight | `#f8fbff` |

## Customization options

Generated Buddies should keep the same frame contract while allowing users to customize:

- palette
- heart antler ears
- tuft
- face panel
- belly heart charm
- accessory
- pose
- outline weight
- highlight pattern
- idle animation
- ASCII style

## Generator

```bash
buddy generate --output my-buddy
```

The command writes:

- `buddy.json`
- `ascii_frames.json`

The manifest records the asset roles, render modes, states, animation cycle, palette, traits, style reference, and frame rules needed by the app renderer.

## Guardrails

Generated Buddies should be pet-like companions, not device-shaped characters. Do not give generated Buddy creatures screen bodies, gamepad controls, a phone silhouette, or a silhouette that reads as an existing copyrighted character.
