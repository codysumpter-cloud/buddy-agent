"""Reference repository manifest for Buddy Agent integration work."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceRepo:
    """A repository used as a reference or integration source."""

    name: str
    repository: str
    role: str
    default_branch: str = "main"

    @property
    def clone_url(self) -> str:
        """Return the public HTTPS clone URL."""
        return f"https://github.com/{self.repository}.git"


REFERENCE_REPOS: tuple[ReferenceRepo, ...] = (
    ReferenceRepo("Hermes Agent", "NousResearch/hermes-agent", "upstream-runtime"),
    ReferenceRepo("Buddy Brain", "codysumpter-cloud/buddy-brain", "operator-layer", "master"),
    ReferenceRepo("Omni Buddy", "codysumpter-cloud/omni-buddy", "local-runtime"),
    ReferenceRepo("Prismtek Apps", "codysumpter-cloud/prismtek-apps", "product-app"),
    ReferenceRepo("Knowledge Vault", "codysumpter-cloud/knowledge-vault", "memory"),
    ReferenceRepo("Hermes Ecosystem", "codysumpter-cloud/hermes-ecosystem", "runtime"),
    ReferenceRepo("Awesome Hermes Agent", "codysumpter-cloud/awesome-hermes-agent", "discovery"),
    ReferenceRepo("Agent Memory", "codysumpter-cloud/agentmemory", "memory"),
    ReferenceRepo("Hermes Control Interface", "codysumpter-cloud/hermes-control-interface", "ui"),
    ReferenceRepo("Caveman", "codysumpter-cloud/caveman", "skills"),
    ReferenceRepo("Hermes Workspace", "codysumpter-cloud/hermes-workspace", "runtime"),
    ReferenceRepo("Arcade MCP", "codysumpter-cloud/arcade-mcp", "mcp"),
    ReferenceRepo("Hermes WebUI", "codysumpter-cloud/hermes-webui", "ui"),
    ReferenceRepo("Hermes HUDUI", "codysumpter-cloud/hermes-hudui", "ui"),
    ReferenceRepo("Gemma", "codysumpter-cloud/gemma", "models"),
    ReferenceRepo("Symphony", "codysumpter-cloud/symphony", "mythos"),
    ReferenceRepo("LibreSprite", "codysumpter-cloud/LibreSprite", "creative"),
    ReferenceRepo("Hermes Wiki", "codysumpter-cloud/Hermes-Wiki", "discovery"),
    ReferenceRepo("OpenMythos", "codysumpter-cloud/OpenMythos", "mythos"),
    ReferenceRepo("Tamagoscii", "codysumpter-cloud/tamagoscii", "creative"),
    ReferenceRepo("PixelLab MCP", "codysumpter-cloud/pixellab-mcp", "mcp"),
    ReferenceRepo("PixelLab JS", "codysumpter-cloud/pixellab-js", "creative"),
)


def repos_by_role(role: str) -> tuple[ReferenceRepo, ...]:
    """Return repositories for a role."""
    return tuple(repo for repo in REFERENCE_REPOS if repo.role == role)
