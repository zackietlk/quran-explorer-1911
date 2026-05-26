# Quran Explorer

3D spatial analysis system treating the Quran as a coordinate space.

## Coordinate System
- X: letter position on line (1=right edge, 76=max) — Arabic RTL
- Y: line number on page (1=top, 15=bottom)
- Z: page number (1=604)
- Bounding box: 76 × 15 × 604

## Files
- `quran-3d.html` — self-contained 3D viewer, open in browser
- `fetch_pages.py` — fetches page mapping from quran.com API
- `fetch_word_positions.py` — fetches word-level page+line positions
- `build_mushaf_final.py` — builds mushaf.json (run after fetching)
- `build_library_final.py` — builds mushaf_library.json
- `search_export.py` — search any Arabic word, export to Maya/JSON
- `mushaf_library.json` — pre-computed structural data (embedded in viewer)
- `quran_pages.json` — verified page mapping from quran.com

## Files NOT in repo (too large, regenerate locally)
- `mushaf.json` (118MB) — run build_mushaf_final.py
- `quran_word_positions.json` (13MB) — run fetch_word_positions.py
- `quran-uthmani.xml` — download from tanzil.net

## Run order (first time setup)
1. fetch_pages.py
2. fetch_word_positions.py
3. build_mushaf_final.py
4. build_library_final.py
5. search_export.py (edit settings at top each run)

## Data path
C:\Users\white\Documents\Coding Apps\Quran Explorer
