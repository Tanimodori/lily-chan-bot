import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import refs  # noqa: E402


class VersionBaseTest(unittest.TestCase):
    def test_reads_mod_version_field(self):
        body = "### 模组版本 / Mod version\n\nv1.0.4\n\n### 描述\n\n..."
        self.assertEqual(refs.version_base(body), "1.0.4")

    def test_strips_uppercase_v(self):
        body = "### 模组版本 / Mod version\n\nV1.0.4\n"
        self.assertEqual(refs.version_base(body), "1.0.4")

    def test_missing_field_is_empty(self):
        self.assertEqual(refs.version_base("### 描述\n\n..."), "")


class VersionCandidatesTest(unittest.TestCase):
    cfg = {"code_ref_mode": "tag", "tag_template": "v{version}"}

    def test_primary_template_then_base(self):
        self.assertEqual(refs.version_candidates("1.0.4", self.cfg), ["v1.0.4", "1.0.4"])

    def test_custom_template(self):
        cfg = {"code_ref_mode": "tag", "tag_template": "release-{version}"}
        self.assertEqual(refs.version_candidates("1.0.4", cfg), ["release-1.0.4", "1.0.4"])

    def test_empty_base(self):
        self.assertEqual(refs.version_candidates("", self.cfg), [])

    def test_non_tag_mode(self):
        self.assertEqual(refs.version_candidates("1.0.4", {"code_ref_mode": "branch"}), [])


class ResolveVersionTagTest(unittest.TestCase):
    cfg = {"code_ref_mode": "tag", "tag_template": "v{version}"}

    def test_prefers_template_match(self):
        self.assertEqual(
            refs.resolve_version_tag("1.0.4", {"v1.0.4", "1.0.4"}, self.cfg), "v1.0.4"
        )

    def test_falls_back_to_base_tag(self):
        self.assertEqual(refs.resolve_version_tag("1.0.4", {"1.0.4"}, self.cfg), "1.0.4")

    def test_missing_tag(self):
        self.assertEqual(refs.resolve_version_tag("1.0.4", {"v9.9.9"}, self.cfg), "")

    def test_no_tags(self):
        self.assertEqual(refs.resolve_version_tag("1.0.4", set(), self.cfg), "")
        self.assertEqual(refs.resolve_version_tag("1.0.4", None, self.cfg), "")

    def test_empty_base(self):
        self.assertEqual(refs.resolve_version_tag("", {"v1.0.4"}, self.cfg), "")


if __name__ == "__main__":
    unittest.main()
