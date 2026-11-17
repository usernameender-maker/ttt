
## Word game prototype

`ievf.wordgame` provides deterministic letter scoring and word-ladder validation.
It is a local game utility, not a word corpus or next-word prediction model.

```python
from ievf.wordgame import best_move, is_valid_word_chain

print(best_move(["dog", "cat", "elephant"]).word)
print(is_valid_word_chain("code", "node"))
```

A supplied dictionary is used as a membership allowlist; an empty dictionary
rejects all words. Run its standard-library tests with:

```sh
python -m unittest discover -s tests -p test_wordgame.py -v
```
