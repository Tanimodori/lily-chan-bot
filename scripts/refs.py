"""版本字段与历史 tag 解析。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as c  # noqa: E402


def version_base(body: str) -> str:
    version = c.form_field(body, "模组版本 / Mod version", "模组版本", "Mod version").strip()
    return version[1:] if version[:1].lower() == "v" else version


def version_candidates(base: str, repo_cfg: dict) -> list[str]:
    if not base or repo_cfg.get("code_ref_mode", "tag") != "tag":
        return []
    template = repo_cfg.get("tag_template", "v{version}")
    candidates: list[str] = []
    formatted = template.replace("{version}", base)
    if formatted:
        candidates.append(formatted)
    if base not in candidates:
        candidates.append(base)
    return candidates


def resolve_version_tag(base: str, tags: set[str] | None, repo_cfg: dict) -> str:
    if not tags:
        return ""
    for candidate in version_candidates(base, repo_cfg):
        if candidate in tags:
            return candidate
    return ""
