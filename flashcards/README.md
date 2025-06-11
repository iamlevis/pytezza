# Flashcards Web UI

This simple Flask application provides a web-based flashcard interface
suitable for elementary school students.

## Features

- Choose from available flashcard sets on the home page.
- A preloaded set of U.S. states and capitals.
- Add new sets by dropping a JSON file into the `data` directory.
- Flashcards are shown in random order each time you view a set.
- The states set includes an interactive U.S. map that highlights the state for each question.

## Running

1. Ensure you have Python 3 and Flask installed. You can install Flask with:
   ```bash
   pip install Flask
   ```
2. Run the application:
   ```bash
   python app.py
   ```
3. Open `http://localhost:5000` in your browser.

The map visualization uses D3 and the public `us-atlas` dataset which are
loaded from a CDN, so internet access is required for the map to appear.

## Adding New Flashcard Sets

To add a new set, create a JSON file in the `data` folder. The file name
(becoming the set name) should have the structure `<name>.json` and contain
an array of objects with `question` and `answer` keys.

Example:
```json
[
  {"question": "1+1", "answer": "2"},
  {"question": "2+2", "answer": "4"}
]
```

Placing `math.json` in the `data` directory will automatically make a
"math" set available on the home page.
