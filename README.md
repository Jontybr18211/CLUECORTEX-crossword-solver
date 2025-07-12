---

# 🧠 ClueCortex - Crossword Solver

**ClueCortex** is an advanced, user-friendly crossword puzzle solver built using Python and Tkinter. It assists users in solving crossword clues by taking a clue and a letter pattern as input, generating word suggestions ranked by semantic relevance using NLTK’s WordNet, and integrating a feedback system to enhance results over time. The elegant GUI supports both light and dark themes, making the experience both functional and visually appealing.

---

## 📑 Table of Contents

* [✨ Features](#-features)
* [⚙️ Prerequisites](#️-prerequisites)
* [📦 Installation](#-installation)
* [📥 Downloading Required Models](#-downloading-required-models)
* [⚡ How It Works](#-how-it-works)
* [🗂️ File Structure](#️-file-structure)
* [🚀 Usage](#-usage)
* [🤝 Contributing](#-contributing)
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
├── crossword_solver.py     # Main script
├── words.txt               # Dictionary file
├── feedback.json           # User feedback (created automatically)
```

### 🔤 Sample `words.txt`

```
ARES
CAT
HAT
EMU
OAK
...
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

