#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبارات جارفس CEO — بدون شبكة، قاعدة مؤقتة عبر CEO_DB."""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.environ["CEO_DB"] = os.path.join(tempfile.mkdtemp(prefix="ceo-test-"), "test.db")

import db  # noqa: E402
import brain  # noqa: E402
import tools  # noqa: E402
import selfedit  # noqa: E402


class TestDB(unittest.TestCase):
    def test_agents_seeded(self):
        db.ensure_agents()
        names = [a["name"] for a in db.list_agents()]
        for expected in ("سعيد", "محمود", "أحمد", "متداول"):
            self.assertIn(expected, names)

    def test_add_and_history(self):
        db.add_message(1234, "user", "مرحبا")
        db.add_message(1234, "assistant", "أهلاً")
        hist = db.history(1234, limit=5)
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[0]["content"].endswith("مرحبا"), True)

    def test_spend_cap(self):
        small = "1"
        db.kv_set(f"spend:{time.strftime('%Y-%m-%d')}", "0")
        self.assertFalse(db.spend_exceeded(small))
        db.add_tokens(10)
        self.assertTrue(db.spend_exceeded(small))
        db.add_tokens(-10)  # لا يرجع للوراء
        self.assertTrue(db.spend_exceeded(small))

    def test_tasks(self):
        tid = db.add_task("سعيد", "افحص example.com")
        open_ids = [t["id"] for t in db.open_tasks(10)]
        self.assertIn(tid, open_ids)
        db.done_task(tid)
        open_ids = [t["id"] for t in db.open_tasks(10)]
        self.assertNotIn(tid, open_ids)


class TestBrain(unittest.TestCase):
    def test_extract_json_plain(self):
        self.assertEqual(brain.extract_json('{"action":"reply","reply":"هلا"}')["action"], "reply")

    def test_extract_json_embedded(self):
        raw = 'تمام، منيحة:\n{"action":"delegate","agent":"سعيد","task":"افحص الموقع"}\nخلصت'
        self.assertEqual(brain.extract_json(raw)["agent"], "سعيد")

    def test_extract_json_garbage(self):
        self.assertIsNone(brain.extract_json("لا يوجد أي جيسون هنا"))


class TestExcel(unittest.TestCase):
    def _make_xlsx(self, path):
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "الصقيع"
        ws["A1"] = "المدينة"
        ws["B1"] = "السعر"
        ws["A2"] = "دمشق"
        ws["B2"] = 100
        wb.save(path)

    def test_excel_report(self):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            p = f.name
        self._make_xlsx(p)
        report = tools.excel_report(p)
        self.assertIn("الصقيع", report)
        self.assertIn("دمشق", report)

    def test_excel_code_happy_path(self):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            p = f.name
        self._make_xlsx(p)
        ok, out = tools.apply_excel_code(p, "ws['C1'] = 'ملاحظة'\nws['C2'] = 'مرحبا'\nlog('done')")
        self.assertTrue(ok, out)
        import openpyxl
        wb = openpyxl.load_workbook(p)
        self.assertEqual(wb.active["C2"].value, "مرحبا")

    def test_excel_code_forbidden(self):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            p = f.name
        self._make_xlsx(p)
        ok, out = tools.apply_excel_code(p, "import os\nwb.save('/tmp/x')")
        self.assertFalse(ok)

    def test_excel_code_failure_restores(self):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            p = f.name
        self._make_xlsx(p)
        ok, out = tools.apply_excel_code(p, "x = 1/0")
        self.assertFalse(ok)
        import openpyxl
        wb = openpyxl.load_workbook(p)
        self.assertEqual(wb.active["B2"].value, 100)  # ما تخرب الملف


class TestSelfEdit(unittest.TestCase):
    def test_revert_empty(self):
        fake_dir = tempfile.mkdtemp(prefix="ceo-selfedit-")
        old_agent, old_backups = selfedit.AGENT_DIR, selfedit.BACKUP_ROOT
        selfedit.AGENT_DIR, selfedit.BACKUP_ROOT = fake_dir, os.path.join(fake_dir, ".backups")
        try:
            ok, _ = selfedit.revert_last()
            self.assertFalse(ok)
        finally:
            selfedit.AGENT_DIR, selfedit.BACKUP_ROOT = old_agent, old_backups
            shutil.rmtree(fake_dir, ignore_errors=True)

    def test_apply_rejects_bad_payload(self):
        fake = lambda messages, temperature=0.3, max_tokens=100: "كلام عشوائي مو JSON"
        ok, msg = selfedit.apply_instruction("أضف ميزة", fake, log_fn=lambda *_: None)
        self.assertFalse(ok)

    def test_apply_succeeds_and_reverts(self):
        if os.environ.get("CEO_SELFTEST_NESTED"):
            self.skipTest("nested self-edit test")
        fake_dir = tempfile.mkdtemp(prefix="ceo-selfedit-")
        for path in os.listdir(BASE):
            if path.endswith((".py", ".md")):
                shutil.copy2(os.path.join(BASE, path), os.path.join(fake_dir, path))
        old_agent, old_backups = selfedit.AGENT_DIR, selfedit.BACKUP_ROOT
        selfedit.AGENT_DIR, selfedit.BACKUP_ROOT = fake_dir, os.path.join(fake_dir, ".backups")
        env_marker = os.environ.get("CEO_SELFTEST_NESTED")
        os.environ["CEO_SELFTEST_NESTED"] = "1"
        try:
            with open(os.path.join(fake_dir, "README_AR.md"), encoding="utf-8") as fh:
                readme = fh.read()
            brain_stub = lambda messages, temperature=0.3, max_tokens=100: json.dumps({
                "plan": "إضافة ملحوظة بالميمو",
                "files": [{"path": "README_AR.md",
                           "content": readme + "\n<!-- test edit -->\n"}],
            })
            ok, msg = selfedit.apply_instruction("أضف ملحوظة بالـ README", brain_stub, log_fn=lambda *_: None)
            self.assertTrue(ok, msg)
            self.assertIn("test edit", open(os.path.join(fake_dir, "README_AR.md"), encoding="utf-8").read())
            ok2, _ = selfedit.revert_last()
            self.assertTrue(ok2)
            self.assertNotIn("test edit", open(os.path.join(fake_dir, "README_AR.md"), encoding="utf-8").read())
        finally:
            if env_marker is None:
                os.environ.pop("CEO_SELFTEST_NESTED", None)
            selfedit.AGENT_DIR, selfedit.BACKUP_ROOT = old_agent, old_backups
            shutil.rmtree(fake_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
