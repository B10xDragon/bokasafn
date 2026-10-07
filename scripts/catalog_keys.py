"""Shared edition-insensitive comparison. Never change the catalog's stored IDs."""
import re,unicodedata

def title_key(title):
    text=unicodedata.normalize('NFKC',title)
    # Store presentation flags, not part of the literary title.
    text=re.sub(r'\s+NÝ\s*$','',text)
    text=re.sub(r'^\(\d+\)\s*','',text)
    text=text.casefold()
    # Forlagið appends this series label to otherwise unchanged volume titles.
    # Keep standalone volume numbers (e.g. Hvísl hrafnanna 3) distinct.
    text=re.sub(r'\s+\(hungurleikar\s+\d+\)\s*$','',text)
    text=re.sub(r'\s*[-–—:]?\s*\((?:kilja|rafbók|hljóðbók|innbundin|[^)]*útgáfa)\)\s*$','',text)
    text=re.sub(r'\s*[-–—]\s*(?:kilja|rafbók|hljóðbók|innbundin|myndskreytt|ný|\d+\.?\s*útgáfa)\s*$','',text)
    return ''.join(x for x in text if x.isalnum())
