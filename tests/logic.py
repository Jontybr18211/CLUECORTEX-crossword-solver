import os
import re
import json
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag
from collections import defaultdict
from functools import lru_cache

# Ensure required NLTK resources are available.
nltk.download('wordnet', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# streak

class CrosswordSolver:
    """
    Crossword solver using WordNet lemmas as the word list.
    Features:
        - Pattern matching (with future-ready indexing hooks)
        - POS-aware pruning from clue
        - Synset-based semantic ranking
        - Feedback persistence
    """

    def __init__(self, feedback_file="feedback.json", min_word_len: int = 2, max_word_len: int = 15):
        self.feedback_file = feedback_file
        self.min_word_len = min_word_len
        self.max_word_len = max_word_len

        # Build master word list from WordNet
        self.word_list = self._build_word_list_from_wordnet(min_word_len, max_word_len)
        if not self.word_list:
            raise FileNotFoundError("WordNet-based word list could not be created.")

        # Prepare for fast future search (length and position indexing)
        self.by_len = defaultdict(list)
        self.pos_char = defaultdict(set)
        for w in self.word_list:
            L = len(w)
            self.by_len[L].append(w)
            for i, ch in enumerate(w):
                self.pos_char[(i, ch)].add(w)

        # Load feedback DB (may be empty)
        self.feedback_db = self._load_feedback_db(feedback_file)

        # Lemmatizer for ranking
        self.lemmatizer = WordNetLemmatizer()

    def _build_word_list_from_wordnet(self, min_len: int, max_len: int) -> list:
        lemmas = set()
        for syn in wordnet.all_synsets():
            for l in syn.lemmas():
                name = l.name()
                if "_" in name:
                    continue
                cleaned = name.strip().upper()
                if cleaned.isalpha() and min_len <= len(cleaned) <= max_len:
                    lemmas.add(cleaned)
        return sorted(lemmas)

    def _resolve_path(self, file_path: str) -> str:
        return file_path if os.path.isabs(file_path) else os.path.join(os.path.dirname(__file__), file_path)

    def _load_feedback_db(self, file_path: str) -> dict:
        path = self._resolve_path(file_path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_feedback(self, clue: str, pattern: str, correct_word: str):
        key = str((clue, pattern.upper()))
        self.feedback_db[key] = correct_word.upper()
        path = self._resolve_path(self.feedback_file)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_db, f, indent=4, ensure_ascii=False)

    def pattern_to_regex(self, pattern: str) -> str:
        pattern = (pattern or "").strip()
        if not pattern:
            return rf"^[A-Z]{{{self.min_word_len},{self.max_word_len}}}$"
        regex_body = ''.join('[A-Z]' if not c.isalpha() else c.upper() for c in pattern)
        return f"^{regex_body}$"

    def _wn_pos(self, tag: str):
        if tag.startswith('N'):
            return wordnet.NOUN
        if tag.startswith('V'):
            return wordnet.VERB
        if tag.startswith('J'):
            return wordnet.ADJ
        if tag.startswith('R'):
            return wordnet.ADV
        return None

    @lru_cache(maxsize=200000)
    def _cached_synsets(self, word: str, pos=None):
        return wordnet.synsets(word, pos=pos)

    @lru_cache(maxsize=200000)
    def _cached_primary_def(self, word: str):
        syns = self._cached_synsets(word)
        return syns[0].definition() if syns else "No definition"

    def find_matches(self, pattern: str, clue: str) -> list:
        # Simple regex scan (replaceable with index-based search later)
        regex = self.pattern_to_regex(pattern)
        matches = [w for w in self.word_list if re.match(regex, w)]

        # POS-aware pruning
        tokens = [t for t in word_tokenize(clue) if t.isalpha()]
        if tokens:
            try:
                last_token = tokens[-1]
                tag = pos_tag([last_token])[0][1]
                guessed_pos = self._wn_pos(tag)
                if guessed_pos:
                    pruned = [w for w in matches if self._cached_synsets(w.lower(), pos=guessed_pos)]
                    if pruned:
                        matches = pruned
            except (LookupError, IndexError):
                pass

        return matches

    def rank_by_clue(self, clue: str, matches: list, pattern: str) -> list:
        if not clue:
            return [(m, 0.0, "No clue provided") for m in matches[:3]]

        key = str((clue, pattern.upper()))
        ranked = []

        correct = self.feedback_db.get(key)
        if correct and re.match(self.pattern_to_regex(pattern), correct):
            ranked.append((correct, 1.0, self._cached_primary_def(correct.lower())))

        other_matches = [m for m in matches if m != correct] if correct else matches
        ranked.extend(self._wordnet_ranking(clue, other_matches)[:2])
        if not ranked:
            ranked = self._wordnet_ranking(clue, matches)[:3]

        return ranked

    def _wordnet_ranking(self, clue: str, matches: list) -> list:
        clue_words = {self.lemmatizer.lemmatize(w.lower()) for w in word_tokenize(clue.lower())}
        ranked = []
        for word in matches:
            syns = self._cached_synsets(word.lower())
            if not syns:
                ranked.append((word, 0.0, "No definition"))
                continue

            primary_def = syns[0].definition()
            def_words = {self.lemmatizer.lemmatize(w.lower()) for w in word_tokenize(primary_def)}
            score = len(clue_words & def_words) * 0.5

            for s in syns:
                syn_name_words = {self.lemmatizer.lemmatize(w.lower()) for w in s.name().replace('.', ' ').split()}
                score += len(clue_words & syn_name_words) * 0.7
                for h in s.hypernyms():
                    hyper_words = {self.lemmatizer.lemmatize(w.lower()) for w in h.name().replace('.', ' ').split()}
                    score += len(clue_words & hyper_words) * 0.3

            ranked.append((word, score, primary_def))

        return sorted(ranked, key=lambda x: x[1], reverse=True)

    def solve(self, clue: str, pattern: str) -> dict:
        matches = self.find_matches(pattern, clue)
        ranked = self.rank_by_clue(clue, matches, pattern)
        return {(clue, pattern.upper()): ranked}
