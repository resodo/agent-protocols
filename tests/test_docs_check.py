"""Tests for scripts/docs_check.py. Each test builds a tiny git repo in a temp dir."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _docs_check_fixture import (  # noqa: E402
    ALL_RULES, DOCS_CHECK, EXC_RESULTS, EXC_SEARCH, Fixture, sha12,
)

SPEC = importlib.util.spec_from_file_location("docs_check", DOCS_CHECK)
assert SPEC is not None and SPEC.loader is not None
docs_check = importlib.util.module_from_spec(SPEC)
sys.modules.setdefault("docs_check", docs_check)
SPEC.loader.exec_module(docs_check)

MASTER = "needs the answer of the master (ledger entry) or the human"
HUMAN = "needs the answer of the human"
INCIDENT = "app/sources/vendor_files/reader.py"
READ_ALL = "\n\nRules-read:\n- sys.R1: applies; no new fetch\n- sys.R3: n/a; no data set\n- data.R1: n/a; read path untouched\n"


class DocsCheckCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.f = Fixture(self._tmp.name)
        self.f.branch("work")

    def ok(self, *args: str) -> str:
        code, out = self.f.check(*args)
        self.assertEqual(code, 0, out)
        return out

    def fails(self, *args: str) -> str:
        code, out = self.f.check(*args)
        self.assertEqual(code, 1, out)
        return out

    def with_exceptions_on_main(self) -> None:
        """Make the two sys.R1 exceptions part of origin/main."""
        self.f.insert_after("AGENTS.md", "- sys.R1", EXC_RESULTS, EXC_SEARCH)
        self.f.commit("sys.R1: two exceptions")
        self.f.mark_main()


class StructuralChecks(DocsCheckCase):
    def test_base_passes_every_check(self) -> None:
        self.assertIn("tags: ok (5 rules, 0 exceptions, 0 existing lines)", self.ok("tags"))
        self.assertIn("paths: ok", self.ok("paths"))
        self.assertIn("claude-md: ok", self.ok("claude-md"))
        self.assertIn("routes: ok (1 rows, 1 current docs)", self.ok("routes"))
        self.assertIn("rule-ids: ok (5 at origin/main, 5 now, 0 declared removed)", self.ok("rule-ids"))
        self.assertIn("rules-read: ok (0 review-only rules", self.ok("rules-read"))
        out = self.ok("numbers")
        self.assertIn("numbers: ok", out)
        self.assertIn("'root_agents_md_lines': 13", out)
        self.assertIn("'layer_exemption_lines': 3", out)
        self.assertIn("'top_modules_without_agents_md': 2", out)
        self.assertIn("'plan_index_lines': 3", out)
        self.assertIn("'plans_outside_changes': 2", out)
        self.assertIn("scope: no trigger, no record needed", self.ok("scope"))
        self.assertIn("gated: nothing to stop on", self.ok("gated"))

    def test_malformed_lines(self) -> None:
        self.f.append("app/sources/AGENTS.md", "- data.R3 Vendor codes are stored as the vendor writes them.\n"
                      "- data.R1 Readers pick the newest eligible row. [review] (#3001)\n")
        self.f.insert_after("AGENTS.md", "- sys.R1", "  - exception: results source stays here (approved: master 2026-11-16)")
        self.f.commit("malformed")
        out = self.fails("tags")
        self.assertIn("app/sources/AGENTS.md:4 data.R3: a rule line needs `[lint: <check>]` or `[review]`, then `(source)`", out)
        self.assertIn("app/sources/AGENTS.md:5 data.R1: the same id is already at app/sources/AGENTS.md:3; one rule, one place", out)
        self.assertIn("AGENTS.md:6: an exception line reads `- exception: <what> (approved: <who> <date>; <plan or issue that ends it>)`, with no review date", out)

    def test_exception_without_a_rule_above(self) -> None:
        self.f.append("app/sources/AGENTS.md", "\n## Notes\n" + EXC_SEARCH + "\n")
        self.f.commit("stray exception")
        self.assertIn("an exception line sits under the rule it belongs to; no rule line above this one", self.fails("tags"))

    def test_exception_after_an_unrelated_bullet(self) -> None:
        self.f.append("app/sources/AGENTS.md", "- a plain note, not a rule\n" + EXC_SEARCH + "\n")
        self.f.commit("exception under a note")
        self.assertIn("app/sources/AGENTS.md:5: an exception line sits under the rule it belongs to", self.fails("tags"))

    def test_dropped_lint_check(self) -> None:
        self.f.replace("pyproject.toml", 'id = "layers"', 'id = "layering"')
        self.f.commit("rename contract")
        out = self.fails("tags")
        self.assertIn("AGENTS.md:6 sys.R2: tagged [lint: importlinter:layers], but no check of that name exists", out)
        self.assertIn("Restore the check, or retag the rule [review], or delete the rule.", out)

    def test_lint_names_from_every_source(self) -> None:
        self.f.append("app/sources/AGENTS.md", "- data.R3 Code here is formatted. [lint: light:format] (#5)\n"
                      "- data.R4 The API reads only the interface. [lint: importlinter:api-only] (#6)\n"
                      "- data.R5 Numbers here only go down. [lint: docs-check:ratchet] (#7)\n")
        self.f.commit("more lint rules")
        self.assertIn("tags: ok (8 rules, 0 exceptions, 0 existing lines)", self.ok("tags"))

    def test_paths_after_a_directory_rename(self) -> None:
        self.f.git("mv", "app/sources", "app/readers")
        self.f.commit("rename sources to readers")
        out = self.fails("paths")
        self.assertIn("AGENTS.md:13: `app/sources/` is named here and is not in the repo. Fix the path, or the line.", out)

    def test_paths_relative_to_the_agents_file(self) -> None:
        self.f.append("app/sources/AGENTS.md", "- data.R3 `vendor_files/reader.py` reads one vendor. [review] (#5)\n")
        self.f.commit("relative path")
        self.assertIn("paths: ok", self.ok("paths"))

    def test_claude_md(self) -> None:
        self.f.write("CLAUDE.md", "# Claude rules\n- Always use tabs.\n")
        self.f.commit("claude")
        self.assertIn("CLAUDE.md: must be a link to AGENTS.md or the single line `@AGENTS.md`", self.fails("claude-md"))
        self.f.write("CLAUDE.md", "@AGENTS.md\n")
        self.f.commit("import")
        self.assertIn("claude-md: ok", self.ok("claude-md"))
        os.remove(self.f.root / "CLAUDE.md")
        os.symlink("AGENTS.md", self.f.root / "app/sources/CLAUDE.md")
        self.f.commit("link")
        self.assertIn("claude-md: ok", self.ok("claude-md"))

    def test_current_doc_not_in_routing_table(self) -> None:
        self.f.write("docs/current/identity.md", "# Identity\n")
        self.f.commit("identity doc")
        self.assertIn("docs/current/identity.md: a current doc that the routing table in AGENTS.md does not list",
                      self.fails("routes"))

    def test_routes_pass_without_a_current_docs_dir(self) -> None:
        self.f.git("rm", "-q", "docs/current/data.md")
        self.f.commit("no current docs")
        self.assertIn("routes: ok (no docs/current/ directory)", self.ok("routes"))

    def test_bad_config_exits_2(self) -> None:
        self.f.write(".agent-protocols/docs-check.json", '{"ratchets": {"x": {"kind": "made_up"}}}\n')
        code, out = self.f.check("numbers")
        self.assertEqual(code, 2, out)
        self.assertIn("ratchet x: kind is one of", out)


class RulesFor(DocsCheckCase):
    def test_rules_and_exceptions_for_a_file(self) -> None:
        self.f.insert_after("AGENTS.md", "- sys.R1", EXC_RESULTS)
        self.f.commit("exception")
        out = self.ok("rules-for", INCIDENT)
        lines = out.splitlines()
        self.assertEqual(lines[0], f"[rules: {INCIDENT}]")
        self.assertTrue(lines[1].startswith("sys.R1    Outbound fetching lives in the fetch service"))
        self.assertTrue(lines[1].endswith("[review] (decided 2026-11-09, data plan)   <- AGENTS.md"))
        self.assertIn("exception: The results source is fetched here until the fetch service moves it "
                      "(approved: human 2026-11-22; docs/agent_plans/changes/results-source)", lines[2])
        self.assertEqual([l.split()[0] for l in lines[3:]], ["sys.R2", "sys.R3", "data.R1", "data.R2"])
        self.assertTrue(lines[-1].endswith("<- app/sources/vendor_files/AGENTS.md"))

    def test_directory_path(self) -> None:
        out = self.ok("rules-for", "app/sources")
        self.assertIn("data.R1", out)
        self.assertNotIn("data.R2", out)


class RuleIds(DocsCheckCase):
    def test_split_drops_an_agents_file(self) -> None:
        self.f.git("rm", "-q", "app/sources/vendor_files/AGENTS.md")
        self.f.commit("split")
        self.assertIn("data.R2: was in app/sources/vendor_files/AGENTS.md at origin/main, is in no AGENTS.md now. "
                      "Move it with its code, or add a line `Rules-removed: <id> - <reason>` to the commit message.",
                      self.fails("rule-ids"))
        self.f.amend("split\n\nRules-removed: data.R2 - the vendor files moved to the fetch service")
        self.assertIn("rule-ids: ok (5 at origin/main, 4 now, 1 declared removed)", self.ok("rule-ids"))
        self.assertIn(f"rule data.R2 or an exception under it changed -> {MASTER}", self.ok("gated"))

    def test_rename_keeps_ids_and_stops_nothing(self) -> None:
        self.f.git("mv", "app/sources/vendor_files", "app/sources/issuer")
        self.f.commit("rename")
        self.assertIn("rule-ids: ok (5 at origin/main, 5 now, 0 declared removed)", self.ok("rule-ids"))
        self.assertIn("scope: no trigger, no record needed", self.ok("scope"))
        self.assertIn("gated: nothing to stop on", self.ok("gated"))

    def test_rule_moved_unchanged_is_a_trigger_for_the_master(self) -> None:
        line = self.f.read("app/sources/vendor_files/AGENTS.md").splitlines()[2]
        self.f.git("rm", "-q", "app/sources/vendor_files/AGENTS.md")
        self.f.append("app/sources/AGENTS.md", line + "\n")
        self.f.commit("data.R2 moves up one level")
        self.assertIn("rule-ids: ok (5 at origin/main, 5 now, 0 declared removed)", self.ok("rule-ids"))
        moved = "data.R2 (app/sources/vendor_files/AGENTS.md -> app/sources/AGENTS.md)"
        out = self.fails("scope")
        self.assertIn(f"  - a rule moved to another file ({moved})", out)
        self.assertNotIn("a rule or an exception changed", out)
        self.assertIn(f"rule {moved} moved, wording unchanged -> {MASTER}", self.ok("gated"))


class RulesRead(DocsCheckCase):
    def test_missing_then_complete(self) -> None:
        self.f.write(INCIDENT, "def read():\n    return []\n")
        self.f.commit("IR: read two-column tables")
        out = self.fails("rules-read")
        self.assertIn("data.R1 (app/sources/AGENTS.md) governs a file this change touches, and the commit message "
                      "does not account for it. Add under `Rules-read:` a line `- data.R1: applies; <how the change "
                      "keeps it>` or `- data.R1: n/a; <why>`.", out)
        self.assertIn("sys.R1 (AGENTS.md)", out)
        self.assertIn("sys.R3 (AGENTS.md)", out)
        self.assertNotIn("sys.R2", out)  # [lint] rules are left to their checks
        self.f.amend("IR: read two-column tables" + READ_ALL)
        self.assertIn("rules-read: ok (3 review-only rules govern the touched paths, all accounted for)", self.ok("rules-read"))

    def test_empty_explanations_do_not_count(self) -> None:
        self.f.write(INCIDENT, "def read():\n    return []\n")
        self.f.commit("fix\n\nRules-read:\n- sys.R1: applies\n- sys.R3: n/a;\n- data.R1: n/a; read path untouched\n")
        out = self.fails("rules-read")
        self.assertIn("sys.R1 (AGENTS.md) governs", out)
        self.assertIn("sys.R3 (AGENTS.md) governs", out)
        self.assertNotIn("data.R1 (", out)

    def test_block_in_an_earlier_commit_of_the_range(self) -> None:
        self.f.write(INCIDENT, "def read():\n    return []\n")
        self.f.commit("first" + READ_ALL)
        self.f.write("notes.txt", "x\n")
        self.f.commit("second")
        self.ok("rules-read")

    def test_deleted_directory_still_needs_its_rules(self) -> None:
        self.f.write("app/jobs/AGENTS.md", "# jobs\n\n- jobs.R1 Jobs here are idempotent. [review] (#9)\n")
        self.f.write("app/jobs/run.py", "pass\n")
        self.f.commit("jobs")
        self.f.mark_main()
        self.f.git("rm", "-q", "-r", "app/jobs")
        self.f.commit("drop jobs\n\nRules-removed: jobs.R1 - the jobs are gone\n\nRules-read:\n"
                      "- sys.R1: n/a; x\n- sys.R3: n/a; x\n")
        self.assertIn("jobs.R1 (app/jobs/AGENTS.md at origin/main) governs a file this change touches",
                      self.fails("rules-read"))
        self.f.amend("drop jobs\n\nRules-removed: jobs.R1 - the jobs are gone\n\nRules-read:\n"
                     "- sys.R1: n/a; x\n- sys.R3: n/a; x\n- jobs.R1: n/a; the directory is deleted\n")
        self.ok("rules-read")
        self.ok("rule-ids")


class Numbers(DocsCheckCase):
    def test_paying_debt_triggers_and_stops_nothing(self) -> None:
        self.f.replace("pyproject.toml", '  "app.sources.a -> app.nodes.b",\n', "")
        self.f.commit("read through the interface")
        out = self.ok("numbers")
        self.assertIn("layer_exemption_lines: 3 at origin/main, 2 now. Nothing to do: once this merges, 2 is the number to beat.", out)
        self.assertIn("scope: no trigger, no record needed", self.ok("scope"))
        self.assertIn("gated: nothing to stop on", self.ok("gated"))

    def test_raise_undeclared_then_declared(self) -> None:
        self.f.replace("pyproject.toml", "ignore_imports = [\n", 'ignore_imports = [\n  "app.nodes.x -> app.api.y",\n')
        self.f.commit("daily registration")
        self.assertIn("layer_exemption_lines: 3 at origin/main, 4 now. This number only goes down. Undo the increase, "
                      "or add a line `Raises: layer_exemption_lines 3 -> 4 - <reason>` to the commit message "
                      "(the merge agent then stops and asks).", self.fails("numbers"))
        self.f.amend("daily registration\n\nRaises: layer_exemption_lines 3 -> 5 - wrong numbers")
        self.fails("numbers")
        self.f.amend("daily registration\n\nRaises: layer_exemption_lines 3 -> 4 - the node calls the writer directly")
        self.assertIn("layer_exemption_lines: 3 at origin/main, 4 now, declared in the commit message. "
                      "The merge agent will stop on it.", self.ok("numbers"))
        out = self.fails("scope")
        self.assertIn("  - layer_exemption_lines goes up (3 -> 4)", out)
        self.assertIn("Write docs/agent_plans/changes/<name>/proposal.md", out)
        self.assertIn(f"layer_exemption_lines goes up 3 -> 4 -> {MASTER}", self.ok("gated"))

    def test_plan_written_the_old_way(self) -> None:
        self.f.write("docs/agent_plans/2026-11-22_new_thing_plan.md", "# new plan\n")
        self.f.append("docs/agent_plans/README.md", "- new thing\n")
        self.f.commit("plan")
        out = self.fails("numbers")
        self.assertIn("plan_index_lines: 3 at origin/main, 4 now. This number only goes down.", out)
        self.assertIn("plans_outside_changes: 2 at origin/main, 3 now. This number only goes down.", out)

    def test_plan_under_changes_is_not_counted(self) -> None:
        self.f.proposal("new-thing", ["app/nodes/"])
        self.f.commit("plan the new way")
        self.ok("numbers")

    def test_top_level_dirs_without_agents_file(self) -> None:
        self.f.write("app/jobs/run.py", "pass\n")
        self.f.commit("new module")
        self.assertIn("top_modules_without_agents_md: 2 at origin/main, 3 now.", self.fails("numbers"))
        self.f.write("app/jobs/AGENTS.md", "# jobs\n")
        self.f.write("app/api/AGENTS.md", "# api\n")
        self.f.amend("new module with rules files")
        self.assertIn("top_modules_without_agents_md: 2 at origin/main, 1 now.", self.ok("numbers"))

    def test_regex_lines_between_markers(self) -> None:
        text = 'a = [\n  "app.x -> app.y",\n]\nignore_imports = [\n  "app.p -> app.q",\n]\n  "app.z -> app.w",\n'
        self.assertEqual(docs_check.count_regex_lines(text, r'"app\.[^"]+ -> ', "ignore_imports = [", "]"), 1)
        self.assertEqual(docs_check.count_regex_lines(text, r'"app\.[^"]+ -> ', None, None), 3)

    def test_glob_match(self) -> None:
        self.assertTrue(docs_check.glob_match("docs/agent_plans/x.md", "docs/agent_plans/*"))
        self.assertFalse(docs_check.glob_match("docs/agent_plans/changes/a/proposal.md", "docs/agent_plans/*"))
        self.assertTrue(docs_check.glob_match("docs/agent_plans/changes/a/proposal.md", "docs/**/proposal.md"))


class Exceptions(DocsCheckCase):
    def test_opening_exceptions_under_a_sys_rule(self) -> None:
        self.f.insert_after("AGENTS.md", "- sys.R1", EXC_RESULTS, EXC_SEARCH)
        self.f.commit("sys.R1: two exceptions")
        self.assertIn("tags: ok (5 rules, 2 exceptions, 0 existing lines)", self.ok("tags"))
        out = self.fails("scope")
        self.assertIn("  - a rule or an exception changed (sys.R1)", out)
        self.assertIn("  - root_agents_md_lines goes up (13 -> 15)", out)
        out = self.ok("gated")
        self.assertIn(f"rule sys.R1 or an exception under it changed -> {HUMAN}", out)
        self.assertIn(f"root_agents_md_lines goes up 13 -> 15 -> {MASTER}", out)
        out = self.ok("exceptions")
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("exception sys.R1   The results source"), out)
        self.assertTrue(lines[1].startswith("exception sys.R1   Two web search clients"), out)
        self.assertTrue(lines[1].endswith("<- AGENTS.md:7"), out)
        self.assertEqual(lines[2], "exceptions: 2 open, existing lines: 0")

    def test_ending_an_exception_stops_nothing(self) -> None:
        self.with_exceptions_on_main()
        self.f.write("AGENTS.md", "".join(l for l in self.f.read("AGENTS.md").splitlines(True) if "web search" not in l))
        self.f.commit("sys.R1: the search exception ended")
        self.assertIn("tags: ok (5 rules, 1 exceptions, 0 existing lines)", self.ok("tags"))
        self.assertIn("root_agents_md_lines: 15 at origin/main, 14 now.", self.ok("numbers"))
        self.assertIn("scope: no trigger, no record needed", self.ok("scope"))
        out = self.ok("gated")
        self.assertIn("note, no stop: an exception ended (sys.R1: Two web search clients live here while the main provider is down)", out)
        self.assertIn("gated: nothing to stop on", out)

    def test_extending_an_exception_needs_the_human(self) -> None:
        self.with_exceptions_on_main()
        self.f.replace("AGENTS.md", "changes/search-vendor", "changes/search-vendor-2")
        self.f.commit("sys.R1: keep the search exception longer")
        self.assertIn("  - a rule or an exception changed (sys.R1)", self.fails("scope"))
        out = self.ok("gated")
        self.assertIn(f"rule sys.R1 or an exception under it changed -> {HUMAN}", out)
        self.assertNotIn("an exception ended", out)

    def test_exceptions_none_open(self) -> None:
        self.assertIn("exceptions: 0 open, existing lines: 0", self.ok("exceptions"))

    def test_an_exception_with_a_review_date_is_rejected(self) -> None:
        old = EXC_SEARCH.replace("approved: human 2026-11-22; ", "approved: human 2026-11-22; review: 2026-11-30; ")
        self.f.insert_after("AGENTS.md", "- sys.R1", old)
        self.f.commit("exception with a review date")
        self.assertIn("with no review date", self.fails("tags"))

    def test_a_review_date_after_the_plan_is_rejected(self) -> None:
        old = EXC_SEARCH[:-1] + "; review: 2026-11-30)"
        self.f.insert_after("AGENTS.md", "- sys.R1", old)
        self.f.commit("review date after the plan")
        self.assertIn("with no review date", self.fails("tags"))

    def test_an_exception_needs_a_plan_or_issue(self) -> None:
        self.f.insert_after("AGENTS.md", "- sys.R1", "  - exception: results stay here (approved: human 2026-11-22)")
        self.f.commit("exception without a plan")
        self.assertIn("with no review date", self.fails("tags"))


EXISTING = ("  - existing: the old fetch code is held by the fetch plan (#12) and is gone when the fetch service "
            "serves every source")


class ExistingLines(DocsCheckCase):
    def with_existing_on_main(self) -> None:
        self.f.insert_after("AGENTS.md", "- sys.R1", EXISTING)
        self.f.commit("sys.R1: existing line")
        self.f.mark_main()

    def test_an_existing_line_is_well_formed_and_counted(self) -> None:
        self.f.insert_after("AGENTS.md", "- sys.R1", EXISTING)
        self.f.commit("sys.R1: existing line")
        self.assertIn("tags: ok (5 rules, 0 exceptions, 1 existing lines)", self.ok("tags"))
        out = self.ok("exceptions")
        self.assertIn("existing  sys.R1   the old fetch code is held by the fetch plan (#12)", out)
        self.assertIn("exceptions: 0 open, existing lines: 1", out)

    def test_an_empty_existing_line_is_rejected(self) -> None:
        self.f.insert_after("AGENTS.md", "- sys.R1", "  - existing:")
        self.f.commit("empty existing")
        self.assertIn("an existing line reads `- existing: <the plan and the condition on which the older code is gone>`", self.fails("tags"))

    def test_an_existing_line_without_a_rule_above(self) -> None:
        self.f.append("app/sources/AGENTS.md", "\n## Notes\n" + EXISTING + "\n")
        self.f.commit("stray existing")
        self.assertIn("an existing line sits under the rule it belongs to; no rule line above this one", self.fails("tags"))

    def test_the_reviewer_is_given_the_existing_line_with_the_rule(self) -> None:
        self.f.insert_after("AGENTS.md", "- sys.R1", EXC_RESULTS, EXISTING)
        self.f.commit("both kinds under one rule")
        lines = self.ok("rules-for", INCIDENT).splitlines()
        self.assertTrue(lines[1].startswith("sys.R1 "))
        self.assertTrue(lines[2].lstrip().startswith("exception: The results source"), lines[2])
        self.assertTrue(lines[3].lstrip().startswith("existing: the old fetch code"), lines[3])

    def test_adding_an_existing_line_is_a_rule_change(self) -> None:
        self.f.insert_after("AGENTS.md", "- sys.R1", EXISTING)
        self.f.commit("sys.R1: existing line")
        self.assertIn("  - a rule or an exception changed (sys.R1)", self.fails("scope"))
        self.assertIn(f"rule sys.R1 or an exception under it changed -> {HUMAN}", self.ok("gated"))

    def test_ending_an_existing_line_stops_nothing(self) -> None:
        self.with_existing_on_main()
        self.f.write("AGENTS.md", "".join(l for l in self.f.read("AGENTS.md").splitlines(True) if "old fetch code" not in l))
        self.f.commit("sys.R1: the old code is gone")
        self.assertIn("scope: no trigger, no record needed", self.ok("scope"))
        out = self.ok("gated")
        self.assertIn("note, no stop: an existing line ended (sys.R1: the old fetch code", out)
        self.assertIn("gated: nothing to stop on", out)


class Gated(DocsCheckCase):
    def test_directory_rule_reworded_goes_to_the_master(self) -> None:
        self.f.replace("app/sources/AGENTS.md", "check time eligibility first", "check time eligibility before anything")
        self.f.commit("reword data.R1")
        self.assertIn(f"rule data.R1 or an exception under it changed -> {MASTER}", self.ok("gated"))

    def test_sys_rule_added_or_removed_needs_the_human(self) -> None:
        self.f.insert_after("AGENTS.md", "- sys.R3", "- sys.R4 Every job is idempotent. [review] (#9)")
        self.f.write("AGENTS.md", "".join(l for l in self.f.read("AGENTS.md").splitlines(True) if not l.startswith("- sys.R3")))
        self.f.commit("add sys.R4, drop sys.R3\n\nRules-removed: sys.R3 - folded into the writers' table")
        out = self.ok("gated")
        self.assertIn(f"rule sys.R3 or an exception under it changed -> {HUMAN}", out)
        self.assertIn(f"rule sys.R4 or an exception under it changed -> {HUMAN}", out)
        self.ok("rule-ids")

    def test_decision_boundary_and_ledger_need_the_human(self) -> None:
        self.f.append(".agent-protocols/decision-boundary.md", "- a new line\n")
        self.f.append(".agent-protocols/authority-ledger.md", "- a new entry\n")
        self.f.commit("boundary and ledger")
        out = self.ok("gated")
        self.assertIn(f".agent-protocols/decision-boundary.md: the decision-boundary file changed -> {HUMAN}", out)
        self.assertIn(f".agent-protocols/authority-ledger.md: the authority ledger changed -> {HUMAN}", out)

    def test_non_rule_text_stops_nothing(self) -> None:
        self.f.replace("app/sources/AGENTS.md", "# sources", "# sources (readers only)")
        self.f.commit("heading")
        self.assertIn("gated: nothing to stop on", self.ok("gated"))
        self.assertIn("scope: no trigger, no record needed", self.ok("scope"))


class Scope(DocsCheckCase):
    def incident_change(self, name: str = "ir-fix") -> None:
        self.f.write(INCIDENT, "def read():\n    return []\n")
        self.f.proposal(name, [INCIDENT])

    def test_incident_folder_without_record(self) -> None:
        self.f.write(INCIDENT, "def read():\n    return []\n")
        self.f.commit("table of contents for decks")
        out = self.fails("scope")
        self.assertIn("This change needs a scope review before merge, because:", out)
        self.assertIn(f"  - {INCIDENT} is under app/sources/vendor_files/AGENTS.md, which is marked incident-fixes-only", out)
        self.assertIn("Write docs/agent_plans/changes/<name>/proposal.md, run the scope review on it", out)
        self.assertIn("gated: nothing to stop on", self.ok("gated"))

    def test_new_plan_is_a_trigger(self) -> None:
        self.f.proposal("new-thing", ["app/nodes/"])
        self.f.commit("plan")
        self.assertIn("  - a new plan", self.fails("scope"))

    def test_go_record_passes(self) -> None:
        self.incident_change()
        rec = self.f.record("ir-fix")
        self.f.commit("IR fix" + READ_ALL)
        self.assertIn(f"scope: ok (2 trigger(s), record {rec})", self.ok("scope"))
        log = self.f.tmp / "log"
        log.write_text(sha12(self.f.read(rec).encode()) + "\n")
        self.assertIn("gated: nothing to stop on", self.ok("gated", "--log", str(log)))

    def test_record_outside_changes_does_not_count(self) -> None:
        self.f.write(INCIDENT, "def read():\n    return []\n")
        self.f.write("docs/scope-review.md", "---\nverdict: go\n---\n")
        self.f.commit("record in the wrong place")
        self.assertIn("This change needs a scope review before merge", self.fails("scope"))

    def test_cut_and_no_fail(self) -> None:
        self.incident_change()
        rec = self.f.record("ir-fix", verdict="cut")
        self.f.commit("cut")
        self.assertIn(f"{rec}: verdict is `cut`. Take the listed parts out of the proposal and run the review again",
                      self.fails("scope"))
        self.f.record("ir-fix", verdict="no")
        self.f.amend("no")
        self.assertIn(f"{rec}: verdict is `no`; this change does not merge.", self.fails("scope"))
        self.f.record("ir-fix", verdict="maybe")
        self.f.amend("maybe")
        self.assertIn("verdict is `maybe`; it is one of go, cut, ask, no", self.fails("scope"))

    def test_proposal_changed_after_review(self) -> None:
        self.incident_change()
        rec = self.f.record("ir-fix")
        self.f.append("docs/agent_plans/changes/ir-fix/proposal.md", "\nAlso add a new downloader.\n")
        self.f.commit("widen")
        self.assertIn(f"{rec}: the proposal changed after the review (proposal_sha does not match); review again",
                      self.fails("scope"))

    def test_record_without_proposal(self) -> None:
        self.incident_change()
        rec = self.f.record("ir-fix")
        os.remove(self.f.root / "docs/agent_plans/changes/ir-fix/proposal.md")
        self.f.commit("no proposal")
        self.assertIn(f"{rec}: no proposal.md next to it", self.fails("scope"))

    def test_record_missing_a_rule_line(self) -> None:
        self.incident_change()
        rec = self.f.record("ir-fix", rules=[r for r in ALL_RULES if r != "data.R1"])
        self.f.commit("short record")
        self.assertIn(f"{rec}: no line for ['data.R1']", self.fails("scope"))

    def test_ask_conflicting_with_a_sys_rule_needs_the_human(self) -> None:
        self.f.replace("pyproject.toml", "ignore_imports = [\n", 'ignore_imports = [\n  "app.nodes.x -> app.api.y",\n')
        self.f.write("app/nodes/registration.py", "pass\n")
        self.f.proposal("daily-registration", ["app/nodes/registration.py", "pyproject.toml"])
        rec = self.f.record("daily-registration", verdict="ask", rules=["sys.R1", "sys.R2", "sys.R3"],
                            words={"sys.R2": "conflict", "sys.R3": "conflict"},
                            tail=["Owner: sys.R3", "Cut: the layering exemption",
                                  "Question: do you approve a standing entry rule for new records?"])
        self.f.commit("daily registration\n\nRaises: layer_exemption_lines 3 -> 4 - the node calls the writer\n\n"
                      "Rules-read:\n- sys.R1: n/a; x\n- sys.R3: n/a; x\n")
        self.assertIn(f"scope: record present, verdict `ask` ({rec}). The check passes; the merge agent stops "
                      "until the question is answered.", self.ok("scope"))
        log = self.f.tmp / "log"
        log.write_text(sha12(self.f.read(rec).encode()) + "\n")
        out = self.ok("gated", "--log", str(log))
        self.assertIn(f"layer_exemption_lines goes up 3 -> 4 -> {MASTER}", out)
        self.assertIn(f"{rec}: verdict ask (conflict with sys.R2, sys.R3) -> {HUMAN}", out)
        self.assertIn("      question to answer: do you approve a standing entry rule for new records?", out)
        self.assertIn("      cut to answer: the layering exemption", out)
        self.assertNotIn("not in the reviewer's run log", out)
        # The author edits the record by hand to say go: the check passes, the run log catches it.
        self.f.replace(rec, "verdict: ask", "verdict: go")
        self.f.commit("x")
        self.assertIn(f"scope: ok (2 trigger(s), record {rec})", self.ok("scope"))
        out = self.ok("gated", "--log", str(log))
        self.assertIn("is not in the reviewer's run log; it was not written by the scope-review runner -> send back to the author", out)

    def test_ask_without_a_sys_conflict_goes_to_the_master(self) -> None:
        self.incident_change()
        rec = self.f.record("ir-fix", verdict="ask", words={"data.R1": "conflict"},
                            tail=["Owner: data.R1", "Cut: nothing", "Question: is the vendor order right?"])
        self.f.commit("ask")
        out = self.ok("gated")
        self.assertIn("scope-review records changed and no run log is set", out)
        self.assertIn(f"{rec}: verdict ask (conflict with data.R1) -> {MASTER}", out)
        self.assertIn("question to answer: is the vendor order right?", out)
        self.assertNotIn("cut to answer", out)

    def test_hand_written_go_record_without_log_flag(self) -> None:
        self.incident_change()
        rec = self.f.record("ir-fix")
        self.f.commit("fix")
        self.assertIn("no run log is set", self.ok("gated"))
        log = self.f.tmp / "log"
        log.write_text("000000000000\n")
        self.f.env["SCOPE_REVIEW_LOG"] = str(log)
        out = self.ok("gated")
        self.assertIn(f"{rec}: this record", out)
        self.assertIn("not in the reviewer's run log", out)
        log.write_text(sha12(self.f.read(rec).encode()) + "\n")
        self.assertIn("gated: nothing to stop on", self.ok("gated"))

    def test_missing_log_file_flags_every_record(self) -> None:
        self.incident_change()
        self.f.record("ir-fix")
        self.f.commit("fix")
        self.assertIn("is not in the reviewer's run log", self.ok("gated", "--log", str(self.f.tmp / "nope.log")))


class Report(DocsCheckCase):
    def test_measuring_table(self) -> None:
        self.f.write(INCIDENT, "def read():\n    return []\n")
        self.f.proposal("ir-fix", [INCIDENT])
        self.f.record("ir-fix")
        self.f.commit("IR fix" + READ_ALL)
        out = self.ok("report", "--range", "origin/main..HEAD")
        self.assertIn("rules: 5 (2 program-checked, 3 review-only)", out)
        self.assertIn("commits with a Rules-read block in origin/main..HEAD: 1; lines in those blocks: 3", out)
        rows = {l.split()[0]: l.split()[1:] for l in out.splitlines() if l.startswith(("sys.", "data."))}
        self.assertEqual(rows["sys.R1"], ["1", "1", "0"])
        self.assertEqual(rows["sys.R3"], ["1", "0", "1"])
        self.assertEqual(rows["data.R1"], ["1", "0", "1"])
        self.assertIn("scope-review verdicts: {'go': 1}", out)
        self.assertIn("measured numbers now: {", out)


class PathsAndGatedMatching(DocsCheckCase):
    def set_config(self, **changes) -> None:
        cfg = json.loads(self.f.read(".agent-protocols/docs-check.json"))
        cfg.update(changes)
        self.f.write(".agent-protocols/docs-check.json", json.dumps(cfg, indent=2) + "\n")

    def test_url_route_is_not_a_path(self) -> None:
        self.f.append("app/sources/AGENTS.md", "- data.R3 Within `/v1` the API only adds fields. [review] (#5)\n")
        self.f.commit("route")
        self.assertIn("paths: ok", self.ok("paths"))

    def test_path_after_a_repo_name_is_not_checked_here(self) -> None:
        line = "- data.R3 Ids are parsed only in example-other `infra/ids`. [review] (#5)\n"
        self.f.append("app/sources/AGENTS.md", line)
        self.f.commit("other repo path")
        self.assertIn("`infra/ids` is named here and is not in the repo", self.fails("paths"))
        self.set_config(repo_name_pattern="example-[a-z]+")
        self.f.commit("repo names")
        self.assertIn("paths: ok", self.ok("paths"))
        self.f.append("app/sources/AGENTS.md", "- data.R4 Readers live in `app/missing/`. [review] (#6)\n")
        self.f.commit("a real missing path")
        self.assertIn("`app/missing/` is named here and is not in the repo", self.fails("paths"))

    def test_directory_path_covers_the_files_under_it(self) -> None:
        self.f.write("policy/boundary/rules.md", "# rules\n")
        self.set_config(decision_boundary_paths=["policy/boundary/"])
        self.f.commit("boundary dir")
        self.f.mark_main()
        self.f.append("policy/boundary/rules.md", "- one more\n")
        self.f.commit("edit inside the boundary dir")
        self.assertIn(f"policy/boundary/: the decision-boundary file changed -> {HUMAN}", self.ok("gated"))

    def make_submodule(self) -> tuple[Path, str]:
        sub = self.f.tmp / "protocols"
        sub.mkdir()
        run = lambda *a: subprocess.run(["git", *a], cwd=sub, env=self.f.env, check=True,  # noqa: E731
                                        capture_output=True, text=True).stdout
        run("init", "-q", "-b", "main")
        (sub / "decision-boundary").mkdir()
        (sub / "decision-boundary" / "SKILL.md").write_text("# boundary\n", encoding="utf-8")
        (sub / "other.md").write_text("# other\n", encoding="utf-8")
        run("add", "-A")
        run("commit", "-q", "-m", "one")
        self.f.git("-c", "protocol.file.allow=always", "submodule", "add", "-q", str(sub), "external/protocols")
        self.set_config(decision_boundary_paths=["external/protocols/decision-boundary/"])
        self.f.commit("add the protocols submodule")
        self.f.mark_main()
        return sub, run

    def bump(self, sub: Path, run, rel: str) -> None:
        (sub / rel).write_text((sub / rel).read_text(encoding="utf-8") + "- more\n", encoding="utf-8")
        run("commit", "-q", "-am", f"edit {rel}")
        inner = self.f.root / "external/protocols"
        subprocess.run(["git", "-c", "protocol.file.allow=always", "pull", "-q", "origin", "main"], cwd=inner,
                       env=self.f.env, check=True, capture_output=True)
        self.f.commit(f"bump protocols ({rel})")

    def test_submodule_bump_outside_the_path_stops_nothing(self) -> None:
        sub, run = self.make_submodule()
        self.bump(sub, run, "other.md")
        self.assertIn("gated: nothing to stop on", self.ok("gated"))

    def test_submodule_bump_that_changes_the_path_needs_the_human(self) -> None:
        sub, run = self.make_submodule()
        self.bump(sub, run, "decision-boundary/SKILL.md")
        self.assertIn(f"external/protocols/decision-boundary/: the decision-boundary file changed -> {HUMAN}",
                      self.ok("gated"))

    def test_submodule_bump_without_its_history_needs_the_human(self) -> None:
        sub, run = self.make_submodule()
        self.bump(sub, run, "other.md")
        self.f.git("submodule", "deinit", "-q", "-f", "external/protocols")
        self.assertIn(f"external/protocols/decision-boundary/: the decision-boundary file changed -> {HUMAN}",
                      self.ok("gated"))


if __name__ == "__main__":
    unittest.main()
