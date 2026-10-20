# Suppressor Bench

A single static page (`index.html`) for comparing suppressors from the 2025 and 2026 TBAC Silencer Summits by sound, weight, length past the muzzle and price.

- **Sound**: mil-spec average dB(A) of the left and right muzzle mics; scores are only compared within the same host and bore.
- **Length past muzzle**: Summit overall length, or the added length for over-the-barrel cans.
- **Price**: `data/price_list.csv` first, then the whichcan.com catalog MSRP.
- **Saving**: stars, weights and your own prices/lengths live in the browser (localStorage). "Copy share link" makes a `?saved=` link; "Copy backup" moves everything to another device.

## Publish with GitHub Pages

Settings → Pages → Build and deployment → Deploy from a branch → `main` / `(root)`.

## Update the data

Edit the files in `data/` (for example a new price in `price_list.csv`), then run:

```
python3 tools/build.py
```

That rebuilds `data/data.json` and re-embeds it in `index.html`. Over-the-barrel added lengths are set in the `OTB` table in `tools/build.py`.
