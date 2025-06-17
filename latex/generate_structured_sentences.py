import os
import re
import csv
from pathlib import Path
import nltk
nltk.download('punkt')
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters

# === CONFIG ===
input_dir = './'  # Set this to the path where your .tex files live
output_csv = 'structured_sentences.csv'
chapter_files = [f'chapter_{i}.tex' for i in range(1, 6)]

# === REGEX PATTERNS ===
patterns = {
    'chapter': re.compile(r'\\chapter(?:\[[^\]]*\])?{([^}]*)}'),
    'section': re.compile(r'\\section(?:\[[^\]]*\])?{([^}]*)}'),
    'subsection': re.compile(r'\\subsection(?:\[[^\]]*\])?{([^}]*)}'),
    'subsubsection': re.compile(r'\\subsubsection(?:\[[^\]]*\])?{([^}]*)}'),
    'paragraph': re.compile(r'\\paragraph(?:\[[^\]]*\])?{([^}]*)}'),
}

# === STATE TRACKING ===
position = {
    'chapter': 0,
    'section': 0,
    'subsection': 0,
    'subsubsection': 0,
    'paragraph': 0,
}
sentence_counter = 0  # resets per file

# === INITIALISE SENTENCE TOKENIZER WITH ABBREVIATIONS ===
punkt_params = PunktParameters()
punkt_params.abbrev_types = set([
    'e.g', 'i.e', 'et', 'al', 'fig', 'dr', 'vs', 'mr', 'mrs', 'prof', 'inc', 'etc'
])
tokenizer = PunktSentenceTokenizer(punkt_params)

# === OUTPUT ===
output_rows = []

def update_position(level):
    levels = ['chapter', 'section', 'subsection', 'subsubsection', 'paragraph']
    for l in levels:
        if l == level:
            position[l] += 1
        elif levels.index(l) > levels.index(level):
            position[l] = 0

def current_position_tuple():
    return tuple(position[level] for level in ['chapter', 'section', 'subsection', 'subsubsection', 'paragraph'])

for filename in chapter_files:
    path = Path(input_dir) / filename
    if not path.exists():
        print(f"⚠️  Skipping: {path} not found.")
        continue

    with open(path, encoding='utf-8') as f:
        lines = f.readlines()

    buffer = ''
    sentence_counter = 0

    for line in lines:
        line = line.strip()

        # Check for structural LaTeX commands
        for level, pattern in patterns.items():
            match = pattern.match(line)
            if match:
                update_position(level)
                buffer = ''
                break
        else:
            if not line or line.startswith('%'):
                continue  # skip comments and blanks

            buffer += ' ' + line

            if re.search(r'[.!?]\s*$', line):
                sentences = tokenizer.tokenize(buffer.strip())
                for sent in sentences:
                    sentence_counter += 1
                    row = {
                        'chapter': position['chapter'],
                        'section': position['section'],
                        'subsection': position['subsection'],
                        'subsubsection': position['subsubsection'],
                        'paragraph': position['paragraph'],
                        'sentence_number': sentence_counter,
                        'sentence': sent,
                        'full_index': f"{position['chapter']}.{position['section']}.{position['subsection']}."
                                      f"{position['subsubsection']}.{position['paragraph']}.{sentence_counter}"
                    }
                    output_rows.append(row)
                buffer = ''

    # Handle any leftover buffer at EOF
    if buffer.strip():
        sentences = tokenizer.tokenize(buffer.strip())
        for sent in sentences:
            sentence_counter += 1
            row = {
                'chapter': position['chapter'],
                'section': position['section'],
                'subsection': position['subsection'],
                'subsubsection': position['subsubsection'],
                'paragraph': position['paragraph'],
                'sentence_number': sentence_counter,
                'sentence': sent,
                'full_index': f"{position['chapter']}.{position['section']}.{position['subsection']}."
                              f"{position['subsubsection']}.{position['paragraph']}.{sentence_counter}"
            }
            output_rows.append(row)

# === OPTIONAL: ADD EMPTY COLUMNS FOR EACH PDF IN ../articles ===
articles_dir = Path('../articles')
if articles_dir.exists():
    pdf_stems = [pdf.stem for pdf in articles_dir.glob('*.pdf') if pdf.is_file()]
    for row in output_rows:
        for stem in pdf_stems:
            row[stem] = None

# === WRITE TO CSV ===
fieldnames = list(output_rows[0].keys())
with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output_rows)

print(f"✅ Done. Saved {len(output_rows)} sentences to: {output_csv}")
