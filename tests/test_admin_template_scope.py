"""Regression test for the V1.6.37 /admin error caused by Jinja include scoping.

Does not contact Supabase or require a logged-in session.
Run: python -m unittest discover -s tests -p test_admin_template_scope.py -v
"""
from pathlib import Path
import unittest
from jinja2 import DictLoader, Environment, FileSystemLoader, UndefinedError

ROOT = Path(__file__).resolve().parents[1]
ADMIN = ROOT / "templates" / "admin.html"


class AdminTemplateScopeTests(unittest.TestCase):
    def test_parent_owns_ops_before_include(self):
        source = ADMIN.read_text(encoding="utf-8")
        setup = "{% set ops = tournament_ops_admin|default({}, true) %}"
        include = '{% include "admin_parts/c1_console.html" %}'
        self.assertIn(setup, source)
        self.assertIn(include, source)
        self.assertLess(source.index(setup), source.index(include))
        self.assertLess(source.index(include), source.index("{% if ops.get('tournament') %}"))
        self.assertNotIn("admin_legacy_recovery.html", source)

    def test_include_scope_bug_is_reproduced_and_fixed(self):
        # Include can read a parent variable but cannot export a {% set %} variable.
        env = Environment(loader=DictLoader({
            "fragment.html": "{% set ops = tournament_ops_admin|default({}, true) %}",
        }))
        broken = '{% include "fragment.html" %}{% if ops.get("tournament") %}C1{% endif %}'
        with self.assertRaises(UndefinedError):
            env.from_string(broken).render(tournament_ops_admin={"tournament": {"id": "C1"}})
        repaired = ('{% set ops = tournament_ops_admin|default({}, true) %}'
                    '{% include "fragment.html" %}'
                    '{% if ops.get("tournament") %}C1{% endif %}')
        self.assertEqual(env.from_string(repaired).render(
            tournament_ops_admin={"tournament": {"id": "C1"}}), "C1")
        self.assertEqual(env.from_string(repaired).render(tournament_ops_admin={}), "")

    def test_all_admin_modules_parse_and_exist(self):
        env = Environment(loader=FileSystemLoader(str(ROOT / "templates")))
        names = ["admin.html", "admin_parts/function_menu.html", "admin_parts/c1_console.html",
                 "admin_parts/c1_stage_header.html", "admin_parts/c1_stage1.html",
                 "admin_parts/c1_gd2_clubs.html", "admin_parts/c1_gd2_matches.html",
                 "admin_parts/c1_knockout.html", "admin_parts/feature_review.html"]
        for name in names:
            with self.subTest(template=name):
                env.parse(env.loader.get_source(env, name)[0])
        menu = (ROOT / "templates/admin_parts/function_menu.html").read_text(encoding="utf-8")
        self.assertIn("Công cụ nâng cao", menu)
        self.assertIn("Giải đấu C1", menu)
        self.assertTrue((ROOT / "templates/admin_parts/feature_review.html").exists())
        self.assertFalse((ROOT / "templates/admin_legacy_recovery.html").exists())


if __name__ == "__main__":
    unittest.main()
