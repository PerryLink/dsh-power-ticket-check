#!/usr/bin/env python3
"""README visuals for dsh-power-ticket-check — read off the shipped pipeline.

Two figures, both derived from the code and the fixtures in this repository:

  hero 1440×576 (Pillow, 4 files: zh/en × light/dark)
      The material itself: a work ticket (DL-2026-0001, 电气第一种工作票) with a
      vertical chronology (签发 2026-03-14 16:00 → 许可 2026-03-15 08:30 →
      终结 2026-03-15 17:00, extension not provided), the five safety technical
      measures of PT-006 (three written, 悬挂标示牌 and 装设遮栏 missing), and
      four check rows: PT-003 (no order difference), PT-006 (error), PT-007
      (warn), PT-001/002/005 (institution lists ship empty → skipped).  The
      bottom strip is the real quickstart fixture's report: 2 issues
      (1 error + 1 warn) and 5 skipped, verdict left to the reviewer.

  flow 1100×660 (hand-written SVG, 2 files: light/dark)
      The ticket dissected into three evidence bands — 清单 (institution lists),
      时间轴 (issuing → permit → termination, extension optional) and 文本
      (measure terms, permit terms) — with the seven rules tagged where they
      read.  Two channels leave the board: `issues[]` (with severity) and
      `skipped[]` (with a reason).  A small force ladder on the right records
      why severity is capped: chapter 6 mandatory → error, chapter 5
      recommendatory → warn, institution configuration → info.
      This is NOT a row of nodes; the time axis and the two report channels
      carry the structure.

Every value shown is taken from this repository's own material:
  tests/fixtures/PT-006/PT-006-unsafe.json   (ticket fields, measures, dates)
  lib/index.mjs / src/check.ts               (rule ids, severities, channels)
  samples/quickstart/expected/result.json    (2 issues, 5 skipped)

Run once:  python scripts/gen-readme-assets.py
Requires:  Pillow + Windows fonts msyh.ttc / msyhbd.ttc / consola.ttf /
           consolab.ttf.  Every label is measured before it is drawn; the
           script exits instead of shipping clipped text.
"""
from __future__ import annotations

import os
from functools import lru_cache
from html import escape

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")

FONT_FILES = {
    "cjk": r"C:\Windows\Fonts\msyh.ttc",
    "cjk_bold": r"C:\Windows\Fonts\msyhbd.ttc",
    "mono": r"C:\Windows\Fonts\consola.ttf",
    "mono_bold": r"C:\Windows\Fonts\consolab.ttf",
}
for _kind, _path in FONT_FILES.items():
    if not os.path.exists(_path):
        raise SystemExit(f"FATAL: font missing: {_path}")

SKIN = {
    "light": dict(
        bg_from="#f9f6fd", bg_to="#e4eaf8",
        card="#ffffff", edge="#e6e2ef",
        text="#141419", sub="#4d5261", faint="#8f94a4",
        accent="#4B67B4", accent_soft="#eef1fb",
        band="#f5f2fb", grid="#e7e4f0",
        green="#15803d", green_bg="#e9f7ee",
        warn="#b45309", warn_bg="#fdf3e9",
        error="#b42318", error_bg="#fbeae8",
        shadow=(32, 26, 64),
    ),
    "dark": dict(
        bg_from="#131a2a", bg_to="#0c1016",
        card="#1b2231", edge="#2e374b",
        text="#f0f3f9", sub="#a8b1c4", faint="#737b8d",
        accent="#8496f5", accent_soft="#242d42",
        band="#202839", grid="#2b3348",
        green="#3fb950", green_bg="#15281c",
        warn="#d9a441", warn_bg="#2a2216",
        error="#f87171", error_bg="#3a2020",
        shadow=(0, 0, 0),
    ),
}


@lru_cache(maxsize=None)
def font(size: int, kind: str = "cjk_bold") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_FILES[kind], size)


def hx(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


_SCRATCH = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def txt(d: ImageDraw.ImageDraw, xy: tuple[float, float], content: str, *,
        font: ImageFont.FreeTypeFont, fill: tuple[int, int, int],
        anchor: str = "ls") -> None:
    """Draw text with a baseline anchor, so every y is a true baseline."""
    d.text(xy, content, font=font, fill=fill, anchor=anchor)


def measure(text: str, size: int, kind: str = "cjk") -> float:
    return _SCRATCH.textlength(text, font=font(size, kind))


def require_w(text: str, size: int, kind: str, max_w: float, what: str) -> None:
    width = measure(text, size, kind)
    if width > max_w + 0.5:
        raise SystemExit(
            f"FATAL: {what} overflows: {text!r} needs {width:.1f}px > {max_w}px")


def fit_size(text: str, kind: str, max_w: float, start: int, minimum: int,
             what: str) -> int:
    for size in range(start, minimum - 1, -1):
        if measure(text, size, kind) <= max_w:
            return size
    raise SystemExit(f"FATAL: {what} does not fit {max_w}px at >= {minimum}px: {text!r}")


def fit_lines(lines: list[str], kind: str, max_w: float, start: int,
              minimum: int, what: str) -> int:
    return min(fit_size(line, kind, max_w, start, minimum, what) for line in lines)


def gradient(w: int, h: int, c1: str, c2: str) -> Image.Image:
    base = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(base)
    a, b = hx(c1), hx(c2)
    for y in range(h):
        t = 0.18 * (y / h) + 0.82 * (y / h) ** 1.3
        d.line([(0, y), (w, y)],
               fill=tuple(int(p + (q - p) * t) for p, q in zip(a, b)))
    return base


def glow(img: Image.Image, cx: int, cy: int, radius: int,
         color: tuple[int, int, int], alpha: int) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(10, 0, -1):
        rr = radius * i / 10
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                  fill=color + (int(alpha * (1 - i / 10) ** 1.4),))
    return Image.alpha_composite(img.convert("RGBA"),
                                 layer.filter(ImageFilter.GaussianBlur(24))).convert("RGB")


def card(img: Image.Image, box: tuple[int, int, int, int], s: dict,
         radius: int = 22, shadow: bool = True) -> Image.Image:
    x0, y0, x1, y1 = box
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        for i in range(18, 0, -3):
            sd.rounded_rectangle(
                [x0 + 2, y0 + 6 + i // 2, x1 - 2, y1 + 6 + i // 2],
                radius=radius + i // 3,
                fill=s["shadow"] + (int(7 * (1 - i / 18)),))
        base = Image.alpha_composite(img.convert("RGBA"),
                                     sh.filter(ImageFilter.GaussianBlur(12)))
    else:
        base = img.convert("RGBA")
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(box, radius=radius, fill=hx(s["card"]),
                        outline=hx(s["edge"]), width=2)
    return base.convert("RGB")


def pill(img: Image.Image, xy: tuple[int, int], text: str, s: dict,
         size: int = 17) -> tuple[int, int]:
    d = ImageDraw.Draw(img)
    f = font(size, "cjk_bold")
    w = measure(text, size, "cjk_bold")
    x, y = xy
    height = size + 20
    d.rounded_rectangle([x, y, x + w + 30, y + height], radius=height / 2,
                        fill=hx(s["band"]), outline=hx(s["edge"]), width=1)
    txt(d, (x + 15, y + height / 2), text, font=f, fill=hx(s["accent"]),
           anchor="lm")
    return int(x + w + 30), int(y + height)


def chip(img: Image.Image, x_right: int, y: int, text: str, fg: str, bg: str,
         size: float = 10.5, height: int = 22, bold: bool = True,
         edge: str | None = None) -> int:
    """Right-anchored pill; returns its left edge."""
    d = ImageDraw.Draw(img)
    kind = "cjk_bold" if bold else "cjk"
    w = measure(text, size, kind) + 22
    x = x_right - w
    d.rounded_rectangle([x, y, x_right, y + height], radius=height / 2,
                        fill=hx(bg), outline=hx(edge) if edge else None,
                        width=1 if edge else 0)
    txt(d, (x + 11, y + height / 2), text, font=font(size, kind),
           fill=hx(fg), anchor="lm")
    return int(x)


def chip_left(img: Image.Image, x: int, y: int, text: str, fg: str, bg: str,
              size: float = 10.5, height: int = 22, bold: bool = True,
              edge: str | None = None) -> int:
    d = ImageDraw.Draw(img)
    kind = "cjk_bold" if bold else "cjk"
    w = measure(text, size, kind) + 22
    d.rounded_rectangle([x, y, x + w, y + height], radius=height / 2,
                        fill=hx(bg), outline=hx(edge) if edge else None,
                        width=1 if edge else 0)
    txt(d, (x + 11, y + height / 2), text, font=font(size, kind),
           fill=hx(fg), anchor="lm")
    return int(x + w)


def check_mark(d: ImageDraw.ImageDraw, cx: int, cy: int, color: tuple,
               r: int = 7) -> None:
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    d.line([(cx - 3.1, cy + 0.1), (cx - 0.7, cy + 2.9), (cx + 3.5, cy - 3.1)],
           fill=(255, 255, 255), width=2, joint="curve")


def cross_mark(d: ImageDraw.ImageDraw, cx: int, cy: int, color: tuple,
               r: int = 7) -> None:
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
    d.line([(cx - 2.6, cy - 2.6), (cx + 2.6, cy + 2.6)], fill=color, width=2)
    d.line([(cx - 2.6, cy + 2.6), (cx + 2.6, cy - 2.6)], fill=color, width=2)


# --------------------------------------------------------------------------- hero
HERO = {
    "zh": dict(
        kicker="DeepSeek Harness 插件 · 核查器",
        value=["一张工作票，七个检位逐条核对", "差异落到栏名与时刻，不判合规"],
        sub=["签发 → 许可 → 终结的顺序、五项安全措施、三项许可手续；",
             "未能执行的检查逐条写明原因——空 issues 不等于没问题。"],
        meta="PT-001..PT-007 · 规则包 2026.1 · 第5章 ≤ warn · 6.1.1 = error",
        foot="Apache-2.0 · PerryLink DSH plugin family",
        title="工作票 · DL-2026-0001",
        kind="电气第一种工作票",
        where="35kV 某某变电站 · 10kV 某某线 01 号杆更换隔离开关",
        issued=("2026-03-14 16:00", "签发"),
        permitted=("2026-03-15 08:30", "许可"),
        finished=("2026-03-15 17:00", "终结"),
        gap1="16.5 h",
        gap2="8.5 h",
        ext="延期未提供 → PT-004 skipped",
        rows=[
            ("PT-003", "skipped", "skip",
             "已执行，未见差异 · 许可 ≥ 签发 · 终结 ≥ 许可"),
            ("PT-006", "error", "error", "五项措施写到 3 项",
             "缺 悬挂标示牌、装设遮栏"),
            ("PT-007", "warn", "warn", "许可手续缺 4 个关键词",
             "再次检查 · 带电部位 · 确认 · 签名"),
            ("PT-001/002/005", "skipped", "skip", "本机构清单出厂为空"),
        ],
        measures="五项安全技术措施",
        legend_written="已写到",
        legend_missing="未写到",
        terms=["停电", "验电", "装设接地线", "悬挂标示牌", "装设遮栏"],
        found="未出现 2 项：悬挂标示牌、装设遮栏",
        strip_l="issues[] 2 条 · 1 error / 1 warn ｜ skipped[] 5 条",
        strip_r="结论留给审核人",
    ),
    "en": dict(
        kicker="DeepSeek Harness plugin · checker",
        value=["One work ticket, seven named checks",
               "differences land on a column, not a verdict"],
        sub=["Issue → permit → termination order, five measures, three formalities.",
             "Every check that cannot run says why; an empty issues list is not a pass."],
        meta="PT-001..PT-007 · ruleset 2026.1 · chapter 5 ≤ warn · 6.1.1 = error",
        foot="Apache-2.0 · PerryLink DSH plugin family",
        title="Work ticket · DL-2026-0001",
        kind="Type-1 electrical ticket",
        where="35 kV Some Substation · 10 kV line, pole 01 disconnector",
        issued=("2026-03-14 16:00", "issued"),
        permitted=("2026-03-15 08:30", "permit"),
        finished=("2026-03-15 17:00", "finish"),
        gap1="16.5 h",
        gap2="8.5 h",
        ext="extension none → PT-004 skipped",
        rows=[
            ("PT-003", "skipped", "skip",
             "ran clean · permit ≥ issue · finish ≥ permit"),
            ("PT-006", "error", "error", "3 of 5 measures written",
             "missing sign board, barrier"),
            ("PT-007", "warn", "warn", "permit formalities missing",
             "re-check · live parts · confirm · sign"),
            ("PT-001/002/005", "skipped", "skip", "institution lists ship empty"),
        ],
        measures="Five safety measures",
        legend_written="written",
        legend_missing="missing",
        terms=["outage", "voltage test", "grounding", "sign board", "barrier"],
        found="2 missing: sign board, barrier",
        strip_l="issues[] 2 · 1 error / 1 warn ｜ skipped[] 5",
        strip_r="the verdict stays human",
    ),
}


def hero(lang: str, skin: str) -> None:
    s = SKIN[skin]
    H = HERO[lang]
    W, HT = 1440, 576
    img = gradient(W, HT, s["bg_from"], s["bg_to"])
    img = glow(img, 1220, 24, 380, hx(s["accent"]),
               26 if skin == "light" else 40)
    img = glow(img, 110, 570, 300, hx(s["accent"]),
               8 if skin == "light" else 14)
    d = ImageDraw.Draw(img)

    m = 64
    left_w = 620
    pill(img, (m, 54), H["kicker"], s, size=17)
    d = ImageDraw.Draw(img)

    # ---- left column --------------------------------------------------------
    title = "dsh-power-ticket-check"
    require_w(title, 48, "mono_bold", left_w, "hero title")
    txt(d, (m - 2, 160), title, font=font(48, "mono_bold"), fill=hx(s["text"]))

    value_size = fit_lines(H["value"], "cjk_bold", left_w, 38, 28, "hero value")
    value_step = value_size + 18
    for i, line in enumerate(H["value"]):
        require_w(line, value_size, "cjk_bold", left_w, "hero value")
        txt(d, (m, 240 + i * value_step), line,
            font=font(value_size, "cjk_bold"), fill=hx(s["text"]))

    sub_size = fit_lines(H["sub"], "cjk", left_w, 20, 15, "hero sub")
    for i, line in enumerate(H["sub"]):
        require_w(line, sub_size, "cjk", left_w, "hero sub")
        txt(d, (m + 1, 366 + i * 34), line, font=font(sub_size, "cjk"),
               fill=hx(s["sub"]))

    require_w(H["meta"], 17, "cjk", left_w, "hero meta")
    txt(d, (m + 1, 456), H["meta"], font=font(17, "cjk"), fill=hx(s["faint"]))
    d.line([m + 1, 484, m + left_w - 6, 484], fill=hx(s["grid"]), width=2)
    require_w(H["foot"], 14, "cjk", left_w, "hero foot")
    txt(d, (m + 1, 508), H["foot"], font=font(14, "cjk"), fill=hx(s["faint"]))

    # ---- right: the ticket card --------------------------------------------
    img = card(img, (700, 40, 1376, 468), s, radius=22)
    d = ImageDraw.Draw(img)
    txt(d, (724, 76), H["title"], font=font(17, "cjk_bold"),
           fill=hx(s["text"]))
    kind_left = chip(img, 1352, 54, H["kind"], s["accent"], s["band"],
                     size=10.5, height=24, edge=s["edge"])
    if kind_left < 1150:
        raise SystemExit(f"FATAL: hero kind chip runs too wide ({kind_left})")
    d = ImageDraw.Draw(img)
    require_w(H["where"], 12, "cjk", 628, "hero where")
    txt(d, (724, 103), H["where"], font=font(12, "cjk"), fill=hx(s["sub"]))
    d.line([724, 114, 1352, 114], fill=hx(s["grid"]), width=2)

    # vertical chronology ------------------------------------------------------
    axis_x = 766
    d.line([axis_x, 120, axis_x, 330], fill=hx(s["grid"]), width=2)
    nodes = [(136, H["issued"]), (218, H["permitted"]), (300, H["finished"])]
    for cy, (moment, role) in nodes:
        d.ellipse([axis_x - 8, cy - 8, axis_x + 8, cy + 8],
                  fill=hx(s["accent_soft"]))
        d.ellipse([axis_x - 5, cy - 5, axis_x + 5, cy + 5],
                  fill=hx(s["accent"]))
        txt(d, (786, cy + 6), moment, font=font(13, "mono_bold"),
               fill=hx(s["text"]))
        txt(d, (786, cy + 22), role, font=font(10.5, "cjk"), fill=hx(s["faint"]))
    # intervals on the left of the axis
    txt(d, (750, 177), H["gap1"], font=font(10.5, "mono"), fill=hx(s["faint"]),
           anchor="rm")
    txt(d, (750, 259), H["gap2"], font=font(10.5, "mono"), fill=hx(s["faint"]),
           anchor="rm")
    # the optional extension: dashed elbow with an open end
    for i in range(4):
        y0 = 300 + 10 + i * 8
        d.line([axis_x, y0, axis_x, y0 + 4], fill=hx(s["faint"]), width=2)
    d.line([axis_x, 336, 900, 336], fill=hx(s["faint"]), width=2)
    d.ellipse([894, 330, 906, 342], outline=hx(s["faint"]), width=2)
    require_w(H["ext"], 10.5, "cjk", 330, "hero extension")
    txt(d, (786, 352), H["ext"], font=font(10.5, "cjk"), fill=hx(s["faint"]))

    # four check rows on the right -------------------------------------------
    row_x = 1000
    row_right = 1352
    d.line([row_x, 172, row_right, 172], fill=hx(s["grid"]), width=1)
    d.line([row_x, 240, row_right, 240], fill=hx(s["grid"]), width=1)
    d.line([row_x, 306, row_right, 306], fill=hx(s["grid"]), width=1)
    sev_colors = {
        "error": (s["error"], s["error_bg"]),
        "warn": (s["warn"], s["warn_bg"]),
        "skip": (s["faint"], s["band"]),
    }
    baselines = [138, 190, 252, 320]
    for (rule, status, kind, *lines), base in zip(H["rows"], baselines):
        fg, bg = sev_colors[kind]
        txt(d, (row_x, base), rule, font=font(11, "mono_bold"),
               fill=hx(s["text"]))
        w = measure(rule, 11, "mono_bold")
        chip_left(img, int(row_x + w + 8), base - 14, status, fg, bg,
                  size=10.5, height=18, edge=fg)
        d = ImageDraw.Draw(img)
        for j, line in enumerate(lines):
            require_w(line, 11, "cjk", 352, f"hero row {rule}")
            txt(d, (row_x, base + 18 + j * 16), line, font=font(11, "cjk"),
                fill=hx(s["sub"] if j == 0 else fg))

    # five measures at the foot of the card ------------------------------------
    txt(d, (724, 378), H["measures"], font=font(11, "cjk_bold"),
           fill=hx(s["sub"]))
    # legend: two drawn glyphs, because msyh has no reliable ✓ / ✗
    legend_items = ((True, H["legend_written"]), (False, H["legend_missing"]))
    legend_w = sum(16 + measure(label, 10.5, "cjk") + 18
                   for _, label in legend_items) - 18
    lx = 1352 - legend_w
    if lx < 1180:
        raise SystemExit(f"FATAL: hero legend overlaps the heading ({lx})")
    for written, label in legend_items:
        if written:
            check_mark(d, lx + 6, 374, hx(s["accent"]), r=6)
        else:
            cross_mark(d, lx + 6, 374, hx(s["error"]), r=6)
        txt(d, (lx + 16, 378), label, font=font(10.5, "cjk"),
               fill=hx(s["faint"]))
        lx += 16 + measure(label, 10.5, "cjk") + 18
    x = 724
    for term, written in zip(H["terms"], (True, True, True, False, False)):
        f = font(11.5, "cjk_bold")
        text_w = measure(term, 11.5, "cjk_bold")
        w = int(12 + 14 + 5 + text_w + 12)
        y = 388
        h = 26
        if written:
            d.rounded_rectangle([x, y, x + w, y + h], radius=h / 2,
                                fill=hx(s["band"]), outline=hx(s["accent"]),
                                width=2)
            check_mark(d, x + 19, y + h // 2, hx(s["accent"]))
            txt(d, (x + 31, y + h / 2), term, font=f, fill=hx(s["text"]),
                   anchor="lm")
        else:
            d.rounded_rectangle([x, y, x + w, y + h], radius=h / 2,
                                fill=hx(s["error_bg"]), outline=hx(s["error"]),
                                width=2)
            cross_mark(d, x + 19, y + h // 2, hx(s["error"]))
            txt(d, (x + 31, y + h / 2), term, font=f, fill=hx(s["error"]),
                   anchor="lm")
        x += w + 10
    if x > 1354:
        raise SystemExit(f"FATAL: hero measure chips overflow to {x}")
    require_w(H["found"], 11.5, "cjk_bold", 628, "hero found")
    txt(d, (724, 440), H["found"], font=font(11.5, "cjk_bold"),
           fill=hx(s["error"]))

    # report strip -------------------------------------------------------------
    img = card(img, (700, 486, 1376, 546), s, radius=20)
    d = ImageDraw.Draw(img)
    require_w(H["strip_l"], 12.5, "cjk", 410, "hero strip left")
    require_w(H["strip_r"], 12.5, "cjk_bold", 200, "hero strip right")
    txt(d, (724, 516), H["strip_l"], font=font(12.5, "cjk"),
           fill=hx(s["text"]), anchor="lm")
    txt(d, (1352, 516), H["strip_r"], font=font(12.5, "cjk_bold"),
           fill=hx(s["green"]), anchor="rm")

    name = f"dsh-power-ticket-check-hero-{lang}-{skin}.webp"
    img.save(os.path.join(OUT, name), "WEBP", quality=92, method=6)
    print(f"wrote {name} ({W}×{HT})")


# --------------------------------------------------------------------------- flow
FLOW = {
    "light": dict(
        bg_from="#f9f6fd", bg_to="#e4eaf8",
        panel="#ffffff", edge="#e6e2ef", band="#f5f2fb",
        text="#141419", sub="#4d5261", faint="#8f94a4",
        accent="#4B67B4", accent_soft="#eef1fb",
        green="#15803d", green_bg="#e9f7ee",
        warn="#b45309", warn_bg="#fdf3e9",
        error="#b42318", error_bg="#fbeae8",
        rule="#e3dfee", shadow="0.10",
    ),
    "dark": dict(
        bg_from="#131a2a", bg_to="#0c1016",
        panel="#1b2231", edge="#2e374b", band="#202839",
        text="#f0f3f9", sub="#a8b1c4", faint="#737b8d",
        accent="#8496f5", accent_soft="#242d42",
        green="#3fb950", green_bg="#15281c",
        warn="#d9a441", warn_bg="#2a2216",
        error="#f87171", error_bg="#3a2020",
        rule="#2b3348", shadow="0.45",
    ),
}

FONT_CSS_CJK = ("'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',"
                "'Source Han Sans SC',sans-serif")
FONT_CSS_MONO = "'Consolas','SFMono-Regular',Menlo,ui-monospace,monospace"


def svg_kind(mono: bool, weight: int | None) -> str:
    if mono:
        return "mono_bold" if weight else "mono"
    return "cjk_bold" if weight else "cjk"


class Svg:
    """Small hand-written SVG writer that measures every label first."""

    def __init__(self, s: dict) -> None:
        self.s = s
        self.parts: list[str] = []
        self.overflows: list[str] = []

    def add(self, markup: str) -> None:
        self.parts.append(markup)

    def text(self, x: float, y: float, content: str, size: float, fill: str, *,
             anchor: str = "start", weight: int | None = None,
             mono: bool = False, max_w: float | None = None) -> None:
        kind = svg_kind(mono, weight)
        if max_w is not None and measure(content, size, kind) > max_w + 0.4:
            self.overflows.append(
                f"{content!r} needs {measure(content, size, kind):.1f}px > {max_w}px")
        family = FONT_CSS_MONO if mono else FONT_CSS_CJK
        attrs = [f'x="{x}"', f'y="{y}"', f'fill="{fill}"',
                 f'font-family="{family}"', f'font-size="{size}"']
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if weight:
            attrs.append(f'font-weight="{weight}"')
        self.add(f'<text {" ".join(attrs)}>{escape(content)}</text>')

    def rect(self, x: float, y: float, w: float, h: float, *, fill: str,
             rx: float = 0, stroke: str | None = None, sw: float = 1.5,
             shadow: bool = False, dash: str | None = None) -> None:
        attrs = [f'x="{x}"', f'y="{y}"', f'width="{w}"', f'height="{h}"']
        if rx:
            attrs.append(f'rx="{rx}"')
        attrs.append(f'fill="{fill}"')
        if stroke:
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{sw}"')
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if shadow:
            attrs.append('filter="url(#soft)"')
        self.add(f'<rect {" ".join(attrs)}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, *, stroke: str,
             sw: float = 1.5, dash: str | None = None,
             opacity: float | None = None) -> None:
        attrs = [f'x1="{x1}"', f'y1="{y1}"', f'x2="{x2}"', f'y2="{y2}"',
                 f'stroke="{stroke}"', f'stroke-width="{sw}"',
                 'stroke-linecap="round"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.add(f'<line {" ".join(attrs)}/>')

    def path(self, d: str, *, stroke: str, sw: float = 1.5,
             fill: str = "none", dash: str | None = None,
             opacity: float | None = None) -> None:
        attrs = [f'd="{d}"', f'fill="{fill}"', f'stroke="{stroke}"',
                 f'stroke-width="{sw}"', 'stroke-linecap="round"',
                 'stroke-linejoin="round"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.add(f'<path {" ".join(attrs)}/>')

    def chip(self, x_right: float, y: float, label: str, fg: str, bg: str,
             *, size: float = 10.5, pad: float = 11, height: float = 22,
             mono: bool = False, weight: int | None = 700,
             edge: str | None = None) -> float:
        kind = svg_kind(mono, weight)
        w = measure(label, size, kind) + pad * 2
        x = x_right - w
        self.rect(x, y, w, height, fill=bg, rx=height / 2,
                  stroke=edge, sw=1)
        self.text(x + pad, y + height / 2 + size * 0.34, label, size, fg,
                  weight=weight, mono=mono)
        return x

    def chip_left(self, x: float, y: float, label: str, fg: str, bg: str,
                  *, size: float = 10.5, pad: float = 11,
                  height: float = 22, mono: bool = False,
                  weight: int | None = 700, edge: str | None = None) -> float:
        kind = svg_kind(mono, weight)
        w = measure(label, size, kind) + pad * 2
        self.rect(x, y, w, height, fill=bg, rx=height / 2, stroke=edge, sw=1)
        self.text(x + pad, y + height / 2 + size * 0.34, label, size, fg,
                  weight=weight, mono=mono)
        return x + w

    def dot(self, cx: float, cy: float, r: float, fill: str,
            stroke: str | None = None, sw: float = 1.5) -> None:
        attrs = [f'cx="{cx}"', f'cy="{cy}"', f'r="{r}"', f'fill="{fill}"']
        if stroke:
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{sw}"')
        self.add(f'<circle {" ".join(attrs)}/>')

    def svg(self, w: int, h: int, label: str) -> str:
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
                f'height="{h}" viewBox="0 0 {w} {h}" role="img" '
                f'aria-label="{escape(label)}">')
        return "\n".join([head, *self.parts, "</svg>"]) + "\n"


def flow_svg(skin: str) -> str:
    s = FLOW[skin]
    W, H = 1100, 660
    v = Svg(s)

    v.add("<defs>")
    v.add(f'<linearGradient id="bg" x1="0" y1="0" x2="0.3" y2="1">'
          f'<stop offset="0" stop-color="{s["bg_from"]}"/>'
          f'<stop offset="1" stop-color="{s["bg_to"]}"/></linearGradient>')
    v.add(f'<filter id="soft" x="-25%" y="-25%" width="150%" height="160%">'
          f'<feDropShadow dx="0" dy="7" stdDeviation="9" '
          f'flood-color="#16122c" flood-opacity="{s["shadow"]}"/></filter>')
    v.add("</defs>")
    v.add(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')

    # ---- header -------------------------------------------------------------
    v.text(44, 58, "dsh-power-ticket-check", 28, s["text"], weight=700,
           mono=True, max_w=700)
    v.text(44, 86,
           "一份工作票拆成清单、时间轴与文本三层证据：七条规则逐层读取，差异与未执行分两条通道离开。",
           14.5, s["sub"], max_w=820)
    v.chip(1056, 36, "规则包 v2026.1 · 7 条", s["accent"], s["band"],
           size=12, pad=12, height=26)

    # ======================================================================
    # LEFT: the work ticket, dissected into three evidence bands.
    # ======================================================================
    v.rect(44, 108, 628, 478, fill=s["panel"], rx=20, stroke=s["edge"],
           sw=1.5, shadow=True)
    v.text(62, 132, "工作票 · DL-2026-0001", 14, s["text"], weight=700,
           max_w=360)
    v.chip(654, 118, "电气第一种工作票", s["accent"], s["band"],
           size=11, pad=11, height=22)
    v.text(62, 154, "35kV 某某变电站 · 10kV 某某线 01 号杆更换隔离开关", 11.5,
           s["sub"], max_w=520)
    v.line(62, 166, 654, 166, stroke=s["rule"], sw=1)

    # band 1 — institution lists that ship empty
    v.rect(62, 176, 592, 46, fill=s["band"], rx=12)
    v.rect(62, 176, 592, 46, fill="none", rx=12, stroke=s["accent"], sw=1.2,
           dash="6 5")
    v.text(76, 196, "本机构清单出厂为空 → PT-001 / 002 / 005 进 skipped", 11,
           s["text"], max_w=560)
    v.text(76, 214,
           "requiredFields · ticketKinds · exclusiveRolePairs 需按本机构填写",
           11, s["sub"], mono=False, max_w=560)

    # band 2 — chronology
    v.text(62, 246, "时间轴", 13, s["text"], weight=700, max_w=70)
    v.text(116, 246, "签发 → 许可 → 终结", 11, s["faint"], max_w=220)
    v.chip(654, 234, "PT-003", s["accent"], s["accent_soft"], size=11,
           pad=9, height=18)
    axis_y = 314
    v.line(100, axis_y, 640, axis_y, stroke=s["rule"], sw=1.5)
    stations = [
        (130, "签发时间", "2026-03-14 16:00"),
        (300, "许可时间", "2026-03-15 08:30"),
        (470, "终结时间", "2026-03-15 17:00"),
    ]
    for x, label, value in stations:
        v.line(x, axis_y - 7, x, axis_y + 7, stroke=s["accent"], sw=2)
        v.dot(x, axis_y, 5.5, s["accent"])
        v.text(x, 292, label, 11, s["faint"], anchor="middle", max_w=150)
        v.text(x, 340, value, 13, s["text"], anchor="middle", mono=True,
               weight=700, max_w=150)
    # optional extension: dashed branch with an open end
    v.line(476, axis_y, 610, axis_y, stroke=s["faint"], sw=1.6, dash="6 5")
    v.dot(610, axis_y, 5.5, s["panel"], stroke=s["faint"], sw=1.8)
    v.text(610, 292, "延期时间", 11, s["faint"], anchor="middle", max_w=90)
    v.text(610, 340, "未提供", 11.5, s["sub"], anchor="middle", max_w=80)
    v.text(610, 362, "PT-004 skipped", 11, s["faint"], anchor="middle",
           mono=True, max_w=110)
    # interval brackets
    for x0, x1, label in ((130, 300, "16.5 h"), (300, 470, "8.5 h")):
        v.line(x0 + 8, 356, x1 - 8, 356, stroke=s["faint"], sw=1.2)
        v.line(x0 + 8, 352, x0 + 8, 360, stroke=s["faint"], sw=1.2)
        v.line(x1 - 8, 352, x1 - 8, 360, stroke=s["faint"], sw=1.2)
        v.text((x0 + x1) / 2, 372, label, 11, s["faint"], anchor="middle",
               mono=True, max_w=80)
    v.text(62, 372, "墙上时钟比较", 11, s["faint"], max_w=110)

    # band 3 — textual evidence: PT-006 and PT-007
    v.text(62, 404, "安全措施", 13, s["text"], weight=700, max_w=80)
    v.text(118, 404, "五项安全技术措施", 11, s["faint"], max_w=180)
    v.chip(654, 392, "PT-006 · error", s["error"], s["error_bg"], size=11,
           pad=9, height=18, edge=s["error"])
    terms = [("停电", True), ("验电", True), ("装设接地线", True),
             ("悬挂标示牌", False), ("装设遮栏", False)]
    x = 62
    for term, written in terms:
        text_w = measure(term, 11.5, "cjk_bold")
        w = 12 + 13 + 5 + text_w + 12
        y, h = 414, 24
        if written:
            v.rect(x, y, w, h, fill=s["band"], rx=h / 2,
                   stroke=s["accent"], sw=1.4)
            v.dot(x + 17, y + h / 2, 6.5, s["accent"])
            v.path(f"M{x + 13.6} {y + h / 2 + 0.4} l2.1 2.6 l4.2 -5",
                   stroke="#ffffff", sw=1.8)
            v.text(x + 30, y + h / 2 + 4, term, 11.5, s["text"], weight=700,
                   max_w=text_w + 1)
        else:
            v.rect(x, y, w, h, fill=s["error_bg"], rx=h / 2,
                   stroke=s["error"], sw=1.4)
            v.dot(x + 17, y + h / 2, 6.5, "none", stroke=s["error"], sw=1.5)
            v.path(f"M{x + 14.4} {y + h / 2 - 2.6} l5.2 5.2 "
                   f"M{x + 19.6} {y + h / 2 - 2.6} l-5.2 5.2",
                   stroke=s["error"], sw=1.5)
            v.text(x + 30, y + h / 2 + 4, term, 11.5, s["error"], weight=700,
                   max_w=text_w + 1)
        x += w + 8
    if x > 660:
        raise SystemExit(f"FATAL: flow measure chips overflow to {x}")
    v.text(62, 458, "未出现 2 项：悬挂标示牌、装设遮栏", 11.5, s["error"],
           weight=700, max_w=420)
    v.text(62, 476, "只核对票面是否写到，不判断措施是否与现场相符", 11,
           s["faint"], max_w=420)

    v.text(62, 502, "许可手续", 13, s["text"], weight=700, max_w=80)
    v.text(118, 502, "三项手续", 11, s["faint"], max_w=100)
    v.chip(654, 490, "PT-007 · warn", s["warn"], s["warn_bg"], size=11,
           pad=9, height=18, edge=s["warn"])
    v.text(62, 526, "未出现 4 项：再次检查、带电设备的位置、确认、签名",
           11.5, s["warn"], max_w=520)
    v.text(62, 546, "读取 安全措施 · 许可开始工作时间 · 角色签名栏", 11,
           s["faint"], max_w=520)
    v.text(62, 570, "只读原件 · 原文不改 · 无网络 · 不调用模型", 11,
           s["faint"], max_w=520)

    # ======================================================================
    # RIGHT: two report channels, then the force ladder.
    # ======================================================================
    v.rect(692, 108, 364, 478, fill=s["panel"], rx=20, stroke=s["edge"],
           sw=1.5, shadow=True)
    v.text(710, 132, "报告", 14, s["text"], weight=700, max_w=80)
    v.chip(1038, 118, "规则包 2026.1", s["faint"], s["band"], size=11,
           pad=10, height=20)
    v.line(710, 144, 1038, 144, stroke=s["rule"], sw=1)

    v.text(710, 164, "issues[]", 13, s["accent"], weight=700, mono=True,
           max_w=120)
    v.chip(1038, 152, "2 条", s["accent"], s["accent_soft"], size=11,
           pad=9, height=18)
    # entry 1
    v.text(710, 188, "PT-006", 12, s["text"], weight=700, mono=True,
           max_w=80)
    v.chip_left(770, 176, "error", s["error"], s["error_bg"], size=11,
                pad=8, height=16, edge=s["error"])
    v.text(1038, 188, "安全措施", 11, s["faint"], anchor="end", max_w=100)
    v.text(710, 206, "未出现 2 项：悬挂标示牌、装设遮栏", 11, s["text"],
           max_w=320)
    # entry 2
    v.text(710, 238, "PT-007", 12, s["text"], weight=700, mono=True,
           max_w=80)
    v.chip_left(770, 226, "warn", s["warn"], s["warn_bg"], size=11, pad=8,
                height=16, edge=s["warn"])
    v.text(1038, 238, "许可手续", 11, s["faint"], anchor="end", max_w=100)
    v.text(710, 256, "未出现 4 项：再次检查、带电设备的位置、确认、签名", 11,
           s["text"], max_w=320)
    v.line(710, 270, 1038, 270, stroke=s["rule"], sw=1)

    v.text(710, 290, "skipped[]", 13, s["sub"], weight=700, mono=True,
           max_w=120)
    v.chip(1038, 278, "5 条", s["faint"], s["band"], size=11, pad=9,
           height=18)
    skipped = [
        "PT-001 · requiredFields 未配置",
        "PT-002 · ticketKinds 未配置",
        "PT-004 · 材料未提供延期时间",
        "PT-005 · exclusiveRolePairs 未配置",
        "PT-003 · 已执行，未见差异",
    ]
    for i, line in enumerate(skipped):
        v.text(710, 314 + i * 20, line, 11, s["text"], max_w=320)
    v.text(710, 414, "空 issues ≠ 没问题：两条通道一起读", 11, s["faint"],
           max_w=320)
    v.line(710, 424, 1038, 424, stroke=s["rule"], sw=1)

    # force ladder ------------------------------------------------------------
    v.text(710, 438, "效力层级 → 严重级", 11.5, s["text"], weight=700,
           max_w=150)
    ladder = [
        ("第 6 章 强制性 · 6.1.1", "error", s["error"], s["error_bg"]),
        ("第 5 章 推荐性 · 5.x", "warn", s["warn"], s["warn_bg"]),
        ("本机构配置 · requiredFields", "info", s["faint"], s["band"]),
    ]
    for i, (left, right, fg, bg) in enumerate(ladder):
        y = 458 + i * 18
        v.dot(714, y - 3, 3, fg)
        v.text(724, y, left, 11, s["sub"], max_w=230)
        v.text(1038, y, right, 11, fg, anchor="end", mono=True, weight=700,
               max_w=60)

    # reviewer gate -----------------------------------------------------------
    v.rect(710, 520, 328, 40, fill=s["green_bg"], rx=13,
           stroke=s["green"], sw=1.2)
    v.text(724, 545, "结论留给审核人 · 不判合规", 11.5, s["green"],
           weight=700, max_w=300)
    v.text(710, 578, "免责声明随报告附带 · 措辞守卫生效", 11, s["faint"],
           max_w=320)

    # ---- footer -------------------------------------------------------------
    v.line(44, 604, 1056, 604, stroke=s["rule"], sw=1)
    v.text(44, 626,
           "严重级跟着证据走：derived-from-principle ≤ warn · "
           "institutional-configuration ≤ info ｜ excerpt 必须是逐字引文",
           11.5, s["sub"], max_w=1012)
    v.text(44, 646,
           "config：rulesFile · disabledRules · onlyRules · timeoutMs ｜ "
           "只读材料 · 无网络 · 不调用模型 ｜ 墙上时钟，不换算时区",
           11.5, s["faint"], max_w=1012)

    if v.overflows:
        raise SystemExit("FATAL: SVG label overflow:\n  " +
                         "\n  ".join(v.overflows))
    return v.svg(
        W, H,
        "dsh-power-ticket-check 结构图：一份工作票拆成清单、时间轴与文本三层"
        "证据带，七条规则（PT-001..PT-007）逐层读取；差异进 issues[]，"
        "未执行或未发现差异进 skipped[]，两条通道汇到审核人；右侧效力阶梯按"
        "GB 26860—2011 的章节效力封顶严重级")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for skin in ("light", "dark"):
        for lang in ("zh", "en"):
            hero(lang, skin)
        name = f"dsh-power-ticket-check-flow-v5-{skin}.svg"
        with open(os.path.join(OUT, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(flow_svg(skin))
        print(f"wrote {name} (1100×660)")


if __name__ == "__main__":
    main()
