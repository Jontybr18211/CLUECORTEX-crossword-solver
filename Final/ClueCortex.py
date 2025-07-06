

"""
Crossword Solver Application with GUI
Combines pattern matching with semantic analysis (WordNet) and AI models (transformers)

"""

# Standard library imports
import os
import re
import json
import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict
from typing import List, Tuple, Dict
from datetime import datetime
from threading import Thread
import webbrowser

# Natural Language Processing imports
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Optional AI/ML imports with graceful fallback
try:
    import torch
    from transformers import pipeline  # For text generation
    from sentence_transformers import SentenceTransformer, util  # For semantic similarity
except ImportError:
    torch = None
    pipeline = None
    SentenceTransformer = None
    util = None

class CrosswordSolver:
    """Core crossword solving engine with enhanced clue-based ranking"""
    
    def __init__(self, word_file="words.txt", feedback_file="feedback.json"):
        self.word_list = self.load_word_database(word_file)
        if not self.word_list:
            raise FileNotFoundError("Word list not loaded. Exiting.")
        self.feedback_db = self.load_feedback_database(feedback_file)
        self.excluded_words = []
        self.current_results = None
        self.generator = self._init_generator()
        self.similarity_model = self._init_similarity_model()
        self.lemmatizer = WordNetLemmatizer()
        #nltk.download('punkt', quiet=True)
        nltk.download('wordnet', quiet=True)

    def _init_generator(self):
        if torch and pipeline:
            try:
                return pipeline("text-generation", model="distilgpt2", device=-1)
            except Exception as e:
                print(f"Failed to load generator: {e}")
        return None

    def _init_similarity_model(self):
        if SentenceTransformer and util:
            try:
                return SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"Failed to load similarity model: {e}")
        return None

    def load_word_database(self, file_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        absolute_path = os.path.join(script_dir, file_path)
        try:
            with open(absolute_path, 'r') as f:
                return [line.strip().upper() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Error: {absolute_path} not found.")
            return []

    def load_feedback_database(self, file_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        absolute_path = os.path.join(script_dir, file_path)
        try:
            with open(absolute_path, 'r') as f:
                return json.load(f)  # JSON loads keys as strings
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_feedback(self, clue, pattern, correct_word):
        key = str((clue, pattern.upper()))
        self.feedback_db[key] = correct_word.upper()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        absolute_path = os.path.join(script_dir, "feedback.json")
        with open(absolute_path, 'w') as f:
            json.dump(self.feedback_db, f, indent=4)

    def pattern_to_regex(self, pattern):
        """Convert pattern to regex with strict length enforcement"""
        if not pattern or pattern.strip() == "":
            return r"^[A-Z]{2,15}$"  # Default range for word length if no pattern
        # Calculate exact length from pattern
        length = len(pattern)
        regex = "".join("[A-Z]" if not c.isalpha() else c.upper() for c in pattern)
        return f"^{regex}$"  # Enforce exact length with ^ and $

    def find_matches(self, pattern, clue):
        """Find matches with exact length enforcement based on pattern"""
        try:
            regex = self.pattern_to_regex(pattern)
            matches = [word for word in self.word_list if re.match(regex, word)]
            if not pattern or all(c == '?' for c in pattern):
                # If pattern is vague, estimate length from clue
                clue_tokens = word_tokenize(clue.lower())
                est_len = max(2, min(15, int(len(clue_tokens) * 1.5)))
                matches = [w for w in matches if abs(len(w) - est_len) <= 3]
            # If pattern is provided, length is already enforced by regex
            return matches
        except Exception as e:
            print(f"Pattern error: {e}")
            return self.word_list[:100]  # Fallback for semantic ranking

    def rank_by_clue(self, clue, matches, pattern):
        """Rank matches prioritizing clue's semantic essence"""
        if not clue:
            return [(match, 0, "No clue provided") for match in matches[:3]]

        key = str((clue, pattern.upper()))
        if key in self.feedback_db and self.feedback_db[key] in matches:
            correct_word = self.feedback_db[key]
            synsets = wordnet.synsets(correct_word.lower())
            definition = synsets[0].definition() if synsets else "User-corrected"
            return [(correct_word, 1.0, definition)]

        if self.similarity_model:
            return self._ai_ranking(clue, matches)
        return self._wordnet_ranking(clue, matches)

    def _ai_ranking(self, clue, matches):
        """Semantic ranking with AI embeddings"""
        clue_embedding = self.similarity_model.encode(clue, convert_to_tensor=True)
        ranked = []
        for word in matches:
            if word in self.excluded_words:
                continue
            synsets = wordnet.synsets(word.lower())
            definitions = [syn.definition() for syn in synsets] if synsets else [word]
            def_embeddings = self.similarity_model.encode(definitions, convert_to_tensor=True)
            similarities = util.pytorch_cos_sim(clue_embedding, def_embeddings)[0]
            max_sim = similarities.max().item()
            best_def = definitions[similarities.argmax()] if similarities.size else "No definition"
            clue_len = len(word_tokenize(clue))
            length_boost = min(0.1, 0.03 * abs(len(word) - clue_len))
            ranked.append((word, max_sim + length_boost, best_def))
        return sorted(ranked, key=lambda x: x[1], reverse=True)[:3]

    def _wordnet_ranking(self, clue, matches):
        """Enhanced WordNet ranking with lemmatization and hypernyms"""
        clue_words = set(self.lemmatizer.lemmatize(w.lower()) for w in word_tokenize(clue.lower()))
        ranked = []
        for word in matches:
            synsets = wordnet.synsets(word.lower())
            if not synsets:
                ranked.append((word, 0, "No definition"))
                continue
            score = 0
            best_def = synsets[0].definition()
            def_words = set(self.lemmatizer.lemmatize(w.lower()) for w in word_tokenize(best_def))
            
            score += len(clue_words.intersection(def_words)) * 0.5
            for syn in synsets:
                syn_name = set(self.lemmatizer.lemmatize(w.lower()) for w in syn.name().split('.'))
                score += len(clue_words.intersection(syn_name)) * 0.7
                for hyper in syn.hypernyms():
                    hyper_name = set(self.lemmatizer.lemmatize(w.lower()) for w in hyper.name().split('.'))
                    score += len(clue_words.intersection(hyper_name)) * 0.3
            
            ranked.append((word, score, best_def))
        return sorted(ranked, key=lambda x: x[1], reverse=True)[:3]

    def solve(self, clue, pattern):
        """Main method to solve crossword clues"""
        matches = self.find_matches(pattern, clue)
        ranked = self.rank_by_clue(clue, matches, pattern)
        self.current_results = {(clue, pattern.upper()): ranked}
        return self.current_results

class ModernCrosswordApp:
    """Professional and attractive GUI with high-contrast, elegant design"""
    
    def __init__(self, solver):
        self.solver = solver
        self.root = tk.Tk()
        self.root.title("ClueCortex - Crossword Solver")
        self.root.geometry("1000x750")
        self.root.minsize(900, 700)
        
        # Sophisticated, high-contrast theme
        self.themes = {
            'light': {
                'main_background': '#f9f5e3',           # Antique paper
                'text_background': '#fcf8e8',           # Faded ivory
                'text_foreground': '#3a2e1c',           # Deep brown ink
                'primary': '#7f4f24',                   # Leather brown
                'secondary': '#936639',                 # Bronze
                'accent': '#9c6644',                    # Rusty gold
                'success': '#3e7c59',                   # Forest green
                'warning': '#b5838d',                   # Mauve pink
                'header_background': '#ede0d4',         # Light parchment
                'header_foreground': '#3a2e1c',         # Deep brown
                'match_foreground': '#582f0e',          # Rich cocoa
                'score_foreground': '#6c584c',          # Sepia
                'definition_foreground': '#5f564d',     # Book dust gray
                'title_foreground': '#3a2e1c',          # Dark ink
                'subtitle_foreground': '#7f4f24'        # Leather highlight
            }
,
    'dark': {
                'main_background': '#1e1a17',            # Old wood
                'text_background': '#2c2623',           # Aged leather
                'text_foreground': '#e6ddc4',           # Faded parchment
                'primary': '#a47148',                   # Warm bronze
                'secondary': '#8c593b',                 # Rustic brown
                'accent': '#ddb892',                    # Golden tan
                'success': '#7fbc8c',                   # Vintage green
                'warning': '#d9a5b3',                   # Rose ink
                'header_background': '#29211d',         # Deep oak
                'header_foreground': '#fefae0',         # Aged paper white
                'match_foreground': '#e76f51',          # Brick red
                'score_foreground': '#b08968',          # Dusty copper
                'definition_foreground': '#a98467',     # Classic beige
                'title_foreground': '#fefae0',          # Old ivory
                'subtitle_foreground': '#ddb892'        # Classic tan
            }
}
        self.current_theme = 'light'
        self.root.configure(bg=self.themes[self.current_theme]['main_background'])

        # Typography for classic aesthetic
        self.title_font = ("Georgia", 24, "bold")
        self.subtitle_font = ("Georgia", 14, "italic")
        self.button_font = ("Georgia", 12)
        self.text_font = ("Georgia", 11)

        self._setup_styles()
        self._create_widgets()
        self.widgets_created = True
        self._bind_events()


    def _setup_styles(self):
        """Configure ttk styles with elegant, high-contrast design"""
        style = ttk.Style()
        style.theme_use("clam")
        theme = self.themes[self.current_theme]
        
        # Frames with clean, high-contrast borders
        style.configure("TFrame", background=theme['main_background'])
        style.configure("Card.TFrame", background=theme['text_background'], 
                        relief="flat", borderwidth=1)
        style.configure("Header.TFrame", background=theme['header_background'], 
                        relief="flat", borderwidth=0)
        
        # Labels with strong contrast
        style.configure("TLabel", background=theme['main_background'], 
                        foreground=theme['text_foreground'], font=self.text_font)
        style.configure("Header.TLabel", background=theme['header_background'], 
                        foreground=theme['header_foreground'])
        
        # Buttons with sleek, professional design
        style.configure("TButton", font=self.button_font, padding=8, 
                        relief="flat", borderwidth=1)
        style.configure("Primary.TButton", background=theme['primary'], foreground='#ffffff')
        style.map("Primary.TButton",
                  background=[("active", theme['secondary'])],
                  foreground=[("active", '#ffffff')])
        
        style.configure("Accent.TButton", background=theme['accent'], foreground='#ffffff')
        style.map("Accent.TButton",
                  background=[("active", theme['secondary'])],
                  foreground=[("active", '#ffffff')])
        
        # Entries with high-contrast text
        entry_foreground = '#000000' if self.current_theme == 'light' else '#ffffff'
        style.configure("TEntry", fieldbackground=theme['text_background'], 
                        foreground=entry_foreground, font=self.text_font, 
                        padding=8, relief="flat", borderwidth=1)

    def _create_widgets(self):
        """Build professional, attractive GUI components"""
        theme = self.themes[self.current_theme]
        
        # Main frame with refined padding
        self.main_frame = ttk.Frame(self.root, style="Card.TFrame")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header frame with elegant design
        self.header_frame = ttk.Frame(self.main_frame, style="Header.TFrame")
        self.header_frame.pack(fill="x", pady=(0, 15))
        
        self.title_label = ttk.Label(self.header_frame, text="ClueCortex", 
                                     font=self.title_font, foreground=theme['title_foreground'],
                                     background=theme['header_background'])
        self.title_label.pack(side="left", padx=15, pady=10)
        
        self.subtitle_label = ttk.Label(self.header_frame, 
                                        text="Crossword Solver", 
                                        font=self.subtitle_font, 
                                        foreground=theme['subtitle_foreground'],
                                        background=theme['header_background'])
        self.subtitle_label.pack(side="left", padx=15)
        
        self.theme_btn = ttk.Button(self.header_frame, text="Theme🌗", 
                                    style="Accent.TButton", command=self._toggle_theme)
        self.theme_btn.pack(side="right", padx=15)
        
        # Input frame with sophisticated styling
        self.input_frame = ttk.LabelFrame(self.main_frame, text="Enter Clue Details", 
                                         padding=15, style="Card.TFrame")
        self.input_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(self.input_frame, text="Clue:", font=self.text_font).grid(row=0, column=0, 
                                                                           sticky="w", pady=5)
        self.clue_entry = ttk.Entry(self.input_frame, width=50)
        self.clue_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ttk.Label(self.input_frame, text="Pattern:", font=self.text_font).grid(row=1, column=0, 
                                                                              sticky="w", pady=5)
        self.pattern_entry = ttk.Entry(self.input_frame, width=50)
        self.pattern_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        self.input_frame.columnconfigure(1, weight=1)
        
        self.solve_btn = ttk.Button(self.input_frame, text="Solve", 
                                    style="Primary.TButton", command=self._solve)
        self.solve_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Results frame with high-contrast layout
        self.results_frame = ttk.LabelFrame(self.main_frame, text="Solutions", 
                                           padding=15, style="Card.TFrame")
        self.results_frame.pack(fill="both", expand=True)
        
        self.results_text = tk.Text(self.results_frame, height=20, wrap="word",
                                    font=self.text_font, padx=10, pady=10,
                                    bg=theme['text_background'], fg=theme['text_foreground'],
                                    borderwidth=0, relief="flat")
        scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", 
                                  command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        self.results_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.results_text.tag_configure("header", font=("Helvetica", 14, "bold"), 
                                        foreground=theme['header_foreground'])
        self.results_text.tag_configure("match", foreground="#ff0000")  # Red for answers
        self.results_text.tag_configure("score", foreground=theme['score_foreground'])
        self.results_text.tag_configure("definition", foreground=theme['definition_foreground'])
        
        # Feedback frame with elegant accents
        self.feedback_frame = ttk.Frame(self.main_frame, style="Card.TFrame")
        self.feedback_frame.pack(fill="x", pady=(15, 0), padx=10)
        
        self.feedback_label = ttk.Label(self.feedback_frame, 
                                        text="Was this helpful?",
                                        font=self.text_font)
        self.feedback_label.pack(side="left", padx=(10, 10), pady=10)
        
        self.yes_btn = ttk.Button(self.feedback_frame, text="Yes", width=6,
                                  style="Accent.TButton", 
                                  command=lambda: self._process_feedback(True))
        self.yes_btn.pack(side="left", padx=5)
        
        self.no_btn = ttk.Button(self.feedback_frame, text="No", width=6,
                                 style="Accent.TButton", 
                                 command=lambda: self._process_feedback(False))
        self.no_btn.pack(side="left", padx=5)
        
        self.correct_entry = ttk.Entry(self.feedback_frame, width=30)
        self.correct_entry.pack(side="left", padx=10, pady=10)
        self.correct_entry.bind("<Return>", lambda e: self._submit_correction())
        
        self.submit_btn = ttk.Button(self.feedback_frame, text="Submit Correction",
                                     style="Accent.TButton", 
                                     command=self._submit_correction)
        self.submit_btn.pack(side="left", pady=10)
        
        # Status bar with high-contrast status
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var,
                                    relief="flat", anchor="w", padding=8,
                                    background=theme['main_background'],
                                    foreground=theme['success'],
                                    font=self.text_font)
        self.status_bar.pack(fill="x", pady=(10, 0))

        # Menu bar with sophisticated design
        self.menu_bar = tk.Menu(self.root, bg=theme['main_background'], 
                               fg=theme['header_foreground'], font=self.text_font)
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0, bg=theme['main_background'],
                                fg=theme['header_foreground'], font=self.text_font)
        self.help_menu.add_command(label="User Guide", command=self._show_help)
        self.help_menu.add_command(label="About", command=self._show_about)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.root.config(menu=self.menu_bar)

    def _toggle_theme(self):
        """Switch themes and update button text to 'Theme🌗'"""
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.set_theme(new_theme)
        self.theme_btn.config(text="Theme🌗")

    def set_theme(self, theme):
        """Apply selected theme"""
        if theme not in self.themes:
            return
        self.current_theme = theme
        self._setup_styles()
        if self.widgets_created:
            self._update_widgets()

    def _update_widgets(self):
        """Refresh widget colors and styles"""
        theme = self.themes[self.current_theme]
        self.root.configure(bg=theme['main_background'])
        self.main_frame.configure(style="Card.TFrame")
        self.header_frame.configure(background=theme['header_background'])
        self.results_text.configure(bg=theme['text_background'], fg=theme['text_foreground'])
        self.status_bar.configure(background=theme['main_background'], 
                                 foreground=theme['success'])
        self.menu_bar.configure(bg=theme['main_background'], fg=theme['header_foreground'])
        self.help_menu.configure(bg=theme['main_background'], fg=theme['header_foreground'])
        
        self.results_text.tag_configure("header", foreground=theme['header_foreground'])
        self.results_text.tag_configure("match", foreground="#ff0000")  # Red for answers
        self.results_text.tag_configure("score", foreground=theme['score_foreground'])
        self.results_text.tag_configure("definition", foreground=theme['definition_foreground'])
        
        self.title_label.configure(foreground=theme['title_foreground'], 
                                  background=theme['header_background'])
        self.subtitle_label.configure(foreground=theme['subtitle_foreground'], 
                                     background=theme['header_background'])

    def _bind_events(self):
        self.root.bind("<Return>", lambda e: self._solve())
        self.root.bind("<Escape>", lambda e: self.root.quit())

    def _solve(self):
        clue = self.clue_entry.get().strip()
        pattern = self.pattern_entry.get().strip()
        self.solver.excluded_words = []
        
        if not clue:
            messagebox.showerror("Error", "Please enter a clue")
            return
            
        self.status_var.set("Solving...")
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Searching for solutions...\n", "header")
        
        Thread(target=self._solve_thread, args=(clue, pattern), daemon=True).start()

    def _solve_thread(self, clue, pattern):
        results = self.solver.solve(clue, pattern)
        self.root.after(0, self._show_results, results)

    def _show_results(self, results):
        self.results_text.delete(1.0, tk.END)
        
        if not results or not any(results.values()):
            self.results_text.insert(tk.END, "No solutions found.\n", "header")
            self.status_var.set("No solutions found")
            return
            
        for (clue, pattern), matches in results.items():
            self.results_text.insert(tk.END, f"Clue: {clue}\n", "header")
            self.results_text.insert(tk.END, f"Pattern: {pattern}\n\n", "header")
            for word, score, definition in matches:
                self.results_text.insert(tk.END, f"• {word} ", "match")
                self.results_text.insert(tk.END, f"(Score: {score:.2f})\n", "score")
                self.results_text.insert(tk.END, f"   {definition}\n\n", "definition")
        
        self.status_var.set(f"Found {len(next(iter(results.values())))} solutions")

    def _process_feedback(self, is_correct):
        clue = self.clue_entry.get()
        pattern = self.pattern_entry.get()
        
        if is_correct:
            top_match = self.solver.current_results[(clue, pattern)][0][0]
            self.solver.save_feedback(clue, pattern, top_match)
            messagebox.showinfo("Thank you!", "Feedback recorded.")
        else:
            self.correct_entry.focus()
            messagebox.showinfo("Help us improve", "Please enter the correct answer.")

    def _submit_correction(self):
        clue = self.clue_entry.get()
        pattern = self.pattern_entry.get()
        correction = self.correct_entry.get().strip().upper()
        
        if not correction:
            messagebox.showerror("Error", "Please enter a correction")
            return
            
        self.solver.save_feedback(clue, pattern, correction)
        messagebox.showinfo("Success", "Correction saved!")
        self.correct_entry.delete(0, tk.END)
        self._solve()

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
        about_window.geometry("450x350")  # Increased from 350x250
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
    solver = CrosswordSolver()
    app = ModernCrosswordApp(solver)
    app.run()