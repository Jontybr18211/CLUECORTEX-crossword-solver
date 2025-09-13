import sys
import re
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox,
    QInputDialog, QMenu, QFormLayout, QHeaderView, QFileDialog, QListWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from logic import CrosswordSolver
# --- MODIFIED: Import both scanner functions ---
from scanner import scan_crossword_image, scan_clues_from_image

class ThemeManager:
    """
    A class to manage the professional themes for the application.
    It provides static methods for light and dark themes.
    """
    @staticmethod
    def _base_font_style():
        """Base font styles for consistency."""
        return "font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px;"

    @staticmethod
    def light_theme():
        """A professional light theme with a cool blue accent and a stylish theme toggle button."""
        return f"""
        QMainWindow, QWidget {{
            background-color: #f0f0f0;
            color: #2c3e50;
            {ThemeManager._base_font_style()}
        }}
        QLabel#title {{
            font-size: 32px;
            font-weight: 700;
            color: #2980b9;
        }}
        QLineEdit {{
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
            border-radius: 6px;
            padding: 8px;
            color: #2c3e50;
        }}
        QLineEdit:focus {{
            border: 1px solid #3498db;
        }}
        QPushButton {{
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #2980b9;
        }}
        QPushButton:pressed {{
            background-color: #1f618d;
        }}
        QTableWidget {{
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            gridline-color: #e0e0e0;
            alternate-background-color: #f7f9fb;
        }}
        QHeaderView::section {{
            background-color: #ecf0f1;
            color: #2c3e50;
            padding: 8px;
            border: 1px solid #e0e0e0;
            font-weight: bold;
        }}
        QTableWidget::item {{
            padding: 8px;
        }}
        QTableWidget::item:selected {{
            background-color: #a9d0f5;
            color: #2c3e50;
        }}
        QMenuBar {{
            background-color: #ecf0f1;
            color: #2c3e50;
        }}
        QMenuBar::item:selected {{
            background-color: #bdc3c7;
        }}
        QMenu {{
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
        }}
        QMenu::item:selected {{
            background-color: #3498db;
            color: white;
        }}
        QScrollBar:vertical, QScrollBar:horizontal {{
            border: 1px solid #e0e0e0;
            background: #f0f0f0;
            width: 12px;
            margin: 0px;
        }}
        QScrollBar::handle {{
            background: #bdc3c7;
            min-height: 20px;
            border-radius: 6px;
        }}
        QScrollBar::handle:hover {{
            background: #95a5a6;
        }}

        /* Stylish theme toggle button (light theme appearance) */
        QPushButton#themeToggle {{
            min-width: 56px;
            max-width: 56px;
            min-height: 28px;
            border-radius: 14px;
            padding: 2px;
            background: #33A1E0;
            border: 1px solid #b6d8f6;
        }}
        QPushButton#themeToggle:checked {{
            background: #33A1E0;
            border: 1px solid #f4b042;
        }}
        QPushButton#themeToggle QLabel {{
            margin-left: 6px;
            margin-right: 6px;
        }}
        """

    @staticmethod
    def dark_theme():
        """A stunning dark theme with a teal accent for high contrast and updated theme toggle styling."""
        return f"""
        QMainWindow, QWidget {{
            background-color: #2c3e50;
            color: #ecf0f1;
            {ThemeManager._base_font_style()}
        }}
        QLabel#title {{
            font-size: 32px;
            font-weight: 700;
            color: #1abc9c;
        }}
        QLineEdit {{
            background-color: #34495e;
            border: 1px solid #566573;
            border-radius: 6px;
            padding: 8px;
            color: #ecf0f1;
        }}
        QLineEdit:focus {{
            border: 1px solid #1abc9c;
        }}
        QPushButton {{
            background-color: #1abc9c;
            color: #2c3e50;
            border: none;
            border-radius: 6px;
            padding: 10px 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #16a085;
        }}
        QPushButton:pressed {{
            background-color: #117864;
        }}
        QTableWidget {{
            background-color: #34495e;
            border: 1px solid #566573;
            gridline-color: #566573;
            alternate-background-color: #3b5268;
            color: #ecf0f1;
        }}
        QHeaderView::section {{
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 8px;
            border: 1px solid #566573;
            font-weight: bold;
        }}
        QTableWidget::item {{
            padding: 8px;
        }}
        QTableWidget::item:selected {{
            background-color: #2980b9;
            color: #ffffff;
        }}
        QMenuBar {{
            background-color: #34495e;
            color: #ecf0f1;
        }}
        QMenuBar::item:selected {{
            background-color: #566573;
        }}
        QMenu {{
            background-color: #34495e;
            border: 1px solid #566573;
            color: #ecf0f1;
        }}
        QMenu::item:selected {{
            background-color: #1abc9c;
            color: #2c3e50;
        }}
        QScrollBar:vertical, QScrollBar:horizontal {{
            border: none;
            background: #2c3e50;
            width: 12px;
            margin: 0px;
        }}
        QScrollBar::handle {{
            background: #566573;
            min-height: 20px;
            border-radius: 6px;
        }}
        QScrollBar::handle:hover {{
            background: #7f8c8d;
        }}

        /* Stylish theme toggle button (dark theme appearance) */
        QPushButton#themeToggle {{
            min-width: 56px;
            max-width: 56px;
            min-height: 28px;
            border-radius: 14px;
            padding: 2px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop:0 #3b5163, stop:1 #2b3e4b);
            border: 1px solid #4b6a7a;
        }}
        QPushButton#themeToggle:checked {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop:0 #ffb347, stop:1 #ff8c42);
            border: 1px solid #d18a3b;
        }}
        """

class ClueCortexWindow(QMainWindow):
    def __init__(self, solver: CrosswordSolver):
        super().__init__()
        self.solver = solver
        self.setWindowTitle("ClueCortex - Crossword Solver")
        self.setMinimumSize(1200, 800)
        self.dark_mode = False
        self.setStyleSheet(ThemeManager.light_theme())

        # New puzzle state holder
        self.puzzle_data = None
        self.current_word_key = None

        # Use standard icons for a professional look
        self.setWindowIcon(QIcon.fromTheme("edit-find-replace"))

        self.create_menu_bar()
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main Layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title area with attractive single-click toggle theme button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        # Title Label (made larger per request)
        title_label = QLabel("ClueCortex")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Theme toggle button - single click toggles between light and dark.
        self.theme_toggle_button = QPushButton()
        self.theme_toggle_button.setObjectName("themeToggle")
        self.theme_toggle_button.setCheckable(True)
        self.theme_toggle_button.setChecked(self.dark_mode)
        self.theme_toggle_button.setToolTip("Toggle Light / Dark Theme")
        # Set icons if available in system theme; fallback to simple text
        light_icon = QIcon.fromTheme("weather-clear")  # sun-like
        dark_icon = QIcon.fromTheme("weather-night")  # moon-like
        if not light_icon.isNull() and not dark_icon.isNull():
            self._light_icon = light_icon
            self._dark_icon = dark_icon
            self.theme_toggle_button.setIcon(self._light_icon if not self.dark_mode else self._dark_icon)
        else:
            # Use text fallback (keeps button attractive via stylesheet)
            self.theme_toggle_button.setText("☀︎" if not self.dark_mode else "☾")

        self.theme_toggle_button.clicked.connect(self.toggle_theme)

        # Layout arrangement: title expands, toggle sits to the right
        title_layout.addWidget(title_label, stretch=1)
        title_layout.addWidget(self.theme_toggle_button, stretch=0, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(title_layout)

        # --- Input Section ---
        input_form_layout = QFormLayout()
        input_form_layout.setSpacing(10)
        input_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.clue_input = QLineEdit()
        self.clue_input.setPlaceholderText("e.g., A small, quick bite")
        self.clue_input.returnPressed.connect(self.solve)
        input_form_layout.addRow("Clue:", self.clue_input)

        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("e.g., N?B?LE")
        self.pattern_input.returnPressed.connect(self.solve)
        input_form_layout.addRow("Pattern:", self.pattern_input)

        main_layout.addLayout(input_form_layout)

        # --- Scan Grid Button (NEW) ---
        self.scan_button = QPushButton("Scan Grid from Image")
        self.scan_button.setIcon(QIcon.fromTheme("image-x-generic"))
        self.scan_button.setToolTip("Scan a crossword image and populate the grid")
        self.scan_button.clicked.connect(self.load_and_scan_image)
        main_layout.addWidget(self.scan_button)

        # --- Solve Button ---
        self.solve_button = QPushButton("Solve")
        self.solve_button.setIcon(QIcon.fromTheme("system-search"))
        self.solve_button.setToolTip("Find possible answers for the clue and pattern")
        self.solve_button.clicked.connect(self.solve)
        main_layout.addWidget(self.solve_button)

        # --- Results + Puzzle Display Area ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # Left: Puzzle visual grid and word list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)

        # 15x15 visual grid (non-editable)
        self.puzzle_table = QTableWidget()
        self.puzzle_table.setRowCount(15)
        self.puzzle_table.setColumnCount(15)
        self.puzzle_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.puzzle_table.horizontalHeader().setVisible(False)
        self.puzzle_table.verticalHeader().setVisible(False)
        self.puzzle_table.setFixedSize(450, 450)  # keep it square visually
        # make cells square-ish
        for i in range(15):
            self.puzzle_table.setColumnWidth(i, 30)
            self.puzzle_table.setRowHeight(i, 30)

        left_layout.addWidget(self.puzzle_table)

        # List of words (e.g., '1-Across', '5-Down')
        self.word_list_widget = QListWidget()
        self.word_list_widget.itemClicked.connect(self.on_word_selected)
        left_layout.addWidget(self.word_list_widget)

        content_layout.addWidget(left_panel, stretch=0)

        # Right: existing results table (keeps previous behavior)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Word", "Score", "Definition"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        content_layout.addWidget(self.table, stretch=1)

        main_layout.addLayout(content_layout)

        # --- Feedback Buttons ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.feedback_button = QPushButton("Save as Correct")
        self.feedback_button.setIcon(QIcon.fromTheme("emblem-ok"))
        self.feedback_button.setToolTip("Save the selected answer as correct feedback")
        self.feedback_button.clicked.connect(self.save_feedback)
        button_layout.addWidget(self.feedback_button)

        self.enter_correct_button = QPushButton("Enter Manual Answer")
        self.enter_correct_button.setIcon(QIcon.fromTheme("document-edit"))
        self.enter_correct_button.setToolTip("Manually enter the correct word if not in the list")
        self.enter_correct_button.clicked.connect(self.enter_correct_word)
        button_layout.addWidget(self.enter_correct_button)

        main_layout.addLayout(button_layout)

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # --- New File menu ---
        file_menu = QMenu("File", self)
        scan_action = QAction("Scan Crossword Image", self)
        scan_action.triggered.connect(self.load_and_scan_image)
        file_menu.addAction(scan_action)
        menu_bar.addMenu(file_menu)

        # Keep Help menu (About & User Guide)
        help_menu = QMenu("Help", self)
        help_action = QAction(QIcon.fromTheme("help-contents"), "User Guide", self)
        help_action.triggered.connect(self.show_help)
        about_action = QAction(QIcon.fromTheme("help-about"), "About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(help_action)
        help_menu.addAction(about_action)

        menu_bar.addMenu(help_menu)

    def load_and_scan_image(self):
        """Open file picker, run grid and clue scanners, and parse results."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Crossword Image", "", "Images (*.png *.jpg *.jpeg)")
        if not file_path:
            return

        grid_data = None
        clues_data = {}
        
        try:
            # --- MODIFIED: Two-stage scanning process ---
            # Stage 1: Scan the grid
            self.statusBar().showMessage("Scanning grid structure...")
            # ASSUMPTION: scan_crossword_image now returns (grid_data, grid_contour)
            grid_data, grid_contour = scan_crossword_image(file_path)
            if not grid_data or grid_contour is None:
                QMessageBox.critical(self, "Scan Error", "Scanner could not detect a valid crossword grid.")
                self.statusBar().clearMessage()
                return

            # Stage 2: Scan the clues
            self.statusBar().showMessage("Scanning clues from image...")
            clues_data = scan_clues_from_image(file_path, grid_contour)
            
            self.statusBar().clearMessage()

            # Stage 3: Parse and populate the UI
            self.parse_scanner_output(grid_data, clues_data)
            
            message = "Crossword grid extracted successfully!"
            if clues_data:
                message += f"\nFound and parsed {len(clues_data)} clues automatically."
            else:
                message += "\nCould not automatically find clues; please enter them manually."
            QMessageBox.information(self, "Scan Successful", message)

        except Exception as e:
            try:
                self.statusBar().clearMessage()
            except Exception:
                pass
            QMessageBox.critical(self, "Scan Error", f"An error occurred during scanning: {e}")

    def parse_scanner_output(self, grid, clues):
        """
        Convert scanner output into self.puzzle_data structure, now including clues.
        
        Args:
            grid (list): 15x15 grid data from scan_crossword_image.
            clues (dict): Dictionary mapping clue numbers to text from scan_clues_from_image.
        """
        self.puzzle_data = {}

        def is_white(r, c):
            return 0 <= r < 15 and 0 <= c < 15 and grid[r][c]['type'] == 'white'

        for r in range(15):
            for c in range(15):
                cell = grid[r][c]
                num = cell.get('number')
                if num is None:
                    continue
                
                # --- MODIFIED: Check for scanned clue text ---
                scanned_clue = clues.get(str(num), "")

                # Across
                if is_white(r, c) and (c == 0 or not is_white(r, c - 1)):
                    cells = []
                    cc = c
                    while cc < 15 and is_white(r, cc):
                        cells.append((r, cc))
                        cc += 1
                    key = f"{num}-Across"
                    pattern = ''.join(['?' for _ in cells])
                    self.puzzle_data[key] = {
                        'clue': scanned_clue,  # Use scanned clue
                        'answer': '',
                        'pattern': pattern,
                        'cells': cells
                    }

                # Down
                if is_white(r, c) and (r == 0 or not is_white(r - 1, c)):
                    cells = []
                    rr = r
                    while rr < 15 and is_white(rr, c):
                        cells.append((rr, c))
                        rr += 1
                    key = f"{num}-Down"
                    pattern = ''.join(['?' for _ in cells])
                    self.puzzle_data[key] = {
                        'clue': scanned_clue,  # Use scanned clue
                        'answer': '',
                        'pattern': pattern,
                        'cells': cells
                    }

        self.update_ui_from_puzzle_data()

    def update_ui_from_puzzle_data(self):
        """Populate the visual grid and the word list from self.puzzle_data."""
        # Clear visual grid first
        for r in range(15):
            for c in range(15):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.puzzle_table.setItem(r, c, item)

        # If no puzzle_data, clear list and return
        if not self.puzzle_data:
            self.word_list_widget.clear()
            return

        # To get numbers at coordinates, build reverse mapping from cells to numbers
        coord_to_number = {}
        for key in self.puzzle_data:
            # key like '1-Across' or '5-Down'
            num_str = key.split('-')[0]
            try:
                num = int(num_str)
            except Exception:
                continue
            # place the number for the first cell of that word if not already placed
            first_cell = self.puzzle_data[key]['cells'][0]
            if first_cell not in coord_to_number:
                coord_to_number[first_cell] = num

        # Now style black squares and put numbers
        # We'll infer black squares by checking if any word includes the cell; else mark black
        # Better: mark black if it's never white in puzzle data cells
        white_cells = set()
        for key, val in self.puzzle_data.items():
            for rc in val['cells']:
                white_cells.add(rc)

        for r in range(15):
            for c in range(15):
                item = self.puzzle_table.item(r, c)
                if (r, c) not in white_cells:
                    # black square
                    item.setBackground(Qt.GlobalColor.black)
                    item.setText("")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                else:
                    # white square
                    item.setBackground(Qt.GlobalColor.white)
                    # If there's a clue number, show it small in the cell (we'll just put the number)
                    if (r, c) in coord_to_number:
                        num = coord_to_number[(r, c)]
                        # show number as a small superscript-like prefix (simple approach)
                        item.setText(str(num))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                    else:
                        item.setText("")
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Populate word list sorted by number then Across/Down (Across before Down)
        def sort_key(k):
            parts = k.split('-')
            num = int(parts[0])
            typ = parts[1]
            return (num, 0 if typ.lower() == 'across' else 1)

        keys = sorted(self.puzzle_data.keys(), key=sort_key)
        self.word_list_widget.clear()
        for k in keys:
            self.word_list_widget.addItem(k)

    def on_word_selected(self, item):
        key = item.text()
        if key not in self.puzzle_data:
            return
        self.current_word_key = key
        entry = self.puzzle_data[key]
        # populate inputs
        self.pattern_input.setText(entry.get('pattern', ''))
        self.clue_input.setText(entry.get('clue', ''))
        self.clue_input.setFocus()

    def solve(self):
        clue = self.clue_input.text().strip()
        pattern = ''.join(self.pattern_input.text().strip().split()).upper()
        # Allow solving when at least one of clue or pattern is provided.
        if not clue and not pattern:
            QMessageBox.warning(self, "Input Error", "Please enter at least a clue or a pattern.")
            return

        try:
            # show simple status feedback while solving
            self.statusBar().showMessage("Searching...")
            results = self.solver.solve(clue, pattern)
            self.statusBar().clearMessage()

            ranked_list = results.get((clue, pattern.upper()), [])
            self.table.setRowCount(0)  # Clear previous results

            if not ranked_list:
                QMessageBox.information(self, "No Results", "No matching words found for the given clue and pattern.")
                return

            for row_idx, (word, score, definition) in enumerate(ranked_list):
                self.table.insertRow(row_idx)
                self.table.setItem(row_idx, 0, QTableWidgetItem(word))
                # score should be numeric; format safely in case it's not
                try:
                    score_text = f"{float(score):.2f}"
                except Exception:
                    score_text = str(score)
                self.table.setItem(row_idx, 1, QTableWidgetItem(score_text))
                self.table.setItem(row_idx, 2, QTableWidgetItem(definition))

            self.table.resizeColumnsToContents()
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        except Exception as e:
            # Ensure status cleared on error
            try:
                self.statusBar().clearMessage()
            except Exception:
                pass
            QMessageBox.critical(self, "Solver Error", f"An error occurred during solving: {e}")

    def save_feedback(self):
        if self.table.currentRow() < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a word from the table first.")
            return

        selected_row = self.table.currentRow()
        word = self.table.item(selected_row, 0).text()
        clue = self.clue_input.text().strip()
        pattern = ''.join(self.pattern_input.text().strip().split()).upper()

        try:
            # Keep existing solver feedback behavior
            self.solver.save_feedback(clue, pattern, word)

            # If we have a loaded puzzle and an active selected word, update puzzle_data and grid
            if self.puzzle_data and self.current_word_key:
                entry = self.puzzle_data.get(self.current_word_key)
                if entry is not None:
                    # store clue and answer
                    entry['clue'] = clue
                    entry['answer'] = word.upper()

                    # write letters into puzzle_table based on entry['cells']
                    for idx, (r, c) in enumerate(entry['cells']):
                        ch = word[idx].upper() if idx < len(word) else ''
                        item = self.puzzle_table.item(r, c)
                        if item is None:
                            item = QTableWidgetItem('')
                            self.puzzle_table.setItem(r, c, item)
                        item.setText(ch)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # update patterns for intersecting words
                    self.propagate_changes()

            QMessageBox.information(self, "Feedback Saved", f"Thank you! The word '{word}' was saved as a correct answer for the clue.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save feedback: {e}")

    def enter_correct_word(self):
        clue = self.clue_input.text().strip()
        pattern = ''.join(self.pattern_input.text().strip().split()).upper()
        # Require at least a clue or a pattern to provide context for the manual answer
        if not clue and not pattern:
            QMessageBox.warning(self, "Input Error", "Please enter the original clue or pattern before providing a manual answer.")
            return

        correct_word, ok = QInputDialog.getText(self, "Enter Correct Word", "Correct word:")
        if ok and correct_word:
            correct_word = correct_word.strip().upper()

            # Simple validation against the pattern (if a pattern exists)
            if pattern and not re.match(self.solver.pattern_to_regex(pattern), correct_word):
                QMessageBox.critical(self, "Pattern Mismatch", f"The word '{correct_word}' does not match the pattern '{pattern}'.")
                return

            try:
                self.solver.save_feedback(clue, pattern, correct_word)

                # If a puzzle is loaded and a word selected, update puzzle data similarly to save_feedback
                if self.puzzle_data and self.current_word_key:
                    entry = self.puzzle_data.get(self.current_word_key)
                    if entry is not None:
                        entry['clue'] = clue
                        entry['answer'] = correct_word.upper()
                        for idx, (r, c) in enumerate(entry['cells']):
                            ch = correct_word[idx].upper() if idx < len(correct_word) else ''
                            item = self.puzzle_table.item(r, c)
                            if item is None:
                                item = QTableWidgetItem('')
                                self.puzzle_table.setItem(r, c, item)
                            item.setText(ch)
                            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                        self.propagate_changes()

                QMessageBox.information(self, "Feedback Saved", f"Thank you! The word '{correct_word}' has been saved.")
                self.solve()  # Optionally re-solve to see updated scores
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save feedback: {e}")

    def propagate_changes(self):
        """Rebuild patterns for all words based on currently filled letters in the puzzle_table."""
        if not self.puzzle_data:
            return

        for key, entry in self.puzzle_data.items():
            chars = []
            for (r, c) in entry['cells']:
                item = self.puzzle_table.item(r, c)
                ch = ''
                if item is not None:
                    text = item.text().strip()
                    # If the cell text is a number (clue), ignore; we want letters
                    if len(text) == 1 and text.isalpha():
                        ch = text.upper()
                    elif len(text) > 1:
                        # In case we placed '5' or 'A' with number prefix, try to extract alpha
                        alpha = ''.join([t for t in text if t.isalpha()])
                        ch = alpha[0].upper() if alpha else ''
                chars.append(ch if ch else '?')
            entry['pattern'] = ''.join(chars)

        # Optionally refresh the currently shown pattern if a word is selected
        if self.current_word_key and self.current_word_key in self.puzzle_data:
            self.pattern_input.setText(self.puzzle_data[self.current_word_key]['pattern'])

    def toggle_theme(self):
        """
        Toggle between light and dark themes. This is wired to the single-click theme toggle button.
        The button's checked state and icon/text will reflect the theme.
        """
        self.dark_mode = not self.dark_mode
        # Apply theme stylesheet
        if self.dark_mode:
            self.setStyleSheet(ThemeManager.dark_theme())
        else:
            self.setStyleSheet(ThemeManager.light_theme())

        # Update toggle button checked state and icon/text
        self.theme_toggle_button.setChecked(self.dark_mode)
        if hasattr(self, "_light_icon") and hasattr(self, "_dark_icon"):
            self.theme_toggle_button.setIcon(self._dark_icon if self.dark_mode else self._light_icon)
            self.theme_toggle_button.setText("")  # no text when icons available
        else:
            self.theme_toggle_button.setText("☾" if self.dark_mode else "☀︎")

    def show_help(self):
        QMessageBox.information(self, "User Guide", (
            "<h3>How to Use ClueCortex</h3>"
            "<p><b>1. Enter Clue:</b> Type the crossword clue into the 'Clue' field (optional if you supply a pattern).</p>"
            "<p><b>2. Enter Pattern:</b> Type the known letters of the word in the 'Pattern' field. Use a question mark (?) for unknown letters (e.g., C?T). You may provide a pattern without a clue.</p>"
            "<p><b>3. Solve:</b> Click the 'Solve' button to see a list of potential answers ranked by relevance.</p>"
            "<p><b>4. Save Feedback:</b> If you find the correct answer in the list, select it and click 'Save as Correct' to help improve the solver.</p>"
            "<p><b>5. Manual Entry:</b> If the answer isn't in the list, you can add it by clicking 'Enter Manual Answer'.</p>"
            "<p><b>6. Scan:</b> Use 'Scan Grid from Image' to populate a 15x15 grid from a photo. Select words from the left list to auto-fill the pattern and then solve as normal.</p>"
        ))

    def show_about(self):
        reply = QMessageBox.question(
            self, "About ClueCortex",
            "ClueCortex v2.0\nA professional AI-powered crossword solver.\n\n"
            "This application uses advanced NLP models to find the best matches for your crossword clues.\n\n"
            "Would you like to visit the project's GitHub page?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Updated to the correct GitHub repository link provided
            webbrowser.open("https://github.com/Jontybr18211/CLUECORTEX-crossword-solver")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        # Initialize solver (WordNet is used internally by logic.py)
        solver = CrosswordSolver(feedback_file="feedback.json")
        window = ClueCortexWindow(solver)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        # Use a message box only if a QApplication exists; fall back to printing if not.
        try:
            QMessageBox.critical(None, "Startup Error", f"An unexpected error occurred: {e}")
        except Exception:
            print(f"Startup Error: {e}")