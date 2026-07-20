import io
from pathlib import Path
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock, patch

import digest_common
import uk_news


class SplitMessageTests(unittest.TestCase):
    def test_short_message_is_unchanged(self):
        self.assertEqual(digest_common.split_message("hello", 10), ["hello"])

    def test_splits_at_line_boundaries(self):
        parts = digest_common.split_message("alpha\nbeta\ngamma", 10)
        self.assertEqual(parts, ["alpha\nbeta", "gamma"])
        self.assertTrue(all(len(part) <= 10 for part in parts))

    def test_hard_splits_single_oversized_line(self):
        parts = digest_common.split_message("x" * 25, 10)
        self.assertEqual([len(part) for part in parts], [10, 10, 5])

    def test_rejects_invalid_limit(self):
        with self.assertRaises(ValueError):
            digest_common.split_message("text", 0)


class TelegramTests(unittest.TestCase):
    @patch("digest_common.requests.post")
    def test_send_posts_every_bounded_part(self, post):
        post.return_value.raise_for_status = Mock()
        digest_common.send_telegram("first line\n" + "x" * 4100, "token", "chat")
        self.assertGreaterEqual(post.call_count, 2)
        for call in post.call_args_list:
            self.assertLessEqual(
                len(call.kwargs["json"]["text"]), digest_common.TELEGRAM_MAX_LENGTH
            )
            self.assertNotIn("token", call.kwargs["json"])

    def test_dry_run_reports_part_count(self):
        output = io.StringIO()
        with redirect_stdout(output):
            digest_common.print_dry_run("hello", "No delivery")
        self.assertIn("[DRY RUN] Message parts: 1", output.getvalue())
        self.assertIn("No delivery", output.getvalue())


class FeedFixtureTests(unittest.TestCase):
    @patch("uk_news.feedparser.parse")
    def test_uk_feed_parsing_uses_offline_fixture(self, parse):
        parse.return_value = SimpleNamespace(
            entries=[
                {
                    "title": "Story A",
                    "summary": "Summary A",
                    "link": "https://example.test/a",
                },
                {
                    "title": "Story B",
                    "summary": "Summary B",
                    "link": "https://example.test/b",
                },
            ]
        )
        stories = uk_news.fetch_news("fixture://uk", limit=1)
        self.assertEqual(stories, [("Story A", "Summary A", "https://example.test/a")])
        parse.assert_called_once_with("fixture://uk")

    @patch(
        "uk_news.fetch_news",
        return_value=[
            ("Fixture story", "Fixture summary", "https://example.test/story")
        ],
    )
    @patch("uk_news.send_telegram")
    def test_uk_digest_dry_run_never_sends(self, send, _fetch):
        output = io.StringIO()
        with redirect_stdout(output):
            uk_news.main(dry_run=True)
        send.assert_not_called()
        self.assertIn("Fixture story", output.getvalue())
        self.assertIn("[DRY RUN]", output.getvalue())


class DryRunContractTests(unittest.TestCase):
    def test_every_executable_digest_exposes_dry_run(self):
        root = Path(__file__).resolve().parents[1]
        excluded = {"digest_common.py"}
        scripts = [path for path in root.glob("*.py") if path.name not in excluded]
        self.assertTrue(scripts)
        missing = [
            path.name
            for path in scripts
            if "--dry-run" not in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(missing, [], f"Digest scripts without --dry-run: {missing}")


if __name__ == "__main__":
    unittest.main()
