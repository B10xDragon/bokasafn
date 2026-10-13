#!/usr/bin/env python3
"""Refresh the browser author registry without changing stable identity IDs."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
authors=json.loads((root/'Resources/authors.json').read_text())
(root/'js/browse-metadata.js').write_text('// Generated from Resources/authors.json. IDs are reserved across display-name changes.\nglobalThis.BOKASAFN_AUTHORS = '+json.dumps(authors,ensure_ascii=False,separators=(',',':'))+';\n')
print(f'Wrote {len(authors)} author identities')
