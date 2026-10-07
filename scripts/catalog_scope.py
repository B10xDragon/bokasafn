"""Exclude clearly identified coloring/activity stationery, not literary diaries."""
import re
ACTIVITY_TITLE=r'litabók|litaðu|þrautabók|krossgát|sudoku|stundaskrá|spilastokk|teikni?bók|skipulagsbók|verkefnabók|skemmtibók með límmiðum|^þankastrik\b'
def is_activity_title(title):
 return bool(re.search(ACTIVITY_TITLE,title,re.I))
