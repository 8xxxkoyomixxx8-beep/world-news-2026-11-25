#!/usr/bin/env python3
"""Draw the 25 November 2026 front page and save it as entry.png.

A one-page editorial summary of the day: masthead, a wide lead story, a
2x2 grid of story cards, a split bottom card and a headline ticker.
Every block of text is measured with PIL's text metrics, wrapped to its
card, and shrunk until it fits both across and down, so nothing overflows
or clips.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
SERIF_BOLD = str(FONT_DIR / "LiberationSerif-Bold.ttf")
SANS_BOLD = str(FONT_DIR / "LiberationSans-Bold.ttf")
SANS = str(FONT_DIR / "LiberationSans-Regular.ttf")

CANVAS = 1024
PAPER = (247, 243, 233)
CARD_BG = (253, 251, 245)
INK = (24, 24, 24)
MUTED = (92, 86, 74)
RED = (163, 22, 33)
BORDER = (186, 176, 156)

MARGIN = 36
CONTENT_W = CANVAS - 2 * MARGIN  # 952
COL_GAP = 16
COL_W = (CONTENT_W - COL_GAP) // 2  # 468
COL_X = (MARGIN, MARGIN + COL_W + COL_GAP)

PAD_X = 16
PAD_Y = 12

_font_cache = {}


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


_probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def text_w(text: str, fnt: ImageFont.FreeTypeFont) -> float:
    return _probe.textlength(text, font=fnt)


def wrap(text: str, fnt: ImageFont.FreeTypeFont, max_w: float) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = word if not current else f"{current} {word}"
        if text_w(trial, fnt) <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def tracked_w(text: str, fnt: ImageFont.FreeTypeFont, tracking: float) -> float:
    return sum(text_w(ch, fnt) for ch in text) + tracking * max(0, len(text) - 1)


def draw_tracked(draw, xy, text, fnt, fill, tracking=2.0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += text_w(ch, fnt) + tracking


def centered(draw, y, text, fnt, fill):
    x = (CANVAS - text_w(text, fnt)) / 2
    draw.text((x, y), text, font=fnt, fill=fill)


def fit_card(label, headline, body, box_w, box_h, headline_max):
    """Pick (headline_size, body_size, headline_lines, body_lines) that fit."""
    inner_w = box_w - 2 * PAD_X
    inner_h = box_h - 2 * PAD_Y
    label_h = 20
    gap1 = 5
    gap2 = 6
    for h_size in range(headline_max, 16, -1):
        h_font = font(SERIF_BOLD, h_size)
        h_lines = wrap(headline, h_font, inner_w)
        h_h = len(h_lines) * int(h_size * 1.16)
        for b_size in (20, 19, 18, 17, 16, 15, 14):
            b_font = font(SANS, b_size)
            b_lines = wrap(body, b_font, inner_w)
            b_h = len(b_lines) * int(b_size * 1.28)
            if label_h + gap1 + h_h + gap2 + b_h <= inner_h:
                return h_size, b_size, h_lines, b_lines
    # Fallback: smallest sizes (should not happen with the given copy).
    h_font = font(SERIF_BOLD, 17)
    b_font = font(SANS, 15)
    return 17, 15, wrap(headline, h_font, inner_w), wrap(body, b_font, inner_w)


def draw_card(draw, x, y, w, h, label, headline, body, headline_max):
    draw.rectangle([x, y, x + w, y + h], fill=CARD_BG, outline=BORDER, width=1)
    fitted = fit_card(label, headline, body, w, h, headline_max)
    h_size, b_size, h_lines, b_lines = fitted
    cx = x + PAD_X
    cy = y + PAD_Y
    draw_tracked(draw, (cx, cy), label.upper(), font(SANS_BOLD, 14), RED)
    cy += 20 + 5
    h_font = font(SERIF_BOLD, h_size)
    for line in h_lines:
        draw.text((cx, cy), line, font=h_font, fill=INK)
        cy += int(h_size * 1.16)
    cy += 6
    b_font = font(SANS, b_size)
    for line in b_lines:
        draw.text((cx, cy), line, font=b_font, fill=INK)
        cy += int(b_size * 1.28)


LEAD = (
    "Disaster · Cairo",
    "Fuel Tanker Fire Near Cairo Kills at Least 31",
    "A fuel tanker crashed on Cairo's Ring Road in Giza and burst into "
    "flames, engulfing the vehicles around it; at least 31 people were "
    "killed and 21 injured, Egypt's Health Ministry said.",
)

GRID = [
    (
        "Markets · Seoul",
        "Asian Markets Plunge as KOSPI Tumbles 6.16%",
        "Chip stocks led a regional sell-off: Samsung fell 9.9% and SK "
        "Hynix 11.1% in Seoul, Japan's Nikkei dropped 2.78% with SoftBank "
        "down 14.8%, and Taiwan's Taiex fell about 5%.",
    ),
    (
        "Justice · Brooklyn",
        "Huawei Convicted in US Court on 10 of 12 Counts",
        "A Brooklyn jury found the Chinese tech giant guilty of bank "
        "fraud, sanctions violations and conspiracy to steal trade "
        "secrets, but acquitted it of racketeering; Huawei will appeal.",
    ),
    (
        "Conflict · Ras Tanura",
        "Houthis Claim Attack on Saudi Refinery",
        "Yemen's Houthis claimed an attack on Saudi Arabia's Ras Tanura "
        "refinery complex, the kingdom's largest oil export terminal on "
        "the Gulf coast.",
    ),
    (
        "War · Samara",
        "Ukrainian Drones Hit Two Rosneft Refineries",
        "Ukrainian drones struck two Rosneft refineries in Russia's "
        "Samara region, in the latest of Kyiv's long-range strikes on "
        "Russian oil infrastructure.",
    ),
]

BOTTOM = [
    (
        "War · Sudan",
        "RSF Drone Strikes Kill 19 Civilians",
        "Sudan's Rapid Support Forces killed 19 civilians in drone "
        "strikes on two cities, as the civil war's toll on noncombatants "
        "deepened.",
    ),
    (
        "Diplomacy · Pacific",
        "Australia and Solomon Islands Sign Treaty Barring Foreign Bases",
        "Australia and Solomon Islands signed a treaty barring foreign "
        "military bases in the Pacific nation, a setback for China's "
        "regional ambitions.",
    ),
]

TICKER_ITEMS = [
    "Dell posts record $54.9bn quarter as AI server sales triple",
    "Russian strike on Odesa kills 2; Kyiv flats set ablaze",
    "Pope Leo voices concern over COP31 climate talks failure",
    "Nigeria seizes $200m of meth, arrests five Mexicans",
    "Colombia forces free all hostages in Cartagena supermarket raid",
    "Shenzhou-24 docks with Tiangong station",
    "Macy's Thanksgiving parade postponed over storm forecast",
]


def main() -> None:
    img = Image.new("RGB", (CANVAS, CANVAS), PAPER)
    draw = ImageDraw.Draw(img)

    # Masthead.
    centered(draw, 22, "THE WORLD IN ONE PAGE", font(SERIF_BOLD, 60), INK)
    centered(draw, 100, "WEDNESDAY 25 NOVEMBER 2026", font(SANS_BOLD, 44), RED)
    draw.rectangle([MARGIN, 168, CANVAS - MARGIN, 173], fill=RED)
    draw.rectangle([MARGIN, 177, CANVAS - MARGIN, 178], fill=INK)

    # Lead story.
    draw_card(draw, MARGIN, 190, CONTENT_W, 172, *LEAD, headline_max=44)

    # 2x2 grid.
    grid_y = (374, 546)
    for idx, story in enumerate(GRID):
        x = COL_X[idx % 2]
        y = grid_y[idx // 2]
        draw_card(draw, x, y, COL_W, 160, *story, headline_max=30)

    # Split bottom card.
    for idx, story in enumerate(BOTTOM):
        draw_card(draw, COL_X[idx], 718, COL_W, 156, *story, headline_max=26)

    # Footer ticker.
    draw.rectangle([MARGIN, 886, CANVAS - MARGIN, 887], fill=INK)
    ticker = "  •  ".join(TICKER_ITEMS)
    t_font = font(SANS, 15)
    lines = wrap(ticker, t_font, CONTENT_W)
    ty = 896
    for line in lines[:5]:
        draw.text((MARGIN, ty), line, font=t_font, fill=MUTED)
        ty += 20

    out = Path(__file__).resolve().parent / "entry.png"
    img.save(out, format="PNG")
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
