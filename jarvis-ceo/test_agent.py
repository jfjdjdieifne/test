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


class TestIntegrations(unittest.TestCase):
    def test_social_status_shape(self):
        import social
        st = social.status()
        self.assertEqual(set(st), {"x", "facebook", "instagram"})
        self.assertFalse(st["x"])  # بلا مفاتيح بالاختبار

    def test_github_whoami_without_token(self):
        import github
        os.environ.pop("GITHUB_TOKEN", None)
        github.TOKEN = ""
        res = github.whoami()
        self.assertFalse(res["ok"])

    def test_gmail_not_configured(self):
        import gmail
        gmail.ADDR = ""
        gmail.APP_PASSWORD = ""
        self.assertFalse(gmail.configured())

    def test_draft_roundtrip(self):
        payload = {"kind": "email", "to": "x@y.com", "subject": "s", "body": "b"}
        db.kv_set("draft:test123", json.dumps(payload, ensure_ascii=False))
        loaded = json.loads(db.kv_get("draft:test123"))
        self.assertEqual(loaded["to"], "x@y.com")
        self.assertEqual(loaded["kind"], "email")

    def test_notes_fts(self):
        import db as dbmod
        dbmod.notes_add("اتفاق مع دكتور العيادة: 1500 دولار للمهمة كاملة", "test")
        hits = dbmod.notes_search("العيادة")
        self.assertTrue(any("1500" in h["text"] for h in hits))
        self.assertGreaterEqual(dbmod.notes_count(), 1)

    def test_git_push_backup_no_token(self):
        # بلا توكن — ما بيعمل ولا شيء وما بيرفع خطأ
        os.environ.pop("GITHUB_TOKEN", None)
        os.environ.pop("GITHUB_OWNER", None)
        selfedit._git_push_backup("20990101-000000")

    def test_debate_three_call_structure(self):
        os.environ.setdefault("TELEGRAM_BOT_TOKEN", "dummy-for-tests")
        import agent
        import brain as brain_mod
        calls = []
        def stub(msgs, temperature=0.6, max_tokens=None):
            calls.append(msgs[0]["content"])
            return "جواب تجريبي للوكيل"
        original = brain_mod.chat
        original_send = agent.send_text
        brain_mod.chat = stub
        agent.send_text = lambda *a, **k: None
        try:
            out = agent.handle_debate(1, "هل استثمر مبلغ كبير هلأ؟")
        finally:
            brain_mod.chat = original
            agent.send_text = original_send
        self.assertEqual(len(calls), 3)  # متفائل + متشائم + قاضي
        self.assertIn("القاضي", out)

    def test_opportunity_none_without_tavily(self):
        os.environ.setdefault("TELEGRAM_BOT_TOKEN", "dummy-for-tests")
        import agent
        import tools as tools_mod
        old = tools_mod.TAVILY_API_KEY
        tools_mod.TAVILY_API_KEY = ""
        try:
            self.assertIsNone(agent.opportunity_of_the_day())
        finally:
            tools_mod.TAVILY_API_KEY = old


class TestNewModules(unittest.TestCase):
    def test_reminders(self):
        import db as dbmod
        rid = dbmod.add_reminder(777, "راجع مثال الساعة 9", "daily", "09:00")
        rows = dbmod.list_reminders(777)
        self.assertTrue(any(r["id"] == rid for r in rows))
        self.assertEqual(dbmod.due_reminders(time.time()), [])  # بكرة الصبح لسا
        self.assertTrue(dbmod.delete_reminder(rid, 777))

    def test_store_env_var(self):
        import integrations
        path = os.path.join(tempfile.mkdtemp(), "test.env")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("GITHUB_TOKEN=old\nCOARENA_API_KEY=keep\n")
        ok, _ = integrations.store_env_var("GITHUB_TOKEN", "newtoken123", path=path)
        self.assertTrue(ok)
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("GITHUB_TOKEN=newtoken123", content)
        self.assertIn("COARENA_API_KEY=keep", content)
        self.assertEqual(oct(os.stat(path).st_mode & 0o777), "0o600")
        ok2, _ = integrations.store_env_var("bad name!", "x", path=path)
        self.assertFalse(ok2)

    def test_image_url(self):
        import images
        url = images.image_url("عيادة أسنان حديثة")
        self.assertIn("image.pollinations.ai", url)
        self.assertTrue(url.startswith("https://"))

    def test_project_module(self):
        import project
        fake = tempfile.mkdtemp()
        with open(os.path.join(fake, "README.md"), "w", encoding="utf-8") as fh:
            fh.write("# مشروع تجريبي\nهاد هو المشروح.")
        os.makedirs(os.path.join(fake, "src"))
        with open(os.path.join(fake, "src", "app.py"), "w", encoding="utf-8") as fh:
            fh.write("def main():\n    printhello = 'demo'\n")
        self.assertIn("src/", project.tree(fake))
        content, err = project.read_file("README.md", fake)
        self.assertIn("مشروع تجريبي", content)
        _, err2 = project.read_file("../secret.txt", fake)
        self.assertIsNotNone(err2)  # ما بيطلع بره المجلد
        hits = project.search("printhello", fake)
        self.assertTrue(hits)
        summ = project.summary(fake, refresh=True)
        self.assertIn("README", summ)

    def test_pool_keys_allowed(self):
        import integrations
        for name in ("COARENA_API_KEYS", "GEMINI_TTS_API_KEYS", "COARENA_API_KEY"):
            self.assertTrue(integrations.env_var_allowed(name), name)

    def test_steps_for(self):
        import integrations
        sid, steps = integrations.steps_for("الجيميل")
        self.assertEqual(sid, "gmail")
        self.assertIn("apppasswords", steps)
        sid2, steps2 = integrations.steps_for("شيء غريب")
        self.assertIsNone(sid2)


class TestKeyImport(unittest.TestCase):
    def test_parse_mixed_messy(self):
        import keyimport
        text = (
            "هيدي كل مفاتيحي يا عزيزي:\n"
            "coarena: coarena_sk-livekey1234567890 (للفايبل)\n"
            "جيميني: AIzaSyD-1234567890abcdefghij-ABCD_xyz — للصوت\n"
            "TAVILY_API_KEY=tvly-abc123def456ghi\n"
            "bearer github_pat_a1b2c3d4e5f6g7h8i9j0k1l2m3 (لجيتهاب)\n"
            "شغلة تانية مو مفتاح: السلام عليكم\n"
        )
        mapping, skipped = keyimport.parse_bulk_text(text)
        self.assertEqual(mapping.get("COARENA_API_KEY"), "coarena_sk-livekey1234567890")
        self.assertEqual(mapping.get("GEMINI_API_KEY"), "AIzaSyD-1234567890abcdefghij-ABCD_xyz")
        self.assertEqual(mapping.get("TAVILY_API_KEY"), "tvly-abc123def456ghi")
        self.assertEqual(mapping.get("GITHUB_TOKEN"), "github_pat_a1b2c3d4e5f6g7h8i9j0k1l2m3")
        self.assertNotIn("السلام عليكم", mapping.values())

    def test_parse_exact_assignment_and_duplicates(self):
        import keyimport
        text = "GEMINI_API_KEY=AIza-first-key-12345678\nGEMINI_API_KEY=AIza-second-key-87654321\n"
        mapping, _ = keyimport.parse_bulk_text(text)
        self.assertEqual(mapping["GEMINI_API_KEY"], "AIza-second-key-87654321")

    def test_parse_numbers_are_not_keys(self):
        import keyimport
        mapping, skipped = keyimport.parse_bulk_text("سعر الذهب 2785 دولار\nاللون ازرق")
        self.assertEqual(mapping, {})

    def test_apply_bulk_saves_and_masks(self):
        import keyimport, integrations
        path = os.path.join(tempfile.mkdtemp(), "test.env")
        os.environ["CEO_ENV_PATH"] = path
        integrations.ENV_PATH = path
        try:
            summary, saved = keyimport.apply_bulk(999,
                "coarena: coarena_sk-livekey1234567890abc\n"
                "tavily: tvly-zzz-pytest-12345",
                delete_fn=lambda: None)
            self.assertIn("COARENA_API_KEY", saved)
            self.assertIn("TAVILY_API_KEY", saved)
            body = open(path, encoding="utf-8").read()
            self.assertNotIn("coarena_sk-livekey1234567890", summary)   # ما بنطبع القيم
            self.assertIn("COARENA_API_KEY=coarena_sk-livekey1234567890", body)
        finally:
            integrations.ENV_PATH = os.path.expanduser("~/jarvis-ceo.env")
            os.environ.pop("CEO_ENV_PATH", None)

    def test_final_report_structure(self):
        import keyimport
        txt = keyimport.final_report()
        self.assertIn("COARENA_API_KEY", txt)


class TestBulkAutoDetect(unittest.TestCase):
    def test_looks_like_bulk_true(self):
        import keyimport
        text = "coarena: sk-livekey1234567890abc\nمفاتيحي: AIzaSyD-xxxxxxxxxxxxxxxxxxxx-xxxxx"
        self.assertTrue(keyimport.looks_like_bulk(text))

    def test_looks_like_bulk_false(self):
        import keyimport
        self.assertFalse(keyimport.looks_like_bulk("السلام عليكم، كيف الحال اليوم؟"))
        self.assertFalse(keyimport.looks_like_bulk(""))
        self.assertFalse(keyimport.looks_like_bulk("شوفي جيميني بكرة تقدري تيجي؟"))

    def test_looks_like_bulk_arabic_labels(self):
        import keyimport
        text = "كوارنيا: cq_live_9f8e7d6c5b4a39281706f5e4\nجيميني: AIzaSyABCDEFGHIJKLMNOPQRSTUVWX12345"
        self.assertTrue(keyimport.looks_like_bulk(text))

    def test_notes_clear(self):
        import db as dbmod
        dbmod.notes_add("ملاحظة مؤقتة", "test")
        self.assertTrue(dbmod.notes_clear())
        self.assertEqual(dbmod.notes_count(), 0)


if __name__ == "__main__":
    unittest.main()
