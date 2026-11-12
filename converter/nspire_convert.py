#!/usr/bin/env python3
"""
Nspire Convert: turn almost any document into images sized for a TI-Nspire CX screen.

Two modes:
  reflow (default)  Pulls the text out and re-lays it in big, sharp type,
                    one screen per image. Best for notes, readings, study guides.
  page              Keeps the original look (diagrams, math, pictures). Each page fills
                    the screen's width and is shown top to bottom, cut between lines.

Supported: PDF, Word (.docx .doc), .rtf, .odt, .txt, .md, .html, EPUB, PowerPoint
(.pptx, text only), Excel (.xlsx, as a table), and images (.png .jpg .gif .bmp ...).

Examples:
  python3 nspire_convert.py notes.docx
  python3 nspire_convert.py textbook.pdf --mode page
  python3 nspire_convert.py guide.pdf --font-size 14 --hd
"""

import argparse
import html
import io
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import fitz  # PyMuPDF
from PIL import Image

# TI-Nspire CX / CX II screen is 320x240; the tab bar at the top uses about 24 rows,
# so a document page has 320x216 to show a picture without shrinking it.
SCREEN_W, SCREEN_H = 320, 216

MUPDF_TYPES = {".pdf", ".epub", ".xps", ".oxps", ".mobi", ".fb2", ".cbz", ".svg"}
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".heic"}
TEXTUTIL_TYPES = {".doc", ".docx", ".rtf", ".rtfd", ".odt", ".wordml", ".webarchive"}
TEXT_TYPES = {".txt", ".md", ".csv", ".py", ".java", ".c", ".js", ".json", ".log"}
HTML_TYPES = {".html", ".htm"}


# ---------------------------------------------------------------- reading files

def html_body(raw):
    """Keep only what's inside <body> and drop <style>/<script>, so our own CSS wins."""
    raw = re.sub(r"(?is)<(style|script|head)\b.*?</\1>", "", raw)
    m = re.search(r"(?is)<body[^>]*>(.*)</body>", raw)
    body = m.group(1) if m else raw
    # drop empty paragraphs (Word uses them as spacers; they waste screen room)
    return re.sub(r"(?is)<p[^>]*>(\s|<br\s*/?>|<span[^>]*>\s*</span>)*</p>", "", body)


def textutil_to_html(path):
    """macOS's built-in textutil reads Word/RTF/ODT files and writes HTML."""
    out = subprocess.run(
        ["textutil", "-convert", "html", "-stdout", str(path)],
        capture_output=True, check=True,
    )
    return html_body(out.stdout.decode("utf-8", "replace"))


def text_to_html(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return "".join("<p>%s</p>" % html.escape(p).replace("\n", "<br>") for p in paras)


def pdf_like_to_html(doc):
    """Rebuild readable paragraphs from a PDF/EPUB, marking where each page starts."""
    parts = []
    for i, page in enumerate(doc, 1):
        parts.append('<p class="src">— page %d —</p>' % i)
        for block in page.get_text("blocks", sort=True):
            if block[6] != 0:  # 0 = text block, 1 = picture
                continue
            text = block[4].strip()
            if not text:
                continue
            text = re.sub(r"-\n(?=[a-z])", "", text)  # rejoin hyphen-split words
            text = re.sub(r"\s*\n\s*", " ", text)
            parts.append("<p>%s</p>" % html.escape(text))
    return "".join(parts)


def xml_texts(data, tag):
    root = ET.fromstring(data)
    return [el.text or "" for el in root.iter() if el.tag.endswith(tag)]


def pptx_to_html(path):
    parts = []
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
        names.sort(key=lambda n: int(re.findall(r"\d+", n)[-1]))
        for i, name in enumerate(names, 1):
            root = ET.fromstring(z.read(name))
            parts.append('<p class="src">— slide %d —</p>' % i)
            for para in root.iter():
                if para.tag.endswith("}p"):
                    line = "".join(t.text or "" for t in para.iter() if t.tag.endswith("}t"))
                    if line.strip():
                        parts.append("<p>%s</p>" % html.escape(line))
    return "".join(parts)


def xlsx_to_html(path):
    parts = []
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root:
                shared.append("".join(t.text or "" for t in si.iter() if t.tag.endswith("}t")))
        sheets = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        for i, name in enumerate(sheets, 1):
            root = ET.fromstring(z.read(name))
            parts.append('<p class="src">— sheet %d —</p><table>' % i)
            for row in root.iter():
                if not row.tag.endswith("}row"):
                    continue
                cells = []
                for c in row:
                    v = next((x.text for x in c.iter() if x.tag.endswith("}v") or x.tag.endswith("}t")), "")
                    if c.get("t") == "s" and v:
                        v = shared[int(v)]
                    cells.append("<td>%s</td>" % html.escape(v or ""))
                parts.append("<tr>%s</tr>" % "".join(cells))
            parts.append("</table>")
    return "".join(parts)


def load_as_html(path):
    """Return the document's content as simple HTML (for reflow mode), or None."""
    ext = path.suffix.lower()
    if ext in TEXTUTIL_TYPES:
        return textutil_to_html(path)
    if ext in HTML_TYPES:
        return html_body(path.read_text(errors="replace"))
    if ext in TEXT_TYPES:
        return text_to_html(path.read_text(errors="replace"))
    if ext == ".pptx":
        return pptx_to_html(path)
    if ext == ".xlsx":
        return xlsx_to_html(path)
    if ext in MUPDF_TYPES:
        with fitz.open(path) as doc:
            return pdf_like_to_html(doc)
    return None


def html_to_pdf(body, width=612, height=792, margin=54, css=""):
    """Lay HTML out onto pages with MuPDF's Story engine; returns an open fitz document."""
    story = fitz.Story(html=body, user_css=css)
    buf = io.BytesIO()
    writer = fitz.DocumentWriter(buf)
    box = fitz.Rect(0, 0, width, height)
    more = True
    while more:
        dev = writer.begin_page(box)
        more, _ = story.place(box + (margin, margin, -margin, -margin))
        story.draw(dev)
        writer.end_page()
    writer.close()
    return fitz.open("pdf", buf.getvalue())


def load_as_pages(path):
    """Return the document as a fitz document of real pages (for page mode)."""
    ext = path.suffix.lower()
    if ext in MUPDF_TYPES or ext in IMAGE_TYPES - {".heic"}:
        return fitz.open(path)
    if ext == ".heic":  # MuPDF can't read HEIC; let macOS's sips turn it into PNG
        tmp = Path(tempfile.mkdtemp()) / "img.png"
        subprocess.run(["sips", "-s", "format", "png", str(path), "--out", str(tmp)],
                       capture_output=True, check=True)
        return fitz.open(tmp)
    body = load_as_html(path)
    if body is None:
        raise ValueError("unsupported file type " + ext)
    return html_to_pdf(body, css="body{font-family:sans-serif;font-size:11pt}")


# ------------------------------------------------------------------ making images

def reflow_images(body, font_size, scale, label):
    """Lay the text out at screen size in large type, one image per screen."""
    margin, footer = 6, 10
    css = (
        "* {font-family: sans-serif; font-size: %dpx; line-height: 1.2;}"
        "p {margin: 0 0 %dpx 0;}"
        "h1, h2, h3, h4, b, strong {font-weight: bold;}"
        "h1 {font-size: %dpx;} h2 {font-size: %dpx;}"
        "p.src {color: #777; font-size: %dpx; text-align: center;}"
        "table {border-collapse: collapse;} td {border: 1px solid #999; padding: 1px 3px;}"
        "img {display: none;}"
    ) % (font_size, font_size // 2, font_size + 4, font_size + 2, max(9, font_size - 5))
    story = fitz.Story(html=body, user_css=css)
    buf = io.BytesIO()
    writer = fitz.DocumentWriter(buf)
    box = fitz.Rect(0, 0, SCREEN_W, SCREEN_H)
    where = box + (margin, margin, -margin, -margin - footer)
    more = True
    while more:
        dev = writer.begin_page(box)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()

    doc = fitz.open("pdf", buf.getvalue())
    total = len(doc)
    for i, page in enumerate(doc, 1):
        tag = "%s  %d/%d" % (label, i, total)
        page.insert_text((margin, SCREEN_H - 3), tag, fontsize=8, color=(0.45, 0.45, 0.45))
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        yield Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def content_box(img):
    """Find the area that isn't blank margin."""
    gray = img.convert("L").point(lambda v: 255 if v < 235 else 0)
    box = gray.getbbox()
    if not box:
        return (0, 0, img.width, img.height)
    pad = 8
    return (max(0, box[0] - pad), max(0, box[1] - pad),
            min(img.width, box[2] + pad), min(img.height, box[3] + pad))


def page_images(doc, scale, fit="width", zoom=1):
    """Show each page in order. fit="width": the page fills the screen's width and is
    cut top-to-bottom into screens, with each cut placed in a blank gap between lines.
    fit="page": the whole page shrunk onto one screen. zoom>1: older side-by-side tiles."""
    out_w, out_h = SCREEN_W * scale, SCREEN_H * scale
    for page in doc:
        # render big enough that the result is sharp
        render_scale = max(1.0, out_w * max(zoom, 1) / page.rect.width) * 2
        pix = page.get_pixmap(matrix=fitz.Matrix(render_scale, render_scale), alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        img = img.crop(content_box(img))

        if fit == "page":
            yield fit_on_white(img, out_w, out_h)
        elif zoom > 1:
            yield from side_by_side_tiles(img, zoom, out_w, out_h)
        else:
            yield from width_strips(img, out_w, out_h)


def ink_rows(img, threshold=200):
    """For each row of pixels, how many are dark (0 = blank row)."""
    gray = img.convert("L").point(lambda v: 1 if v < threshold else 0)
    w, data = img.width, gray.tobytes()
    return [data[y * w:(y + 1) * w].count(1) for y in range(img.height)]


def content_bands(img):
    """Split a page into bands of writing separated by blank gaps; each is (top, bottom, left, right)."""
    ink = ink_rows(img)
    gap = max(3, img.height // 150)  # this many blank rows in a row count as a gap
    bands, top, blank = [], None, 0
    for y, n in enumerate(ink + [0] * gap):
        if n:
            if top is None:
                top = y
            blank = 0
        elif top is not None:
            blank += 1
            if blank >= gap:
                bands.append([top, y - blank + 1])
                top = None
    out = []
    for t, b in bands:
        box = img.crop((0, t, img.width, b)).convert("L").point(lambda v: 255 if v < 200 else 0).getbbox()
        if box:
            out.append((t, b, box[0], box[2]))
    return out


def width_strips(img, out_w, out_h):
    """Show the page top to bottom, zoomed in as far as each part allows.
    Blocks of writing are grouped into screens; narrow parts (handwriting, graphs) get bigger.
    Cuts only happen in blank space, so no line is split between two screens."""
    pad = max(4, img.width // 100)
    base = out_w / img.width            # zoom that fits the whole page width
    max_zoom = base * 2.2               # don't blow tiny bits up to giant size
    bands = content_bands(img)

    def zoom_for(group):
        left = max(0, min(b[2] for b in group) - pad)
        right = min(img.width, max(b[3] for b in group) + pad)
        top, bottom = max(0, group[0][0] - pad), min(img.height, group[-1][1] + pad)
        z = min(out_w / (right - left), out_h / (bottom - top), max_zoom)
        return z, (left, top, right, bottom)

    i = 0
    while i < len(bands):
        group = [bands[i]]
        z, box = zoom_for(group)
        # keep adding blocks while the screen stays at least as zoomed as the plain page-width view
        while i + len(group) < len(bands):
            z2, box2 = zoom_for(group + [bands[i + len(group)]])
            if z2 < max(base, z * 0.8):
                break
            group.append(bands[i + len(group)])
            z, box = z2, box2
        i += len(group)

        if z >= base * 0.999:
            yield place(img.crop(box), z, out_w, out_h)
        else:  # a single block too tall to fit (e.g. a big graph): page-width slices of it
            part = img.crop((0, box[1], img.width, box[3]))
            yield from tall_slices(part, out_w, out_h)


def place(region, z, out_w, out_h):
    region = region.resize((max(1, round(region.width * z)), max(1, round(region.height * z))), Image.LANCZOS)
    canvas = Image.new("RGB", (out_w, out_h), "white")
    canvas.paste(region, ((out_w - region.width) // 2, 0))
    return canvas


def tall_slices(img, out_w, out_h):
    h = max(1, round(img.height * out_w / img.width))
    img = img.resize((out_w, h), Image.LANCZOS)
    ink = ink_rows(img)
    top = 0
    while top < h:
        cut = h if h - top <= out_h else min(range(top + out_h, top + int(out_h * 0.6) - 1, -1), key=lambda y: ink[y])
        canvas = Image.new("RGB", (out_w, out_h), "white")
        canvas.paste(img.crop((0, top, out_w, cut)), (0, 0))
        yield canvas
        top = cut if cut == h or ink[cut - 1] == 0 else cut - int(out_h * 0.08)


def side_by_side_tiles(img, zoom, out_w, out_h):
    tile_w = img.width / zoom
    tile_h = tile_w * SCREEN_H / SCREEN_W
    overlap = 0.08  # tiles share a little edge so no line is lost between them
    step_x = tile_w * (1 - overlap)
    step_y = tile_h * (1 - overlap)
    y = 0.0
    while True:
        for col in range(zoom):
            x = min(col * step_x, img.width - tile_w)
            tile = img.crop((int(x), int(y), int(x + tile_w), int(min(y + tile_h, img.height))))
            yield fit_on_white(tile, out_w, out_h, top=True)
        if y + tile_h >= img.height:
            break
        y += step_y


def fit_on_white(img, w, h, top=False):
    r = min(w / img.width, h / img.height)
    img = img.resize((max(1, round(img.width * r)), max(1, round(img.height * r))), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), "white")
    canvas.paste(img, ((w - img.width) // 2, 0 if top else (h - img.height) // 2))
    return canvas



# ------------------------------------------------------------- .tns (calculator file)
#
# A .tns holds a small Lua "document viewer" program with every page packed inside it.
# Pages are stored at two sizes: fitting the screen's width, and 2x zoomed in.
# On the calculator: up/down scroll, Enter (or click) zooms, left/right pan or turn pages.
# Luna (open source, github.com/ndless-nspire/Luna) turns the Lua program into a .tns.

TNS_W, TNS_H = 318, 212    # the space a Lua program gets on the handheld screen
TNS_ZOOM = 2               # the zoomed-in level is this many times bigger
TNS_BAND = 96              # pages are stored in strips this tall, decoded only when visible
TNS_MAX_CHARS = 1_400_000  # about this much picture data per .tns (calculator memory)
B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

VIEWER_LUA = r"""platform.apiLevel = '2.0'
-- Document viewer made by Nspire Convert.
-- up/down: scroll   Enter or click: zoom   left/right: pan, or turn page   Tab: next page
local A = "%(alphabet)s"
local V = {}
for i = 1, 64 do V[A:byte(i)] = i - 1 end
local P = {}
%(pages)s
local W, H = 318, 212
local pg, lv, x, y = 1, 1, 0, 0
local cache, info, infoOn = {}, "", true

local function u32(n) return string.char(n %% 256, math.floor(n / 256) %% 256, math.floor(n / 65536) %% 256, 0) end

-- turn one packed strip back into a picture
local function build(L, b)
  local pal, d, parts, k, i, n = {}, b.d, {}, 0, 1, #b.d
  for j = 1, #b.c, 3 do  -- palette: 3 letters per color
    local p, q, r = b.c:byte(j, j + 2)
    local v = 32768 + (V[p] * 64 + V[q]) * 64 + V[r]
    pal[#pal + 1] = string.char(v %% 256, math.floor(v / 256))
  end
  while i <= n do
    local v = V[d:byte(i)]
    k = k + 1
    if v < 16 then parts[k] = pal[v + 1]; i = i + 1
    elseif v < 32 then parts[k] = string.rep(pal[v - 15], V[d:byte(i + 1)] + 2); i = i + 2
    else parts[k] = string.rep(pal[v - 31], V[d:byte(i + 1)] * 64 + V[d:byte(i + 2)] + 66); i = i + 3 end
  end
  return image.new(u32(L.w) .. u32(b.h) .. "\0\0\0\0" .. u32(L.w * 2) .. "\16\0\1\0" .. table.concat(parts))
end

local function level() return P[pg][lv] end
local function clamp()
  local L = level()
  x = math.floor(math.max(0, math.min(x, L.w - W)) + 0.5)
  y = math.floor(math.max(0, math.min(y, L.h - H)) + 0.5)
end
local function note()
  local z = (#P[pg] > 1) and (lv == 1 and "  fit" or "  zoom") or ""
  info = "page " .. pg .. "/" .. #P .. z
  infoOn = true
  timer.start(1.5)
  platform.window:invalidate()
end
local function turn(n, atBottom)
  if n < 1 or n > #P then return end
  pg, x = n, 0
  if lv > #P[pg] then lv = #P[pg] end
  y = atBottom and level().h or 0
  clamp(); cache = {}; collectgarbage(); note()
end
local function zoom(to, cx, cy)
  if to < 1 or to > #P[pg] or to == lv then return end
  local L = level()
  cx, cy = cx or W / 2, cy or H / 2
  local fx, fy = (x + cx) / L.w, (y + cy) / L.h
  lv = to
  L = level()
  x, y = fx * L.w - cx, fy * L.h - cy
  clamp(); cache = {}; collectgarbage(); note()
end
local function scroll(dy)
  local L = level()
  if dy > 0 and y + H >= L.h then turn(pg + 1, false)
  elseif dy < 0 and y <= 0 then turn(pg - 1, true)
  else y = y + dy; clamp(); platform.window:invalidate() end
end
local function pan(dx)
  local L = level()
  if L.w <= W then turn(pg + (dx > 0 and 1 or -1), dx < 0); return end
  if dx > 0 and x + W >= L.w then x = 0; scroll(math.floor(H * 0.8)); return end
  if dx < 0 and x <= 0 then return end
  x = x + dx; clamp(); platform.window:invalidate()
end

function on.resize(w, h) W, H = w, h; clamp(); cache = {}; platform.window:invalidate() end
function on.construction() note() end
function on.timer() timer.stop(); infoOn = false; platform.window:invalidate() end
function on.arrowKey(k)
  if k == "down" then scroll(math.floor(H * 0.8))
  elseif k == "up" then scroll(-math.floor(H * 0.8))
  elseif k == "right" then pan(math.floor(W * 0.8))
  else pan(-math.floor(W * 0.8)) end
end
function on.enterKey() if lv < #P[pg] then zoom(lv + 1) else zoom(1) end end
function on.mouseUp(mx, my) if lv < #P[pg] then zoom(lv + 1, mx, my) else zoom(1, mx, my) end end
function on.escapeKey() zoom(1) end
function on.charIn(c) if c == "+" or c == "*" then zoom(lv + 1) elseif c == "-" then zoom(lv - 1) end end
function on.tabKey() turn(pg + 1, false) end
function on.backtabKey() turn(pg - 1, false) end
function on.backspaceKey() turn(pg - 1, false) end

function on.paint(gc)
  gc:setColorRGB(255, 255, 255)
  gc:fillRect(0, 0, W, H)
  local L = level()
  local ox = (L.w < W) and math.floor((W - L.w) / 2) or -x
  local top, keep = 0, {}
  for i, b in ipairs(L.b) do
    local sy = top - y
    if sy < H and sy + b.h > 0 then
      keep[i] = cache[i] or build(L, b)
      gc:drawImage(keep[i], ox, sy)
    end
    top = top + b.h
  end
  cache = keep
  if L.h > H then  -- thin scroll bar on the right
    gc:setColorRGB(150, 150, 150)
    gc:fillRect(W - 3, math.floor(y / L.h * H), 3, math.max(6, math.floor(H / L.h * H)))
  end
  if infoOn then
    gc:setFont("sansserif", "r", 9)
    local tw, th = gc:getStringWidth(info), gc:getStringHeight(info)
    gc:setColorRGB(60, 60, 60)
    gc:fillRect(W - tw - 12, H - th - 6, tw + 8, th + 4)
    gc:setColorRGB(255, 255, 255)
    gc:drawString(info, W - tw - 8, H - th - 4, "top")
  end
end
"""


def b64_number(n, digits):
    return "".join(B64[(n >> (6 * i)) & 63] for i in reversed(range(digits)))


def encode_strip(img):
    """Pack a strip of picture as text: up to 16 colors, then runs of same-colored pixels."""
    img = img.convert("RGB")
    # near-white paper (scans, light gray) becomes pure white: much smaller and cleaner
    img = Image.eval(img, lambda v: 255 if v > 232 else v)
    q = img.quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    rgb = q.getpalette()[: 16 * 3]
    colors = "".join(b64_number(((rgb[i] >> 3) << 10) | ((rgb[i + 1] >> 3) << 5) | (rgb[i + 2] >> 3), 3)
                     for i in range(0, len(rgb), 3))
    data, out, i, n = q.tobytes(), [], 0, img.width * img.height
    while i < n:
        j = i
        while j < n and data[j] == data[i] and j - i < 4161:
            j += 1
        run, c = j - i, data[i]
        if run == 1:
            out.append(B64[c])
        elif run <= 65:
            out.append(B64[16 + c] + B64[run - 2])
        else:
            out.append(B64[32 + c] + b64_number(run - 66, 2))
        i = j
    return '{h=%d, c="%s", d="%s"}' % (img.height, colors, "".join(out))


def encode_level(img):
    strips = [encode_strip(img.crop((0, t, img.width, min(t + TNS_BAND, img.height))))
              for t in range(0, img.height, TNS_BAND)]
    return "{w=%d, h=%d, b={%s}}" % (img.width, img.height, ", ".join(strips))


def encode_page(img, zoomable):
    """One page for the viewer: fit-to-width, plus a 2x level if it's a real document page."""
    if not zoomable:
        return "{%s}" % encode_level(fit_on_white(img.convert("RGB"), TNS_W, TNS_H, top=True))
    levels = []
    for z in (1, TNS_ZOOM):
        w = TNS_W * z
        levels.append(encode_level(img.resize((w, max(1, round(img.height * w / img.width))), Image.LANCZOS)))
    return "{%s}" % ", ".join(levels)


def tns_page_images(doc):
    """Each page of the document as one sharp, margin-trimmed picture (for the zoomable viewer)."""
    for page in doc:
        s = TNS_W * TNS_ZOOM * 1.5 / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(s, s), alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        yield img.crop(content_box(img))


def find_luna():
    here = Path(__file__).resolve().parent
    for p in (here / "luna", here / "app_source" / "luna" / "luna"):
        if p.is_file():
            return p
    raise FileNotFoundError("the Luna tool is missing, so no .tns could be made")


def write_tns(pages, out_dir, stem):
    """pages: list of (picture, zoomable). Saves one or more .tns files; returns their paths."""
    luna = find_luna()
    for old in out_dir.glob(stem + "*.tns"):
        old.unlink()
    chunks, cur, size = [], [], 0
    for img, zoomable in pages:
        packed = encode_page(img, zoomable)
        if cur and size + len(packed) > TNS_MAX_CHARS:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(packed)
        size += len(packed)
    if cur:
        chunks.append(cur)

    made = []
    for k, chunk in enumerate(chunks, 1):
        lua = VIEWER_LUA % {"alphabet": B64,
                            "pages": "\n".join("P[%d] = %s" % (i, p) for i, p in enumerate(chunk, 1))}
        name = stem + ("" if len(chunks) == 1 else "_part%d" % k) + ".tns"
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "viewer.lua"
            src.write_text(lua)
            subprocess.run([str(luna), str(src), str(out_dir / name)], capture_output=True, check=True)
        made.append(out_dir / name)
    return made


# --------------------------------------------------------------------------- main

def convert(path, args):
    path = Path(path).expanduser()
    if not path.is_file():
        raise FileNotFoundError("file not found")
    stem = re.sub(r"[^A-Za-z0-9]+", "_", path.stem).strip("_")[:20] or "doc"
    out_dir = Path(args.out).expanduser() if args.out else path.parent / (stem + "_nspire")
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.tns:  # make the pictures exactly the size a calculator program gets
        global SCREEN_W, SCREEN_H
        SCREEN_W, SCREEN_H = TNS_W, TNS_H
    for old in out_dir.glob(stem + "_[0-9][0-9][0-9].*"):  # clear a previous run's images
        old.unlink()
    scale = 2 if args.hd else 1
    ext = path.suffix.lower()

    mode = args.mode
    body = None
    if mode == "reflow":
        if ext in IMAGE_TYPES:
            mode = "page"
        else:
            body = load_as_html(path)
            plain = re.sub(r"<[^>]+>|— (page|slide|sheet) \d+ —", "", body or "")
            if len(plain.strip()) < 20:  # scanned PDF or picture-only: no text to reflow
                print("  (no text found, so keeping the pages as pictures)")
                mode = "page"

    if mode == "reflow":
        images = reflow_images(body, args.font_size, scale, stem[:14])
    else:
        fit = "page" if ext in IMAGE_TYPES and args.fit == "width" and not args.zoom else args.fit  # a photo fits on one screen
        images = page_images(load_as_pages(path), scale, fit, args.zoom or 1)

    count, kept = 0, []
    for count, img in enumerate(images, 1):
        img = img.convert("L").convert("RGB") if args.gray else img
        name = out_dir / ("%s_%03d.%s" % (stem, count, args.format))
        if args.format == "jpg":
            img.save(name, quality=95, subsampling=0)
        else:
            img.save(name, optimize=True)
        if args.tns:
            kept.append(img)
    if args.tns and kept:
        if mode == "page":  # whole pages, zoomable on the calculator
            tns_pages = [(img, True) for img in tns_page_images(load_as_pages(path))]
        else:               # big-text screens are already sized for the calculator
            tns_pages = [(img, False) for img in kept]
        for t in write_tns(tns_pages, out_dir, stem):
            print("  calculator file: %s" % t.name)
    print("  %d images (%s mode) -> %s" % (count, mode, out_dir))
    return out_dir


def main():
    p = argparse.ArgumentParser(description="Convert documents into TI-Nspire-sized images.")
    p.add_argument("files", nargs="+", help="documents to convert")
    p.add_argument("--mode", choices=["reflow", "page"], default="reflow",
                   help="reflow = big re-laid-out text (default); page = original look, page by page")
    p.add_argument("--font-size", type=int, default=16, help="reflow text size in pixels (default 16)")
    p.add_argument("--fit", choices=["width", "page"], default="width",
                   help="page mode: width = page fills the screen's width, shown top to bottom (default); page = whole page on one screen")
    p.add_argument("--zoom", type=int, help="page mode: cut each page into this many tiles side by side instead")
    p.add_argument("--format", choices=["png", "jpg"], default="jpg", help="image type (default jpg)")
    p.add_argument("--hd", action="store_true", help="make 640x480 images instead of 320x240")
    p.add_argument("--gray", action="store_true", help="black-and-white images (for older non-CX models)")
    p.add_argument("--tns", action="store_true", help="also make a .tns calculator file you can send straight to the TI-Nspire")
    p.add_argument("--out", help="folder to save into (default: next to the document)")
    args = p.parse_args()

    failed = 0
    for f in args.files:
        print(Path(f).name)
        try:
            convert(f, args)
        except Exception as e:  # keep going with the other files
            failed += 1
            print("  could not convert: %s" % e)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
