# Physics solver for TI-Nspire CX II
# 2-D motion the way a first physics class does it:
# x / y up / y down table, g = 10, up is +.
# Arrows move, enter picks, esc goes back one screen.
from math import sin, cos, atan, sqrt, radians, degrees
from ti_draw import *
from ti_system import get_key

W = 318
H = 212
G = 10.0
CW = 7  # rough width of one letter, for centering
ROWS = ["Vo", "Vf", "Vavg", "dV", "d", "t", "a"]
NEG = ("-", "−", "(-)", "neg")
DATA = [["", ""]]  # Desmos rows, kept while the program runs

NAVY = (24, 54, 120)
ACCENT = (0, 100, 210)
INK = (25, 25, 25)
MUTED = (110, 110, 110)
LINE = (200, 200, 200)
SOFT = (231, 238, 250)
WHITE = (255, 255, 255)
RED = (200, 30, 30)
ROCK = (212, 212, 212)


# ---------- numbers ----------

def q(x):
    # Round to 2 places. Each step uses the rounded number,
    # so the screen matches doing it by hand.
    return round(x, 2)


def r(x):
    # Text for the screen: 2 places, no "-0", no ".0"
    x = q(x)
    if x == int(x):
        return str(int(x))
    return str(x)


def r4(x):
    return str(round(x, 4))


def pm(b):
    # " + 2" or " - 2" (nothing for 0)
    if q(b) < 0:
        return " - " + r(-b)
    if q(b) > 0:
        return " + " + r(b)
    return ""


def eq(m, b, xname):
    return "y = " + r(m) + xname + pm(b)


# ---------- drawing ----------

def col(c):
    set_color(c[0], c[1], c[2])


def pen(size):
    try:
        set_pen(size, "solid")
    except Exception:
        pass


def text(x, y, s, c=INK):
    col(c)
    draw_text(int(x), int(y), s)


def bold(x, y, s, c=INK):
    # Drawn twice, 1 pixel apart, so it looks bold
    text(x, y, s, c)
    text(x + 1, y, s, c)


def line(x1, y1, x2, y2, c=LINE):
    col(c)
    draw_line(int(x1), int(y1), int(x2), int(y2))


def box(x, y, w, h, c):
    col(c)
    fill_rect(int(x), int(y), int(w), int(h))


def frame(x, y, w, h, c):
    col(c)
    draw_rect(int(x), int(y), int(w), int(h))


def mark(x, y, w, s):
    # A highlighted answer line: blue text on a light band
    box(x, y - 14, w, 19, SOFT)
    box(x, y - 14, 3, 19, ACCENT)
    text(x + 8, y, s, ACCENT)


def scroll(y, h, top, shown, total):
    # Thin scroll bar on the right edge
    box(W - 7, y, 3, h, LINE)
    th = max(10, h * shown // total)
    box(W - 7, y + (h - th) * top // max(1, total - shown), 3, th, ACCENT)


def start(title, right=""):
    # New screen with the title bar
    try:
        use_buffer()
    except Exception:
        pass
    box(0, 0, W, H, WHITE)
    box(0, 0, W, 24, NAVY)
    box(0, 24, W, 2, ACCENT)
    bold(8, 18, title, WHITE)
    if right:
        text(W - 8 - CW * len(right), 18, right, WHITE)


def finish(hint):
    # Key hints at the bottom, then show the screen
    box(0, H - 21, W, 21, SOFT)
    line(0, H - 22, W, H - 22)
    text(8, H - 6, hint, (60, 60, 60))
    try:
        paint_buffer()
    except Exception:
        pass


def key():
    while True:
        k = get_key()
        if k:
            return "enter" if k in ("return", "center") else k


# ---------- menu ----------

def menu():
    items = [("Angled launch off a cliff", angled),
             ("Horizontal launch", horizontal),
             ("Add vectors (N, S, E, W)", add_vectors),
             ("Desmos: data + regressions", desmos),
             ("Average trials", average),
             ("Help: which one? + formulas", help_page)]
    ys = [32, 56, 80, 110, 134, 164]
    i = 0
    while True:
        start("PHYSICS SOLVER", "g = 10")
        line(10, 106, W - 10, 106)
        line(10, 160, W - 10, 160)
        for n in range(6):
            y = ys[n]
            if n == i:
                box(6, y, W - 12, 22, SOFT)
                box(6, y, 3, 22, ACCENT)
                box(14, y + 3, 16, 16, ACCENT)
                text(18, y + 16, str(n + 1), WHITE)
                bold(38, y + 16, items[n][0])
            else:
                box(14, y + 3, 16, 16, LINE)
                text(18, y + 16, str(n + 1))
                text(38, y + 16, items[n][0])
        finish("1-6 or arrows + enter: open    esc: quit")
        k = key()
        if k == "up":
            i = (i - 1) % 6
        elif k == "down":
            i = (i + 1) % 6
        elif k in ("1", "2", "3", "4", "5", "6"):
            i = int(k) - 1
            items[i][1]()
        elif k == "enter":
            items[i][1]()
        elif k == "esc":
            return


# ---------- typing numbers ----------

def typed(v, k, fresh):
    # One key on a number box: the new text, or None if k is not
    # a typing key. In a fresh box the first key starts over.
    if k == "del":
        return "" if fresh else v[:-1]
    if k == "clear":
        return ""
    if fresh:
        v = ""
    if k in NEG:
        return v[1:] if v[:1] == "-" else "-" + v
    if len(k) == 1 and (k.isdigit() or k == "."):
        if (k == "." and "." in v) or len(v) >= 9:
            return v
        return v + k
    return None


def cell(x, y, w, h, v, cur, fresh):
    # One number box. The current box is blue; a fresh one is
    # filled in, meaning typing replaces it.
    if cur and fresh and v:
        box(x, y, w, h, ACCENT)
        text(x + 7, y + h - 6, v, WHITE)
        return
    box(x, y, w, h, SOFT if cur else WHITE)
    frame(x, y, w, h, ACCENT if cur else LINE)
    text(x + 7, y + h - 6, v + ("_" if cur else ""))


def form(title, labels, vals=None, blank=False, note="", check=None,
         one_of=()):
    # Number boxes. Returns (numbers, texts) or None for esc.
    # With blank=True an empty box gives None. Typing in one box
    # of one_of clears the others (only one can be filled).
    # check(nums) returns None, or (message, box to fix).
    n = len(labels)
    vals = list(vals) if vals else [""] * n
    gap = 40 if n <= 3 else (34 if n == 4 else 28)
    bh = 26 if n <= 4 else 24
    top = 36 if n <= 4 else 32
    i = 0
    fresh = True
    err = ""
    while True:
        start(title)
        for f in range(n):
            y = top + f * gap
            if f == i:
                bold(10, y + bh - 7, labels[f], ACCENT)
            else:
                text(10, y + bh - 7, labels[f])
            cell(170, y, 138, bh, vals[f], f == i, fresh)
        if err:
            text(10, H - 30, err, RED)
        elif note:
            text(10, H - 30, note, MUTED)
        last = i == n - 1
        finish(("enter: SOLVE" if last else "enter: next box") +
               "   del: erase   esc: back")
        k = key()
        err = ""
        t = typed(vals[i], k, fresh)
        if t is not None:
            vals[i] = t
            fresh = False
            if t and i in one_of:
                for o in one_of:
                    if o != i:
                        vals[o] = ""
        elif k == "esc":
            return None
        elif k in ("up", "left") and i > 0:
            i -= 1
            fresh = True
        elif k in ("down", "right", "tab") and i < n - 1:
            i += 1
            fresh = True
        elif k == "enter" and not last:
            i += 1
            fresh = True
        elif k == "enter":
            nums = []
            for f in range(n):
                if blank and vals[f] == "":
                    nums.append(None)
                    continue
                try:
                    nums.append(float(vals[f]))
                except ValueError:
                    err = "Type a number for " + labels[f]
                    i = f
                    fresh = True
                    break
            bad = None if err or not check else check(nums)
            if bad:
                err, i = bad
                fresh = True
            if not err:
                return nums, vals


def ask(title, lines, hint, keys):
    # A simple question screen; returns the key pressed
    while True:
        start(title)
        y = 58
        for s in lines:
            text(12, y, s)
            y += 22
        finish(hint)
        k = key()
        if k in keys:
            return k


# ---------- result pages ----------
# ("text", title, lines)       "*" answer, "#" gray heading,
#                              a tab starts a second column
# ("part", title, vals, work)  table row in class order + work
# ("ans", title, [(label, value), ...])
# ("draw", title, fn)          a picture
# ("act", title, lines, fn)    enter runs fn

def draw_lines(lines, top):
    y = 46
    for s in lines[top:top + 8]:
        if s[:1] == "*":
            mark(4, y, W - 16, s[1:])
            y += 19
            continue
        c = INK
        if s[:1] == "#":
            c = MUTED
            s = s[1:]
        parts = s.split("\t")
        text(12, y, parts[0], c)
        if len(parts) > 1:
            text(160, y, parts[1], c)
        y += 19
    more = len(lines) > top + 8
    if more or top:
        scroll(30, 155, top, 8, len(lines))
    return more


def draw_part(vals, work):
    for n in range(7):
        y = 30 + n * 22
        if n % 2 == 0:
            box(4, y, 148, 22, SOFT)
        text(12, y + 16, ROWS[n])
        text(66, y + 16, r(vals[n]), ACCENT)
    line(158, 32, 158, 184)
    y = 46
    for s in work:
        if s[:1] == "*":
            mark(162, y, W - 166, s[1:])
        else:
            text(170, y, s)
        y += 19


def draw_answers(items):
    y = 34
    for lab, val in items:
        box(6, y, W - 12, 44, SOFT)
        box(6, y, 4, 44, ACCENT)
        text(18, y + 17, lab, MUTED)
        bold(18, y + 37, val, ACCENT)
        y += 50


def view(pages):
    # Result pages: < > change page, esc goes back
    p = 0
    top = 0
    while True:
        page = pages[p]
        kind = page[0]
        many = len(pages) > 1
        start(page[1], str(p + 1) + "/" + str(len(pages)) if many else "")
        more = False
        if kind == "part":
            draw_part(page[2], page[3])
        elif kind == "ans":
            draw_answers(page[2])
        elif kind == "draw":
            pen("thin")
            page[2]()
            pen("thin")
        else:
            more = draw_lines(page[2], top)
        hint = []
        if kind == "act":
            hint.append("enter: start")
        if many:
            hint.append("< >: pages")
        if more or top:
            hint.append("up/down: scroll")
        hint.append("esc: back")
        finish("  ".join(hint))
        k = key()
        if k == "esc":
            return
        elif k == "enter" and kind == "act":
            page[3]()
        elif k in ("right", "enter", "tab") and p < len(pages) - 1:
            p += 1
            top = 0
        elif k == "left" and p > 0:
            p -= 1
            top = 0
        elif k == "down" and more:
            top += 1
        elif k == "up" and top > 0:
            top -= 1


# ---------- pictures ----------

def path_pic(info1, info2, h, vy0, vx, t_all, rng):
    # The flight: facts on top, cliff on the left, ground below
    text(12, 44, info1)
    text(12, 62, info2, MUTED)
    gy = 158
    ox = 46 if h > 0 else 16
    top = h + (vy0 * vy0 / (2 * G) if vy0 > 0 else 0)
    sx = (W - ox - 16) / rng if rng > 0 else 1
    sy = 84.0 / top if top > 0 else 1
    line(4, gy, W - 4, gy, MUTED)
    if h > 0:
        ch = h * sy
        box(0, gy - ch, ox, ch, ROCK)
        lab = r(h) + " m"
        text(4, gy - ch / 2 + 5 if ch >= 18 else gy - ch - 4, lab)
    box(ox - 2, gy - h * sy - 2, 5, 5, ACCENT)
    col(ACCENT)
    pen("medium")
    px = ox
    py = gy - h * sy
    for k in range(1, 31):
        t = t_all * k / 30
        nx = ox + vx * t * sx
        ny = gy - (h + vy0 * t - G / 2 * t * t) * sy
        draw_line(int(px), int(py), int(nx), int(ny))
        px = nx
        py = ny
    pen("thin")
    line(px, gy - 5, px, gy + 5, INK)
    lab = "range " + r(rng) + " m"
    text(max(4, (ox + px) / 2 - CW * len(lab) / 2), gy + 18, lab)


def tri(bx, by, bw, bh, x, y, xl, yl, hl, al):
    # Right triangle in a box: x leg, y leg, long side in blue.
    # xl / yl label the legs, hl the long side, al the angle.
    ax = abs(x)
    ay = abs(y)
    ml = CW * len(al) + 12 if al else 10
    mr = CW * len(yl) + 12
    s = min((bw - ml - mr) / ax if ax else 1e9,
            (bh - 40) / ay if ay else 1e9)
    if s >= 1e9:
        return
    padx = (bw - ml - mr - ax * s) / 2
    pady = (bh - 40 - ay * s) / 2
    ox = bx + ml + padx if x >= 0 else bx + bw - ml - padx
    oy = by + bh - 20 - pady if y >= 0 else by + 20 + pady
    ex = ox + x * s
    ey = oy - y * s
    line(ox, oy, ex, oy, MUTED)
    line(ex, oy, ex, ey, MUTED)
    col(ACCENT)
    pen("medium")
    draw_line(int(ox), int(oy), int(ex), int(ey))
    pen("thin")
    box(ex - 3, ey - 3, 7, 7, ACCENT)
    text((ox + ex) / 2 - CW * len(xl) / 2, oy + 16 if y >= 0 else oy - 6, xl)
    text(ex + 6 if x >= 0 else ex - 6 - CW * len(yl), (oy + ey) / 2 + 5, yl)
    if al and ax and ay:
        text(ox - 6 - CW * len(al) if x >= 0 else ox + 6, oy + 5, al, MUTED)
    # Long side label, pushed away from the square corner
    mx = (ox + ex) / 2
    my = (oy + ey) / 2
    dx = mx - ex
    dy = my - oy
    d = sqrt(dx * dx + dy * dy) or 1
    lx = mx + dx / d * 12
    if dx < 0:
        lx -= CW * len(hl)
    bold(lx, my + dy / d * 12 + 5, hl, ACCENT)


def split_pic(v, ang, vx, vy):
    # The launch speed broken into x and y parts
    text(12, 48, "vx = " + r(v) + " cos " + r(ang))
    mark(4, 70, 148, "= " + r(vx) + " m/s")
    text(12, 100, "vy = " + r(v) + " sin " + r(ang))
    mark(4, 122, 148, "= " + r(vy) + " m/s")
    text(12, 152, "Use vx for X,", MUTED)
    text(12, 170, "vy as Vo for " + ("Y UP" if vy > 0 else "Y DOWN"), MUTED)
    tri(160, 30, 150, 156, vx, vy, r(vx), r(vy), r(v), r(ang) + " deg")


# ---------- 1: angled launch ----------

def fall(h, vy0):
    # Time to drop h meters starting at vertical speed vy0
    # (vy0 <= 0). Solves -h = vy0 t - (g/2) t^2
    return (vy0 + sqrt(vy0 * vy0 + 2 * G * h)) / G


def angled_ok(nums):
    v, ang, h = nums
    if v <= 0:
        return "Launch speed must be above 0", 0
    if ang < -90 or ang > 90:
        return "Angle must be from -90 to 90", 1
    if h < 0:
        return "Height can't be below 0", 2
    if h == 0 and ang <= 0:
        return "From the ground, aim above 0 deg", 1
    return None


def angled():
    vals = None
    while True:
        got = form("ANGLED LAUNCH", ["Launch speed (m/s)",
                                     "Angle above horiz.",
                                     "Cliff height (m)"], vals,
                   note="On flat ground? Use height 0", check=angled_ok)
        if got is None:
            return
        nums, vals = got
        view(angled_pages(nums[0], nums[1], nums[2]))


def angled_pages(v, ang, h):
    vx = q(v * cos(radians(ang)))
    vy0 = q(v * sin(radians(ang)))
    pages = [("draw", "BREAK IT UP", lambda: split_pic(v, ang, vx, vy0))]

    if vy0 > 0:
        t_up = q(vy0 / G)
        d_up = q(q(vy0 / 2) * t_up)
        pages.append(("part", "Y UP", [vy0, 0, vy0 / 2, -vy0, d_up, t_up, -G], [
            "Vf = 0 at the top",
            "t = dV / a",
            " = " + r(-vy0) + " / " + r(-G),
            "*t = " + r(t_up),
            "d = Vavg t",
            " = " + r(vy0 / 2) + "(" + r(t_up) + ")",
            "*d = " + r(d_up)]))
        vo = 0.0
    else:
        t_up = 0.0
        d_up = 0.0
        vo = vy0

    drop = q(h + d_up)
    t_dn = q(fall(drop, vo))
    vf = q(vo - G * t_dn)
    if h and d_up:
        work = ["falls " + r(h) + " + " + r(d_up), " = " + r(drop) + " m"]
    else:
        work = ["falls " + r(drop) + " m"]
    work.append("d = Vo t + 1/2 a t^2")
    if vo == 0:
        work.append(r(-drop) + " = " + r(-G / 2) + " t^2")
    else:
        work.append(r(-drop) + " = " + r(vo) + "t - " + r(G / 2) + "t^2")
    work += ["*t = " + r(t_dn), "Vf = Vo + a t", "*Vf = " + r(vf)]
    pages.append(("part", "Y DOWN",
                  [vo, vf, (vo + vf) / 2, vf - vo, -drop, t_dn, -G], work))

    t_all = q(t_up + t_dn)
    rng = q(vx * t_all)
    if t_up:
        work = ["a = 0, V stays", "t = up + down",
                " = " + r(t_up) + " + " + r(t_dn)]
    else:
        work = ["a = 0, V stays", "same t as Y DOWN"]
    work += ["*t = " + r(t_all), "d = V t",
             " = " + r(vx) + "(" + r(t_all) + ")", "*d = " + r(rng)]
    pages.append(("part", "X", [vx, vx, vx, 0, rng, t_all, 0], work))

    pages.append(("ans", "ANSWER", [
        ("Time to hit the ground", r(t_all) + " s"),
        ("Range (x distance)", r(rng) + " m")]))
    info1 = r(v) + " m/s at " + r(ang) + " deg"
    info1 += " off a " + r(h) + " m cliff" if h else " from the ground"
    info2 = ("rises " + r(d_up) + " m,  " if d_up else "") + \
        "in the air " + r(t_all) + " s"
    pages.insert(0, ("draw", "PICTURE",
                     lambda: path_pic(info1, info2, h, vy0, vx, t_all, rng)))
    return pages


# ---------- 2: horizontal launch ----------

def horiz_ok(nums):
    h, vx, x = nums
    if h is None:
        return "Type the cliff height", 0
    if h <= 0:
        return "Height must be above 0", 0
    if (vx is None) == (x is None):
        return "Fill in ONE: speed or distance", 1
    return None


def horizontal():
    vals = None
    while True:
        got = form("HORIZONTAL LAUNCH", ["Cliff height (m)",
                                         "Thrown at (m/s)",
                                         "Lands how far (m)"], vals, True,
                   "Leave the one you want blank", horiz_ok, (1, 2))
        if got is None:
            return
        nums, vals = got
        view(horiz_pages(nums[0], nums[1], nums[2]))


def horiz_pages(h, vx, x):
    t = q(sqrt(2 * h / G))
    vy = q(-G * t)
    pages = [("part", "Y DOWN", [0, vy, vy / 2, vy, -h, t, -G], [
        "Vo = 0 (thrown flat)",
        "d = 1/2 a t^2",
        r(-h) + " = " + r(-G / 2) + " t^2",
        "*t = " + r(t),
        "Vf = a t",
        "*Vf = " + r(vy)])]
    if x is None:
        x = q(vx * t)
        work = ["a = 0, V stays", "same t as Y DOWN", "d = V t",
                " = " + r(vx) + "(" + r(t) + ")", "*d = " + r(x)]
        ans = ("Lands this far out", r(x) + " m")
    else:
        vx = q(x / t)
        work = ["a = 0, V stays", "same t as Y DOWN", "V = d / t",
                " = " + r(x) + " / " + r(t), "*V = " + r(vx)]
        ans = ("Thrown at", r(vx) + " m/s")
    pages.append(("part", "X", [vx, vx, vx, 0, x, t, 0], work))
    pages.append(("ans", "ANSWER", [ans, ("Time in the air", r(t) + " s")]))
    info1 = "thrown flat at " + r(vx) + " m/s off " + r(h) + " m"
    info2 = "in the air " + r(t) + " s"
    pages.insert(0, ("draw", "PICTURE",
                     lambda: path_pic(info1, info2, h, 0, vx, t, x)))
    return pages


# ---------- 3: vectors ----------

def vec_ok(nums):
    e, w, n, s = [v or 0.0 for v in nums]
    if not (e or w or n or s):
        return "Type at least one direction", 0
    if e == w and n == s:
        return "They cancel out: the total is 0", 0
    return None


def add_vectors():
    vals = None
    while True:
        got = form("ADD VECTORS", ["East", "West", "North", "South"], vals,
                   True, "Leave unused directions blank", vec_ok)
        if got is None:
            return
        nums, vals = got
        view(vec_pages([v or 0.0 for v in nums]))


def vec_pages(d):
    e, w, n, s = d
    x = e - w
    y = n - s
    ew = "E" if x >= 0 else "W"
    ns = "N" if y >= 0 else "S"
    ax = abs(x)
    ay = abs(y)
    mag = sqrt(x * x + y * y)
    xl = r(ax) + " " + ew if ax else ""
    yl = r(ay) + " " + ns if ay else ""
    work = [("x = " + r(e) + " E - " + r(w) + " W = " if e and w else "x = ") +
            (xl or "0"),
            ("y = " + r(n) + " N - " + r(s) + " S = " if n and s else "y = ") +
            (yl or "0")]
    work += ["size = sqrt(" + r(ax) + "^2 + " + r(ay) + "^2)",
             "*size = " + r(mag)]
    if ax and ay:
        ang = q(degrees(atan(ay / ax)))
        way = r(ang) + " deg " + ns + " of " + ew
        work += ["angle = tan-1(" + r(ay) + " / " + r(ax) + ")",
                 "*angle = " + way]
        ans = [("Size (magnitude)", r(mag)),
               ("Direction", way),
               ("Same as", r(90 - ang) + " deg " + ew + " of " + ns)]
        al = r(ang) + " deg"
    else:
        way = "straight " + (ew if ax else ns)
        work.append("*" + way)
        ans = [("Size (magnitude)", r(mag)), ("Direction", way)]
        al = ""
    return [("draw", "PICTURE",
             lambda: tri(8, 30, W - 16, 156, x, y, xl, yl, r(mag), al)),
            ("text", "WORK", work),
            ("ans", "ANSWER", ans)]


# ---------- 4: desmos ----------

def fit(xs, ys):
    # Best straight line y = m x + b, and R^2 (like Desmos)
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = 0.0
    sxx = 0.0
    syy = 0.0
    for k in range(n):
        dx = xs[k] - mx
        dy = ys[k] - my
        sxy += dx * dy
        sxx += dx * dx
        syy += dy * dy
    if sxx == 0:
        return 0.0, my, 0.0
    m = sxy / sxx
    r2 = sxy * sxy / (sxx * syy) if syy else 1.0
    return m, my - m * mx, r2


def desmos():
    n = len([row for row in DATA if row != ["", ""]])
    if n:
        k = ask("DESMOS", ["You already typed " + str(n) + " rows.", "",
                           "enter: keep them (fix or add more)",
                           "del: erase them and start new"],
                "enter: keep   del: start new   esc: back",
                ("enter", "del", "esc"))
        if k == "esc":
            return
        if k == "del":
            while DATA:
                DATA.pop()
            DATA.append(["", ""])
    while True:
        got = table_entry(DATA)
        if got is None:
            return
        view(desmos_pages(got[0], got[1]))


def table_entry(rows):
    # Type x, y pairs. Returns (xs, ys) or None for esc.
    i = len(rows) - 1
    j = 0
    top = 0
    fresh = True
    err = ""
    while True:
        if rows[-1] != ["", ""]:
            rows.append(["", ""])
        full = len([row for row in rows if row != ["", ""]])
        top = min(top, i)
        if i > top + 4:
            top = i - 4
        start("DESMOS: TYPE THE DATA",
              str(full) + (" row" if full == 1 else " rows"))
        text(12, 44, "#", MUTED)
        text(42, 44, "x  (time)", MUTED)
        text(178, 44, "y  (distance)", MUTED)
        for n in range(top, min(top + 5, len(rows))):
            y = 50 + (n - top) * 24
            text(12, y + 15, str(n + 1), MUTED)
            cell(36, y, 130, 21, rows[n][0], n == i and j == 0, fresh)
            cell(172, y, 130, 21, rows[n][1], n == i and j == 1, fresh)
        if len(rows) > 5:
            scroll(50, 117, top, 5, len(rows))
        text(12, H - 30, err or "Done? Press enter on an empty row.",
             RED if err else MUTED)
        finish("enter: next   arrows: move   esc: back")
        k = key()
        err = ""
        t = typed(rows[i][j], k, fresh)
        if t is not None:
            rows[i][j] = t
            fresh = False
        elif k == "esc":
            return None
        elif k == "up" and i > 0:
            i -= 1
            fresh = True
        elif k == "down" and i < len(rows) - 1:
            i += 1
            fresh = True
        elif k == "left" and j == 1:
            j = 0
            fresh = True
        elif k in ("right", "tab") and j == 0:
            j = 1
            fresh = True
        elif k == "enter" and rows[i] != ["", ""]:
            if j == 0:
                j = 1
            else:
                i += 1
                j = 0
            fresh = True
        elif k == "enter":
            # Enter on an empty row: done
            xs = []
            ys = []
            for n in range(len(rows)):
                if rows[n] == ["", ""]:
                    continue
                try:
                    xs.append(float(rows[n][0]))
                except ValueError:
                    err = "Row " + str(n + 1) + " needs an x"
                    i, j = n, 0
                    break
                try:
                    ys.append(float(rows[n][1]))
                except ValueError:
                    err = "Row " + str(n + 1) + " needs a y"
                    i, j = n, 1
                    break
            if not err and len(xs) < 3:
                err = "Type at least 3 rows"
            if not err:
                return xs, ys
            fresh = True


def plot(x0, xs, ys, m, b, name, r2, best):
    # One small graph: dots, best-fit line in red, R^2 under it
    y0 = 32
    w = 146
    box(x0, y0, w, 18, NAVY if best else LINE)
    text(x0 + 6, y0 + 14, name, WHITE if best else INK)
    frame(x0, y0, w, 132, NAVY if best else LINE)
    px0 = x0 + 10
    pw = w - 20
    py0 = y0 + 26
    ph = 96
    lo = min(0, min(xs))
    hi = max(0, max(xs))
    if hi == lo:
        hi = lo + 1
    blo = min(0, min(ys))
    bhi = max(0, max(ys))
    if bhi == blo:
        bhi = blo + 1
    sx = pw / (hi - lo)
    sy = ph / (bhi - blo)
    gx = px0 - lo * sx
    gy = py0 + ph + blo * sy
    line(px0, gy, px0 + pw, gy, MUTED)
    line(gx, py0, gx, py0 + ph, MUTED)
    # Red line, cut off at the edges of the graph
    xa = lo
    xb = hi
    if m:
        for yv in (blo, bhi):
            xv = (yv - b) / m
            if (m > 0) == (yv == blo):
                xa = max(xa, xv)
            else:
                xb = min(xb, xv)
    if xa < xb:
        line(gx + xa * sx, gy - (m * xa + b) * sy,
             gx + xb * sx, gy - (m * xb + b) * sy, RED)
    for k in range(len(xs)):
        box(gx + xs[k] * sx - 2, gy - ys[k] * sy - 2, 5, 5, ACCENT)
    if best:
        bold(x0 + 4, 182, "R^2 = " + r4(r2), ACCENT)
    else:
        text(x0 + 4, 182, "R^2 = " + r4(r2), MUTED)


def desmos_pages(xs, ys):
    x2 = [q(x * x) for x in xs]
    m1, b1, r1 = fit(xs, ys)
    m2, b2, r2 = fit(x2, ys)
    win2 = r2 >= r1
    m, b = (m2, b2) if win2 else (m1, b1)
    sq = " x^2" if win2 else " x"
    n = len(xs)

    g1 = ["#IN DESMOS: CLICK +, THEN TABLE",
          "#x1  (time)\ty1  (distance)"]
    g1 += [r(xs[k]) + "\t" + r(ys[k]) for k in range(n)]
    g1 += ["#UNDER THE TABLE, TYPE:",
           "*y1 ~ m1 x1 + b1",
           "#( ~ is Shift + ` )",
           "#DESMOS WILL SHOW:",
           "m1 = " + r(m1) + "\tb1 = " + r(b1),
           "*R^2 = " + r4(r1)]

    g2 = ["#ADD A 2ND TABLE: TIMES SQUARED",
          "#x2  (time^2)\ty2  (distance)"]
    g2 += [r(x2[k]) + "\t" + r(ys[k]) for k in range(n)]
    g2 += ["#UNDER IT, TYPE:",
           "*y2 ~ m2 x2 + b2",
           "#DESMOS WILL SHOW:",
           "m2 = " + r(m2) + "\tb2 = " + r(b2),
           "*R^2 = " + r4(r2)]

    best = ["#R^2: CLOSER TO 1 IS BETTER",
            "Graph 1:  y vs x\t" + r4(r1),
            "Graph 2:  y vs x^2\t" + r4(r2),
            "*Graph " + ("2" if win2 else "1") + " is the better line",
            "#ITS EQUATION",
            "*" + eq(m, b, sq)]

    if win2:
        mean = ["#IF y = DISTANCE AND x = TIME:",
                "d vs t^2 is straight, so it is",
                "speeding up:  d = 1/2 a t^2",
                "slope = 1/2 a,  so  a = 2(slope)",
                "a = 2(" + r(m2) + ")",
                "*a = " + r(2 * q(m2)),
                "#(cm/s^2 if distance is in cm)"]
    else:
        mean = ["#IF y = DISTANCE AND x = TIME:",
                "d vs t is straight, so it moves",
                "at a steady speed:  d = v t",
                "speed = slope",
                "*speed = " + r(m1),
                "#(cm/s if distance is in cm)"]

    def both():
        plot(8, xs, ys, m1, b1, "1: y vs x", r1, not win2)
        plot(164, x2, ys, m2, b2, "2: y vs x^2", r2, win2)

    def use():
        predict(q(m), q(b), win2)

    return [("text", "GRAPH 1 IN DESMOS", g1),
            ("text", "GRAPH 2 IN DESMOS", g2),
            ("draw", "THE TWO GRAPHS", both),
            ("text", "BEST FIT", best),
            ("text", "WHAT IT MEANS", mean),
            ("act", "USE THE EQUATION", [
                "#USING THE BEST FIT:",
                eq(m, b, sq),
                "#FOR QUESTIONS LIKE:",
                "How far does it go in 4 s?",
                "How long to go 200 cm?",
                "*Press enter to work one out"], use)]


def one_blank(nums):
    if (nums[0] is None) == (nums[1] is None):
        return "Fill in ONE box, leave one blank", 0
    return None


def predict(m, b, sq):
    vals = None
    while True:
        got = form("USE THE EQUATION", ["x  (time)", "y  (distance)"], vals,
                   True, "Leave the one you want blank", one_blank, (0, 1))
        if got is None:
            return
        nums, vals = got
        view([("text", "ANSWER", solve_eq(m, b, sq, nums[0], nums[1]))])


def solve_eq(m, b, sq, x, y):
    lines = ["#EQUATION", eq(m, b, " x^2" if sq else " x"), "#WORK"]
    if y is None:
        xx = q(x * x) if sq else x
        if sq:
            lines.append("x^2 = " + r(x) + "^2 = " + r(xx))
        return lines + ["y = " + r(m) + "(" + r(xx) + ")" + pm(b),
                        "*y = " + r(q(m * xx) + b)]
    top = q(y - b)
    lines.append(r(y) + pm(-b) + " = " + r(top))
    if m == 0:
        return lines + ["Slope is 0: no answer"]
    v = q(top / m)
    if not sq:
        return lines + ["*x = " + r(top) + " / " + r(m) + " = " + r(v)]
    lines.append("x^2 = " + r(top) + " / " + r(m) + " = " + r(v))
    if v < 0:
        return lines + ["Below 0: no answer"]
    return lines + ["*x = sqrt(" + r(v) + ") = " + r(sqrt(v))]


# ---------- 5: average trials ----------

def some_typed(nums):
    if [v for v in nums if v is not None]:
        return None
    return "Type at least one trial", 0


def average():
    vals = None
    while True:
        got = form("AVERAGE TRIALS", ["Trial 1", "Trial 2", "Trial 3",
                                      "Trial 4", "Trial 5"], vals, True,
                   check=some_typed)
        if got is None:
            return
        nums, vals = got
        t = [v for v in nums if v is not None]
        total = q(sum(t))
        avg = q(total / len(t))
        view([("text", "AVERAGE", [
            "#ADD THEM UP",
            " + ".join([r(v) for v in t]) + " = " + r(total),
            "#DIVIDE BY " + str(len(t)),
            r(total) + " / " + str(len(t)),
            "*mean = " + r(avg) + " s",
            "#SQUARE IT (FOR A t^2 COLUMN)",
            r(avg) + "^2",
            "*mean^2 = " + r(avg * avg) + " s^2"])])


# ---------- 6: help ----------

def help_page():
    view([("text", "WHICH ONE?", [
        "#LAUNCHED AT AN ANGLE",
        "*1  Angled launch",
        "#THROWN OR ROLLED OFF FLAT",
        "*2  Horizontal launch",
        "#N S E W: WALKS, BOATS, TUGBOATS",
        "*3  Add vectors",
        "#A DATA TABLE TO GRAPH",
        "*4  Desmos",
        "#SEVERAL TIMES FOR ONE DISTANCE",
        "*5  Average trials"]),
        ("text", "TABLE FORMULAS", [
        "vx = v cos(angle)\tvy = v sin(angle)",
        "Vavg = (Vo + Vf) / 2\tdV = Vf - Vo",
        "t = dV / a\td = Vavg t",
        "d = Vo t + 1/2 a t^2",
        "#REMEMBER",
        "X: a = 0\tY: a = -10",
        "Top: Vf = 0\tt = up + down",
        "Y down falls cliff + rise"]),
        ("text", "VECTOR FORMULAS", [
        "x = East - West",
        "y = North - South",
        "size = sqrt(x^2 + y^2)",
        "angle = tan-1(y / x)",
        "#SAY THE DIRECTION LIKE",
        "24 deg N of W:",
        "face W, then turn 24 deg to N"]),
        ("text", "DESMOS", [
        "#MAKE TWO GRAPHS",
        "1: y vs x\t2: y vs x^2",
        "Type  y1 ~ m1 x1 + b1",
        "( ~ is Shift + ` on a keyboard)",
        "#BETTER LINE: R^2 CLOSER TO 1",
        "d vs t^2 wins: speeding up",
        "*a = 2(slope)",
        "d vs t wins: speed = slope"]),
        ("text", "KEYS", [
        "arrows\tmove, change page",
        "enter\tnext box / solve",
        "1 - 6\topen from the menu",
        "del\terase",
        "(-)\tnegative number",
        "esc\tgo back one screen",
        "up / down\tscroll long pages"])])


menu()
