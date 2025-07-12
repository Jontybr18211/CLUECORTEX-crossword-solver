import os
import re
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from threading import Thread
import webbrowser

import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Ensure necessary NLTK data is present
nltk.download('wordnet', quiet=True)
nltk.download('punkt', quiet=True)


class CrosswordSolver:
    """Core crossword solving engine with enhanced clue-based ranking"""

    def __init__(self, word_file="words.txt", feedback_file="feedback.json"):
        self.word_list = self._load_word_db(word_file)
        if not self.word_list:
            raise FileNotFoundError(f"Word list {word_file} not loaded. Exiting.")
        self.feedback_db = self._load_feedback_db(feedback_file)
        self.excluded_words = []
        self.current_results = None
        self.lemmatizer = WordNetLemmatizer()

    def _load_word_db(self, file_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, file_path)
        try:
            with open(path, 'r') as f:
                return [line.strip().upper() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Error: {path} not found.")
            return []

    def _load_feedback_db(self, file_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, file_path)
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_feedback(self, clue, pattern, correct_word):
        key = str((clue, pattern.upper()))
        self.feedback_db[key] = correct_word.upper()
        path = os.path.join(os.path.dirname(__file__), "feedback.json")
        with open(path, 'w') as f:
            json.dump(self.feedback_db, f, indent=4)

    def pattern_to_regex(self, pattern: str) -> str:
        if not pattern or pattern.strip() == "":
            return r"^[A-Z]{2,15}$"
        regex = "".join("[A-Z]" if not c.isalpha() else c.upper() for c in pattern)
        return f"^{regex}$"

    def find_matches(self, pattern: str, clue: str) -> list:
        try:
            regex = self.pattern_to_regex(pattern)
            matches = [w for w in self.word_list if re.match(regex, w)]
            if not pattern or all(c == '?' for c in pattern):
                tokens = word_tokenize(clue.lower())
                est_len = max(2, min(15, int(len(tokens) * 1.5)))
                matches = [w for w in matches if abs(len(w) - est_len) <= 3]
            return matches
        except Exception as e:
            print(f"Pattern error: {e}")
            return self.word_list[:100]

    def rank_by_clue(self, clue: str, matches: list, pattern: str) -> list:
        """Rank matches by clue, prioritizing user feedback with definitions."""
        if not clue:
            return [(m, 0.0, "No clue provided") for m in matches[:3]]

        key = str((clue, pattern.upper()))
        ranked = []

        # Check for feedback and include it if it matches the pattern
        if key in self.feedback_db:
            correct = self.feedback_db[key]
            if re.match(self.pattern_to_regex(pattern), correct):
                syns = wordnet.synsets(correct.lower())
                definition = syns[0].definition() if syns else "User-provided"
                ranked.append((correct, 1.0, definition))

        # Get additional ranked matches, excluding the feedback word
        other_matches = [m for m in matches if m != correct] if 'correct' in locals() else matches
        other_ranked = self._wordnet_ranking(clue, other_matches)[:2]
        ranked.extend(other_ranked)

        # If no feedback or no ranked results, return top 3 from all matches
        if not ranked:
            ranked = self._wordnet_ranking(clue, matches)[:3]

        return ranked

    def _wordnet_ranking(self, clue: str, matches: list) -> list:
        clue_words = {
            self.lemmatizer.lemmatize(w.lower())
            for w in word_tokenize(clue.lower())
        }
        ranked = []
        for w in matches:
            syns = wordnet.synsets(w.lower())
            if not syns:
                ranked.append((w, 0.0, "No definition"))
                continue

            base_def = syns[0].definition()
            def_words = {
                self.lemmatizer.lemmatize(x.lower())
                for x in word_tokenize(base_def)
            }
            score = len(clue_words & def_words) * 0.5

            for s in syns:
                name_words = {
                    self.lemmatizer.lemmatize(x.lower())
                    for x in s.name().split('.')
                }
                score += len(clue_words & name_words) * 0.7
                for h in s.hypernyms():
                    hyper_words = {
                        self.lemmatizer.lemmatize(x.lower())
                        for x in h.name().split('.')
                    }
                    score += len(clue_words & hyper_words) * 0.3

            ranked.append((w, score, base_def))

        return sorted(ranked, key=lambda x: x[1], reverse=True)[:3]

    def solve(self, clue: str, pattern: str) -> dict:
        matches = self.find_matches(pattern, clue)
        ranked = self.rank_by_clue(clue, matches, pattern)
        self.current_results = {(clue, pattern.upper()): ranked}
        return self.current_results


class ModernCrosswordApp:
    """GUI wrapper around CrosswordSolver with elegant themes."""

    def __init__(self, solver: CrosswordSolver):
        self.solver = solver
        self.root = tk.Tk()
        self.root.title("ClueCortex - Crossword Solver")
        self.root.geometry("1000x750")
        self.root.minsize(900, 700)

        # Define themes with provided elegant, high-contrast design
        self.themes = {
            'light': {
                'main_background': '#f9f5e3',
                'text_background': '#fcf8e8',
                'text_foreground': '#3a2e1c',
                'primary': '#7f4f24',
               'secondary': '#936639',
                'accent': '#9c6644',
                'success': '#3e7c59',
                'warning': '#b5838d',
                'header_background': '#ede0d4',
                'header_foreground': '#3a2e1c',
                'match_foreground': '#582f0e',
                'score_foreground': '#6c584c',
                'definition_foreground': '#5f564d',
                'title_foreground': '#3a2e1c',
                'subtitle_foreground': '#7f4f24'
            },
            'dark': {
                'main_background': '#1e1a17',
                'text_background': '#2c2623',
                'text_foreground': '#e6ddc4',
                'primary': '#a47148',
                'secondary': '#8c593b',
                'accent': '#ddb892',
                'success': '#7fbc8c',
                'warning': '#d9a5b3',
                'header_background': '#29211d',
                'header_foreground': '#fefae0',
                'match_foreground': '#e76f51',
                'score_foreground': '#b08968',
                'definition_foreground': '#a98467',
                'title_foreground': '#fefae0',
                'subtitle_foreground': '#ddb892'
            }
        }
        self.current_theme = 'light'
        self.root.configure(bg=self.themes[self.current_theme]['main_background'])

        self.title_font = ("Georgia", 24, "bold")
        self.subtitle_font = ("Georgia", 14, "italic")
        self.button_font = ("Georgia", 12)
        self.text_font = ("Georgia", 11)

        self._setup_styles()
        self._create_widgets()
        self.widgets_created = True
        self._bind_events()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        t = self.themes[self.current_theme]

        style.configure("TFrame", background=t['main_background'])
        style.configure("Card.TFrame", background=t['text_background'], relief="flat", borderwidth=1)
        style.configure("Header.TFrame", background=t['header_background'], relief="flat", borderwidth=0)

        style.configure("TLabel", background=t['main_background'], foreground=t['text_foreground'], font=self.text_font)
        style.configure("Header.TLabel", background=t['header_background'], foreground=t['header_foreground'])

        style.configure("TButton", font=self.button_font, padding=8, relief="flat", borderwidth=1)
        style.configure("Primary.TButton", background=t['primary'], foreground='#ffffff')
        style.map("Primary.TButton",
                  background=[("active", t['secondary'])], foreground=[("active", '#ffffff')])

        style.configure("Accent.TButton", background=t['accent'], foreground='#ffffff')
        style.map("Accent.TButton",
                  background=[("active", t['secondary'])], foreground=[("active", '#ffffff')])

        entry_fg = t['text_foreground']
        style.configure("TEntry",
                        fieldbackground=t['text_background'],
                        foreground=entry_fg,
                        font=self.text_font,
                        padding=8,
                        relief="flat",
                        borderwidth=1)

        style.configure("Treeview",
                        background=t['text_background'],
                        foreground=t['text_foreground'],
                        fieldbackground=t['text_background'],
                        font=self.text_font)
        style.configure("Treeview.Heading",
                        background=t['header_background'],
                        foreground=t['header_foreground'],
                        font=self.button_font)

    def _create_widgets(self):
        t = self.themes[self.current_theme]

        # Menu bar for theme switching and help
        self.menu_bar = tk.Menu(self.root, bg=t['main_background'], fg=t['text_foreground'])
        self.root.config(menu=self.menu_bar)
        theme_menu = tk.Menu(self.menu_bar, tearoff=0, bg=t['main_background'], fg=t['text_foreground'])
        self.menu_bar.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Light", command=lambda: self.set_theme('light'))
        theme_menu.add_command(label="Dark", command=lambda: self.set_theme('dark'))
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0, bg=t['main_background'], fg=t['text_foreground'])
        self.help_menu.add_command(label="User Guide", command=self._show_help)
        self.help_menu.add_command(label="About", command=self._show_about)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        # Input frame
        input_frame = ttk.LabelFrame(self.root, text="Enter Clue Details", style="Card.TFrame")
        input_frame.pack(pady=20, fill="x")
        ttk.Label(input_frame, text="Clue:", style="TLabel").grid(row=0, column=0, padx=5, sticky='e')
        self.clue_entry = ttk.Entry(input_frame, width=50)
        self.clue_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(input_frame, text="Pattern:", style="TLabel").grid(row=1, column=0, padx=5, sticky='e')
        self.pattern_entry = ttk.Entry(input_frame, width=50)
        self.pattern_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        input_frame.columnconfigure(1, weight=1)
        self.solve_button = ttk.Button(input_frame, text="Solve", style="Primary.TButton", command=self.solve)
        self.solve_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Results frame
        results_frame = ttk.LabelFrame(self.root, text="Solutions", style="Card.TFrame")
        results_frame.pack(pady=20, fill="both", expand=True)
        self.results_tree = ttk.Treeview(results_frame, columns=('Word', 'Score', 'Definition'), show='headings')
        self.results_tree.heading('Word', text='Word')
        self.results_tree.heading('Score', text='Score')
        self.results_tree.heading('Definition', text='Definition')
        self.results_tree.pack(fill='both', expand=True)

        # Feedback buttons
        self.feedback_button = ttk.Button(results_frame, text="Save as Feedback", style="Accent.TButton", command=self.save_feedback)
        self.feedback_button.pack(pady=10)
        self.enter_correct_button = ttk.Button(results_frame, text="Enter Correct Word", style="Accent.TButton", command=self.enter_correct_word)
        self.enter_correct_button.pack(pady=10)

    def _bind_events(self):
        self.root.bind("<Return>", lambda e: self.solve())
        self.root.bind("<Escape>", lambda e: self.root.quit())

    def set_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme = theme_name
            self._setup_styles()
            self.root.configure(bg=self.themes[theme_name]['main_background'])

    def solve(self):
        clue = self.clue_entry.get().strip()
        pattern = self.pattern_entry.get().strip().upper()
        if not clue or not pattern:
            messagebox.showwarning("Input Error", "Please enter both clue and pattern.")
            return
        results = self.solver.solve(clue, pattern)
        ranked_list = results.get((clue, pattern.upper()), [])
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        for word, score, definition in ranked_list:
            self.results_tree.insert('', 'end', values=(word, f"{score:.2f}", definition))

    def save_feedback(self):
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a word to save as feedback.")
            return
        values = self.results_tree.item(selected[0])['values']
        word = values[0]
        clue = self.clue_entry.get().strip()
        pattern = self.pattern_entry.get().strip().upper()
        self.solver.save_feedback(clue, pattern, word)
        messagebox.showinfo("Feedback Saved", f"Word '{word}' saved as feedback for clue '{clue}' and pattern '{pattern}'.")

    def enter_correct_word(self):
        """Allow user to input a custom correct word and save it as feedback."""
        clue = self.clue_entry.get().strip()
        pattern = self.pattern_entry.get().strip().upper()
        if not clue or not pattern:
            messagebox.showwarning("Input Error", "Please enter both clue and pattern.")
            return
        correct_word = simpledialog.askstring("Enter Correct Word", "Please enter the correct word:")
        if correct_word:
            correct_word = correct_word.strip().upper()
            regex = self.solver.pattern_to_regex(pattern)
            if not re.match(regex, correct_word):
                messagebox.showerror("Invalid Word", f"The word '{correct_word}' does not match the pattern '{pattern}'.")
                return
            self.solver.save_feedback(clue, pattern, correct_word)
            messagebox.showinfo("Feedback Saved", f"Word '{correct_word}' saved as feedback for clue '{clue}' and pattern '{pattern}'.")
            self.solve()  # Refresh results to show the feedback immediately

    def _show_help(self):
        help_text = """ClueCortex - Crossword Solver Help

1. Enter your crossword clue in the 'Clue' field
2. Enter the letter pattern (? for unknown letters, e.g., "C?T")
3. Click 'Solve' or press Enter
4. Review the solutions
5. Provide feedback to improve results

Tips:
- Be specific with clues
- Patterns can be partial or omitted
- Use feedback for better accuracy"""
        help_window = tk.Toplevel(self.root)
        help_window.title("User Guide")
        help_window.geometry("500x350")
        help_window.configure(bg=self.themes[self.current_theme]['main_background'])
        text = tk.Text(help_window, wrap="word", padx=15, pady=15,
                       font=self.text_font,
                       bg=self.themes[self.current_theme]['text_background'],
                       fg=self.themes[self.current_theme]['text_foreground'],
                       borderwidth=0)
        text.insert("1.0", help_text)
        text.config(state="disabled")
        text.pack(fill="both", expand=True)

    def _show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About ClueCortex")
        about_window.geometry("450x350")
        about_window.configure(bg=self.themes[self.current_theme]['main_background'])
        about_frame = ttk.Frame(about_window, style="Card.TFrame")
        about_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ttk.Label(about_frame, text="ClueCortex", font=self.title_font,
                  foreground=self.themes[self.current_theme]['title_foreground']).pack(pady=10)
        ttk.Label(about_frame, text="Crossword Solver",
                  font=self.subtitle_font,
                  foreground=self.themes[self.current_theme]['subtitle_foreground']).pack()
        ttk.Label(about_frame, text="\nVersion 2.0\n\n© 2025 ClueCortex Team",
                  font=self.text_font).pack()
        ttk.Button(about_frame, text="Visit Website", style="Accent.TButton",
                   command=lambda: webbrowser.open("https://example.com")).pack(pady=15)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        solver = CrosswordSolver("words.txt", "feedback.json")
        app = ModernCrosswordApp(solver)
        app.run()
    except FileNotFoundError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", str(e))
        root.destroy()
        exit(1)