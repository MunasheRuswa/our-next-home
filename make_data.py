"""Build listings.json for the public site from an export of the private board.

Usage: python3 make_data.py <folder of listing JSON files> listings.json
       python3 make_data.py --overlay listings.json   (re-apply extras.json only)

extras.json (next to this script) is applied last: its "patch" updates homes by
id (shortlist picks, reduced flags, re-check dates, extra questions) and its
"homes" adds adverts the board doesn't hold yet.

Keeps active homes that have an advert link and don't exclude children.
Bains homes are flagged so the site can show them first; everything else
is sorted cheapest first. Drawing hints come only from what the advert says.
"""
import glob
import hashlib
import json
import os
import re
import sys

src, out = sys.argv[1], sys.argv[2]
EXTRAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extras.json")


def overlay(data):
    if not os.path.exists(EXTRAS):
        return data
    ex = json.load(open(EXTRAS, encoding="utf-8"))
    ids = {h["id"] for h in data["homes"]}
    data["homes"] += [h for h in ex.get("homes", []) if h["id"] not in ids]
    for h in data["homes"]:
        patch = dict(ex.get("patch", {}).get(h["id"], {}))
        for q in patch.pop("add_unknowns", []):
            if q not in h["unknowns"]:
                h["unknowns"].append(q)
        h.update(patch)
    data["homes"].sort(key=lambda h: (h["rent"], h["title"]))
    data["checked"] = ex.get("checked", data["checked"])
    return data


if src == "--overlay":
    d = overlay(json.load(open(out, encoding="utf-8")))
    json.dump(d, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(len(d["homes"]), "homes after extras")
    sys.exit()


def has(text, *words):
    return any(w in text for w in words)


homes = []
for path in glob.glob(os.path.join(src, "*.json")):
    d = json.load(open(path))
    d = d.get("data", d)
    if d.get("status") != "active" or d.get("children") is False:
        continue
    if not d.get("rent") or not d.get("url"):
        continue

    facts = [f.get("t", "") for f in d.get("facts", [])]
    agent = next((t.split(":", 1)[1].strip() for t in facts if t.startswith("Agent:")), None)
    shown_facts = [re.sub(r"^Pets:\s*", "", t) for t in facts if not t.startswith("Agent:")]
    security = [re.sub(r",?\s*in the advert'?s words", "", s, flags=re.I).strip() for s in (d.get("security") or [])]
    unknowns = [u for u in (d.get("unknowns") or []) if "old site" not in u.lower() and "existing bains lodge tenant" not in u.lower()]

    typ = (d.get("type") or "").strip()
    title = d.get("title") or ""
    outdoor = d.get("outdoor") or ""
    parking = d.get("parking") or ""
    blob = " ".join([title, typ, outdoor, parking, " ".join(facts), " ".join(security)]).lower()

    if typ.lower() in ("apartment", "flat"):
        form = "apartment"
    elif has(blob, "duet", "simplex"):
        form = "duet"
    elif typ.lower() in ("house", "cottage") or has(blob, "single-storey", "single storey"):
        form = "house"
    else:
        form = "townhouse"

    suburb = d.get("suburb") or ""
    bains = "lodge" if suburb == "Bains Lodge" else ("area" if suburb in ("Bainsvlei", "Arcadia SH") else None)

    homes.append({
        "id": os.path.basename(path)[:-5],
        "title": title,
        "suburb": suburb,
        "type": typ,
        "rent": d["rent"],
        "deposit": d.get("deposit"),
        "beds": d.get("beds"),
        "baths": d.get("baths"),
        "size": d.get("size"),
        "parking": parking or None,
        "outdoor": outdoor or None,
        "security": security,
        "available": d.get("available"),
        "utilities": d.get("utilities"),
        "agency": d.get("agency"),
        "agent": agent,
        "ref": d.get("ref"),
        "source": d.get("source"),
        "url": d["url"],
        "checked": d.get("lastChecked"),
        "areaNote": d.get("areaNote") if bains else None,
        "facts": shown_facts[:8],
        "unknowns": unknowns,
        "bains": bains,
        "draw": {
            "form": form,
            "garden": has(blob, "garden", "courtyard", "lawn") and "no garden" not in blob,
            "balcony": has(blob, "balcony"),
            "garage": has(blob, "garage"),
            "carport": has(blob, "carport", "covered", "shade"),
            "wall": bool(security) or has(blob, "walled", "perimeter wall"),
            "pool": has(blob, "pool"),
            "wendy": has(blob, "wendy"),
            "palette": int(hashlib.md5(os.path.basename(path).encode()).hexdigest(), 16) % 5,
        },
    })

homes.sort(key=lambda h: (h["rent"], h["title"]))
homes = overlay({"checked": "31 October and 1 November 2026", "homes": homes})["homes"]
checked = json.load(open(EXTRAS, encoding="utf-8")).get("checked") if os.path.exists(EXTRAS) else "31 October and 1 November 2026"
json.dump({"checked": checked, "homes": homes}, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

dec = [h for h in homes if h["available"] and "2026-11-24" <= h["available"] <= "2026-12-08"]
print(len(homes), "homes;", len(dec), "advertised for 1 December;", sum(1 for h in homes if h["bains"]), "at Bains")
for h in homes:
    if h["bains"]:
        print("  Bains:", h["rent"], h["title"], h["draw"])
