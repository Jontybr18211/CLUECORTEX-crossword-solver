


# 🧠 ClueCortex - Crossword Solver

**ClueCortex** is an advanced, user-friendly crossword puzzle solver built using Python and PyQt6. It assists users in solving crossword clues by taking a clue and a letter pattern as input, generating word suggestions ranked by semantic relevance and part-of-speech (POS) tagging to filter candidate words based on the clue using NLTK’s WordNet, and integrating a feedback system to enhance results over time. The elegant GUI supports both light and dark themes, making the experience both functional and visually appealing.

---

## 📑 Table of Contents

* [✨ Features](#-features)
* [⚙️ Prerequisites](#️-prerequisites)
* [📦 Installation](#-installation)
* [📥 Downloading Required Models](#-downloading-required-models)
* [⚡ How It Works](#-how-it-works)
* [🗂️ File Structure](#️-file-structure)
* [🚀 Usage](#-usage)
* [🪪 License](#-license)

---

## ✨ Features

* 🔍 **Clue & Pattern Input**: Solve clues like `"Feline friend"` with patterns like `"C?T"`.
* 📚 **WordNet Integration**: Uses NLTK’s WordNet to rank suggestions based on semantic similarity.
* 🧠 **User Feedback System**: Saves correct words for specific clue-pattern pairs to improve future results.
* 🎨 **Elegant GUI**: Supports light/dark themes with a modern and user-friendly interface.
* 📈 **Interactive Results**: Displays suggestions with confidence scores and word definitions.
* ✏️ **Custom Word Input**: Allows users to manually input correct answers if needed.
* 🛡️ **Error Handling**: Validates inputs and provides clear error messages.

---

## ⚙️ Prerequisites

Before running ClueCortex, make sure you have:

* **Python**: Version 3.8 or higher
* **OS Compatibility**: Windows, macOS, or Linux
* **Required Files**:

  * `words.txt`: Dictionary of words (one per line). A sample is included.
  * `feedback.json`: Stores user feedback (auto-created if not found).
* **Internet Connection**: Needed once for downloading NLTK models.

---

## 📦 Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/<your-username>/ClueCortex.git
   cd ClueCortex
   ```

2. **Install Dependencies**:

   ```bash
   pip install nltk
   ```

3. **Prepare Required Files**:

   * Ensure `words.txt` is present in the same folder as `crossword_solver.py`.
   * `feedback.json` will be created automatically when feedback is saved. You may initialize it with `{}`.

4. **Run the Application**:

   ```bash
   python crossword_solver.py
   ```

---

## 📥 Downloading Required Models

ClueCortex uses NLTK's **WordNet** and **Punkt** models. These are downloaded automatically on the first run, but you can also download them manually:

```python
import nltk
nltk.download('wordnet')
nltk.download('punkt')
```

> 📁 These models are stored in `~/nltk_data` (Linux/macOS) or `%APPDATA%\nltk_data` (Windows). Total size \~50MB.

---

## ⚡ How It Works

ClueCortex uses a combination of **pattern matching** and **semantic ranking**:

### 🔡 Input Processing

* Users input a **clue** and a **pattern** (e.g., `"A?ES"`).
* The pattern is converted into a regular expression (e.g., `^A[A-Z]ES$`) to find matches in `words.txt`.

### 🧩 Word Matching

* Words matching the regex pattern are filtered using `CrosswordSolver`.
* If no pattern is given or it's all wildcards (`"???"`), word length is inferred from the clue.

### 🧠 Semantic Ranking

* Suggestions are ranked using **WordNet synsets**.
* Matching is based on:

  * Definitions (weight: `0.5`)
  * Synset names (weight: `0.7`)
  * Hypernyms (weight: `0.3`)
* Feedback from `feedback.json` is prioritized with a score of `1.0`.

### 💬 Feedback System

* Save correct suggestions or enter custom words.
* Feedback is stored as:
  `("Clue", "Pattern") : "Correct Word"`

### 🖼️ GUI Features

* Tkinter-based GUI with table view: Word | Score | Definition
* Light/Dark theme toggle
* Help and About pages

---

## 🗂️ File Structure

```
ClueCortex/
├── logic.py                # Main script
├── gui.py                  # Gui
├── words.txt               # Dictionary file
├── feedback.json           # User feedback (created automatically)
```

### 🔤 Sample `words.txt`

```
>>>>>>> 0c2082be5f1b9e4fac4a900597283cc1bb6c3d31
ARES
CAT
HAT
EMU
OAK
...
<<<<<<< HEAD

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
=======
```

### 📝 Sample `feedback.json`

```json
{
  "(\"Greek god of war\", \"A?ES\")": "ARES",
  "(\"Feline friend\", \"C?T\")": "CAT"
}
```

---

## 🚀 Usage

### 🏁 Launch

```bash
python crossword_solver.py
```

### 🧠 Solve a Clue

* Enter the **clue** (e.g., "Feline friend")
* Enter the **pattern** (e.g., `"C?T"`)
* Click **Solve** or press **Enter**

### 📊 Review Results

* View top 3 suggestions with:

  * Confidence scores
  * Word definitions
* Saved feedback appears at the top.

### 🧩 Provide Feedback

* Select a suggestion and click **"Save as Feedback"**
* Or click **"Enter Correct Word"** and input your answer.
  (It must match the pattern.)

### 🎨 Switch Theme

* Use the **Theme** menu for Light or Dark mode

### ❓ Help

* `Help > User Guide`: Instructions
* `Help > About`: App info

---


## 🪪 License

This project is licensed under the **MIT License**.
See the [LICENSE](./LICENSE) file for more information.

---

>>>>>>> 0c2082be5f1b9e4fac4a900597283cc1bb6c3d31
