import urllib.request
import json
import time
import os

os.chdir(r"C:\Users\white\Documents\Coding Apps\Quran Explorer")

print("Fetching word-by-word position data from quran.com...")
print("This includes line_number and page_number for every word.")
print("604 pages to fetch. Will take 5-10 minutes.")
print("")

all_words = []
errors = []

for page_num in range(1, 605):
    url = (
        f"https://api.quran.com/api/v4/verses/by_page/{page_num}"
        f"?words=true"
        f"&word_fields=text_uthmani,line_number,page_number,position"
        f"&per_page=50"
        f"&fields=chapter_id,verse_number"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        response = urllib.request.urlopen(req, timeout=20)
        data = json.loads(response.read())

        for verse in data.get("verses", []):
            surah = verse.get("chapter_id")
            ayah  = verse.get("verse_number")
            for word in verse.get("words", []):
                # Skip non-text tokens (punctuation markers)
                if word.get("char_type_name") in ("end", "pause", "sajdah", "rub-el-hizb"):
                    continue
                all_words.append({
                    "surah":       surah,
                    "ayah":        ayah,
                    "word_idx":    word.get("position", 0),
                    "text":        word.get("text_uthmani", ""),
                    "page":        word.get("page_number", page_num),
                    "line":        word.get("line_number", 0),
                    "char_type":   word.get("char_type_name", "word"),
                })

        if page_num % 50 == 0 or page_num == 1:
            print(f"  Page {page_num}/604 — words collected so far: {len(all_words):,}")

        time.sleep(0.2)

    except Exception as e:
        print(f"  ERROR on page {page_num}: {e}")
        errors.append(page_num)
        time.sleep(2)

print(f"\nDone. Total word records: {len(all_words):,}")

if errors:
    print(f"Failed pages (retry manually): {errors}")

# Quick sanity check
pages_seen  = len(set(w["page"] for w in all_words))
lines_seen  = len(set((w["page"], w["line"]) for w in all_words))
print(f"Unique pages: {pages_seen}")
print(f"Unique page+line combinations: {lines_seen}")
print(f"Average lines per page: {lines_seen/pages_seen:.1f}")

# Show first page sample
print("\nSample — first 10 words:")
for w in all_words[:10]:
    print(f"  page={w['page']} line={w['line']} {w['surah']}:{w['ayah']} pos={w['word_idx']} '{w['text']}'")

# Save
output = {
    "description": "Word-by-word positions from quran.com (page + line + position)",
    "total_words": len(all_words),
    "failed_pages": errors,
    "words": all_words
}

with open("quran_word_positions.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

size_mb = os.path.getsize("quran_word_positions.json") / 1024 / 1024
print(f"\nSaved: quran_word_positions.json ({size_mb:.1f} MB)")
