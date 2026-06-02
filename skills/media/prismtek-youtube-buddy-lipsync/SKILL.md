---
name: prismtek-youtube-buddy-lipsync
description: Produce a Prismtek/Buddy talking-host overlay for narrated videos using pixel-art visemes and FFmpeg audio RMS animation.
version: 1.1.0
author: Prismtek
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [youtube, video, ffmpeg, imagemagick, pixel-art, vtuber, buddy, prismtek]
    related_skills: [youtube-content, media-rendering, buddy-appearance]
    safety:
      stores_credentials: false
      uploads_to_youtube: false
      commits_media_assets: false
---

# Prismtek YouTube Buddy Lip-Sync

## Overview

This skill turns a clean Buddy host PNG into a lightweight audio-reactive talking-host overlay for Prismtek/Buddy videos.

It is intentionally boring in the best way:

- no ML lip-sync dependency;
- no face-swap, cloning, impersonation, or deepfake pipeline;
- no YouTube upload automation;
- no OAuth tokens, cookies, videos, receipts, or private assets committed;
- ImageMagick for deterministic pixel-art mouth/viseme generation;
- FFmpeg/ffprobe for audio RMS analysis and video compositing;
- JSON receipts for repeatable render review.

## When to Use

Use this when:

- a Prismtek/Buddy video has narration and Buddy should visibly speak;
- a static Buddy overlay feels too lifeless;
- you need proof clips before full rendering;
- you need a reproducible pixel-art mouth workflow that avoids visual regressions.

Do **not** use this for deceptive impersonation, face-swapping a real person, or uploading to accounts without explicit operator approval.

## Required Tools

```bash
command -v magick
command -v ffmpeg
command -v ffprobe
python3 --version
```

The scripts intentionally avoid PIL/Pillow so the workflow works in small runtimes.

## Recommended Asset Layout

Keep production assets outside git:

```text
~/.hermes/assets/prismtek-youtube/avatar/buddy-host-main-clean.png
~/.hermes/outputs/prismtek-youtube/
```

The checked-in skill stores the reusable workflow only. Generated PNGs, rendered MP4s, receipts, and source videos should stay in local output folders or private artifact storage.

## Generate Buddy Visemes

```bash
python3 scripts/generate_buddy_v12_visemes.py \
  ~/.hermes/assets/prismtek-youtube/avatar/buddy-host-main-clean.png \
  --out-dir ~/.hermes/assets/prismtek-youtube/avatar
```

Outputs:

```text
buddy-host-main-v12-no-mouth-base.png
buddy-host-main-v12-mouth-closed.png
buddy-host-main-v12-mouth-small-open.png
buddy-host-main-v12-mouth-wide-open.png
buddy-host-main-v12-mouth-round-o.png
buddy-host-main-v12-mouth-soft.png
```

## Render a Proof Clip

```bash
python3 scripts/prismtek_youtube_avatar_lipsync.py \
  /path/to/base-video.mp4 \
  --closed ~/.hermes/assets/prismtek-youtube/avatar/buddy-host-main-v12-mouth-closed.png \
  --open ~/.hermes/assets/prismtek-youtube/avatar/buddy-host-main-v12-mouth-small-open.png \
  --output /tmp/buddy-lipsync-proof.mp4 \
  --limit-seconds 20
```

For full render, omit `--limit-seconds`.

## v12 Mouth Style Rules

Accepted style:

- small/cute pixel-art mouth;
- slightly larger than the first tiny-mouth attempt;
- one visible mouth only;
- no darker mint rectangle around the mouth;
- no original-smile leftovers creating a second mouth;
- full Buddy crop remains intact.

Rejected styles:

- oversized oval or Pac-Man mouth;
- darker mint erase patch;
- two-mouth artifacts from leftover smile pixels;
- cropped arms, source-sheet borders, or sparkles.

## Verification Checklist

Before publishing, render a proof clip and inspect frames around speech and silence:

```bash
ffmpeg -y -v error -ss 00:00:05 -i /tmp/buddy-lipsync-proof.mp4 -frames:v 1 /tmp/buddy-open.png
ffmpeg -y -v error -ss 00:00:10 -i /tmp/buddy-lipsync-proof.mp4 -frames:v 1 /tmp/buddy-closed.png
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,codec_name,width,height -of compact=p=0:nk=1 /tmp/buddy-lipsync-proof.mp4
```

Visual QA:

- Buddy has one mouth only;
- mouth opens/closes with narration energy;
- no darker face patch appears around the mouth;
- Buddy remains fully visible in the chosen overlay position;
- output duration and audio stream are preserved;
- receipt JSON exists next to the output.

## Repository Ownership

- `buddy-agent`: runtime-facing skill copy.
- `buddy-brain`: operator/source-of-truth skill copy.
- `omni-buddy`: local device/voice host skill copy.
- `prismtek-apps`: app-facing documentation and future UI contract reference.
- `knowledge-vault`: durable skill reference and operating notes.
- `hermes-agent` fork/upstream PR: optional Hermes-compatible media skill.

## Safety Notes

This skill does not perform account login, upload to YouTube, scrape private sessions, or commit private media. Keep secrets in environment variables or a secret manager, and keep generated media out of public git history.
