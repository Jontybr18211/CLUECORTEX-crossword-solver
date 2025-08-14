import os
import re
import json
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Ensure required NLTK resources are available.
nltk.download('wordnet', quiet=True)
nltk.download('punkt', quiet=True)


class CrosswordSolver:
    """
    Crossword solver that uses WordNet (NLTK) as the word source instead of a local words.txt.
    Keeps existing behavior for pattern matching, ranking by clue using WordNet synsets,
    and a simple feedback (correct answers) persistence.
    """

    def __init__(self, feedback_file="feedback.json", min_word_len: int = 2, max_word_len: int = 15):
        """
        :param feedback_file: path or filename for feedback storage (created if missing)
        :param min_word_len: minimum length of words to include from WordNet
        :param max_word_len: maximum length of words to include from WordNet
        """
        self.feedback_file = feedback_file
        self.min_word_len = min_word_len
        self.max_word_len = max_word_len

        # Build word list from WordNet
        self.word_list = self._build_word_list_from_wordnet(self.min_word_len, self.max_word_len)
        if not self.word_list:
            raise FileNotFoundError("WordNet-based word list could not be created. Ensure NLTK WordNet is installed.")

        # Load feedback DB (may be empty)
        self.feedback_db = self._load_feedback_db(self.feedback_file)

        # Lemmatizer for ranking
        self.lemmatizer = WordNetLemmatizer()

    def _build_word_list_from_wordnet(self, min_len: int, max_len: int) -> list:
        """
        Extracts a deduplicated, filtered list of lemmas from WordNet.
        Filters out multi-word lemmas (contains '_'), non-alpha characters, and words outside length bounds.
        Returns uppercase words suitable for pattern matching.
        """
        lemmas = set()
        # Iterate synsets and collect lemma names
        for syn in wordnet.all_synsets():
            for l in syn.lemmas():
                name = l.name()  # lemma names often contain underscores for multi-word expressions
                # Remove underscores (multiword) or skip them — crosswords usually expect single tokens
                if "_" in name:
                    continue
                cleaned = name.strip().upper()
                # Keep only simple alphabetic words within length bounds
                if cleaned.isalpha() and min_len <= len(cleaned) <= max_len:
                    lemmas.add(cleaned)
        return sorted(lemmas)

    def _resolve_path(self, file_path: str) -> str:
        """
        Return an absolute path for a file path that is relative to the module directory if not already absolute.
        """
        if os.path.isabs(file_path):
            return file_path
        return os.path.join(os.path.dirname(__file__), file_path)

    def _load_feedback_db(self, file_path: str) -> dict:
        """
        Loads (or creates) a JSON file used to store user-correct answers for (clue, pattern).
        If file missing or invalid, returns empty dict.
        """
        path = self._resolve_path(file_path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_feedback(self, clue: str, pattern: str, correct_word: str):
        """
        Save a single piece of feedback (mapping (clue, pattern) -> correct_word).
        The feedback file is created/overwritten as JSON each time.
        """
        key = str((clue, pattern.upper()))
        self.feedback_db[key] = correct_word.upper()

        path = self._resolve_path(self.feedback_file)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_db, f, indent=4, ensure_ascii=False)
        except Exception as e:
            # propagate upwards so GUI can show an error if needed
            raise RuntimeError(f"Failed to save feedback to {path}: {e}")

    def pattern_to_regex(self, pattern: str) -> str:
        """
        Convert a pattern like 'C?T' or 'N?B?LE' to a regex string.
        Non-alpha characters (like '?') are treated as unknown letters -> [A-Z].
        If pattern is empty, returns a general length-based regex using configured min/max.
        """
        pattern = (pattern or "").strip()
        if not pattern:
            return rf"^[A-Z]{{{self.min_word_len},{self.max_word_len}}}$"
        # Each non-alpha becomes [A-Z], letters are kept uppercase
        regex_body = ''.join('[A-Z]' if not c.isalpha() else c.upper() for c in pattern)
        return f"^{regex_body}$"

    def find_matches(self, pattern: str, clue: str) -> list:
        """
        Find words from the WordNet-built word list that match the supplied pattern.
        If pattern is empty or all question marks, use an estimated length from the clue to narrow candidates.
        """
        try:
            regex = self.pattern_to_regex(pattern)
            matches = [w for w in self.word_list if re.match(regex, w)]

            # If the pattern contains no fixed letters (empty or all '?'), estimate length from clue tokens
            if not pattern or all(c == '?' for c in pattern):
                tokens = word_tokenize(clue.lower())
                # Estimate length using token count heuristic, then clamp to min/max
                est_len = int(max(self.min_word_len, min(self.max_word_len, max(2, int(len(tokens) * 1.5)))))
                matches = [w for w in matches if abs(len(w) - est_len) <= 3]

            return matches
        except Exception:
            # Fallback: return a small sample so caller can still operate
            return self.word_list[:100]

    def rank_by_clue(self, clue: str, matches: list, pattern: str) -> list:
        """
        Ranks matches according to:
         - any user-correct feedback for the (clue, pattern) pair (highest priority),
         - WordNet-based semantic overlap between clue words and candidate definitions / synset names / hypernyms.
        Returns list of tuples: (word, score, definition)
        """
        if not clue:
            return [(m, 0.0, "No clue provided") for m in matches[:3]]

        key = str((clue, pattern.upper()))
        ranked = []

        # If user provided feedback exists and matches the pattern, return it at top
        correct = self.feedback_db.get(key)
        if correct and re.match(self.pattern_to_regex(pattern), correct):
            syns = wordnet.synsets(correct.lower())
            definition = syns[0].definition() if syns else "User-provided"
            ranked.append((correct, 1.0, definition))

        other_matches = [m for m in matches if m != correct] if correct else matches
        # Add top 2 from WordNet ranking after feedback (or top 3 if no feedback)
        ranked.extend(self._wordnet_ranking(clue, other_matches)[:2])
        if not ranked:
            ranked = self._wordnet_ranking(clue, matches)[:3]

        return ranked

    def _wordnet_ranking(self, clue: str, matches: list) -> list:
        """
        Score candidates by measuring overlap between lemmatized clue words and:
         - the definition of the first synset
         - synset names
         - hypernym names
        The resulting list is sorted by score descending.
        """
        clue_words = {self.lemmatizer.lemmatize(w.lower()) for w in word_tokenize(clue.lower())}
        ranked = []
        for word in matches:
            syns = wordnet.synsets(word.lower())
            if not syns:
                ranked.append((word, 0.0, "No definition"))
                continue

            # Use first definition as representative definition
            primary_def = syns[0].definition()
            def_words = {self.lemmatizer.lemmatize(w.lower()) for w in word_tokenize(primary_def)}
            score = len(clue_words & def_words) * 0.5

            # Additional scoring from synset names and hypernyms
            for s in syns:
                syn_name_words = {self.lemmatizer.lemmatize(w.lower()) for w in s.name().replace('.', ' ').split()}
                score += len(clue_words & syn_name_words) * 0.7
                for h in s.hypernyms():
                    hyper_words = {self.lemmatizer.lemmatize(w.lower()) for w in h.name().replace('.', ' ').split()}
                    score += len(clue_words & hyper_words) * 0.3

            ranked.append((word, score, primary_def))

        return sorted(ranked, key=lambda x: x[1], reverse=True)

    def solve(self, clue: str, pattern: str) -> dict:
        """
        Top-level solver method expected by the GUI. Returns a dict keyed by (clue, pattern)
        to match previous interface.
        """
        matches = self.find_matches(pattern, clue)
        ranked = self.rank_by_clue(clue, matches, pattern)
        return {(clue, pattern.upper()): ranked}
