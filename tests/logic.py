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
from typing import List, Tuple, Dict, Optional, Set

# NOTE: optional downloads; keeps import-time behavior but wrapped
try:
    nltk.data.find('corpora/wordnet')
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)


class CrosswordSolver:
    """
    Improved Crossword solver:
      - fixed unreachable code in find_matches (POS pruning now runs)
      - normalized synset lookups to lowercase to make caching effective
      - use lemma_names() and definitions for meaningful semantic tokens
      - filter tokenization to alphabetic tokens
      - safer handling of empty / wildcard patterns
    """

    def __init__(self, feedback_file: str = "feedback.json", min_word_len: int = 2, max_word_len: int = 15):
        self.feedback_file = feedback_file
        self.min_word_len = min_word_len
        self.max_word_len = max_word_len

        # Build master word list from WordNet (uppercase for easy GUI matching)
        self.word_list: List[str] = self._build_word_list_from_wordnet(min_word_len, max_word_len)
        if not self.word_list:
            raise FileNotFoundError("WordNet-based word list could not be created.")

        # Indexes for fast search
        self.by_len: Dict[int, List[str]] = defaultdict(list)
        self.pos_char: Dict[Tuple[int, str], Set[str]] = defaultdict(set)
        for w in self.word_list:
            L = len(w)
            self.by_len[L].append(w)
            for i, ch in enumerate(w):
                # w is stored uppercase; store char as uppercase
                self.pos_char[(i, ch)].add(w)

        # Load feedback DB (may be empty)
        self.feedback_db = self._load_feedback_db(feedback_file)

        # Lemmatizer
        self.lemmatizer = WordNetLemmatizer()

    def _build_word_list_from_wordnet(self, min_len: int, max_len: int) -> List[str]:
        lemmas = set()
        for syn in wordnet.all_synsets():
            # gather lemma names (these are the actual words)
            for lname in syn.lemma_names():
                # lemma_names may include underscores; we skip multiword entries
                if "_" in lname:
                    continue
                cleaned = lname.strip().upper()
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

    def pattern_to_regex(self, pattern: Optional[str]) -> str:
        """
        Convert a pattern like 'A__LE' or 'A.LE' or None into a regex string.
        Non-alpha characters are treated as wildcards for a single letter.
        If pattern is None or empty, return a regex that enforces min/max length.
        """
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

    # Normalize word to lowercase before calling WordNet; caching uses normalized form
    @lru_cache(maxsize=100000)
    def _cached_synsets(self, word: str, pos=None):
        wn_word = (word or "").lower()
        return wordnet.synsets(wn_word, pos=pos)

    @lru_cache(maxsize=100000)
    def _cached_primary_def(self, word: str) -> str:
        syns = self._cached_synsets(word)
        return syns[0].definition() if syns else "No definition"

    def find_matches(self, pattern: str, clue: str = "") -> List[str]:
        """
        Find candidate words matching the pattern using positional indexes.
        Supports patterns where unknown letters are any non-alpha character.
        """
        pattern = (pattern or "").strip()
        if pattern == "":
            # no explicit pattern: return all words within allowed length bounds
            candidate_words = set()
            for L in range(self.min_word_len, self.max_word_len + 1):
                candidate_words.update(self.by_len.get(L, []))
        else:
            pattern_len = len(pattern)
            candidate_words = set(self.by_len.get(pattern_len, []))
            if not candidate_words:
                return []

            # filter by known characters
            for i, ch in enumerate(pattern):
                if ch.isalpha():
                    matching_subset = self.pos_char.get((i, ch.upper()), set())
                    candidate_words &= matching_subset
                    if not candidate_words:
                        break

        # Now do optional POS-aware pruning using clue (if it helps)
        # Build alpha-only tokens and tag them
        tokens = [t for t in word_tokenize(clue) if t.isalpha()]
        if tokens:
            try:
                # use the last token heuristic (as before) but normalized
                last_token = tokens[-1]
                tag = pos_tag([last_token])[0][1]
                guessed_pos = self._wn_pos(tag)
                if guessed_pos:
                    pruned = [w for w in candidate_words if self._cached_synsets(w.lower(), pos=guessed_pos)]
                    if pruned:
                        candidate_words = set(pruned)
            except (LookupError, IndexError):
                # if POS tagging fails just continue with unpruned candidates
                pass

        matches = sorted(candidate_words)
        return matches

    def rank_by_clue(self, clue: str, matches: List[str], pattern: str) -> List[Tuple[str, float, str]]:
        if not matches:
            return []

        if not clue:
            # no clue: simple fallback list with zero scores
            return [(m, 0.0, self._cached_primary_def(m.lower())) for m in matches[:3]]

        key = str((clue, pattern.upper()))
        ranked: List[Tuple[str, float, str]] = []

        # strong bias for user feedback
        correct = self.feedback_db.get(key)
        if correct and re.match(self.pattern_to_regex(pattern), correct):
            ranked.append((correct, 10.0, self._cached_primary_def(correct.lower())))

        # Score the remaining candidates with WordNet-aware heuristics
        other_matches = [m for m in matches if (not correct or m != correct)]
        ranked.extend(self._wordnet_ranking(clue, other_matches)[:3])

        # If nothing has been ranked (rare), return top raw matches
        if not ranked:
            ranked = [(m, 0.0, self._cached_primary_def(m.lower())) for m in matches[:3]]

        return ranked

    def _wordnet_ranking(self, clue: str, matches: List[str]) -> List[Tuple[str, float, str]]:
        """
        Improved ranking:
         - use alpha-only lemmatized clue tokens
         - compare with lemma_names() from synsets and hypernyms via lemma names
         - produce stable scores; higher is better
        """
        # Prepare clue words: alpha-only, lemmatized
        clue_tokens = [t.lower() for t in word_tokenize(clue) if t.isalpha()]
        clue_words = {self.lemmatizer.lemmatize(w) for w in clue_tokens}

        ranked: List[Tuple[str, float, str]] = []
        for word in matches:
            syns = self._cached_synsets(word.lower())
            if not syns:
                ranked.append((word, 0.0, "No definition"))
                continue

            primary_def = syns[0].definition() if syns else "No definition"

            # tokens from primary definition
            def_tokens = [t.lower() for t in word_tokenize(primary_def) if t.isalpha()]
            def_words = {self.lemmatizer.lemmatize(w) for w in def_tokens}

            score = 0.0
            # Match clue words to def words (weight 1)
            score += len(clue_words & def_words) * 1.0

            # Match clue words to lemma names across all synsets (weight 1.5)
            for s in syns:
                lemmas = {l.lower() for l in s.lemma_names()}
                lemmas_lemmatized = {self.lemmatizer.lemmatize(l.replace('_', ' ')) for l in lemmas}
                score += len(clue_words & lemmas_lemmatized) * 1.5

                # hypernyms lemma names (weight 0.6)
                for h in s.hypernyms():
                    h_lemmas = {l.lower() for l in h.lemma_names()}
                    h_lemmas_lem = {self.lemmatizer.lemmatize(l.replace('_', ' ')) for l in h_lemmas}
                    score += len(clue_words & h_lemmas_lem) * 0.6

            ranked.append((word, score, primary_def))

        # sort by score (desc), tie-break lexicographically
        return sorted(ranked, key=lambda x: (x[1], x[0]), reverse=True)

    def solve(self, clue: str, pattern: str) -> dict:
        matches = self.find_matches(pattern, clue)
        ranked = self.rank_by_clue(clue, matches, pattern)
        # consistent output shape: a dict keyed by (clue, PATTERN)
        return {(clue, pattern.upper()): ranked}
