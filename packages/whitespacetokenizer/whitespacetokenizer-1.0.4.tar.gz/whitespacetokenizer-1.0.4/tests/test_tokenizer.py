import unittest
from whitespacetokenizer import whitespace_tokenizer
from whitespacetokenizer.tokenizer import WhitespaceTokenizer


class TestWhitespaceTokenizer(unittest.TestCase):
    def test_tokenize_empty(self):
        self.assertEqual(whitespace_tokenizer(""), [])

    def test_tokenize_single(self):
        self.assertEqual(whitespace_tokenizer("hello"), [("hello", 0, 5)])

    def test_tokenize_multiple(self):
        self.assertEqual(whitespace_tokenizer("hello world"), [("hello", 0, 5), ("world", 6, 11)])

    def test_tokenize_multiple_spaces(self):
        self.assertEqual(whitespace_tokenizer("hello  world"), [("hello", 0, 5), ("world", 7, 12)])

    def test_tokenize_multiple_newlines(self):
        self.assertEqual(whitespace_tokenizer("hello\nworld"), [("hello", 0, 5), ("world", 6, 11)])

    def test_tokenize_multiple_tabs(self):
        self.assertEqual(whitespace_tokenizer("hello\tworld"), [("hello", 0, 5), ("world", 6, 11)])

    def test_tokenize_multiple_mixed(self):
        self.assertEqual(whitespace_tokenizer("hello \tworld"), [("hello", 0, 5), ("world", 7, 12)])

    def test_readme_case(self):
        self.assertEqual(
            whitespace_tokenizer("Hello, world! How are you?"),
            [("Hello,", 0, 6), ("world!", 7, 13), ("How", 14, 17), ("are", 18, 21), ("you?", 22, 26)]
        )


class TestWhitespaceTokenizerClass(unittest.TestCase):

    def setUp(self):
        self.tokenizer = WhitespaceTokenizer()
    def test_tokenize_empty(self):
        self.assertEqual(self.tokenizer(""), [])

    def test_tokenize_single(self):
        self.assertEqual(self.tokenizer("hello"), [(0, 0, 5)])

    def test_tokenize_multiple(self):
        self.assertEqual(self.tokenizer("hello world"), [(0, 0, 5), (1, 6, 11)])

    def test_tokenize_multiple_spaces(self):
        self.assertEqual(self.tokenizer("hello  world"), [(0, 0, 5), (1, 7, 12)])

    def test_tokenize_multiple_newlines(self):
        self.assertEqual(self.tokenizer("hello\nworld"), [(0, 0, 5), (1, 6, 11)])

    def test_tokenize_multiple_tabs(self):
        self.assertEqual(self.tokenizer("hello\tworld"), [(0, 0, 5), (1, 6, 11)])

    def test_tokenize_multiple_mixed(self):
        self.assertEqual(self.tokenizer("hello \tworld"), [(0, 0, 5), (1, 7, 12)])

    def test_tokenize_same(self):
        self.assertEqual(self.tokenizer("hello hello"), [(0, 0, 5), (0, 6, 11)])

    def test_readme_case(self):
        self.assertEqual(
            self.tokenizer("Hello, world! How are you?"),
            [(0, 0, 6), (1, 7, 13), (2, 14, 17), (3, 18, 21), (4, 22, 26)]
        )
