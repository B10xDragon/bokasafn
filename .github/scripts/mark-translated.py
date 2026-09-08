import json
from pathlib import Path

path = Path('Resources/books.json')
books = json.loads(path.read_text(encoding='utf-8'))

translated_ids = {
    2,   # Nicole Yoon
    10,  # Roald Dahl
    24,  # Vikas Swarup
    25,  # Fredrik/Frederik Backman
    26,  # Yeonmi Park
    27,  # John Green
    31,  # Fredrik/Frederik Backman
    32,  # J.R.R. Tolkien
    33,  # Johan Harstad
    35,  # Suzanne Collins
    36,  # Suzanne Collins
    37,  # Christopher Paolini
    38,  # Suzanne Collins
    39,  # Maggie Stiefvater
}

for book in books:
    if int(book.get('id', -1)) in translated_ids:
        categories = book.setdefault('categories', [])
        if 'Þýddar bækur' not in categories:
            categories.append('Þýddar bækur')

path.write_text(json.dumps(books, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

marked = [book for book in books if 'Þýddar bækur' in book.get('categories', [])]
print(f'Merktar sem þýddar: {len(marked)} bækur')
print(', '.join(f"{book['id']}: {book['title']}" for book in marked))
