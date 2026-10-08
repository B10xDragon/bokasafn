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

def author_key(author):
    return ''.join(c for c in unicodedata.normalize('NFKC',author).casefold() if c.isalnum())

def likely_duplicate(a,b):
    from difflib import SequenceMatcher
    # Shared creators may include a translator/illustrator; this is a candidate,
    # never an automatic merge. Volume numbers prevent collapsing a series.
    if author_key(a.get('author','').split(',')[0])!=author_key(b.get('author','').split(',')[0]):return False
    x,y=title_key(a.get('title','')),title_key(b.get('title',''))
    if x==y:return True
    nx,ny=re.findall(r'\d+',x),re.findall(r'\d+',y)
    if nx and ny and nx!=ny:return False
    return bool(x and y) and (x in y or y in x or SequenceMatcher(None,x,y).ratio()>.84)
