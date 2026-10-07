"""Map Forlagið store categories and explicit genre claims to a small UI vocabulary."""
import re
CATEGORY_MAP={
 '13 ára og eldri':'Ungmenni','6-12 ára':'Barnabækur','0-5 ára':'Barnabækur',
 'Barna- og unglingabækur':'Barnabækur','Íslenskar skáldsögur':'Skáldsögur',
 'Þýddar skáldsögur':'Þýddar bækur','Spennusögur':'Spenna','Klassísk verk':'Klassík',
 'Smásögur':'Skáldverk','Skáldverk':'Skáldverk','Ástarsögur':'Rómantík',
 'Vísindaskáldskapur':'Vísindaskáldsaga','Sögulegar skáldsögur':'Skáldsögur',
 'Myndasögur fyrir börn og unglinga':'Myndasögur','Myndasögur fyrir fullorðna':'Myndasögur',
 'Fræði- og handbækur':'Fræðibækur','Fræðibækur':'Fræðibækur','Ævisögur':'Ævisögur','Ljóð':'Ljóð','Íslensk klassík':'Klassík','Þýdd klassík':'Klassík','Erlend klassík':'Klassík','Samtímaklassík':'Klassík',
 'Fantasíur':'Fantasía','Sígildar barnabækur':'Klassík',
 'Norrænar glæpasögur':'Glæpir','Spennusögur í rafbók':'Spenna','Jólarómans':'Rómantík',
}
CLAIMS=[
 (r'fantasí[au]|fantas[yí]|furðusag','Fantasía'),(r'hrollvekj','Hrollvekja'),
 (r'ráðgát','Ráðgáta'),(r'ljóðabók|barnaljóð|ljóðasafn','Ljóð'),
 (r'ástarsaga|rómantísk','Rómantík'),(r'glæpasag','Glæpir'),
 (r'spennusag|spennutryll','Spenna'),(r'gamansag|brandarabók','Grín'),
 (r'vísindaskáldskap|vísindaskáldsag','Vísindaskáldsaga'),
]
def normalize_categories(source_categories,description):
 result=list(dict.fromkeys(CATEGORY_MAP[c] for c in source_categories if c in CATEGORY_MAP))
 if 'Þýddar skáldsögur' in source_categories and 'Skáldsögur' not in result:result.append('Skáldsögur')
 for pattern,category in CLAIMS:
  # A nonfiction description may discuss romance/crime/fantasy as a topic.
  # Keep explicit store genres, but do not turn a topic mention into a fiction genre.
  if 'Fræðibækur' in result:continue
  if re.search(pattern,description,re.I) and category not in result:result.append(category)
 if 'Ungmenni' in result and 'Barnabækur' in result:result.remove('Barnabækur')
 return result
