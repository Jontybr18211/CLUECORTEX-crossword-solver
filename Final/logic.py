import os
import json
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag
from collections import defaultdict
from typing import List, Tuple, Dict, Optional, Set

# Ensure NLTK data packages are downloaded once before running:
# nltk.download('wordnet')
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')


class CrosswordSolver:
    """
    An efficient, index-based crossword solver using WordNet for semantic ranking.
    """
    def __init__(self, feedback_file: str = "feedback.json", min_word_len: int = 2, max_word_len: int = 15):
        self.feedback_file = feedback_file
        self.min_word_len = min_word_len
        self.max_word_len = max_word_len

        # Build master word list from WordNet lemmas
        self.word_list: List[str] = self._build_word_list_from_wordnet(min_word_len, max_word_len)

        # Create indexes for fast, non-regex searching
        self.by_len: Dict[int, List[str]] = defaultdict(list)
        self.pos_char: Dict[Tuple[int, str], Set[str]] = defaultdict(set)
        for w in self.word_list:
            self.by_len[len(w)].append(w)
            for i, char in enumerate(w):
                self.pos_char[(i, char)].add(w)

        self.feedback_db: Dict[str, str] = self._load_feedback_db(feedback_file)
        self.lemmatizer = WordNetLemmatizer()

    def _build_word_list_from_wordnet(self, min_len: int, max_len: int) -> List[str]:
        """Extracts a clean, sorted list of single words from all of WordNet."""
        lemmas = set()
        for syn in wordnet.all_synsets():
            for lemma_name in syn.lemma_names():
                # Skip multi-word phrases which often contain underscores
                if "_" in lemma_name:
                    continue
                cleaned = lemma_name.strip().upper()
                if cleaned.isalpha() and min_len <= len(cleaned) <= max_len:
                    lemmas.add(cleaned)
        return sorted(list(lemmas))

    def _resolve_path(self, file_path: str) -> str:
        """Returns the absolute path for a file, relative to this script if needed."""
        return file_path if os.path.isabs(file_path) else os.path.join(os.path.dirname(__file__), file_path)

    def _load_feedback_db(self, file_path: str) -> Dict[str, str]:
        """Loads the user feedback JSON file, returning an empty dict if it fails."""
        path = self._resolve_path(file_path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_feedback(self, clue: str, pattern: str, correct_word: str):
        """Saves a confirmed correct word for a given clue/pattern to the feedback file."""
        key = str((clue, pattern.upper()))
        self.feedback_db[key] = correct_word.upper()
        path = self._resolve_path(self.feedback_file)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_db, f, indent=4, ensure_ascii=False)

    def pattern_to_regex(self, pattern: Optional[str]) -> str:
        """Converts a user pattern like 'A?PLE' into a valid regex."""
        pattern = (pattern or "").strip()
        if not pattern:
            return rf"^[A-Z]{{{self.min_word_len},{self.max_word_len}}}$"
        
        # Treat any non-alphabetic character as a wildcard for one letter.
        regex_body = ''.join('[A-Z]' if not c.isalpha() else c.upper() for c in pattern)
        return f"^{regex_body}$"
            
    def _get_synsets(self, word: str, pos=None) -> list:
        """Wrapper for the wordnet.synsets call."""
        return wordnet.synsets(word.lower(), pos=pos)

    def _get_primary_def(self, word: str) -> str:
        """Gets the primary definition for a word from WordNet."""
        syns = self._get_synsets(word)
        return syns[0].definition() if syns else "No definition available"

    def find_matches(self, pattern: str, clue: str = "") -> List[str]:
        """Finds candidate words matching the pattern using efficient positional indexes."""
        pattern = (pattern or "").strip().upper()
        
        # Start with a set of candidate words based on pattern length
        if not pattern:
            return [] # Or handle as an open search if desired
            
        candidate_words = set(self.by_len.get(len(pattern), []))
        if not candidate_words:
            return []

        # Filter down candidates by intersecting sets of words with correct letters in correct positions
        for i, char in enumerate(pattern):
            if char.isalpha():
                matching_subset = self.pos_char.get((i, char), set())
                candidate_words &= matching_subset
                if not candidate_words:
                    return [] # No need to continue if set is empty

        # Optional: Prune candidates based on the Part-of-Speech of the clue's last word
        tokens = [t for t in word_tokenize(clue) if t.isalpha()]
        if tokens:
            try:
                last_word_tag = pos_tag([tokens[-1]])[0][1]
                guessed_pos = self._wn_pos_from_tag(last_word_tag)
                if guessed_pos:
                    pruned_words = {w for w in candidate_words if self._get_synsets(w, pos=guessed_pos)}
                    if pruned_words:
                        candidate_words = pruned_words
            except IndexError:
                # Silently ignore if POS tagging fails for any reason
                pass
                
        return sorted(list(candidate_words))

    def rank_by_clue(self, clue: str, matches: List[str], pattern: str) -> List[Tuple[str, float, str]]:
        """Ranks a list of matching words based on a clue, prioritizing user feedback."""
        if not matches:
            return []

        if not clue:
            # If no clue is provided, return top matches with a zero score
            return [(m, 0.0, self._get_primary_def(m)) for m in matches[:5]]

        key = str((clue, pattern.upper()))
        ranked_results: List[Tuple[str, float, str]] = []

        # Give a massive score boost to a user-confirmed answer from feedback
        correct_word = self.feedback_db.get(key)
        if correct_word and correct_word in matches:
            ranked_results.append((correct_word, 10.0, self._get_primary_def(correct_word)))

        # Rank all other words using semantic analysis
        other_matches = [m for m in matches if m != correct_word]
        if other_matches:
            ranked_results.extend(self._wordnet_ranking(clue, other_matches))

        # Sort final list by score (highest first)
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        
        return ranked_results[:5] # Return top 5 suggestions

    def _wordnet_ranking(self, clue: str, matches: List[str]) -> List[Tuple[str, float, str]]:
        """Calculates a semantic relevance score for each word against a clue."""
        clue_words = {self.lemmatizer.lemmatize(w) for w in word_tokenize(clue.lower()) if w.isalpha()}
        ranked = []
        
        for word in matches:
            syns = self._get_synsets(word)
            if not syns:
                continue

            primary_def = syns[0].definition()
            def_words = {self.lemmatizer.lemmatize(w) for w in word_tokenize(primary_def.lower()) if w.isalpha()}
            
            score = 0.0
            # Weight 1.0: Clue words found in the definition
            score += len(clue_words.intersection(def_words)) * 1.0

            all_lemmas = set()
            all_hypernym_lemmas = set()
            for s in syns:
                # Collect all synonyms (lemmas)
                for lemma in s.lemmas():
                    all_lemmas.add(self.lemmatizer.lemmatize(lemma.name().replace('_', ' ').lower()))
                # Collect all parent concepts (hypernym lemmas)
                for hypernym in s.hypernyms():
                    for lemma in hypernym.lemmas():
                        all_hypernym_lemmas.add(self.lemmatizer.lemmatize(lemma.name().replace('_', ' ').lower()))
            
            # Weight 1.5: Clue words matching any synonym of the word
            score += len(clue_words.intersection(all_lemmas)) * 1.5
            # Weight 0.6: Clue words matching any parent concept
            score += len(clue_words.intersection(all_hypernym_lemmas)) * 0.6

            if score > 0:
                ranked.append((word, score, primary_def))
        
        # Sort by score (desc), then alphabetically for tie-breaking
        return sorted(ranked, key=lambda x: (x[1], x[0]), reverse=True)

    def _wn_pos_from_tag(self, tag: str) -> Optional[str]:
        """Converts a Penn Treebank POS tag to a WordNet POS tag."""
        if tag.startswith('N'):
            return wordnet.NOUN
        if tag.startswith('V'):
            return wordnet.VERB
        if tag.startswith('J'):
            return wordnet.ADJ
        if tag.startswith('R'):
            return wordnet.ADV
        return None

    def solve(self, clue: str, pattern: str) -> Dict[Tuple[str, str], List[Tuple[str, float, str]]]:
        """The main entry point to find and rank solutions for a clue and pattern."""
        matches = self.find_matches(pattern, clue)
        ranked_solutions = self.rank_by_clue(clue, matches, pattern)
        return {(clue, pattern.upper()): ranked_solutions}