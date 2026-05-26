import json
import os
from collections import defaultdict

os.chdir(r"C:\Users\white\Documents\Coding Apps\Quran Explorer")

print("Loading mushaf.json...")
with open("mushaf.json", "r", encoding="utf-8") as f:
    data = json.load(f)

words        = data['words']
text_words   = [w for w in words if w['type'] == 'text']
bsm_words    = [w for w in words if w['type'] == 'bismillah']
MAX_X        = data['meta']['max_x']

# ── Normalization ─────────────────────────────────────────────────────────────

DIACRITICS = set(range(0x064B, 0x0660))
DIACRITICS.add(0x0640); DIACRITICS.add(0x0670)
DIACRITICS.update(range(0x06D6, 0x06EF))
ALEF = {'\u0627','\u0623','\u0625','\u0622','\u0671'}

def normalize(text):
    result = []
    for c in text:
        if ord(c) in DIACRITICS: continue
        result.append('\u0627' if c in ALEF else c)
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

print("1. Surah boundaries...")

surah_data = defaultdict(lambda: {
    'words': [], 'letter_count': 0, 'word_count': 0,
    'ayat': set(), 'pages': set(), 'lines': set()
})

for w in text_words:
    s = w['surah']
    surah_data[s]['words'].append(w)
    surah_data[s]['letter_count'] += w['letter_count']
    surah_data[s]['word_count']   += 1
    surah_data[s]['ayat'].add(w['ayah'])
    surah_data[s]['pages'].add(w['z'])
    surah_data[s]['lines'].add((w['z'], w['y']))

surah_boundaries = {}
for s in range(1, 115):
    sd = surah_data[s]
    if not sd['words']:
        continue
    first = sd['words'][0]
    last  = sd['words'][-1]
    pages = sorted(sd['pages'])
    surah_boundaries[str(s)] = {
        'surah':        s,
        'name_en':      SURAH_NAMES.get(s, ''),
        'ayat_count':   len(sd['ayat']),
        'word_count':   sd['word_count'],
        'letter_count': sd['letter_count'],
        'page_start':   pages[0],
        'page_end':     pages[-1],
        'page_span':    len(pages),
        'line_count':   len(sd['lines']),
        'first_word': {
            'text': first['text'],
            'x': first['x'], 'y': first['y'], 'z': first['z'],
            'x_norm': first['x_norm'], 'y_norm': first['y_norm'],
            'z_norm': first['z_norm'],
        },
        'last_word': {
            'text': last['text'],
            'x': last['x'], 'y': last['y'], 'z': last['z'],
            'x_norm': last['x_norm'], 'y_norm': last['y_norm'],
            'z_norm': last['z_norm'],
        },
    }

library['surah_boundaries'] = surah_boundaries
print(f"   {len(surah_boundaries)} surahs mapped")

# ── 2. Bismillah locations ────────────────────────────────────────────────────

print("2. Bismillah locations...")

# 112 header bismillahs (surah 2-114 except 9, stored as type=bismillah)
# Plus surah 1 ayah 1 which is the bismillah as revealed text
bismillah_locations = []

# Surah 1: its bismillah is ayah 1 itself
s1_a1_first = next(
    (w for w in text_words if w['surah'] == 1 and w['ayah'] == 1 and w['word_idx'] == 1),
    None
)
if s1_a1_first:
    bismillah_locations.append({
        'surah':    1,
        'name_en':  'Al-Fatiha',
        'type':     'revealed_ayah',
        'note':     'Bismillah is ayah 1 of Al-Fatiha',
        'page':     s1_a1_first['z'],
        'line':     s1_a1_first['y'],
        'x':        s1_a1_first['x'],
        'y':        s1_a1_first['y'],
        'z':        s1_a1_first['z'],
        'x_norm':   s1_a1_first['x_norm'],
        'y_norm':   s1_a1_first['y_norm'],
        'z_norm':   s1_a1_first['z_norm'],
    })

# Header bismillahs (surah 2-114 except 9)
seen_surahs = set()
for w in bsm_words:
    s = w['surah']
    if s not in seen_surahs:
        seen_surahs.add(s)
        bismillah_locations.append({
            'surah':    s,
            'name_en':  SURAH_NAMES.get(s, ''),
            'type':     'header',
            'note':     'Bismillah header preceding surah',
            'page':     w['z'],
            'line':     w['y'],
            'x':        w['x'],
            'y':        w['y'],
            'z':        w['z'],
            'x_norm':   w['x_norm'],
            'y_norm':   w['y_norm'],
            'z_norm':   w['z_norm'],
        })

bismillah_locations.sort(key=lambda b: b['surah'])
library['bismillah_locations'] = bismillah_locations
print(f"   {len(bismillah_locations)} bismillahs (1 revealed + {len(bismillah_locations)-1} headers)")

# ── 3. Sajdah locations ───────────────────────────────────────────────────────

print("3. Sajdah (prostration) locations...")

# 15 places of prostration — known ayat
SAJDAH_AYAT = [
    (7,206),(13,15),(16,50),(17,109),(19,58),(22,18),
    (22,77),(25,60),(27,26),(32,15),(38,24),(41,38),
    (53,62),(84,21),(96,19)
]

sajdah_locations = []
for s, a in SAJDAH_AYAT:
    # Find the last word of this ayah (where the sajdah marker was)
    ayah_words = [w for w in text_words if w['surah'] == s and w['ayah'] == a]
    if ayah_words:
        last_w = ayah_words[-1]
        sajdah_locations.append({
            'surah':   s,
            'ayah':    a,
            'name_en': SURAH_NAMES.get(s, ''),
            'ref':     f"{s}:{a}",
            'page':    last_w['z'],
            'line':    last_w['y'],
            'x':       last_w['x'],
            'y':       last_w['y'],
            'z':       last_w['z'],
            'x_norm':  last_w['x_norm'],
            'y_norm':  last_w['y_norm'],
            'z_norm':  last_w['z_norm'],
        })

library['sajdah_locations'] = sajdah_locations
print(f"   {len(sajdah_locations)} sajdah locations")

# ── 4. Juz boundaries ────────────────────────────────────────────────────────

print("4. Juz boundaries...")

JUZ_STARTS = [
    (1,1),(2,142),(2,253),(3,92),(4,24),(4,147),(5,82),(6,111),(7,87),
    (8,75),(9,121),(11,6),(12,53),(15,1),(17,1),(18,75),(21,1),(23,1),
    (25,21),(27,56),(29,46),(33,31),(36,28),(39,32),(41,47),(46,1),
    (51,31),(58,1),(67,1),(78,1)
]

juz_boundaries = []
for juz_num, (s, a) in enumerate(JUZ_STARTS, 1):
    first_w = next(
        (w for w in text_words if w['surah'] == s and w['ayah'] == a and w['word_idx'] == 1),
        None
    )
    if first_w:
        juz_boundaries.append({
            'juz':      juz_num,
            'starts_at': f"{s}:{a}",
            'surah':    s,
            'ayah':     a,
            'name_en':  SURAH_NAMES.get(s, ''),
            'page':     first_w['z'],
            'line':     first_w['y'],
            'x':        first_w['x'],
            'y':        first_w['y'],
            'z':        first_w['z'],
            'x_norm':   first_w['x_norm'],
            'y_norm':   first_w['y_norm'],
            'z_norm':   first_w['z_norm'],
        })

library['juz_boundaries'] = juz_boundaries
print(f"   {len(juz_boundaries)} juz boundaries")

# ── 5. Hizb boundaries ───────────────────────────────────────────────────────

print("5. Hizb boundaries (60 total = 30 juz x 2)...")

# Each juz has 2 hizb. Hizb starts are well documented.
HIZB_STARTS = [
    (1,1),(2,75),(2,142),(2,203),(2,253),(3,14),(3,92),(3,156),
    (4,1),(4,24),(4,92),(4,147),(5,1),(5,52),(5,82),(6,1),
    (6,111),(7,1),(7,87),(7,171),(8,1),(8,40),(8,75),(9,33),
    (9,94),(9,121),(10,1),(10,71),(11,6),(11,84),(12,1),(12,53),
    (13,1),(13,35),(14,1),(15,1),(16,1),(16,75),(17,1),(17,49),
    (18,1),(18,75),(19,1),(20,1),(21,1),(21,51),(22,1),(22,56),
    (23,1),(23,75),(24,1),(25,1),(25,21),(26,1),(26,111),(27,1),
    (27,26),(27,56),(28,22),(28,51),(29,1),(29,46),(30,1),(31,1),
    (32,1),(33,1),(33,31),(34,1),(35,1),(36,1),(36,28),(37,1),
    (38,1),(38,63),(39,1),(39,32),(40,1),(40,41),(41,1),(41,47),
    (42,1),(43,1),(43,45),(44,1),(45,1),(46,1),(47,1),(48,1),
    (49,1),(50,1),(51,31),(52,1),(53,1),(54,1),(55,1),(56,1),
    (57,1),(58,1),(59,1),(60,1),(61,1),(62,1),(63,1),(64,1),
    (65,1),(66,1),(67,1),(68,1),(69,1),(70,1),(71,1),(72,1),
    (73,1),(74,1),(75,1),(76,1),(77,1),(78,1),(79,1),(80,1),
    (81,1),(82,1),(83,1),(84,1),(85,1),(86,1),(87,1),(88,1),
    (89,1),(90,1),(91,1),(92,1),(93,1),(94,1),(95,1),(96,1),
    (97,1),(98,1),(99,1),(100,1),(101,1),(102,1),(103,1),(104,1),
    (105,1),(106,1),(107,1),(108,1),(109,1),(110,1),(111,1),(112,1),
    (113,1),(114,1)
]

# Use only the first 60 standard hizb starts
HIZB_STARTS_60 = [
    (1,1),(2,75),(2,142),(2,203),(2,253),(3,14),(3,92),(3,156),
    (4,1),(4,24),(4,92),(4,147),(5,1),(5,52),(5,82),(6,1),
    (6,111),(7,1),(7,87),(7,171),(8,1),(8,40),(8,75),(9,33),
    (9,94),(9,121),(10,1),(10,71),(11,6),(11,84),(12,1),(12,53),
    (13,1),(13,35),(14,1),(15,1),(16,1),(16,75),(17,1),(17,49),
    (18,1),(18,75),(19,1),(20,1),(21,1),(21,51),(22,1),(22,56),
    (23,1),(23,75),(24,1),(25,1),(25,21),(26,1),(26,111),(27,1),
    (27,26),(27,56),(28,22),(28,51)
]

hizb_boundaries = []
for hizb_num, (s, a) in enumerate(HIZB_STARTS_60, 1):
    first_w = next(
        (w for w in text_words if w['surah'] == s and w['ayah'] == a and w['word_idx'] == 1),
        None
    )
    if first_w:
        hizb_boundaries.append({
            'hizb':     hizb_num,
            'starts_at': f"{s}:{a}",
            'surah':    s,
            'ayah':     a,
            'page':     first_w['z'],
            'line':     first_w['y'],
            'x':        first_w['x'],
            'y':        first_w['y'],
            'z':        first_w['z'],
        })

library['hizb_boundaries'] = hizb_boundaries
print(f"   {len(hizb_boundaries)} hizb boundaries mapped")

# ── 6. Line statistics ────────────────────────────────────────────────────────

print("6. Line statistics...")

line_groups = defaultdict(list)
for w in text_words:
    if w['y'] > 0 and w['z'] > 0:
        line_groups[(w['z'], w['y'])].append(w)

line_letter_counts = {k: sum(w['letter_count'] for w in v)
                      for k, v in line_groups.items()}
line_word_counts   = {k: len(v) for k, v in line_groups.items()}

all_lc   = sorted(line_letter_counts.values())
max_key  = max(line_letter_counts, key=line_letter_counts.get)
min_key  = min(line_letter_counts, key=line_letter_counts.get)

from collections import Counter
lc_dist = Counter(all_lc)

line_stats = {
    'total_lines':           len(line_groups),
    'max_letters_per_line':  {
        'count':   line_letter_counts[max_key],
        'page':    max_key[0],
        'line':    max_key[1],
        'surah_ayah': f"{line_groups[max_key][0]['surah']}:{line_groups[max_key][0]['ayah']}",
        'text':    ' '.join(w['text'] for w in line_groups[max_key]),
    },
    'min_letters_per_line':  {
        'count':   line_letter_counts[min_key],
        'page':    min_key[0],
        'line':    min_key[1],
        'text':    ' '.join(w['text'] for w in line_groups[min_key]),
    },
    'average_letters_per_line': round(sum(all_lc) / len(all_lc), 2),
    'median_letters_per_line':  all_lc[len(all_lc) // 2],
    'max_words_per_line': max(line_word_counts.values()),
    'distribution': {
        'under_20':  sum(1 for c in all_lc if c < 20),
        '20_to_29':  sum(1 for c in all_lc if 20 <= c < 30),
        '30_to_39':  sum(1 for c in all_lc if 30 <= c < 40),
        '40_to_49':  sum(1 for c in all_lc if 40 <= c < 50),
        '50_to_59':  sum(1 for c in all_lc if 50 <= c < 60),
        '60_plus':   sum(1 for c in all_lc if c >= 60),
    }
}

library['line_stats'] = line_stats
print(f"   Total lines: {line_stats['total_lines']:,}")
print(f"   MAX_X={MAX_X} at page {max_key[0]} line {max_key[1]}: {line_letter_counts[max_key]} letters")
print(f"   Average: {line_stats['average_letters_per_line']} letters/line")

# ── 7. Page statistics ────────────────────────────────────────────────────────

print("7. Page statistics...")

page_word_map = defaultdict(list)
for w in text_words:
    page_word_map[w['z']].append(w)

page_stats = {}
for pg, pw in sorted(page_word_map.items()):
    first, last = pw[0], pw[-1]
    total_letters = sum(w['letter_count'] for w in pw)
    max_line = max(w['y'] for w in pw if w['y'] > 0)
    surahs_on_page = sorted(set(w['surah'] for w in pw))
    page_stats[str(pg)] = {
        'page':          pg,
        'first_ayah':    f"{first['surah']}:{first['ayah']}",
        'last_ayah':     f"{last['surah']}:{last['ayah']}",
        'word_count':    len(pw),
        'letter_count':  total_letters,
        'line_count':    max_line,
        'surahs':        surahs_on_page,
    }

library['page_stats'] = page_stats
print(f"   {len(page_stats)} pages")

# ── 8. Surah rankings ─────────────────────────────────────────────────────────

print("8. Surah rankings...")

surah_rankings = sorted(
    [{'surah': int(s), 'name_en': v['name_en'],
      'letter_count': v['letter_count'],
      'word_count':   v['word_count'],
      'ayat_count':   v['ayat_count'],
      'page_span':    v['page_span']}
     for s, v in surah_boundaries.items()],
    key=lambda x: x['letter_count'],
    reverse=True
)
library['surah_rankings_by_letters'] = surah_rankings
print(f"   Longest:  {surah_rankings[0]['name_en']} ({surah_rankings[0]['letter_count']:,} letters)")
print(f"   Shortest: {surah_rankings[-1]['name_en']} ({surah_rankings[-1]['letter_count']} letters)")

# ── 9. Word frequency (text only, no bismillah, cleaned) ─────────────────────

print("9. Word frequency...")

freq         = defaultdict(int)
freq_by_surah = defaultdict(lambda: defaultdict(int))

for w in text_words:
    norm = normalize(w['text'])
    if norm:  # skip empty strings
        freq[norm] += 1
        freq_by_surah[norm][w['surah']] += 1

# Remove empty string if present
freq.pop('', None)

top_words = sorted(freq.items(), key=lambda x: -x[1])[:100]

word_frequency = []
for norm_text, count in top_words:
    surah_dist = dict(sorted(freq_by_surah[norm_text].items()))
    word_frequency.append({
        'normalized':    norm_text,
        'count':         count,
        'surah_distribution': surah_dist,
    })

library['word_frequency'] = word_frequency
print(f"   Top word: '{top_words[0][0]}' ({top_words[0][1]:,} times)")
print(f"   Top 5: {[(w, c) for w, c in top_words[:5]]}")

# ── 10. Allah occurrences (full detail) ───────────────────────────────────────

print("10. Allah occurrences...")

allah_norm = normalize('الله')
allah_occurrences = []
for w in text_words:
    if allah_norm in normalize(w['text']):
        allah_occurrences.append({
            'surah':    w['surah'],
            'ayah':     w['ayah'],
            'word_idx': w['word_idx'],
            'text':     w['text'],
            'page':     w['z'],
            'line':     w['y'],
            'x':        w['x'],
            'y':        w['y'],
            'z':        w['z'],
            'x_norm':   w['x_norm'],
            'y_norm':   w['y_norm'],
            'z_norm':   w['z_norm'],
        })

# Distribution by surah
allah_by_surah = defaultdict(int)
for r in allah_occurrences:
    allah_by_surah[r['surah']] += 1

library['allah_occurrences'] = {
    'count':              len(allah_occurrences),
    'note':               'Text words only. Excludes bismillah headers. Includes billaahi, lillaahi, etc.',
    'by_surah':           dict(sorted(allah_by_surah.items())),
    'top_5_surahs':       sorted(allah_by_surah.items(), key=lambda x: -x[1])[:5],
    'locations':          allah_occurrences,
}
print(f"   Allah occurrences: {len(allah_occurrences):,}")
top5s = sorted(allah_by_surah.items(), key=lambda x: -x[1])[:3]
print(f"   Top 3 surahs: {[(SURAH_NAMES.get(s,''), c) for s,c in top5s]}")

# ── 11. Key word locations (starter library) ──────────────────────────────────

print("11. Key word searches...")

KEY_WORDS = {
    'الرحمن':  'Ar-Rahman (The Most Gracious)',
    'الرحيم':  'Ar-Raheem (The Most Merciful)',
    'الناس':   'An-Nas (Mankind)',
    'العالمين': 'Al-Alameen (The Worlds)',
    'الحمد':   'Al-Hamd (Praise)',
    'رب':      'Rabb (Lord)',
    'قل':      'Qul (Say)',
    'يوم':     'Yawm (Day)',
    'الجنة':   'Al-Jannah (Paradise)',
    'النار':   'An-Nar (Fire/Hell)',
    'الارض':   'Al-Ard (The Earth)',
    'السماء':  'As-Sama (The Sky/Heaven)',
    'النور':   'An-Nur (The Light)',
    'الحق':    'Al-Haqq (The Truth)',
    'العلم':   'Al-Ilm (Knowledge)',
}

key_word_data = {}
for arabic, label in KEY_WORDS.items():
    norm = normalize(arabic)
    matches = [
        {'surah': w['surah'], 'ayah': w['ayah'],
         'page': w['z'], 'line': w['y'],
         'x': w['x'], 'y': w['y'], 'z': w['z'],
         'x_norm': w['x_norm'], 'y_norm': w['y_norm'], 'z_norm': w['z_norm'],
         'text': w['text']}
        for w in text_words if norm in normalize(w['text'])
    ]
    by_surah = defaultdict(int)
    for m in matches:
        by_surah[m['surah']] += 1
    key_word_data[arabic] = {
        'label':   label,
        'count':   len(matches),
        'by_surah': dict(sorted(by_surah.items())),
        'locations': matches,
    }
    print(f"   '{arabic}' ({label}): {len(matches):,}")

library['key_words'] = key_word_data

# ── 12. Summary ───────────────────────────────────────────────────────────────

total_letters_text = sum(w['letter_count'] for w in text_words)

library['summary'] = {
    'version':                  'final',
    'source':                   'quran.com verified positions + Tanzil Uthmani text',
    'total_pages':              604,
    'total_words_text':         len(text_words),
    'total_words_incl_bismillah': len(words),
    'total_letters':            total_letters_text,
    'total_ayat':               len(set(f"{w['surah']}:{w['ayah']}" for w in text_words)),
    'total_surahs':             114,
    'max_x':                    MAX_X,
    'bounding_box':             f"{MAX_X} x 15 x 604",
    'allah_count_text_only':    len(allah_occurrences),
    'bismillah_count':          len(bismillah_locations),
    'sajdah_count':             len(sajdah_locations),
    'juz_boundaries_mapped':    len(juz_boundaries),
    'hizb_boundaries_mapped':   len(hizb_boundaries),
    'longest_surah':            surah_rankings[0]['name_en'],
    'shortest_surah':           surah_rankings[-1]['name_en'],
    'max_letters_one_line':     line_stats['max_letters_per_line']['count'],
    'max_letters_line_at':      f"page {line_stats['max_letters_per_line']['page']}, line {line_stats['max_letters_per_line']['line']}",
    'avg_letters_per_line':     line_stats['average_letters_per_line'],
    'top_word':                 top_words[0][0],
    'top_word_count':           top_words[0][1],
}

# ── Write output ──────────────────────────────────────────────────────────────

print("\nWriting mushaf_library.json...")
with open("mushaf_library.json", "w", encoding="utf-8") as f:
    json.dump(library, f, ensure_ascii=False, indent=2)

size_mb = os.path.getsize("mushaf_library.json") / 1024 / 1024
print(f"Done. mushaf_library.json ({size_mb:.1f} MB)")
print("\nSummary:")
for k, v in library['summary'].items():
    print(f"  {k}: {v}")
