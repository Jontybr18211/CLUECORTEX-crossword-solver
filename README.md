"""
 ClueCortex - Crossword SolverClueCortex is an advanced, user-friendly crossword puzzle solver built with Python and Tkinter. It assists users in solving crossword clues by taking a clue and a letter pattern as input, generating word suggestions ranked by relevance using WordNet from NLTK, and incorporating a user feedback system to improve accuracy over time. The application features an elegant GUI with light and dark themes, making it both functional and visually appealing.Table of ContentsFeatures (#features)
Prerequisites (#prerequisites)
Installation (#installation)
Downloading Required Models (#downloading-required-models)
How It Works (#how-it-works)
File Structure (#file-structure)
Usage (#usage)
Contributing (#contributing)
License (#license)

FeaturesClue and Pattern Input: Enter a crossword clue (e.g., "Feline friend") and a pattern (e.g., "C?T") to get word suggestions.
WordNet Integration: Uses NLTK's WordNet to rank suggestions based on semantic similarity to the clue, providing definitions for each word.
User Feedback System: Save correct words for specific clue-pattern pairs to improve future results, with an option to input custom words.
Elegant GUI: Offers light and dark themes with a modern, high-contrast design for an enhanced user experience.
Interactive Results: Displays suggestions with confidence scores and definitions in a scrollable table.
Custom Word Input: Allows users to enter a correct word if the suggestions are unsatisfactory, which is saved for future use.
Error Handling: Validates inputs and provides clear error messages for invalid patterns or missing files.

PrerequisitesBefore using ClueCortex, ensure you have the following:Python 3.8 or higher: The application is built with Python and requires a compatible version.
Operating System: Compatible with Windows, macOS, or Linux.
Required Files:words.txt: A text file containing a list of words (one per line) to serve as the dictionary. A sample file is included in the repository.
feedback.json: A JSON file to store user feedback (created automatically if not present).

Internet Connection: Required for the initial download of NLTK models (see Downloading Required Models (#downloading-required-models)).

InstallationClone the Repository:bash

git clone https://github.com/<your-username>/ClueCortex.git
cd ClueCortex

Install Python Dependencies:
The application requires the nltk library. Install it using pip:bash

pip install nltk

Prepare Required Files:Ensure words.txt is in the same directory as the main script (crossword_solver.py). This file should contain one word per line (uppercase recommended). A sample words.txt is provided in the repository.
The feedback.json file will be created automatically when you save feedback, but you can initialize it with an empty JSON object ({}) if desired.

Run the Application:bash

python crossword_solver.py

Downloading Required ModelsClueCortex uses NLTK's WordNet and Punkt models for semantic ranking and tokenization. These are downloaded automatically on the first run, but you can ensure they are installed manually:Open a Python shell:python

import nltk
nltk.download('wordnet')
nltk.download('punkt')

Alternatively, if the application fails to download these models due to network issues, run the above commands before launching the app.

Note: The models require approximately 50 MB of disk space and are stored in your NLTK data directory (e.g., ~/nltk_data on Linux/macOS or %APPDATA%\nltk_data on Windows).How It WorksClueCortex combines pattern matching with semantic analysis to provide accurate crossword solutions:Input Processing:Users enter a clue (e.g., "Greek god of war") and a pattern (e.g., "A?ES", where ? represents an unknown letter).
The pattern is converted to a regular expression (e.g., ^A[A-Z]ES$) to find matching words from words.txt.

Word Matching:The CrosswordSolver class filters words from the dictionary that match the pattern.
If no pattern is provided or it’s all wildcards (e.g., "???"), the solver estimates word length based on clue complexity.

Ranking with WordNet:Matches are ranked using WordNet’s synsets, comparing clue words to definitions, synset names, and hypernyms.
Scores are computed based on word overlap, with weights (0.5 for definitions, 0.7 for synset names, 0.3 for hypernyms).
Feedback from feedback.json prioritizes user-corrected words with a score of 1.0 and a definition (WordNet or "User-provided").

Feedback System:Users can select a suggested word and save it as feedback for the clue-pattern pair, stored in feedback.json.
Alternatively, users can input a custom correct word via the "Enter Correct Word" button, which is validated against the pattern and saved.
Saved feedback ensures the correct word appears first with its definition in future queries for the same clue-pattern.

GUI Features:The Tkinter-based GUI displays results in a table with columns for Word, Score, and Definition.
Supports light and dark themes, switchable via the "Theme" menu.
Includes a help guide and about page for user assistance.

File StructureThe project requires the following files in the same directory as crossword_solver.py:

ClueCortex/
├── crossword_solver.py     # Main application script
├── words.txt              # Dictionary file (one word per line)
├── feedback.json          # Feedback storage (created automatically if missing)

Example words.txt

ARES
CAT
HAT
EMU
OAK
...

Example feedback.jsonjson

{
    "(\"Greek god of war\", \"A?ES\")": "ARES",
    "(\"Feline friend\", \"C?T\")": "CAT"
}

UsageLaunch the Application:
Run python crossword_solver.py to start the GUI.
Enter Clue and Pattern:In the "Clue" field, enter the crossword clue (e.g., "Feline friend").
In the "Pattern" field, enter the letter pattern (e.g., "C?T" for a three-letter word starting with C and ending with T).
Click "Solve" or press Enter to see suggestions.

Review Results:The results table shows up to three words, with their confidence scores and definitions.
Feedback words (if saved) appear at the top with a score of 1.0.

Provide Feedback:Select a word from the results and click "Save as Feedback" to store it.
If no suggestions are correct, click "Enter Correct Word," input the correct word (e.g., "CAT"), and save it. The word is validated against the pattern.

Switch Themes:Use the "Theme" menu to toggle between light and dark modes for better visibility.

Access Help:Click "Help" > "User Guide" for instructions or "About" for project details.

ContributingContributions to ClueCortex are welcome! To contribute:Fork the repository.
Create a new branch (git checkout -b feature/your-feature).
Make changes and commit (git commit -m "Add your feature").
Push to the branch (git push origin feature/your-feature).
Open a pull request with a description of your changes.

Please ensure code follows PEP 8 style guidelines and includes relevant tests.LicenseThis project is licensed under the MIT License. See the LICENSE file for details.
"""
