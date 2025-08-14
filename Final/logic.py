import os
import re
import json
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

nltk.download('wordnet', quiet=True)
nltk.download('punkt', quiet=True)


class CrosswordSolver:
    def __init__(self, word_file="words.txt", feedback_file="feedback.json"):
        self.word_list = self._load_word_db(word_file)
        if not self.word_list:
            raise FileNotFoundError(f"Word list {word_file} not loaded. Exiting.")
        self.feedback_db = self._load_feedback_db(feedback_file)
        self.lemmatizer = WordNetLemmatizer()

    def _load_word_db(self, file_path):
        path = os.path.join(os.path.dirname(__file__), file_path)
        try:
            with open(path, 'r') as f:
                return [line.strip().upper() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Error: {path} not found.")
            return []

    def _load_feedback_db(self, file_path):
        path = os.path.join(os.path.dirname(__file__), file_path)
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_feedback(self, clue, pattern, correct_word):
        key = str((clue, pattern.upper()))
        self.feedback_db[key] = correct_word.upper()
        with open(os.path.join(os.path.dirname(__file__), "feedback.json"), 'w') as f:
            json.dump(self.feedback_db, f, indent=4)

    def pattern_to_regex(self, pattern: str) -> str:
        if not pattern.strip():
            return r"^[A-Z]{2,15}$"
        return f"^{''.join('[A-Z]' if not c.isalpha() else c.upper() for c in pattern)}$"

    def find_matches(self, pattern: str, clue: str) -> list:
        try:
            regex = self.pattern_to_regex(pattern)
            matches = [w for w in self.word_list if re.match(regex, w)]
            if not pattern or all(c == '?' for c in pattern):
                tokens = word_tokenize(clue.lower())
                est_len = max(2, min(15, int(len(tokens) * 1.5)))
                matches = [w for w in matches if abs(len(w) - est_len) <= 3]
            return matches
        except Exception:
            return self.word_list[:100]

    def rank_by_clue(self, clue: str, matches: list, pattern: str) -> list:
        if not clue:
            return [(m, 0.0, "No clue provided") for m in matches[:3]]

        key = str((clue, pattern.upper()))
        ranked = []

        correct = self.feedback_db.get(key)
        if correct and re.match(self.pattern_to_regex(pattern), correct):
            syns = wordnet.synsets(correct.lower())
            definition = syns[0].definition() if syns else "User-provided"
            ranked.append((correct, 1.0, definition))

        other_matches = [m for m in matches if m != correct] if correct else matches
        ranked.extend(self._wordnet_ranking(clue, other_matches)[:2])
        if not ranked:
            ranked = self._wordnet_ranking(clue, matches)[:3]

        return ranked

    def _wordnet_ranking(self, clue: str, matches: list) -> list:
        clue_words = {
            self.lemmatizer.lemmatize(w.lower()) for w in word_tokenize(clue.lower())
        }
        ranked = []
        for word in matches:
            syns = wordnet.synsets(word.lower())
            if not syns:
                ranked.append((word, 0.0, "No definition"))
                continue
            def_words = {
                self.lemmatizer.lemmatize(w.lower())
                for w in word_tokenize(syns[0].definition())
            }
            score = len(clue_words & def_words) * 0.5
            for s in syns:
                score += len(clue_words & set(s.name().split('.'))) * 0.7
                for h in s.hypernyms():
                    score += len(clue_words & set(h.name().split('.'))) * 0.3
            ranked.append((word, score, syns[0].definition()))
        return sorted(ranked, key=lambda x: x[1], reverse=True)

    def solve(self, clue: str, pattern: str) -> dict:
        matches = self.find_matches(pattern, clue)
        ranked = self.rank_by_clue(clue, matches, pattern)
        return {(clue, pattern.upper()): ranked}
