#!/usr/bin/env python3
"""生成分析用代码清单：gt6ce、golden、history、extra 与 auxiliary。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as c  # noqa: E402

INPUTS = c.ROOT / "inputs"
MANIFEST = INPUTS / "code_manifest.json"


def slug(ref: str) -> str:
    return ref.replace("/", "_").replace(" ", "_")


def files_for(root: Path) -> list[str]:
    if not root.exists():
        return []
    if root.is_file():
        return [root.name]
    if (root / ".git").exists():
        try:
            result = subprocess.run(
                ["git", "-C", str(root), "ls-files"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return sorted(line for line in result.stdout.splitlines() if line)
        except Exception:
            pass
    return sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )


def section(root: Path, ref: str, base: Path) -> dict:
    try:
        relative = str(root.relative_to(base)).replace("\\", "/")
    except ValueError:
        relative = str(root)
    return {"root": relative, "ref": ref, "files": files_for(root)}


def build_manifest(root: Path, snapshot: dict, repo_cfg: dict) -> dict:
    code = root / "code"
    primary = str(snapshot.get("code_ref") or "master")
    raw_refs = snapshot.get("code_refs") or [primary]
    if isinstance(raw_refs, str):
        raw_refs = raw_refs.split()
    refs = [str(item) for item in raw_refs]
    version_tag = str(snapshot.get("version_tag") or "")
    manifest = {
        "gt6ce": section(code / "current", primary, root),
        "golden": None,
        "history": [],
        "extra": [],
        "auxiliary": [],
    }
    golden = code / "golden"
    if golden.exists():
        golden_cfg = snapshot.get("golden") or {}
        manifest["golden"] = section(golden, str(golden_cfg.get("commit") or ""), root)
    for ref in refs:
        if ref == primary:
            continue
        path = code / slug(ref)
        if not path.exists():
            continue
        item = section(path, ref, root)
        if ref == version_tag:
            manifest["history"].append(item)
        else:
            manifest["extra"].append(item)
    for item in repo_cfg.get("auxiliary_materials") or []:
        path = root / str(item)
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        if path.exists():
            manifest["auxiliary"].append(section(path, str(item), root))
    return manifest


def main() -> None:
    snapshot_path = INPUTS / "snapshot.json"
    snapshot = {}
    if snapshot_path.exists():
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    repo = os.environ.get("REPO", "")
    repo_cfg = c.load_repo(repo) if repo else {}
    manifest = build_manifest(c.ROOT, snapshot, repo_cfg)
    c.dump_json(MANIFEST, manifest)
    print(
        json.dumps(
            {
                "manifest": "inputs/code_manifest.json",
                "gt6ce": len(manifest["gt6ce"]["files"]),
                "golden": len(manifest["golden"]["files"]) if manifest["golden"] else 0,
                "history": [len(item["files"]) for item in manifest["history"]],
                "extra": [len(item["files"]) for item in manifest["extra"]],
                "auxiliary": [len(item["files"]) for item in manifest["auxiliary"]],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
