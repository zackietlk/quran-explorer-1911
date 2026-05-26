import json
import os

os.chdir(r"C:\Users\white\Documents\Coding Apps\Quran Explorer")

# ══════════════════════════════════════════════════════════════════
#  SETTINGS — edit these before each run
# ══════════════════════════════════════════════════════════════════

SEARCH_WORD       = "الله"      # Arabic word to search for
INCLUDE_BISMILLAH = False        # True = include bismillah headers
SEARCH_LEVEL      = "word"       # "word" or "letter"

# Scale mode for Maya coordinates
# "raw"      -> x up to 76, y up to 15, z up to 604
# "tens"     -> multiply all by 10
# "compress" -> x*10, y*10, z*1  (wide flat volume)
# "unit"     -> normalized 0.0 to 1.0
SCALE_MODE        = "tens"

# Output filename (no extension). Files go to Search Results folder.
OUTPUT_NAME       = "allah"

# ══════════════════════════════════════════════════════════════════

RESULTS_DIR = os.path.join(os.getcwd(), "Search Results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────

print(f"Loading mushaf.json...")
with open("mushaf.json", "r", encoding="utf-8") as f:
    data = json.load(f)

all_words   = data['words']
all_letters = data['letters']
MAX_X       = data['meta']['max_x']

# ── Normalization ─────────────────────────────────────────────────

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

# ── Filter pool ───────────────────────────────────────────────────

if INCLUDE_BISMILLAH:
    word_pool = all_words
    print("Including bismillah headers.")
else:
    word_pool = [w for w in all_words if w['type'] == 'text']
    print("Excluding bismillah headers.")

# ── Scale ─────────────────────────────────────────────────────────

def scale(x, y, z):
    if SCALE_MODE == "raw":
        return x, y, z
    elif SCALE_MODE == "tens":
        return round(x*10, 1), round(y*10, 1), round(z*10, 1)
    elif SCALE_MODE == "compress":
        return round(x*10, 1), round(y*10, 1), round(z*1, 1)
    elif SCALE_MODE == "unit":
        return (round(x/MAX_X, 4),
                round((y-1)/14, 4),
                round((z-1)/603, 4))
    return x, y, z

# ── Search ────────────────────────────────────────────────────────

query_norm = normalize(SEARCH_WORD)
print(f"\nSearch:  {SEARCH_WORD}")
print(f"Level:   {SEARCH_LEVEL}")
print(f"Scale:   {SCALE_MODE}")
print(f"Bismillah: {INCLUDE_BISMILLAH}")

results = []

if SEARCH_LEVEL == "word":
    for w in word_pool:
        if query_norm in normalize(w['text']):
            mx, my, mz = scale(w['x'], w['y'], w['z'])
            results.append({
                'text':     w['text'],
                'surah':    w['surah'],
                'ayah':     w['ayah'],
                'word_idx': w['word_idx'],
                'type':     w['type'],
                'page':     w['z'],
                'line':     w['y'],
                'x_raw':    w['x'],
                'y_raw':    w['y'],
                'z_raw':    w['z'],
                'x':        mx,
                'y':        my,
                'z':        mz,
                'x_norm':   w['x_norm'],
                'y_norm':   w['y_norm'],
                'z_norm':   w['z_norm'],
            })

elif SEARCH_LEVEL == "letter":
    query_letters = set(normalize(SEARCH_WORD))
    query_letters.discard('')
    for l in all_letters:
        # Respect bismillah filter at letter level
        if not INCLUDE_BISMILLAH:
            # Check parent word type via surah/ayah — ayah=0 means bismillah
            if l['ayah'] == 0:
                continue
        char_norm = normalize(l['char'])
        if char_norm in query_letters:
            mx, my, mz = scale(l['x'], l['y'], l['z'])
            results.append({
                'char':       l['char'],
                'surah':      l['surah'],
                'ayah':       l['ayah'],
                'word_idx':   l['word_idx'],
                'letter_idx': l['letter_idx'],
                'page':       l['z'],
                'line':       l['y'],
                'x_raw':      l['x'],
                'y_raw':      l['y'],
                'z_raw':      l['z'],
                'x':          mx,
                'y':          my,
                'z':          mz,
            })

print(f"\nFound: {len(results):,} matches")

if not results:
    print("No results. Check spelling or try a different search term.")
    exit()

# ── Export JSON ───────────────────────────────────────────────────

json_path = os.path.join(RESULTS_DIR, OUTPUT_NAME + ".json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({
        'query':            SEARCH_WORD,
        'query_normalized': query_norm,
        'level':            SEARCH_LEVEL,
        'scale_mode':       SCALE_MODE,
        'include_bismillah':INCLUDE_BISMILLAH,
        'count':            len(results),
        'results':          results,
    }, f, ensure_ascii=False, indent=2)
print(f"JSON:  {json_path}")

# ── Export plain coordinates (.txt) ──────────────────────────────

txt_path = os.path.join(RESULTS_DIR, OUTPUT_NAME + ".txt")
with open(txt_path, "w", encoding="utf-8") as f:
    f.write(f"# Search: {SEARCH_WORD}\n")
    f.write(f"# Level: {SEARCH_LEVEL} | Scale: {SCALE_MODE} | Bismillah: {INCLUDE_BISMILLAH}\n")
    f.write(f"# Count: {len(results)}\n")
    f.write("# name, x, y, z, surah, ayah, page, line\n")
    for r in results:
        label = f"S{r['surah']}_A{r['ayah']}_W{r.get('word_idx', r.get('letter_idx', 0))}"
        f.write(f"{label},{r['x']},{r['y']},{r['z']},{r['surah']},{r['ayah']},{r['page']},{r['line']}\n")
print(f"TXT:   {txt_path}")

# ── Export Maya MEL script ────────────────────────────────────────
# Maya coordinate mapping:
#   Mushaf X (RTL, right=1) -> Maya -X  (negate so right=negative in Maya)
#   Mushaf Y (top=1)        -> Maya -Y  (negate so top is higher in Maya)
#   Mushaf Z (page 1=front) -> Maya  Z  (depth into scene)

mel_path = os.path.join(RESULTS_DIR, OUTPUT_NAME + ".mel")
with open(mel_path, "w", encoding="utf-8") as f:
    f.write(f'// Mushaf 3D — Search: {SEARCH_WORD}\n')
    f.write(f'// Count: {len(results)} | Scale: {SCALE_MODE} | Bismillah: {INCLUDE_BISMILLAH}\n')
    f.write(f'// Bounding box: {MAX_X} x 15 x 604 (raw)\n\n')
    f.write(f'// Create a group for all results\n')
    f.write(f'group -empty -name "{OUTPUT_NAME}_group";\n\n')
    for r in results:
        label = f"S{r['surah']}_A{r['ayah']}_W{r.get('word_idx', r.get('letter_idx', 0))}"
        text  = r.get('text') or r.get('char', '')
        # Negate x and y for Maya coordinate convention
        mx = -r['x']
        my = -r['y']
        mz =  r['z']
        f.write(f'// {text} | {r["surah"]}:{r["ayah"]} | page {r["page"]} line {r["line"]}\n')
        f.write(f'spaceLocator -p {mx} {my} {mz} -n "{label}";\n')
        f.write(f'parent "{label}" "{OUTPUT_NAME}_group";\n')
print(f"MEL:   {mel_path}")

# ── Summary ───────────────────────────────────────────────────────

print(f"\nAll 3 files saved to: Search Results/")
print(f"\nSample (first 5):")
for r in results[:5]:
    text = r.get('text') or r.get('char', '')
    print(f"  {text:20s} | {r['surah']:3d}:{r['ayah']:<4d} | "
          f"page {r['page']:3d} line {r['line']:2d} | "
          f"Maya ({-r['x']:.0f}, {-r['y']:.0f}, {r['z']:.0f})")

print(f"\nIn Maya: File -> Import -> select the .mel file")
print(f"All {len(results):,} locators will appear grouped under '{OUTPUT_NAME}_group'")
