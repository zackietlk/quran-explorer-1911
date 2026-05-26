import json
import os
from collections import defaultdict

os.chdir(r"C:\Users\white\Documents\Coding Apps\Quran Explorer")

print("Loading mushaf.json...")
with open("mushaf.json", "r", encoding="utf-8") as f:
    data = json.load(f)

words = data['words']
letters = data['letters']

# ── Normalization ─────────────────────────────────────────────────────────────

DIACRITICS = set(range(0x064B, 0x0660))
DIACRITICS.add(0x0640)
DIACRITICS.add(0x0670)
DIACRITICS.update(range(0x06D6, 0x06EF))
ALEF = {'\u0627', '\u0623', '\u0625', '\u0622', '\u0671'}

def normalize(text):
    result = []
    for c in text:
        if ord(c) in DIACRITICS:
            continue
        if c in ALEF:
            result.append('\u0627')
        else:
            result.append(c)
    return ''.join(result)

def base_letters(text):
    return [c for c in text
            if 0x0600 <= ord(c) <= 0x06FF
            and ord(c) not in DIACRITICS
            and c not in ' \n\t\r']

SURAH_NAMES = {
    1:'Al-Fatiha', 2:'Al-Baqara', 3:'Ali-Imran', 4:'An-Nisa',
    5:'Al-Maida', 6:'Al-Anam', 7:'Al-Araf', 8:'Al-Anfal',
    9:'At-Tawba', 10:'Yunus', 11:'Hud', 12:'Yusuf',
    13:'Ar-Rad', 14:'Ibrahim', 15:'Al-Hijr', 16:'An-Nahl',
    17:'Al-Isra', 18:'Al-Kahf', 19:'Maryam', 20:'Taha',
    21:'Al-Anbiya', 22:'Al-Hajj', 23:'Al-Muminun', 24:'An-Nur',
    25:'Al-Furqan', 26:'Ash-Shuara', 27:'An-Naml', 28:'Al-Qasas',
    29:'Al-Ankabut', 30:'Ar-Rum', 31:'Luqman', 32:'As-Sajda',
    33:'Al-Ahzab', 34:'Saba', 35:'Fatir', 36:'Ya-Sin',
    37:'As-Saffat', 38:'Sad', 39:'Az-Zumar', 40:'Ghafir',
    41:'Fussilat', 42:'Ash-Shura', 43:'Az-Zukhruf', 44:'Ad-Dukhan',
    45:'Al-Jathiya', 46:'Al-Ahqaf', 47:'Muhammad', 48:'Al-Fath',
    49:'Al-Hujurat', 50:'Qaf', 51:'Adh-Dhariyat', 52:'At-Tur',
    53:'An-Najm', 54:'Al-Qamar', 55:'Ar-Rahman', 56:'Al-Waqia',
    57:'Al-Hadid', 58:'Al-Mujadila', 59:'Al-Hashr', 60:'Al-Mumtahana',
    61:'As-Saf', 62:'Al-Jumua', 63:'Al-Munafiqun', 64:'At-Taghabun',
    65:'At-Talaq', 66:'At-Tahrim', 67:'Al-Mulk', 68:'Al-Qalam',
    69:'Al-Haqqa', 70:'Al-Maarij', 71:'Nuh', 72:'Al-Jinn',
    73:'Al-Muzzammil', 74:'Al-Muddaththir', 75:'Al-Qiyama',
    76:'Al-Insan', 77:'Al-Mursalat', 78:'An-Naba', 79:'An-Naziat',
    80:'Abasa', 81:'At-Takwir', 82:'Al-Infitar', 83:'Al-Mutaffifin',
    84:'Al-Inshiqaq', 85:'Al-Buruj', 86:'At-Tariq', 87:'Al-Ala',
    88:'Al-Ghashiya', 89:'Al-Fajr', 90:'Al-Balad', 91:'Ash-Shams',
    92:'Al-Layl', 93:'Ad-Duha', 94:'Ash-Sharh', 95:'At-Tin',
    96:'Al-Alaq', 97:'Al-Qadr', 98:'Al-Bayyina', 99:'Az-Zalzala',
    100:'Al-Adiyat', 101:'Al-Qaria', 102:'At-Takathur', 103:'Al-Asr',
    104:'Al-Humaza', 105:'Al-Fil', 106:'Quraysh', 107:'Al-Maun',
    108:'Al-Kawthar', 109:'Al-Kafirun', 110:'An-Nasr',
    111:'Al-Masad', 112:'Al-Ikhlas', 113:'Al-Falaq', 114:'An-Nas'
}

library = {}

# ── 1. Surah boundaries ───────────────────────────────────────────────────────

print("Computing surah boundaries...")

text_words = [w for w in words if w['type'] == 'text']
bismillah_words = [w for w in words if w['type'] == 'bismillah']

surah_data = defaultdict(lambda: {
    'words': [], 'letters_count': 0, 'word_count': 0,
    'ayat': set(), 'pages': set()
})

for w in text_words:
    s = w['surah']
    surah_data[s]['words'].append(w)
    surah_data[s]['letters_count'] += w['letter_count']
    surah_data[s]['word_count'] += 1
    surah_data[s]['ayat'].add(w['ayah'])
    surah_data[s]['pages'].add(w['z'])

surah_boundaries = {}
for s in range(1, 115):
    sd = surah_data[s]
    if not sd['words']:
        continue
    first = sd['words'][0]
    last = sd['words'][-1]
    pages = sorted(sd['pages'])
    surah_boundaries[s] = {
        'surah': s,
        'name_en': SURAH_NAMES.get(s, ''),
        'ayat_count': len(sd['ayat']),
        'word_count': sd['word_count'],
        'letter_count': sd['letters_count'],
        'page_start': pages[0],
        'page_end': pages[-1],
        'page_span': len(pages),
        'first_word': {
            'text': first['text'],
            'x': first['x'], 'y': first['y'], 'z': first['z']
        },
        'last_word': {
            'text': last['text'],
            'x': last['x'], 'y': last['y'], 'z': last['z']
        }
    }

library['surah_boundaries'] = surah_boundaries
print(f"  Done: {len(surah_boundaries)} surahs")

# ── 2. Bismillah locations ────────────────────────────────────────────────────

print("Locating bismillahs...")

bismillah_locations = []
seen_surahs = set()
for w in bismillah_words:
    s = w['surah']
    if s not in seen_surahs:
        seen_surahs.add(s)
        bismillah_locations.append({
            'surah': s,
            'name_en': SURAH_NAMES.get(s, ''),
            'page': w['z'],
            'line': w['y'],
            'x_start': w['x_start'] if 'x_start' in w else w['x'],
            'x_center': w['x'],
            'z': w['z'],
            'y': w['y'],
        })

# Also include Fatiha bismillah (it is ayah 1, type=text)
fatiha_bsm = next((w for w in text_words
                   if w['surah'] == 1 and w['ayah'] == 1
                   and 'بسم' in normalize(w['text'])), None)

library['bismillah_locations'] = bismillah_locations
print(f"  Found {len(bismillah_locations)} bismillahs in headers")

# ── 3. Line statistics ────────────────────────────────────────────────────────

print("Computing line statistics...")

line_letter_counts = defaultdict(int)
line_word_counts = defaultdict(int)
line_contents = defaultdict(list)

for w in text_words:
    key = (w['z'], w['y'])
    line_letter_counts[key] += w['letter_count']
    line_word_counts[key] += 1
    line_contents[key].append(w['text'])

max_line_key = max(line_letter_counts, key=line_letter_counts.get)
min_line_key = min(line_letter_counts, key=line_letter_counts.get)

all_counts = list(line_letter_counts.values())
avg_letters = sum(all_counts) / len(all_counts)

line_stats = {
    'total_lines': len(line_letter_counts),
    'max_letters_per_line': {
        'count': line_letter_counts[max_line_key],
        'page': max_line_key[0],
        'line': max_line_key[1],
        'text': ' '.join(line_contents[max_line_key])
    },
    'min_letters_per_line': {
        'count': line_letter_counts[min_line_key],
        'page': min_line_key[0],
        'line': min_line_key[1],
        'text': ' '.join(line_contents[min_line_key])
    },
    'average_letters_per_line': round(avg_letters, 2),
    'distribution': {
        'under_20': sum(1 for c in all_counts if c < 20),
        '20_to_29': sum(1 for c in all_counts if 20 <= c < 30),
        '30_to_35': sum(1 for c in all_counts if 30 <= c <= 35),
        'over_35': sum(1 for c in all_counts if c > 35),
    }
}

library['line_stats'] = line_stats
print(f"  Max line: page {max_line_key[0]}, line {max_line_key[1]}, {line_letter_counts[max_line_key]} letters")
print(f"  Average letters per line: {avg_letters:.1f}")

# ── 4. Page statistics ────────────────────────────────────────────────────────

print("Computing page statistics...")

page_stats = {}
page_words = defaultdict(list)
for w in text_words:
    page_words[w['z']].append(w)

for pg, pw in sorted(page_words.items()):
    first = pw[0]
    last = pw[-1]
    total_letters = sum(w['letter_count'] for w in pw)
    max_line = max(w['y'] for w in pw)
    page_stats[str(pg)] = {
        'page': pg,
        'first_ayah': f"{first['surah']}:{first['ayah']}",
        'last_ayah': f"{last['surah']}:{last['ayah']}",
        'word_count': len(pw),
        'letter_count': total_letters,
        'line_count': max_line,
    }

library['page_stats'] = page_stats
print(f"  Done: {len(page_stats)} pages")

# ── 5. Surah letter rankings ──────────────────────────────────────────────────

print("Computing surah rankings...")

surah_rankings = sorted(
    [{'surah': s, 'name_en': SURAH_NAMES.get(s,''),
      'letter_count': surah_boundaries[s]['letter_count'],
      'word_count': surah_boundaries[s]['word_count'],
      'ayat_count': surah_boundaries[s]['ayat_count'],
      'page_span': surah_boundaries[s]['page_span']}
     for s in surah_boundaries],
    key=lambda x: x['letter_count'],
    reverse=True
)

library['surah_rankings_by_letters'] = surah_rankings
print(f"  Longest surah by letters: {surah_rankings[0]['name_en']} ({surah_rankings[0]['letter_count']} letters)")
print(f"  Shortest surah by letters: {surah_rankings[-1]['name_en']} ({surah_rankings[-1]['letter_count']} letters)")

# ── 6. Word frequency (top 100, excluding bismillah) ─────────────────────────

print("Computing word frequencies...")

freq = defaultdict(int)
freq_locations = defaultdict(list)

for w in text_words:
    norm = normalize(w['text'])
    freq[norm] += 1
    freq_locations[norm].append({
        'surah': w['surah'], 'ayah': w['ayah'],
        'x': w['x'], 'y': w['y'], 'z': w['z']
    })

top_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:100]

word_frequency = []
for norm_text, count in top_words:
    first_loc = freq_locations[norm_text][0]
    word_frequency.append({
        'normalized': norm_text,
        'count': count,
        'first_occurrence': first_loc,
        'sample_locations': freq_locations[norm_text][:5]
    })

library['word_frequency'] = word_frequency
print(f"  Top word: {top_words[0][0]} ({top_words[0][1]} times)")
print(f"  Top 5: {[(w, c) for w, c in top_words[:5]]}")

# ── 7. Allah specifically (excluding bismillah) ───────────────────────────────

print("Finding Allah occurrences (text only, no bismillah)...")

allah_norm = normalize('الله')
allah_occurrences = [
    {'surah': w['surah'], 'ayah': w['ayah'], 'word_idx': w['word_idx'],
     'text': w['text'], 'x': w['x'], 'y': w['y'], 'z': w['z'],
     'x_norm': w['x_norm'], 'y_norm': w['y_norm'], 'z_norm': w['z_norm']}
    for w in text_words
    if allah_norm in normalize(w['text'])
]

library['allah_occurrences'] = {
    'count': len(allah_occurrences),
    'note': 'Excludes bismillah headers. Includes forms like billaahi, lillaahi.',
    'locations': allah_occurrences
}
print(f"  Allah (text only): {len(allah_occurrences)} occurrences")

# ── 8. Juz boundaries ────────────────────────────────────────────────────────

print("Loading juz boundaries from page data...")

with open("quran_pages.json", "r", encoding="utf-8") as f:
    pages_raw = json.load(f)

# Juz boundaries are well known - hardcoded from standard Mushaf
JUZ_STARTS = [
    (1,1),(2,142),(2,253),(3,92),(4,24),(4,147),(5,82),(6,111),(7,87),
    (8,75),(9,121),(11,6),(12,53),(15,1),(17,1),(18,75),(21,1),(23,1),
    (25,21),(27,56),(29,46),(33,31),(36,28),(39,32),(41,47),(46,1),
    (51,31),(58,1),(67,1),(78,1)
]

juz_boundaries = []
for juz_num, (s, a) in enumerate(JUZ_STARTS, 1):
    matching = next((w for w in text_words
                     if w['surah'] == s and w['ayah'] == a
                     and w['word_idx'] == 0), None)
    if matching:
        juz_boundaries.append({
            'juz': juz_num,
            'starts_at': f"{s}:{a}",
            'page': matching['z'],
            'line': matching['y'],
            'x': matching['x'],
            'y': matching['y'],
            'z': matching['z'],
        })

library['juz_boundaries'] = juz_boundaries
print(f"  Found {len(juz_boundaries)} juz boundaries")

# ── 9. Summary ────────────────────────────────────────────────────────────────

library['summary'] = {
    'total_pages': 604,
    'total_words': len(text_words),
    'total_letters': sum(w['letter_count'] for w in text_words),
    'total_ayat': len(set(f"{w['surah']}:{w['ayah']}" for w in text_words)),
    'total_surahs': 114,
    'max_x': data['meta']['max_x'],
    'bounding_box': f"{data['meta']['max_x']} x 15 x 604",
    'allah_count_text_only': len(allah_occurrences),
    'bismillah_count': len(bismillah_locations),
    'longest_surah': surah_rankings[0]['name_en'],
    'shortest_surah': surah_rankings[-1]['name_en'],
    'max_letters_on_one_line': line_stats['max_letters_per_line']['count'],
    'max_letters_line_location': f"page {line_stats['max_letters_per_line']['page']}, line {line_stats['max_letters_per_line']['line']}",
}

# ── Write output ──────────────────────────────────────────────────────────────

print("\nWriting mushaf_library.json...")
with open("mushaf_library.json", "w", encoding="utf-8") as f:
    json.dump(library, f, ensure_ascii=False, indent=2)

import os
size_mb = os.path.getsize("mushaf_library.json") / 1024 / 1024
print(f"Done. mushaf_library.json written ({size_mb:.1f} MB)")
print("\nSummary:")
for k, v in library['summary'].items():
    print(f"  {k}: {v}")