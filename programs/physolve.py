# Physics solver for TI-Nspire CX II, version 7: FORCES
# Force problems the way a first physics class does them:
# 1. draw the free-body diagram, 2. write Fnet = ma with every
# force on it, 3. solve. Weight is W = mg with g = 10, up is +.
# Arrows move, enter picks, esc goes back one screen,
# home or menu quits the program right away.
# Each tool remembers what you typed last, even after quitting.
# (The 2-D motion and Desmos tools are in physolve_2d.)
from math import sqrt
from ti_draw import *
from ti_system import get_key
try:
    from ti_system import store_list, recall_list
except ImportError:
    store_list = recall_list = None

VER = "v7"
W = 318
H = 212
G = 10.0
CW = 7  # rough width of one letter, for centering
NEG = ("-", "−", "(-)", "neg")
EE = ("EE", "E", "e", "ee")
HOME = ("menu", "home")
CH = "0123456789-.e"  # what a number box can hold
LAST = {}  # tool number -> the boxes typed last


class Home(Exception):
    # The home or menu key: drop everything and quit
    pass


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
    # Round the way you would by hand: 2 places, or 3 figures
    # for small numbers (0.00118). Each step uses the rounded
    # number, so the screen matches your paper.
    if x == 0:
        return 0.0
    t = abs(x)
    if t >= 1:
        return round(x, 2)
    d = 2
    while t < 1:
        t *= 10
        d += 1
    return round(x, d)


def r(x):
    # Text for the screen: no "-0", no ".0", 4.9e-7 for tiny ones
    x = q(x)
    if x == int(x):
        return str(int(x))
    t = abs(x)
    if t >= 0.001:
        return str(x)
    e = 0
    while t < 1:
        t *= 10
        e += 1
    return ("-" if x < 0 else "") + r(t) + "e-" + str(e)


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
        if k in HOME:
            raise Home
        if k:
            return "enter" if k in ("return", "center") else k


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
    if k in EE:
        # 4.9e-7 is typed 4.9 EE (-) 7
        return v + "e" if v[-1:].isdigit() and "e" not in v else v
    if k in NEG:
        if v[-1:] == "e":
            return v + "-"
        return v[1:] if v[:1] == "-" else "-" + v
    if len(k) == 1 and (k.isdigit() or k == "."):
        if (k == "." and ("." in v or "e" in v)) or len(v) >= 12:
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
        if kind == "ans":
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


# ---------- remembering what you typed ----------

def remember(n, vals):
    LAST[n] = list(vals)
    out = []
    for v in vals:
        for c in v:
            if c not in CH:
                return
        out.append(len(v))
        out += [CH.index(c) for c in v]
    try:
        store_list("phy7n" + str(n), out)
    except Exception:
        pass


def recall(n, count):
    # The boxes typed last in tool n, or None
    if n in LAST:
        return list(LAST[n])
    try:
        got = [int(round(x)) for x in recall_list("phy7n" + str(n))]
        vals = []
        i = 0
        while i < len(got):
            m = got[i]
            part = got[i + 1:i + 1 + m]
            if m < 0 or len(part) < m:
                return None
            vals.append("".join([CH[c] for c in part]))
            i += 1 + m
        if len(vals) == count:
            LAST[n] = vals
            return list(vals)
    except Exception:
        pass
    return None


def tool(n, title, labels, note, check, one_of, pages):
    # Boxes -> pages; esc on the pages comes back to the boxes
    vals = recall(n, len(labels))
    while True:
        got = form(title, labels, vals, True, note, check, one_of)
        if got is None:
            return
        nums, vals = got
        remember(n, vals)
        view(pages(nums))


# ---------- pictures ----------

def arrow(x1, y1, x2, y2, c):
    col(c)
    pen("medium")
    draw_line(int(x1), int(y1), int(x2), int(y2))
    d = sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) or 1
    ux = (x2 - x1) / d
    uy = (y2 - y1) / d
    for s in (-1, 1):
        draw_line(int(x2), int(y2), int(x2 - 8 * ux + 5 * s * uy),
                  int(y2 - 8 * uy - 5 * s * ux))
    pen("thin")


def fbd(up, down, left, right, note):
    # Free-body diagram: a box with a labeled arrow for each force.
    # The arrows are not to scale (same as in class).
    cx = 159
    cy = 110
    box(cx - 26, cy - 20, 52, 40, ROCK)
    frame(cx - 26, cy - 20, 52, 40, INK)
    if up:
        arrow(cx, cy - 20, cx, cy - 60, ACCENT)
        text(cx - CW * len(up) / 2, cy - 66, up)
    if down:
        arrow(cx, cy + 20, cx, cy + 58, ACCENT)
        text(cx - CW * len(down) / 2, cy + 74, down)
    if left:
        arrow(cx - 26, cy, cx - 74, cy, RED)
        text(max(2, cx - 80 - CW * len(left)), cy + 5, left)
    if right:
        arrow(cx + 26, cy, cx + 74, cy, ACCENT)
        text(cx + 80, cy + 5, right)
    text(8, 160, note, MUTED)


def stack_pic(push, blocks):
    # blocks: (mass, normal force under it), top one first
    cx = 120
    n = len(blocks)
    line(20, 176, 198, 176, INK)
    for k in range(n):
        m, fn = blocks[k]
        wd = 150 - 34 * (n - 1 - k)
        y = 176 - 34 * (n - k)
        box(cx - wd / 2, y, wd, 33, ROCK)
        frame(cx - wd / 2, y, wd, 33, INK)
        t = r(m) + " kg"
        text(cx - CW * len(t) / 2, y + 21, t)
        bold(204, y + 38, "FN = " + r(fn) + " N", ACCENT)
        line(cx + wd / 2 + 2, y + 33, 200, y + 33, ACCENT)
    top = 176 - 34 * n
    if push:
        arrow(cx, top - 34, cx, top - 2, RED)
        text(cx + 10, top - 16, r(push) + " N push")
    text(204, 44, "FN = the push up", MUTED)
    text(204, 60, "from below", MUTED)


# ---------- shared physics ----------

def mw(m, w):
    # Mass or weight typed -> both, with the line of work
    if m is not None:
        wt = q(m * G)
        return m, wt, ["W = m g = " + r(m) + "(" + r(G) + ")",
                       "*W = " + r(wt) + " N"]
    m = q(w / G)
    return m, w, ["m = W / g = " + r(w) + " / " + r(G),
                  "*m = " + r(m) + " kg"]


def blanks(nums, pair, rest):
    # How many unknowns: the mass/weight pair counts as one
    n = 1 if nums[pair[0]] is None and nums[pair[1]] is None else 0
    for i in rest:
        if nums[i] is None:
            n += 1
    return n


def positive(nums, idx):
    for i in idx:
        if nums[i] is not None and nums[i] <= 0:
            return i
    return None


# ---------- 1: weight and mass ----------

def weight_ok(nums):
    m, w, g = nums
    if m is None and w is None:
        return "Type the mass or the weight", 0
    if m is not None and w is not None and g is not None:
        return "Leave one box blank", 2
    bad = positive(nums, (0, 1, 2))
    if bad is not None:
        return "It must be above 0", bad
    return None


def weight_pages(nums):
    m, w, g = nums
    if m is not None and w is not None:
        g = q(w / m)
        work = ["#W = m g,  SO  g = W / m",
                "g = " + r(w) + " / " + r(m),
                "*g = " + r(g) + " m/s^2"]
        ans = [("Gravity there", r(g) + " m/s^2"),
               ("Compared to Earth (g = 10)", r(g / G) + " times Earth's")]
    else:
        earth = g is None
        if earth:
            g = G
        if w is None:
            w = q(m * g)
            work = ["#WEIGHT IS A FORCE:  W = m g",
                    "W = " + r(m) + "(" + r(g) + ")",
                    "*W = " + r(w) + " N"]
            ans = [("Weight", r(w) + " N")]
        else:
            m = q(w / g)
            work = ["#W = m g,  SO  m = W / g",
                    "m = " + r(w) + " / " + r(g),
                    "*m = " + r(m) + " kg"]
            ans = [("Mass", r(m) + " kg")]
        ans.append(("That weight in pounds (1 N = 0.225 lb)",
                    r(w * 0.225) + " lb"))
        ans.append(("Mass is the same anywhere", r(m) + " kg"))
        work.append("#g = 10 ON EARTH IN THIS CLASS" if earth else
                    "#(g = " + r(g) + " IS WHAT YOU TYPED)")
    return [("text", "WORK", work), ("ans", "ANSWER", ans)]


# ---------- 2: up and down forces ----------

def vert_ok(nums):
    if blanks(nums, (0, 1), (2, 3)) != 1:
        return "Leave exactly ONE thing blank", 2
    bad = positive(nums, (0, 1))
    if bad is not None:
        return "It must be above 0", bad
    if nums[0] is None and nums[1] is None and nums[3] + G <= 0:
        return "Can't find the mass from that", 3
    return None


def vert_pages(nums):
    m, w, f, a = nums
    work = ["#DIAGRAM: F UP, W DOWN"]
    law = "#NEWTON'S 2ND LAW (UP IS +)"
    if m is None and w is None:
        den = q(G + a)
        m = q(f / den)
        wt = q(m * G)
        work += [law, "F - W = m a   and   W = m g",
                 r(f) + " - m(" + r(G) + ") = m(" + r(a) + ")",
                 r(f) + " = m(" + r(den) + ")",
                 "*m = " + r(m) + " kg",
                 "*W = m g = " + r(wt) + " N"]
        ans = [("Mass", r(m) + " kg"), ("Weight", r(wt) + " N")]
    else:
        m, wt, lines = mw(m, w)
        work += lines + [law, "F - W = m a"]
        if f is None:
            ma = q(m * a)
            f = q(ma + wt)
            work += ["F - " + r(wt) + " = " + r(m) + "(" + r(a) + ")",
                     "F = " + r(ma) + " + " + r(wt),
                     "*F = " + r(f) + " N"]
            ans = [("Upward force (lift, rope, seat, scale)",
                    r(f) + " N")]
            if f > wt:
                ans.append(("More than the weight (" + r(wt) + " N)",
                            "feels heavier"))
                cap = q(f / G)
                ans.append(("That force could just hold up",
                            r(cap) + " kg  (" + r(cap - m) + " kg more)"))
            else:
                ans.append(("Same as the weight: balanced" if f == wt else
                            "Less than the weight (" + r(wt) + " N)",
                            "no acceleration" if f == wt else
                            "feels lighter"))
                ans.append(("Shared by 2 ropes or arms",
                            r(f / 2) + " N each"))
        else:
            net = q(f - wt)
            a = q(net / m)
            work += [r(f) + " - " + r(wt) + " = " + r(m) + " a",
                     r(net) + " = " + r(m) + " a",
                     "*a = " + r(a) + " m/s^2"]
            if a > 0:
                ans = [("Acceleration", r(a) + " m/s^2 up"),
                       ("If it is moving up", "it is speeding up"),
                       ("If it is moving down", "it is slowing down")]
            elif a < 0:
                ans = [("Acceleration", r(a) + " m/s^2 (down)"),
                       ("If it is moving down", "it is speeding up"),
                       ("If it is moving up", "it is slowing down")]
            else:
                ans = [("Acceleration", "0: the forces balance"),
                       ("So it is", "still, or at a steady speed")]
    way = " up" if a > 0 else (" down" if a < 0 else "")
    note = "a = " + r(abs(a)) + " m/s^2" + way

    def pic():
        fbd("F = " + r(f) + " N", "W = " + r(wt) + " N", "", "", note)

    return [("draw", "FREE-BODY DIAGRAM", pic),
            ("text", "WORK", work),
            ("ans", "ANSWER", ans)]


# ---------- 3: side to side forces ----------

def side_ok(nums):
    if blanks(nums, (0, 1), (2, 3, 4)) != 1:
        return "Leave exactly ONE thing blank", 2
    bad = positive(nums, (0, 1))
    if bad is not None:
        return "It must be above 0", bad
    for i in (2, 3):
        if nums[i] is not None and nums[i] < 0:
            return "Type the size (no minus sign)", i
    if nums[0] is None and nums[1] is None and nums[4] == 0:
        return "Need an acceleration to find mass", 4
    return None


def side_pages(nums):
    m, w, ff, fb, a = nums
    work = ["#DIAGRAM: F FORWARD, f BACK"]
    law = "#NEWTON'S 2ND LAW (FORWARD IS +)"
    if m is None and w is None:
        net = q(ff - fb)
        m = q(net / a)
        wt = q(m * G)
        work += [law, "F - f = m a",
                 r(ff) + " - " + r(fb) + " = m(" + r(a) + ")",
                 "m = " + r(net) + " / " + r(a),
                 "*m = " + r(m) + " kg",
                 "*W = m g = " + r(wt) + " N"]
        ans = [("Mass", r(m) + " kg")]
    else:
        m, wt, lines = mw(m, w)
        work += lines + [law, "F - f = m a"]
        if a is None:
            net = q(ff - fb)
            a = q(net / m)
            work += [r(ff) + " - " + r(fb) + " = " + r(m) + " a",
                     r(net) + " = " + r(m) + " a",
                     "*a = " + r(a) + " m/s^2"]
            ans = [("Acceleration", r(a) + " m/s^2" +
                    (" (backward)" if a < 0 else ""))]
        elif ff is None:
            ma = q(m * a)
            ff = q(ma + fb)
            work += ["F - " + r(fb) + " = " + r(m) + "(" + r(a) + ")",
                     "F = " + r(ma) + " + " + r(fb),
                     "*F = " + r(ff) + " N"]
            ans = [("Forward force (push, pull, tension)", r(ff) + " N")]
        else:
            ma = q(m * a)
            fb = q(ff - ma)
            work += [r(ff) + " - f = " + r(m) + "(" + r(a) + ")",
                     "f = " + r(ff) + " - " + r(ma),
                     "*f = " + r(fb) + " N"]
            ans = [("Backward force (friction)", r(fb) + " N")]
    ans.append(("Net force = F - f", r(ff - fb) + " N"))
    if fb > 0:
        ans.append(("If f is friction:  mu = f / FN",
                    r(fb) + " / " + r(wt) + " = " + r(fb / wt)))

    def pic():
        fbd("FN = " + r(wt) + " N", "W = " + r(wt) + " N",
            "f = " + r(fb) + " N" if fb else "",
            "F = " + r(ff) + " N" if ff else "",
            "a = " + r(a) + " m/s^2")

    return [("draw", "FREE-BODY DIAGRAM", pic),
            ("text", "WORK", work),
            ("ans", "ANSWER", ans)]


# ---------- 4: friction ----------

def fric_ok(nums):
    if blanks(nums, (0, 1), (2, 3)) != 1:
        return "Leave exactly ONE thing blank", 2
    bad = positive(nums, (0, 1, 2))
    if bad is not None:
        return "It must be above 0", bad
    if nums[3] is not None and nums[3] < 0:
        return "Type the size (no minus sign)", 3
    return None


def fric_pages(nums):
    m, w, mu, f = nums
    work = ["#FLAT GROUND: FN = W"]
    if m is None and w is None:
        wt = q(f / mu)
        m = q(wt / G)
        work += ["#f = mu FN,  SO  FN = f / mu",
                 "FN = " + r(f) + " / " + r(mu),
                 "*FN = " + r(wt) + " N  (= W)",
                 "m = W / g = " + r(wt) + " / " + r(G),
                 "*m = " + r(m) + " kg"]
        ans = [("Normal force (and weight)", r(wt) + " N"),
               ("Mass", r(m) + " kg")]
    else:
        m, wt, lines = mw(m, w)
        work += lines
        if f is None:
            f = q(mu * wt)
            work += ["#FRICTION:  f = mu FN",
                     "f = " + r(mu) + "(" + r(wt) + ")",
                     "*f = " + r(f) + " N"]
            ans = [("Friction force", r(f) + " N"),
                   ("If mu is STATIC", "push harder than this to move it"),
                   ("If mu is KINETIC", "the drag while it slides")]
        else:
            mu = q(f / wt)
            work += ["#f = mu FN,  SO  mu = f / FN",
                     "mu = " + r(f) + " / " + r(wt),
                     "*mu = " + r(mu) + "  (no units)"]
            ans = [("Coefficient of friction", r(mu))]

    def pic():
        fbd("FN = " + r(wt) + " N", "W = " + r(wt) + " N",
            "f = " + r(f) + " N", "push", "mu = " + r(mu))

    return [("draw", "FREE-BODY DIAGRAM", pic),
            ("text", "WORK", work),
            ("ans", "ANSWER", ans)]


# ---------- 5: stacked blocks ----------

def stack_ok(nums):
    if nums[1] is None and nums[2] is None and nums[3] is None:
        return "Type at least one mass", 1
    bad = positive(nums, (1, 2, 3))
    if bad is not None:
        return "It must be above 0", bad
    if nums[0] is not None and nums[0] < 0:
        return "Type the size (no minus sign)", 0
    return None


def stack_pages(nums):
    push = nums[0] or 0.0
    ms = [m for m in nums[1:] if m is not None]
    work = ["#ONE DIAGRAM PER BLOCK, TOP FIRST"]
    ans = []
    blocks = []
    load = push
    for k in range(len(ms)):
        m = ms[k]
        wt = q(m * G)
        fn = q(load + wt)
        work += ["#" + r(m) + " kg BLOCK:  FN - LOAD - W = 0",
                 "W = " + r(m) + "(" + r(G) + ") = " + r(wt) + " N",
                 "FN = " + (r(load) + " + " if load else "") + r(wt),
                 "*FN on it = " + r(fn) + " N"]
        under = "the table" if k == len(ms) - 1 else \
            "the " + r(ms[k + 1]) + " kg block"
        ans.append(("Pushing up on the " + r(m) + " kg block",
                    r(fn) + " N  (from " + under + ")"))
        blocks.append((m, fn))
        load = fn
    work.append("#EACH PUSHES BACK JUST AS HARD")
    return [("draw", "PICTURE", lambda: stack_pic(push, blocks)),
            ("text", "WORK", work),
            ("ans", "ANSWER", ans[-3:])]


# ---------- 6: acceleration from motion ----------

def motion_ok(nums):
    vi, vf, t, d, m = nums
    if vi is None:
        return "Type the start speed (0 = from rest)", 0
    if vf is None:
        return "Type the end speed (0 = stops)", 1
    if t is None and d is None:
        return "Type the time OR the distance", 2
    bad = positive(nums, (2, 3, 4))
    if bad is not None:
        return "It must be above 0", bad
    return None


def motion_pages(nums):
    vi, vf, t, d, m = nums
    if t is not None:
        a = q((vf - vi) / t)
        work = ["#a = CHANGE IN SPEED / TIME",
                "a = (Vf - Vo) / t",
                "a = (" + r(vf) + " - " + r(vi) + ") / " + r(t)]
    else:
        a = q((q(vf * vf) - q(vi * vi)) / q(2 * d))
        work = ["#NO TIME:  Vf^2 = Vo^2 + 2 a d",
                "a = (Vf^2 - Vo^2) / (2 d)",
                "a = (" + r(vf * vf) + " - " + r(vi * vi) + ") / " +
                r(2 * d)]
    work.append("*a = " + r(a) + " m/s^2")
    ans = [("Acceleration", r(a) + " m/s^2" +
            (" (slowing down)" if abs(vf) < abs(vi) else ""))]
    if m is not None:
        fnet = q(m * a)
        work += ["#NET FORCE = m a",
                 "Fnet = " + r(m) + "(" + r(a) + ")",
                 "*Fnet = " + r(fnet) + " N"]
        ans.append(("Net force", r(fnet) + " N"))
    if abs(vf) < abs(vi):
        mu = q(abs(a) / G)
        work += ["#IF ONLY FRICTION SLOWS IT:",
                 "mu m g = m a,  so  mu = a / g",
                 "mu = " + r(abs(a)) + " / " + r(G),
                 "*mu = " + r(mu)]
        ans.append(("mu, if friction is what stops it",
                    r(mu)))
    return [("text", "WORK", work), ("ans", "ANSWER", ans)]


# ---------- 7: help ----------

def help_page():
    view([("text", "WHICH ONE?", [
        "#MASS <-> WEIGHT, OTHER PLANETS",
        "*1  Weight and mass",
        "#LIFT, ELEVATOR, ROPE, SEAT",
        "*2  Up and down forces",
        "#PUSH OR PULL ALONG THE GROUND",
        "*3  Side to side forces",
        "#A COEFFICIENT (mu) IS IN IT",
        "*4  Friction",
        "#THINGS SITTING ON EACH OTHER",
        "*5  Stacked blocks",
        "#SPEEDS GIVEN, NO a YET",
        "*6  Acceleration from motion"]),
        ("text", "THE METHOD", [
        "#EVERY FORCE PROBLEM",
        "1. Draw the free-body diagram.",
        "2. Write Fnet = m a with every force",
        "   on it (pick + and stick to it).",
        "3. Put in the numbers and solve.",
        "#REMEMBER",
        "W = m g\tm = W / g",
        "g = 10\tgrams / 1000 = kg",
        "Steady speed or still: Fnet = 0",
        "One direction at a time (x or y)",
        "km/h / 3.6 = m/s\tN = lb / 0.225"]),
        ("text", "NEWTON'S LAWS", [
        "#1ST: NO NET FORCE, NO CHANGE",
        "Still stays still, moving keeps a",
        "steady speed in a straight line.",
        "#2ND: Fnet = m a",
        "Net force points the way of a,",
        "NOT always the way it is moving.",
        "#3RD: EQUAL AND OPPOSITE PAIRS",
        "A pushes B, B pushes A just as",
        "hard. The two forces are on",
        "DIFFERENT objects (never cancel)."]),
        ("text", "WEIGHT + NORMAL FORCE", [
        "Mass (kg): how much stuff. It is",
        "the same everywhere.",
        "Weight (N): the pull of gravity.",
        "It changes with g.",
        "#NORMAL FORCE = SUPPORT FORCE",
        "You FEEL the normal force:",
        "a up: FN > W, you feel heavier",
        "a down: FN < W, you feel lighter",
        "Free fall: FN = 0, weightless",
        "#FRICTION",
        "f = mu FN,  flat ground: FN = W",
        "Static: before it moves.",
        "Kinetic: while it slides."]),
        ("text", "KEYS", [
        "arrows\tmove, change page",
        "enter\tnext box / solve",
        "1 - 7\topen from the menu",
        "del\terase",
        "(-)\tnegative number",
        "EE\ttiny numbers: 4.9 EE (-) 7",
        "esc\tgo back one screen",
        "home, menu\tquit right away",
        "up / down\tscroll long pages"])])


# ---------- menu ----------

MW = ("Mass (kg)", "or Weight (N)")
ONE = "Leave ONE blank: the one you want"


def weight():
    tool(1, "WEIGHT AND MASS", [MW[0], MW[1], "g  (blank = 10)"],
         "Type 2 boxes. Moon: g = 1.66", weight_ok, (), weight_pages)


def vertical():
    tool(2, "UP AND DOWN FORCES", [MW[0], MW[1], "Upward force (N)",
                                   "Accel. (+up, -down)"],
         ONE, vert_ok, (0, 1), vert_pages)


def sideways():
    tool(3, "SIDE TO SIDE FORCES", [MW[0], MW[1], "Force forward (N)",
                                    "Force back (N)", "Acceleration"],
         "Leave ONE blank. None? Type 0", side_ok, (0, 1), side_pages)


def friction():
    tool(4, "FRICTION", [MW[0], MW[1], "Coefficient mu",
                         "Friction force (N)"],
         ONE, fric_ok, (0, 1), fric_pages)


def stacked():
    tool(5, "STACKED BLOCKS", ["Push down on top (N)", "Top mass (kg)",
                               "Next mass (kg)", "Bottom mass (kg)"],
         "Leave unused boxes blank", stack_ok, (), stack_pages)


def motion():
    tool(6, "ACCEL. FROM MOTION", ["Start speed (m/s)", "End speed (m/s)",
                                   "Time (s)", "or Distance (m)",
                                   "Mass (kg, if given)"],
         "", motion_ok, (2, 3), motion_pages)


def menu():
    items = [("Weight and mass", weight),
             ("Up and down forces", vertical),
             ("Side to side forces", sideways),
             ("Friction", friction),
             ("Stacked blocks", stacked),
             ("Acceleration from motion", motion),
             ("Help: which one? + laws", help_page)]
    last = recall(0, 1)
    i = int(last[0]) if last and last[0] and last[0] in "0123456" else 0
    while True:
        start("PHYSICS: FORCES", "g = 10   " + VER)
        for n in range(7):
            y = 30 + n * 22
            if n == i:
                box(6, y, W - 12, 21, SOFT)
                box(6, y, 3, 21, ACCENT)
                box(14, y + 3, 16, 16, ACCENT)
                text(18, y + 16, str(n + 1), WHITE)
                bold(38, y + 16, items[n][0])
            else:
                box(14, y + 3, 16, 16, LINE)
                text(18, y + 16, str(n + 1))
                text(38, y + 16, items[n][0])
        finish("1-7 or arrows + enter: open    esc: quit")
        k = key()
        if k == "up":
            i = (i - 1) % 7
        elif k == "down":
            i = (i + 1) % 7
        elif k == "esc":
            return
        elif k == "enter" or k in ("1", "2", "3", "4", "5", "6", "7"):
            if k != "enter":
                i = int(k) - 1
            remember(0, [str(i)])
            items[i][1]()


try:
    menu()
except Home:
    pass
