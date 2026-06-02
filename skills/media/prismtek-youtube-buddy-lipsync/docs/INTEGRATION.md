# Integration Notes

This package is shared across the Prismtek/Buddy ecosystem without moving ownership away from the correct repo.

## Ownership Map

| Repo | Role |
| --- | --- |
| `buddy-agent` | Runtime-facing skill copy that Buddy can invoke locally. |
| `buddy-brain` | Operator/source-of-truth skill copy and policy reference. |
| `omni-buddy` | Local device/voice host copy for embodied Buddy experiments. |
| `prismtek-apps` | App-facing documentation and future UI contract reference. |
| `knowledge-vault` | Durable operating note and long-term skill archive. |
| `hermes-agent` | Hermes-compatible optional skill contribution. |

## Runtime Boundary

The skill renders local media only. It does not manage external accounts or commit generated media.

A product UI may wrap this workflow later, but it should preserve these boundaries:

1. user selects or imports a Buddy avatar;
2. user selects a source video/audio file;
3. runtime renders a proof clip;
4. user reviews visual QA;
5. release/distribution remains a separate explicit operator step.

## Expected Commands

From this skill directory:

```bash
python3 -m py_compile scripts/*.py
python3 -m pytest tests/test_prismtek_youtube_buddy_lipsync.py
```

Optional full tool check:

```bash
command -v magick
command -v ffmpeg
command -v ffprobe
```

## Generated Files

Do not commit generated render artifacts:

```text
*.mp4
*.mov
*.wav
*.aac
*.lipsync-receipt.json
buddy-host-main-v12-*.png
```

Generated files should stay under local output folders or private artifact storage.
