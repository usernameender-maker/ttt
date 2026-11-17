import unittest

from ievf.wordgame import (
    WordMove,
    best_move,
    build_word_game,
    is_valid_word_chain,
    letter_score,
    score_word,
    validate_word_sequence,
)


class WordGameTests(unittest.TestCase):
    def test_letter_scoring(self):
        self.assertEqual(letter_score("a"), 1)
        self.assertEqual(letter_score("Z"), 10)
        self.assertEqual(letter_score("?"), 0)
        with self.assertRaises(ValueError):
            letter_score("ab")

    def test_word_scoring(self):
        self.assertEqual(score_word("cat"), 5)
        self.assertEqual(score_word("quiz"), 22)
        self.assertEqual(score_word(""), 0)
        with self.assertRaises(TypeError):
            score_word(None)

    def test_build_and_best_move(self):
        moves = build_word_game(["dog", "cat", "elephant"])
        self.assertEqual(moves, [
            WordMove("dog", 5, 1),
            WordMove("cat", 5, 2),
            WordMove("elephant", 15, 3),
        ])
        self.assertEqual(best_move(["dog", "cat", "elephant"]).word, "elephant")
        self.assertEqual(best_move(["cat", "dog"]).word, "cat")  # stable tie
        with self.assertRaises(ValueError):
            best_move([])
        with self.assertRaises(TypeError):
            build_word_game("cat")

    def test_word_chain_validation(self):
        self.assertTrue(is_valid_word_chain("cat", "cot"))
        self.assertTrue(is_valid_word_chain("DOG", "dot"))
        self.assertFalse(is_valid_word_chain("cat", "dog"))
        self.assertFalse(is_valid_word_chain("cat", "cats"))
        self.assertFalse(is_valid_word_chain("", ""))
        self.assertFalse(is_valid_word_chain(None, "cat"))

    def test_sequence_validation(self):
        chain = ["cat", "cot", "cog", "dog"]
        self.assertTrue(validate_word_sequence(chain, {"cat", "cot", "cog", "dog"}))
        self.assertFalse(validate_word_sequence(["cat", "dog", "cog"], {"cat", "dog", "cog"}))
        self.assertFalse(validate_word_sequence(chain, set()))
        self.assertFalse(validate_word_sequence([]))
        self.assertFalse(validate_word_sequence(["cat", "cot"], {"cat"}))
        self.assertTrue(validate_word_sequence(["CAT", "cot"], {"cat", "cot"}))
        self.assertFalse(validate_word_sequence("cat"))


if __name__ == "__main__":
    unittest.main()
