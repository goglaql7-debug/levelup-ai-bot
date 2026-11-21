import unittest
from collections import deque

from core import allowed_to_ask, build_model_input, get_instructions, split_long_text


class BotTest(unittest.TestCase):
    def test_split_large_text(self):
        text = ("Matematika javobi bir necha qator.\n" * 300).strip()
        parts = split_long_text(text)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(p) <= 3900 for p in parts))
        self.assertEqual(" ".join(parts).split(), text.split())

    def test_chunk_no_spaces(self):
        parts = split_long_text("x" * 8001)
        self.assertEqual("".join(parts), "x" * 8001)
        self.assertEqual([len(part) for part in parts], [3900, 3900, 201])

    def test_modes(self):
        self.assertIn("SAT", get_instructions("sat"))
        self.assertIn("milliy", get_instructions("milliy").lower())
        self.assertIn("umumiy", get_instructions("unknown"))

    def test_rate_limit(self):
        times = deque()
        self.assertTrue(allowed_to_ask(times, 100, 2))
        self.assertTrue(allowed_to_ask(times, 101, 2))
        self.assertFalse(allowed_to_ask(times, 102, 2))
        self.assertTrue(allowed_to_ask(times, 3701, 2))

    def test_text_message(self):
        msgs = build_model_input([], "2x=10")
        self.assertEqual(msgs[0], {"role": "user", "content": "2x=10"})

    def test_photo_message(self):
        msgs = build_model_input([], "Misolni yech", image_bytes=b"\xff\xd8\xff")
        self.assertEqual(msgs[0]["content"][1]["type"], "input_image")
        self.assertIn("base64", msgs[0]["content"][1]["image_url"])


if __name__ == "__main__":
    unittest.main()
