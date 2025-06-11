# Flashcards Web UI

This simple Flask application provides a web-based flashcard interface
suitable for elementary school students.

## Features

- Choose from available flashcard sets on the home page.
- A preloaded set of U.S. states and capitals.
- Add new sets by dropping a JSON file into the `data` directory.

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
