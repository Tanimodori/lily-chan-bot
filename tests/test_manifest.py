import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import manifest  # noqa: E402


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._write("code/current/core/Foo.java", "class Foo {}")
        self._write("code/current/docs/decisions/parity/README.md", "parity")
        self._write("code/golden/src/Bar.java", "class Bar {}")
        self._write("code/v1.0.4/core/Old.java", "class Old {}")
        self._write("code/extra-branch/README.md", "extra")
        self._write("materials/parity/README.md", "aux")

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_build_manifest_sections(self):
        snapshot = {
            "code_ref": "master",
            "code_refs": ["master", "v1.0.4", "extra-branch"],
            "version_tag": "v1.0.4",
            "golden": {"commit": "abc123"},
        }
        repo_cfg = {"auxiliary_materials": ["materials/parity"]}
        data = manifest.build_manifest(self.root, snapshot, repo_cfg)

        self.assertEqual(data["gt6ce"]["root"], "code/current")
        self.assertEqual(data["gt6ce"]["ref"], "master")
        self.assertIn("core/Foo.java", data["gt6ce"]["files"])
        self.assertIn("docs/decisions/parity/README.md", data["gt6ce"]["files"])

        self.assertEqual(data["golden"]["root"], "code/golden")
        self.assertEqual(data["golden"]["ref"], "abc123")
        self.assertIn("src/Bar.java", data["golden"]["files"])

        self.assertEqual([item["ref"] for item in data["history"]], ["v1.0.4"])
        self.assertIn("core/Old.java", data["history"][0]["files"])

        self.assertEqual([item["ref"] for item in data["extra"]], ["extra-branch"])
        self.assertIn("README.md", data["extra"][0]["files"])

        self.assertEqual(len(data["auxiliary"]), 1)
        self.assertEqual(data["auxiliary"][0]["root"], "materials/parity")
        self.assertIn("README.md", data["auxiliary"][0]["files"])

    def test_missing_golden_is_none(self):
        shutil.rmtree(self.root / "code/golden")
        data = manifest.build_manifest(
            self.root,
            {"code_ref": "master", "code_refs": ["master"]},
            {},
        )
        self.assertIsNone(data["golden"])

    def test_missing_refs_are_skipped(self):
        data = manifest.build_manifest(
            self.root,
            {"code_ref": "master", "code_refs": ["master", "missing"], "version_tag": "missing"},
            {},
        )
        self.assertEqual(data["history"], [])
        self.assertEqual(data["extra"], [])

    def test_files_for_skips_git_directory(self):
        self._write("code/current/.git/HEAD", "ref")
        files = manifest.files_for(self.root / "code/current")
        self.assertNotIn(".git/HEAD", files)
        self.assertIn("core/Foo.java", files)

    def test_files_for_uses_git_ls_files(self):
        repo = self.root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "tracked.txt").write_text("tracked", encoding="utf-8")
        (repo / "untracked.txt").write_text("untracked", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
        subprocess.run(
            [
                "git", "-C", str(repo),
                "-c", "user.name=test", "-c", "user.email=test@example.test",
                "commit", "-q", "-m", "init",
            ],
            check=True,
        )
        files = manifest.files_for(repo)
        self.assertIn("tracked.txt", files)
        self.assertNotIn("untracked.txt", files)

    def test_slug(self):
        self.assertEqual(manifest.slug("release/1.0"), "release_1.0")


if __name__ == "__main__":
    unittest.main()
