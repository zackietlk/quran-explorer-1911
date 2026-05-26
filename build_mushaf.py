import json
import os

os.chdir(r"C:\Users\white\Documents\Coding Apps\Quran Explorer")

# ── Load inputs ───────────────────────────────────────────────────────────────

print("Loading quran_pages.json...")
with open("quran_pages.json", "r", encoding="utf-8") as f:
    pages_data = json.load(f)
page_map = pages_data["page_map"]  # "surah:ayah" -> page number

print("Loading quran-uthmani.xml...")
import xml.etree.ElementTree as ET
tree = ET.parse("quran-uthmani.xml")
root = tree.getroot()

# ── Arabic letter tools ───────────────────────────────────────────────────────

DIACRITICS = set(range(0x064B, 0x0660))
DIACRITICS.add(0x0640)
DIACRITICS.add(0x0670)
DIACRITICS.update(range(0x06D6, 0x06EF))
DIACRITICS.update([0x200C, 0x200D, 0x200F, 0xFEFF])

ALEF_VARIANTS = {'\u0627', '\u0623', '\u0625', '\u0622',
                 '\u0671', '\u0672', '\u0673'}

def base_letters(text):
    return [c for c in text
            if 0x0600 <= ord(c) <= 0x06FF
            and ord(c) not in DIACRITICS
            and c not in ' \n\t\r']

def letter_count(text):
    return len(base_letters(text))

# ── Parse Tanzil XML into word list ───────────────────────────────────────────

print("Parsing Quran text...")

all_words = []  # flat list of every word token in Mushaf order

for sura in root.findall('sura'):
    s = int(sura.get('index'))
    sura_name = sura.get('name', '')

    for aya in sura.findall('aya'):
        a = int(aya.get('index'))
        text = aya.get('text', '')
        bismillah = aya.get('bismillah', None)

        # Bismillah header for this surah (stored on ayah 1, not ayah 0)
        # We inject it as a separate word group before ayah 1
        if bismillah and a == 1 and s not in (1, 9):
            bsm_words = bismillah.split()
            for wi, w in enumerate(bsm_words):
                ltrs = base_letters(w)
                all_words.append({
                    'surah': s,
                    'ayah': 0,           # 0 = bismillah header
                    'word_idx': wi,
                    'text': w,
                    'letters': ltrs,
                    'letter_count': len(ltrs),
                    'is_ayah_end': wi == len(bsm_words) - 1,
                    'type': 'bismillah',
                    'surah_name': sura_name,
                })

        wlist = text.split()
        for wi, w in enumerate(wlist):
            ltrs = base_letters(w)
            all_words.append({
                'surah': s,
                'ayah': a,
                'word_idx': wi,
                'text': w,
                'letters': ltrs,
                'letter_count': len(ltrs),
                'is_ayah_end': wi == len(wlist) - 1,
                'type': 'text',
                'surah_name': sura_name,
            })

print(f"  Total word tokens: {len(all_words)}")

# ── Assign page numbers from verified map ─────────────────────────────────────

print("Assigning verified page numbers...")

for word in all_words:
    s, a = word['surah'], word['ayah']
    if a == 0:
        # Bismillah: same page as ayah 1 of this surah
        page = page_map.get(f"{s}:1", 1)
    else:
        page = page_map.get(f"{s}:{a}", 0)
    word['page'] = page

# ── Assign line numbers within each page ──────────────────────────────────────
# Strategy: within each page, group words into lines by letter count.
# We know exactly which ayat are on each page (from page_map).
# We flow words into lines greedily by letter count.
# Line capacity calibrated to produce ~15 lines per page on average.
#
# Calibration: from verified data, page 3 has ayat 2:6 through 2:16.
# We count their letters and find LINE_CAP that gives ~15 lines.

print("Calibrating line capacity...")

# Collect words for page 3 as calibration sample
page3_words = [w for w in all_words if w['page'] == 3 and w['type'] == 'text']
total_letters_p3 = sum(w['letter_count'] for w in page3_words)
print(f"  Page 3: {len(page3_words)} words, {total_letters_p3} letters")
print(f"  Average letters per line (15 lines): {total_letters_p3/15:.1f}")

# Simple calibration: average letters per line across many pages
sample_pages = [3, 4, 5, 10, 20, 50, 100, 200]
totals = []
for pg in sample_pages:
    pg_words = [w for w in all_words if w['page'] == pg and w['type'] == 'text']
    if pg_words:
        totals.append(sum(w['letter_count'] for w in pg_words))

avg_letters_per_page = sum(totals) / len(totals) if totals else 500
LINE_CAP_LETTERS = avg_letters_per_page / 15
print(f"  Calibrated LINE_CAP: {LINE_CAP_LETTERS:.1f} letters per line")

SPACE_COST = 0.5  # inter-word space cost in letter units

# ── Flow words into lines within each page ────────────────────────────────────

print("Flowing words into lines...")

# Group all words by page
from collections import defaultdict
words_by_page = defaultdict(list)
for word in all_words:
    words_by_page[word['page']].append(word)

# For each page, flow into lines
line_records = []  # (page, line_num, [words])

for page_num in sorted(words_by_page.keys()):
    page_words = words_by_page[page_num]

    lines = []
    current_line = []
    current_width = 0

    for word in page_words:
        cost = word['letter_count'] + (SPACE_COST if current_line else 0)

        if current_width + cost > LINE_CAP_LETTERS and current_line:
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
        line_records.append((page_num, line_num, line_words))

print(f"  Total lines across all pages: {len(line_records)}")

# ── Find MAX_X: most letters on any single line ───────────────────────────────

print("Computing MAX_X...")

max_x = 0
for page_num, line_num, line_words in line_records:
    line_letters = sum(w['letter_count'] for w in line_words)
    if line_letters > max_x:
        max_x = line_letters

print(f"  MAX_X = {max_x}")

# ── Assign X coordinates to every word and letter ────────────────────────────

print("Assigning 3D coordinates...")

word_records = []
letter_records = []
word_id = 0
letter_id = 0

for page_num, line_num, line_words in line_records:
    x_cursor = 1  # start from right edge (x=1 is rightmost letter)

    for word in line_words:
        lc = word['letter_count']
        x_start = x_cursor
        x_end = x_cursor + lc - 1
        x_center = x_start + (lc - 1) / 2.0

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

        # Individual letters
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

# ── Build page summary ────────────────────────────────────────────────────────

page_summary = {}
for page_num in sorted(words_by_page.keys()):
    page_words = words_by_page[page_num]
    # Find first and last ayah on this page
    text_words = [w for w in page_words if w['type'] == 'text']
    if text_words:
        first = text_words[0]
        last = text_words[-1]
        page_summary[str(page_num)] = {
            'page': page_num,
            'first': f"{first['surah']}:{first['ayah']}",
            'last': f"{last['surah']}:{last['ayah']}",
            'line_count': max(w.get('line', 1) for w in page_words),
        }

# ── Write mushaf.json ─────────────────────────────────────────────────────────

print("Writing mushaf.json...")

output = {
    'meta': {
        'description': 'Mushaf 3D Coordinate System',
        'source': 'quran.com verified page mapping + Tanzil Uthmani text',
        'total_pages': 604,
        'total_words': len(word_records),
        'total_letters': len(letter_records),
        'max_x': max_x,
        'coordinate_system': {
            'x': 'Letter position from right (1=rightmost). RTL.',
            'y': 'Line number on page (1=top)',
            'z': 'Page number (1 to 604)',
            'x_norm': '0=right edge, 1=left edge',
            'y_norm': '0=top, 1=bottom',
            'z_norm': '0=first page, 1=last page',
        }
    },
    'pages': page_summary,
    'words': word_records,
    'letters': letter_records,
}

with open("mushaf.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

size_mb = os.path.getsize("mushaf.json") / 1024 / 1024
print(f"\nDone. mushaf.json written ({size_mb:.1f} MB)")
print(f"  Pages: 604")
print(f"  Words: {len(word_records):,}")
print(f"  Letters: {len(letter_records):,}")
print(f"  MAX_X: {max_x}")
print(f"  Bounding box: {max_x} x 15 x 604")
print(f"\nThe coordinate system is locked.")