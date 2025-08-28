from flask import Flask, render_template, abort
import json
import random
from pathlib import Path

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / 'data'


def get_available_sets():
    return [p.stem for p in DATA_DIR.glob('*.json')]


def load_set(set_name):
    file_path = DATA_DIR / f'{set_name}.json'
    if not file_path.exists():
        return None
    with open(file_path) as f:
        return json.load(f)


@app.route('/')
def index():
    sets = get_available_sets()
    return render_template('index.html', sets=sets)


@app.route('/flashcards/<set_name>')
def flashcards_view(set_name):
    cards = load_set(set_name)
    if cards is None:
        abort(404)
    random.shuffle(cards)
    return render_template('flashcards.html', set_name=set_name, cards=cards)


if __name__ == '__main__':
    app.run(debug=True)
