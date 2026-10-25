import tempfile
import unittest
from pathlib import Path

from tradebot.core import Bar, FindingsStore, PatternBacktester


class BacktestTests(unittest.TestCase):
    def test_event_study_uses_close_to_close_forward_return(self):
        bars = [
            Bar("2024-01-02", 10, 11, 9, 10.5),
            Bar("2024-01-03", 11, 13, 10, 12),
            Bar("2024-01-04", 9, 10, 8, 10),
        ]

        result = PatternBacktester().backtest(bars, "green_any", forward_bars=1)

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["win_rate_pct"], 50.0)
        self.assertAlmostEqual(result["events"][0]["return_pct"], (12 - 10.5) / 10.5 * 100)
        self.assertAlmostEqual(result["events"][1]["return_pct"], (10 - 12) / 12 * 100)
        self.assertAlmostEqual(result["mean_return_pct"], (result["events"][0]["return_pct"] + result["events"][1]["return_pct"]) / 2)


class FindingsTests(unittest.TestCase):
    def test_lookup_is_scoped_to_symbol_pattern_and_window(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FindingsStore(Path(directory) / "findings.db")
            store.save("aapl", "hammer", "1D:2024:5", "AAPL result", {"count": 4})
            store.save("AAPL", "hammer", "1D:2024:10", "Different horizon", {"count": 2})
            store.save("MSFT", "hammer", "1D:2024:5", "Different symbol", {"count": 3})

            matches = store.lookup("AAPL", "hammer", "1D:2024:5")

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["symbol"], "AAPL")
        self.assertEqual(matches[0]["summary"], "AAPL result")
        self.assertEqual(matches[0]["result"], {"count": 4})


if __name__ == "__main__":
    unittest.main()
