# Buddy Reference Images

This folder tracks the visual reference set used for Buddy Agent's app icon, default Buddy, pixel/ascii mode, and Buddy Generate template direction.

The original files were provided in chat and are tracked here by role, intended use, and SHA-256 checksum so the asset set can be reproduced and audited. The GitHub connector used in this session supports reliable UTF-8 text/SVG writes, but not direct raw JPEG binary upload through the contents API. For now, the canonical repo assets are SVG/vector/template files and this manifest records the original JPEG references exactly.

## Reference set

| ID | Role | Intended repo use | Original filename | SHA-256 |
| --- | --- | --- | --- | --- |
| `ref-01` | Color + ASCII state sheet | Pixel/ascii parity and state layout | `E9FDD9E3-DA5C-409D-A592-61D358B48656.jpeg` | `b76c8640ad8cf1234d5b72b946300eeb0b385a6a9d2c798b5bb21b63aaa3cbd6` |
| `ref-02` | Buddy Generate template | Canonical template layout and generator UX | `060A58D8-6D88-4122-9EB5-E274B9D7D1D8.jpeg` | `2aa9ae7dbdfba9bfeb76a6d0f599e3ef1990c48b5fa48086f43c8ca929e3b37c` |
| `ref-03` | Default Buddy spec | Pixel/ascii selectable appearance spec | `9677D5CC-F99A-4B72-8129-424A1742BB27.jpeg` | `c49e301df4ee966c6339e7f916440cd5f37a6d333236d70b5a64af45d650b36d` |
| `ref-04` | App icon device mark | App icon only; not the in-app Buddy creature | `CC5DD62E-7D09-41A8-A43D-0FE28974DB3D.jpeg` | `3e6ca7b010645e0efd939de5590941392e3563524f858d4cd07be9f1dbb1647a` |
| `ref-05` | Default Buddy state sheet | Default Buddy animation and emotion reference | `DD2D2976-46A1-46BD-BCA6-43386ABE6BCA.jpeg` | `2ff84444d68c827b2f0b54630aac899fd1070722b4300aef0ddff21be81afa9e` |

## Canonical implemented assets

| Purpose | Repo asset |
| --- | --- |
| README animated mascot | `assets/buddy-agent-mascot.svg` |
| App icon | `assets/buddy-app-icon.svg` |
| Default Buddy | `assets/default-buddy.svg` |
| Default Buddy template | `templates/default-buddy/buddy.json` |
| Default ASCII metadata | `templates/default-buddy/ascii_frames.json` |

## Asset rules

- The app icon may use the pocket-pet device direction.
- The in-app Buddy should be the tama-like creature direction, not the device.
- Generated buddies must keep a `64x64` canvas, centered placement, equal padding, and four base states: `idle`, `happy`, `thinking`, and `sleepy`.
- Generated buddies must support both `pixel` and `ascii` modes.
