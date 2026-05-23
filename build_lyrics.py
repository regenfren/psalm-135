#!/usr/bin/env python3
"""Build data/chant.json from the Psalm 135 lyrics with evenly-spaced
placeholder timings. Real timings come from studio.html (tapping)."""
import json

# (Cyrillic line, English line) — faithful 1:1 of Daničić's Serbian wording.
PAIRS = [
    ("Славите Господа, јер је добар; Алилуија", "Praise the Lord, for he is good; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Славите Бога над боговима; Алилуија", "Praise the God above gods; Alleluia"),
    ("јер је довијека милост његова. Алилуија", "for his mercy endures forever; Alleluia"),
    ("Славите господа над господарима; Алилуија", "Praise the Lord above lords; Alleluia"),
    ("јер је довијека милост Његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Онога који Једини твори чудеса велика; Алилуија", "Him who alone works great wonders; Alleluia"),
    ("Јер је довијека милост Његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Који је створио небеса премудро; Алилуија", "Who created the heavens in wisdom; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Утврдио земљу на води; Алилуија", "Who set the earth firm upon the waters; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Створио велика видјела; Алилуија", "Who made the great lights; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Сунце, да управља даном; Алилуија", "The sun, to rule the day; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Мјесец и звијезде, да управљају ноћу; Алилуија", "The moon and stars, to rule the night; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Који поби Мисир у првенцима његовијем; Алилуија", "Who smote Egypt in its firstborn; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Изведе из њега Израиља; Алилуија", "Brought Israel out from among it; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Руком крјепком и мишицом подигнутом; Алилуија", "With a mighty hand and an outstretched arm; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Који раздвоји Црвено Море; Алилуија", "Who divided the Red Sea asunder; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("И проведе Израиља кроз сред њега; Алилуија", "And led Israel through the midst of it; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("А Фараона и војску његову врже у Море Црвено; Алилуија", "But cast Pharaoh and his army into the Red Sea; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Преведе народ свој преко пустиње; Алилуија", "Who led his people across the wilderness; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Поби цареве велике; Алилуија", "Who smote great kings; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("И изгуби цареве знатне; Алилуија", "And destroyed mighty kings; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Сиона цара Аморејскога; Алилуија", "Sihon, king of the Amorites; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("И Ога цара Васанскога; Алилуија", "And Og, king of Bashan; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("И даде земљу њихову у наслеђе; Алилуија", "And gave their land as an inheritance; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("У наслеђе Израиљу, слузи својему; Алилуија", "An inheritance to Israel, his servant; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Који нас се опомену у понижењу нашем; Алилуија", "Who remembered us in our low estate; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("И избави нас од непријатеља наших; Алилуија", "And delivered us from our enemies; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Који даје храну свакому тијелу; Алилуија", "Who gives food to all flesh; Alleluia"),
    ("јер је довијека милост његова; Алилуија", "for his mercy endures forever; Alleluia"),
    ("Славите Бога небескога, Алилуја,", "Praise the God of heaven; Alleluia"),
    ("јер је довијека милост Његова. Алилуја", "for his mercy endures forever. Alleluia"),
]

# Spread words evenly across the sung portion of the recording.
DURATION = 438.0
START = 5.0      # a few seconds of intro before the first word
END = 432.0      # leave a breath at the end

total_words = sum(len(cy.split()) for cy, _ in PAIRS)
gap = (END - START) / total_words

lines = []
t = START
for cy, en in PAIRS:
    words = []
    for w in cy.split():
        words.append({"cy": w, "t": round(t, 2)})
        t += gap
    lines.append({"en": en, "words": words})

data = {
    "title": "Тиха Молитва",
    "subtitle": "Psalm 135 — the Polyeleos",
    "placeholder_timing": True,  # remove/overwrite via studio.html for precise sync
    "lines": lines,
}

with open("data/chant.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Wrote data/chant.json — {len(lines)} lines, {total_words} words, gap {gap:.2f}s")
