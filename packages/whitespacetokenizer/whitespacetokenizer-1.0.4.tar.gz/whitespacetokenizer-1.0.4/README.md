# whitespacetokenizer
Fast python whitespace tokenizer written in cython that also gives start and end character positions of tokens.

## Installation

    pip install whitespacetokenizer

## Usage

```python
from whitespacetokenizer import whitespace_tokenizer

text = "Hello, world! How are you?"
tokens = whitespace_tokenizer(text)

print(tokens)
# [("Hello,", 0, 6), ("world!", 7, 13), ("How", 14, 17), ("are", 18, 21), ("you?", 22, 26)]
```
