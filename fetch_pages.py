import urllib.request
import json
import time

print("Starting download of Mushaf page data from quran.com...")
print("This will fetch all 604 pages. It will take a few minutes.")
print("")

page_map = {}
errors = []

for page_num in range(1, 605):
    url = f"https://api.quran.com/api/v4/verses/by_page/{page_num}?per_page=50"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        response = urllib.request.urlopen(req, timeout=15)
        data = json.loads(response.read())
        
        for verse in data.get("verses", []):
            key = verse["verse_key"]
            parts = key.split(":")
            surah = int(parts[0])
            ayah = int(parts[1])
            page_map[f"{surah}:{ayah}"] = page_num
        
        if page_num % 50 == 0:
            print(f"  Done: page {page_num}/604")
        
        time.sleep(0.15)
    
    except Exception as e:
        print(f"  Error on page {page_num}: {e}")
        errors.append(page_num)
        time.sleep(1)

print("")
print(f"Finished. Got data for {len(page_map)} ayat.")

if errors:
    print(f"Failed pages: {errors}")
    print("You can retry those manually if needed.")

output = {
    "description": "Quran page mapping from quran.com API",
    "total_ayat": len(page_map),
    "page_map": page_map
}

with open("quran_pages.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("")
print("Saved to quran_pages.json")
print("Check the folder where this script is saved.")