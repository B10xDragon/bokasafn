"""Conservative, explicit language evidence from Forlagið metadata only."""
import re,unicodedata

def icelandic_evidence(record):
 if record.get('language')=='is':return record['languageEvidence']
 if 'Íslensk klassík' in record.get('sourceCategories',[]):return 'Icelandic classics source category'
 if 'Þýdd klassík' in record.get('sourceCategories',[]):return 'Icelandic translated-classics source category'
 text=unicodedata.normalize('NFC',record.get('sourceDescription',''))
 # Do not infer an edition language just from its author's nationality or title.
 patterns=[
  (r'íslensk\w* þýðing\w*','Product description explicitly identifies an Icelandic translation'),
  (r'(?:kemur|kom|komu|koma|komin|komið|út|gefin|gefið|gefnar|gefinn|útgáfa)\b[^.!?]{0,50}\bá íslensku\b','Product description explicitly identifies an Icelandic edition'),
  (r'þýddi\b[^.!?]{0,40}\bfyrir íslenska lesendur','Product description explicitly identifies translation for Icelandic readers'),
  (r'þýddi\b[^.!?]{0,30}\byfir á íslensk\w*','Product description explicitly identifies translation into Icelandic'),
 ]
 for pattern,evidence in patterns:
  if re.search(pattern,text,re.I):return evidence
 return None
