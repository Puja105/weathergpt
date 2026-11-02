import unittest

from backend.rag import chunk_text


class RagChunkingTests(unittest.TestCase):
    def test_empty_text_returns_no_chunks(self):
        self.assertEqual(chunk_text("   "), [])

    def test_short_text_returns_one_chunk(self):
        self.assertEqual(chunk_text("WeatherGPT reference."), ["WeatherGPT reference."])

    def test_long_text_is_chunked_with_overlap(self):
        text = " ".join(f"word{i}" for i in range(100))
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunks))
        self.assertLessEqual(max(map(len, chunks)), 100)

    def test_invalid_overlap_is_rejected(self):
        with self.assertRaises(ValueError):
            chunk_text("some text", chunk_size=10, overlap=10)


if __name__ == "__main__":
    unittest.main()
