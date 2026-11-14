#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبارات وحدات لرعد — كلها محلية، بلا شبكة."""
import math
import unittest

import raad

class TestIndicators(unittest.TestCase):
    def test_ema_flat(self):
        self.assertEqual(raad.ema([5, 5, 5, 5], 3)[-1], 5)

    def test_ema_trend(self):
        seq = [float(i) for i in range(1, 60)]
        out = raad.ema(seq, 10)
        self.assertGreater(out[-1], out[-10])

    def test_atr_positive(self):
        bars = [{"ts": i, "o": 100, "h": 105, "l": 99, "c": 103, "v": 1} for i in range(30)]
        self.assertTrue(all(v > 0 for v in raad.atr(bars)))

    def test_pct_rank(self):
        vals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.assertEqual(raad.pct_rank(vals, 10), 100.0)
        self.assertEqual(raad.pct_rank(vals, 0), 0.0)

class TestLedger(unittest.TestCase):
    def setUp(self):
        import tempfile, os
        os.environ["RAAD_DB"] = tempfile.mktemp(suffix=".db")
        raad.RAAD_DB = os.environ["RAAD_DB"]

    def tearDown(self):
        import os
        try:
            os.remove(raad.RAAD_DB)
        except OSError:
            pass

    def test_log_and_stats_empty(self):
        s = raad.stats()
        self.assertEqual(s["n"], 0)
        cid = raad.log_call({"symbol": "TESTUSDT", "tf": "4h", "side": "long",
                             "entry": 100.0, "stop": 95.0, "target": 112.5, "atr": 2.0,
                             "confidence": 70, "regime": "ترند صاعد", "reason": "اختبار"})
        self.assertGreater(cid, 0)
        with raad.db() as conn:
            conn.execute("UPDATE calls SET status='win', r_multiple=2.5, pnl_pct=12.5 WHERE id=?", (cid,))
        s = raad.stats()
        self.assertEqual(s["n"], 1)
        self.assertEqual(s["win_rate"], 100.0)

if __name__ == "__main__":
    unittest.main()
