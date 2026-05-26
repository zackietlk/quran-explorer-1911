import json
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

os.chdir(r"C:\Users\white\Documents\Coding Apps\Quran Explorer")

# ── Arabic character definitions ──────────────────────────────────────────────

# All diacritics, vowel marks, and recitation markers
# that should be stripped when counting base letters
DIACRITICS = set(range(0x064B, 0x0660))   # standard harakat
DIACRITICS.add(0x0640)                     # tatweel
DIACRITICS.add(0x0670)                     # superscript alef
DIACRITICS.update(range(0x06D6, 0x06EF))  # extended marks including ۞ ۩ pause marks
DIACRITICS.update([0x200C, 0x200D, 0x200F, 0xFEFF])

# Alef variants — all normalize to plain alef ا for searching
ALEF_VARIANTS = {'\u0627','\u0623','\u0625','\u0622','\u0671'}

def is_marker_token(word):
    """
    Returns True if this word token contains ONLY markers/diacritics
    and no real Arabic letters. These are standalone recitation markers
    like pause signs ۖ ۗ ۚ and the rub el-hizb ۞ and sajdah ۩.
    They must be excluded from word counting entirely.
    """
    for c in word:
        cp = ord(c)
        if cp not in DIACRITICS and 0x0600 <= cp <= 0x06FF:
            return False
    return True

def base_letters(text):
    """Return list of real Arabic base letters, stripping all diacritics."""
    return [c for c in text
            if 0x0600 <= ord(c) <= 0x06FF
            and ord(c) not in DIACRITICS
            and c not in ' \n\t\r']

def letter_count(text):
    return len(base_letters(text))

def normalize(text):
    """Normalize for search: strip diacritics, collapse alef variants."""
    result = []
    for c in text:
        if ord(c) in DIACRITICS:
            continue
        if c in ALEF_VARIANTS:
            result.append('\u0627')
        else:
            result.append(c)
    return ''.join(result)

# ── Load inputs ───────────────────────────────────────────────────────────────

print("Loading quran_pages.json...")
with open("quran_pages.json", "r", encoding="utf-8") as f:
    pages_data = json.load(f)
page_map = pages_data["page_map"]

print("Loading quran-uthmani.xml...")
tree = ET.parse("quran-uthmani.xml")
root = tree.getroot()

# ── Parse into word list ──────────────────────────────────────────────────────

print("Parsing Quran text...")

all_words = []
marker_token_count = 0

for sura in root.findall('sura'):
    s = int(sura.get('index'))
    sura_name = sura.get('name', '')

    for aya in sura.findall('aya'):
        a = int(aya.get('index'))
        text = aya.get('text', '')
        bismillah = aya.get('bismillah', None)

        # Bismillah header: inject before ayah 1 of each surah except 1 and 9
        if bismillah and a == 1 and s not in (1, 9):
            bsm_tokens = bismillah.split()
            real_bsm = [w for w in bsm_tokens if not is_marker_token(w)]
            for wi, w in enumerate(real_bsm):
                ltrs = base_letters(w)
                all_words.append({
                    'surah': s, 'ayah': 0, 'word_idx': wi,
                    'text': w, 'letters': ltrs,
                    'letter_count': len(ltrs),
                    'is_ayah_end': wi == len(real_bsm) - 1,
                    'type': 'bismillah',
                    'surah_name': sura_name,
                })

        # Main ayah text — filter out marker tokens
        raw_tokens = text.split()
        real_tokens = []
        for w in raw_tokens:
            if is_marker_token(w):
                marker_token_count += 1
            else:
                real_tokens.append(w)

        for wi, w in enumerate(real_tokens):
            ltrs = base_letters(w)
            all_words.append({
                'surah': s, 'ayah': a, 'word_idx': wi,
                'text': w, 'letters': ltrs,
                'letter_count': len(ltrs),
                'is_ayah_end': wi == len(real_tokens) - 1,
                'type': 'text',
                'surah_name': sura_name,
            })

text_words = [w for w in all_words if w['type'] == 'text']
bismillah_words = [w for w in all_words if w['type'] == 'bismillah']

print(f"  Marker tokens removed:  {marker_token_count:,}")
print(f"  Real word tokens:       {len(text_words):,}")
print(f"  Bismillah header words: {len(bismillah_words):,}")
print(f"  Total in all_words:     {len(all_words):,}")

# ── Assign page numbers ───────────────────────────────────────────────────────

print("Assigning verified page numbers...")

for word in all_words:
    s, a = word['surah'], word['ayah']
    if a == 0:
        page = page_map.get(f"{s}:1", 1)
    else:
        page = page_map.get(f"{s}:{a}", 0)
    word['page'] = page

# ── Calibrate line capacity ───────────────────────────────────────────────────

print("Calibrating line capacity...")

sample_pages = [3, 4, 5, 6, 7, 8, 10, 15, 20, 50, 100, 200, 300]
totals = []
for pg in sample_pages:
    pg_words = [w for w in text_words if w['page'] == pg]
    if pg_words:
        totals.append(sum(w['letter_count'] for w in pg_words))

avg = sum(totals) / len(totals) if totals else 540
LINE_CAP = avg / 15
SPACE_COST = 0.5

print(f"  Average letters per page (sample): {avg:.0f}")
print(f"  Line capacity: {LINE_CAP:.1f} letters")

# ── Flow words into lines within each page ────────────────────────────────────

print("Flowing words into lines...")

words_by_page = defaultdict(list)
for word in all_words:
    words_by_page[word['page']].append(word)

for page_num in sorted(words_by_page.keys()):
    page_words = words_by_page[page_num]
    lines = []
    current_line = []
    current_width = 0

    for word in page_words:
        cost = word['letter_count'] + (SPACE_COST if current_line else 0)
        if current_width + cost > LINE_CAP and current_line:
            lines.append(current_line[:])
            current_line = [word]
            current_width = word['letter_count']
        else:
            current_line.append(word)
            current_width += cost

    if current_line:
        lines.append(current_line)

    for line_idx, line_words in enumerate(lines):
        line_num = line_idx + 1
        for word in line_words:
            word['line'] = line_num

total_lines = len(set((w['page'], w['line']) for w in all_words))
print(f"  Total lines: {total_lines:,}")

# ── Find MAX_X ────────────────────────────────────────────────────────────────

print("Computing MAX_X...")

line_letter_totals = defaultdict(int)
for w in text_words:
    line_letter_totals[(w['page'], w.get('line', 1))] += w['letter_count']

max_x = max(line_letter_totals.values()) if line_letter_totals else 35
max_x_key = max(line_letter_totals, key=line_letter_totals.get)
print(f"  MAX_X = {max_x} (page {max_x_key[0]}, line {max_x_key[1]})")

# ── Assign 3D coordinates ─────────────────────────────────────────────────────

print("Assigning 3D coordinates...")

word_records = []
letter_records = []
word_id = 0
letter_id = 0

# Group by page then line for coordinate assignment
from itertools import groupby

sorted_words = sorted(all_words, key=lambda w: (w['page'], w.get('line', 1), w.get('word_idx', 0)))

for (page_num, line_num), group in groupby(sorted_words, key=lambda w: (w['page'], w.get('line', 1))):
    x_cursor = 1
    for word in group:
        lc = word['letter_count']
        x_start = x_cursor
        x_end = x_cursor + lc - 1 if lc > 0 else x_cursor
        x_center = x_start + (lc - 1) / 2.0 if lc > 0 else x_cursor

        wrec = {
            'id': word_id,
            'surah': word['surah'],
            'ayah': word['ayah'],
            'word_idx': word['word_idx'],
            'type': word['type'],
            'text': word['text'],
            'letter_count': lc,
            'page': page_num,
            'line': line_num,
            'x': round(x_center, 2),
            'x_start': x_start,
            'x_end': x_end,
            'y': line_num,
            'z': page_num,
            'x_norm': round(x_center / max_x, 4),
            'y_norm': round((line_num - 1) / 14, 4),
            'z_norm': round((page_num - 1) / 603, 4),
        }
        word_records.append(wrec)

        for li, char in enumerate(word['letters']):
            lx = x_cursor + li
            letter_records.append({
                'id': letter_id,
                'word_id': word_id,
                'surah': word['surah'],
                'ayah': word['ayah'],
                'word_idx': word['word_idx'],
                'letter_idx': li,
                'char': char,
                'x': lx,
                'y': line_num,
                'z': page_num,
                'x_norm': round(lx / max_x, 4),
                'y_norm': round((line_num - 1) / 14, 4),
                'z_norm': round((page_num - 1) / 603, 4),
            })
            letter_id += 1

        x_cursor += lc
        word_id += 1

print(f"  Words: {len(word_records):,}")
print(f"  Letters: {len(letter_records):,}")

# ── Page summary ──────────────────────────────────────────────────────────────

page_summary = {}
for page_num, page_words in sorted(words_by_page.items()):
    tw = [w for w in page_words if w['type'] == 'text']
    if tw:
        first, last = tw[0], tw[-1]
        page_summary[str(page_num)] = {
            'page': page_num,
            'first': f"{first['surah']}:{first['ayah']}",
            'last': f"{last['surah']}:{last['ayah']}",
            'line_count': max(w.get('line', 1) for w in page_words),
        }

# ── Verification ──────────────────────────────────────────────────────────────

print("\nVerification:")
print(f"  Marker tokens removed:      {marker_token_count:,}")
print(f"  Text word tokens:           {len(text_words):,}  (expected ~77,433)")
print(f"  Total letters (text only):  {sum(w['letter_count'] for w in text_words):,}  (expected 325,386)")
print(f"  MAX_X:                      {max_x}")
print(f"  Pages:                      {len(page_summary)}")
print(f"  Allah (text, normalized):   {sum(1 for w in text_words if 'الله' in normalize(w['text']))}")

# ── Write mushaf.json ─────────────────────────────────────────────────────────

print("\nWriting mushaf.json...")

output = {
    'meta': {
        'description': 'Mushaf 3D Coordinate System — v2 (markers filtered)',
        'source': 'quran.com verified page mapping + Tanzil Uthmani XML',
        'total_pages': 604,
        'total_words': len([w for w in word_records if w['type'] == 'text']),
        'total_words_including_bismillah': len(word_records),
        'total_letters': len(letter_records),
        'max_x': max_x,
        'marker_tokens_excluded': marker_token_count,
        'coordinate_system': {
            'x': 'Letter position from right edge (1=rightmost). RTL.',
            'y': 'Line number on page (1=top)',
            'z': 'Page number (1 to 604)',
            'x_norm': '0=right edge 1=left edge',
            'y_norm': '0=top 1=bottom',
            'z_norm': '0=first page 1=last page',
        }
    },
    'pages': page_summary,
    'words': word_records,
    'letters': letter_records,
}

with open("mushaf.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

size_mb = os.path.getsize("mushaf.json") / 1024 / 1024
print(f"Done. mushaf.json written ({size_mb:.1f} MB)")
print(f"\nFinal counts:")
print(f"  Pages:   604")
print(f"  Words:   {output['meta']['total_words']:,}")
print(f"  Letters: {output['meta']['total_letters']:,}")
print(f"  MAX_X:   {max_x}")
print(f"  Bounding box: {max_x} x 15 x 604")
