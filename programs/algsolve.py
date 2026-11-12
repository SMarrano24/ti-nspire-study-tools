# Algebra solver for TI-Nspire CX II, version 3
# Topic 3: polynomial functions (lessons 3-1 and 3-2), with the work
# shown the way an Algebra 2 class does it: standard form, leading
# coefficient, degree, terms and the name; the leading coefficient
# test for end behavior; adding, subtracting and multiplying (FOIL
# for two binomials, the box method for bigger ones).
# You type the problem the way it looks on the paper.
# Arrows move, enter picks, esc goes back one screen,
# home or menu quits the program right away.
# Each tool remembers what you typed last, even after quitting.
# (The Topic 2 tools, quadratics and complex numbers, are in
# algsolve_topic2.)
from ti_draw import *
from ti_system import get_key
try:
    from ti_system import store_list, recall_list
except ImportError:
    store_list = recall_list = None

VER = "v3"
W = 318
H = 212
CW = 7  # rough width of one letter, for centering
PW = 8  # width of one letter on a typing line
NEG = ("-", "−", "(-)", "neg")
DIV = ("/", "÷")
MUL = ("*", "×", "·")
HOME = ("menu", "home")


class Home(Exception):
    # The home or menu key: drop everything and quit
    pass


class Bad(Exception):
    # Something typed can't be read: (message, line to fix)
    pass

TOP = (20, 78, 92)
ACCENT = (0, 122, 148)
INK = (25, 25, 25)
MUTED = (110, 110, 110)
LINE = (200, 200, 200)
GRID = (228, 228, 228)
SOFT = (228, 242, 246)
WHITE = (255, 255, 255)
RED = (200, 30, 30)
FAINT = (130, 185, 196)


# ---------- exact numbers ----------
# A fraction is a pair (top, bottom) in lowest terms, bottom > 0.

def gcd(a, b):
    a = abs(a)
    b = abs(b)
    while b:
        a, b = b, a % b
    return a


def F(n, d=1):
    if d < 0:
        n = -n
        d = -d
    g = gcd(n, d) or 1
    return (n // g, d // g)


ZERO = (0, 1)
ONE = (1, 1)
DEC = [False]  # True when a decimal point was typed: answer in decimals


def fr(v):
    # A whole number or a fraction -> fraction
    return v if type(v) == tuple else (v, 1)


def add(x, y):
    x = fr(x)
    y = fr(y)
    return F(x[0] * y[1] + y[0] * x[1], x[1] * y[1])


def neg(x):
    x = fr(x)
    return (-x[0], x[1])


def mul(x, y):
    x = fr(x)
    y = fr(y)
    return F(x[0] * y[0], x[1] * y[1])


def div(x, y):
    x = fr(x)
    y = fr(y)
    return F(x[0] * y[1], x[1] * y[0])


def val(x):
    x = fr(x)
    return x[0] / x[1]


def fs(x):
    # "7/2", "-91"; "6.26" when decimals were typed and it comes out even
    x = fr(x)
    if x[1] == 1:
        return str(x[0])
    if DEC[0]:
        k = 0
        t = 1
        while t % x[1] and k < 12:
            t *= 10
            k += 1
        if t % x[1] == 0:
            s = str(abs(x[0]) * (t // x[1]))
            s = "0" * (k + 1 - len(s)) + s
            return ("-" if x[0] < 0 else "") + s[:-k] + "." + s[-k:]
    return str(x[0]) + "/" + str(x[1])


def dec(x):
    # A decimal: 2 places, no "-0", no ".0"
    x = round(x, 2)
    if x == int(x):
        return str(int(x))
    return str(x)


# ---------- polynomials ----------
# A term is [number, letters]: the letters are a tuple of
# (letter, power) pairs in a-z order, () for a plain number.
# A polynomial is a list of terms, in the order they were written.

def kmul(k1, k2):
    # Letters times letters: the powers add
    out = [[v, p] for v, p in k1]
    for v, p in k2:
        for o in out:
            if o[0] == v:
                o[1] += p
                break
        else:
            out.append([v, p])
    out.sort(key=lambda o: o[0])
    return tuple([(o[0], o[1]) for o in out])


def kdeg(k):
    d = 0
    for v, p in k:
        d += p
    return d


def letters(terms):
    vs = []
    for t in terms:
        for v, p in t[1]:
            if v not in vs:
                vs.append(v)
    return vs


def combine(terms):
    # Add up the like terms (same letters, same powers)
    out = []
    for c, k in terms:
        for o in out:
            if o[1] == k:
                o[0] = add(o[0], c)
                break
        else:
            out.append([c, k])
    return [o for o in out if o[0][0] != 0]


def order(terms):
    # Standard form: highest power first. With two letters there is
    # no one right order, so keep the order written, numbers last.
    if len(letters(terms)) <= 1:
        return sorted(terms, key=lambda t: -kdeg(t[1]))
    return [t for t in terms if t[1]] + [t for t in terms if not t[1]]


def pmul(p, q):
    # Every term of p times every term of q, row by row
    return [[mul(a[0], b[0]), kmul(a[1], b[1])] for a in p for b in q]


def tt(c, k):
    # The size of one term, no sign: "2x^5", "x", "(1/3)x^2", "6a^2b^2"
    m = (abs(c[0]), c[1])
    s = ""
    for v, p in k:
        s += v + ("^" + str(p) if p != 1 else "")
    if not k:
        return fs(m)
    if m == ONE:
        return s
    t = fs(m)
    return ("(" + t + ")" if "/" in t else t) + s


def ptext(terms):
    # "2x^5 + 6x^3 + x^2 - 4"
    out = ""
    for t in terms:
        c = t[0]
        if c[0] == 0:
            continue
        if out:
            out += (" - " if c[0] < 0 else " + ") + tt(c, t[1])
        else:
            out = ("-" if c[0] < 0 else "") + tt(c, t[1])
    return out or "0"


ORD = ("zero", "first", "second", "third", "fourth", "fifth", "sixth",
       "seventh", "eighth", "ninth", "tenth")
KIND = ("", "monomial", "binomial", "trinomial")


def pname(d, n):
    # The full name: degree + number of terms
    kind = KIND[n] if n < 4 else "polynomial"
    if d == 0:
        return "constant " + kind
    return (ORD[d] if d < len(ORD) else str(d) + "th") + "-degree " + kind


# ---------- reading what was typed ----------
# An expression is a list of parts that get added. A part is
# [sign, number, letters, groups]; a group is [expression, power]:
#   5x(3x - 1) - 4  ->  [[1, 5, x, [[3x - 1, 1]]], [-1, 4, (), []]]

def p_num(s, i):
    n = len(s)
    j = i
    while i < n and (s[i].isdigit() or s[i] == "."):
        i += 1
    p = s[j:i].split(".")
    if len(p) > 2 or not "".join(p).isdigit():
        raise Bad("Check the decimal point")
    tail = p[1] if len(p) == 2 else ""
    v = F(int("".join(p)), 10 ** len(tail))
    if i < n and s[i] == "/":
        j = i + 1
        i = j
        while i < n and s[i].isdigit():
            i += 1
        if i == j or int(s[j:i]) == 0:
            raise Bad("After / type the bottom number")
        v = div(v, int(s[j:i]))
    return v, i


def p_pow(s, i, top):
    if i < len(s) and s[i] == "^":
        j = i + 1
        i = j
        while i < len(s) and s[i].isdigit():
            i += 1
        if i == j:
            raise Bad("After ^ type a whole number")
        if int(s[j:i]) > top:
            raise Bad("That power is too big")
        return int(s[j:i]), i
    return 1, i


def p_term(s, i):
    c = ONE
    key = ()
    groups = []
    n = len(s)
    got = False
    while i < n:
        ch = s[i]
        if ch == "*":
            i += 1
            if not got or i >= n or s[i] in "+-*)":
                raise Bad("Something is missing by the *")
            continue
        if ch == "(":
            e, i = p_expr(s, i + 1)
            if i >= n or s[i] != ")":
                raise Bad("A ( needs its )")
            p, i = p_pow(s, i + 1, 4)
            if len(e) == 1 and not e[0][3]:
                # Just one term inside, like (3x): part of the number
                for j in range(p):
                    c = mul(c, mul(e[0][0], e[0][1]))
                    key = kmul(key, e[0][2])
            elif p:
                groups.append([e, p])
        elif ch.isdigit() or ch == ".":
            v, i = p_num(s, i)
            p, i = p_pow(s, i, 9)
            for j in range(p):
                c = mul(c, v)
        elif "a" <= ch <= "z":
            p, i = p_pow(s, i + 1, 99)
            if p:
                key = kmul(key, ((ch, p),))
        else:
            break
        got = True
    if not got:
        raise Bad("Something is missing")
    if i < n and s[i] not in "+-)":
        raise Bad("Use / only in numbers, like (1/2)x" if s[i] == "/"
                  else "Check the " + s[i])
    return [1, c, key, groups], i


def p_expr(s, i):
    parts = []
    n = len(s)
    while True:
        sg = 1
        while i < n and s[i] in "+-":
            if s[i] == "-":
                sg = -sg
            i += 1
        if i >= n or s[i] == ")":
            raise Bad("Something is missing" if parts or i < n
                      else "Type the problem first")
        part, i = p_term(s, i)
        part[0] = sg
        parts.append(part)
        if i >= n or s[i] == ")":
            return parts, i


def parse(s):
    e, i = p_expr(s, 0)
    if i < len(s):
        raise Bad("There is an extra )")
    return e


def parttext(part):
    # One part the way it was typed, without its sign
    sg, c, key, groups = part
    s = ""
    if not groups or key or (abs(c[0]), c[1]) != ONE:
        s = tt(c, key)
    for e, p in groups:
        s += "(" + etext(e) + ")" + ("^" + str(p) if p != 1 else "")
    return s


def etext(e):
    out = ""
    for part in e:
        minus = part[0] * (1 if part[1][0] >= 0 else -1) < 0
        if out:
            out += (" - " if minus else " + ") + parttext(part)
        else:
            out = ("-" if minus else "") + parttext(part)
    return out


def ev(e):
    # An expression all multiplied out and combined (no work shown)
    out = []
    for sg, c, key, groups in e:
        cur = [[mul(sg, c), key]]
        for g, p in groups:
            gp = ev(g)
            for j in range(p):
                cur = combine(pmul(cur, gp))
        out += cur
    return combine(out)


def raw(g):
    # The terms inside parentheses just as written, when it is a
    # plain sum; multiplied out if there is more going on inside
    for part in g:
        if part[3]:
            return ev(g)
    return [[mul(part[0], part[1]), part[2]] for part in g]


# ---------- the work, the way class does it ----------

def wrap(s, mark=""):
    # A long line of math breaks before a + or - (or = or |),
    # or between two sets of parentheses
    out = []
    while len(s) > 40:
        cut = -1
        for sep in (" + ", " - ", " = ", " | "):
            j = s.rfind(sep, 6, 40)
            if j > cut:
                cut = j
        if cut < 6:
            cut = s.rfind(")(", 6, 40)
            if cut < 6:
                break
            out.append(mark + s[:cut + 1])
            s = "   " + s[cut + 1:]
            continue
        out.append(mark + s[:cut])
        s = "   " + s[cut + 1:]
    return out + [mark + s]


def like_lines(terms, singles):
    # Add up each set of like terms: (the lines, the result)
    comb = []
    for c, k in terms:
        for o in comb:
            if o[1] == k:
                o[0] = add(o[0], c)
                o[2] += 1
                break
        else:
            comb.append([c, k, 1])
    comb = order(comb)
    lines = []
    found = False
    for c, k, cnt in comb:
        grp = [t for t in terms if t[1] == k]
        if cnt > 1:
            found = True
            lines += wrap(ptext(grp) + " = " + ptext([[c, k]]))
        elif singles:
            lines.append(ptext(grp) + "\t(no like term)")
    res = [[c, k] for c, k, cnt in comb if c[0] != 0]
    if found:
        return ["#COMBINE LIKE TERMS"] + lines, res
    return ["#NO LIKE TERMS TO COMBINE"], res


def times_steps(a, b, lines, boxes, keep):
    # a times b: distribute, FOIL (two binomials) or the box method.
    # keep leaves the like terms for later. Returns (terms, shown):
    # shown means the last line written already is the result
    if len(a) == 1 or len(b) == 1:
        prod = pmul(a, b)
        lines.append("#DISTRIBUTE: TIMES EVERY TERM")
        lines += wrap(ptext(prod))
        return prod, True
    if len(a) == 2 and len(b) == 2:
        prod = pmul(a, b)
        lines.append("#FOIL: FIRST, OUTER, INNER, LAST")
        lines += wrap(ptext(prod))
        res = order(combine(prod))
        if keep or len(res) == len(prod):
            return prod, True
        lines.append("#COMBINE LIKE TERMS")
        return res, False
    # The shorter one goes down the side, the longer across the top
    rows, cols = (a, b) if len(a) <= len(b) else (b, a)
    lines.append("#BOX METHOD: EACH ROW TIMES THE TOP")
    for r in rows:
        lines += wrap(ptext([r]) + "  |  " + ptext(pmul([r], cols)))
    boxes.append((rows, cols))
    ll, res = like_lines(pmul(rows, cols), False)
    lines += ll
    return res, False


def expand_part(part, lines, boxes, many):
    # One product, one piece at a time. Returns (terms, shown)
    sg, c, key, groups = part
    gs = []
    top = 1
    for g, p in groups:
        gs += [combine(raw(g))] * p
        top = max(top, p)
    if top > 1:
        lines.append("#SQUARED MEANS TIMES ITSELF" if top == 2
                     else "#A POWER: WRITE IT THAT MANY TIMES")
        lines += wrap("".join(["(" + ptext(g) + ")" for g in gs]))
    if len(gs) > 2:
        lines.append("#ONE PIECE AT A TIME: THE FIRST TWO")
    solo = c == ONE and not key
    cur = gs[0] if gs else [[ONE, ()]]
    shown = True
    for j in range(1, len(gs)):
        if j > 1:
            if not shown:
                lines += wrap("= " + ptext(cur))
            lines += wrap("NOW TIMES (" + ptext(gs[j]) + ")", "#")
        cur, shown = times_steps(cur, gs[j], lines, boxes,
                                 many and solo and j == len(gs) - 1)
    if not solo:
        if not shown:
            lines += wrap("= " + ptext(cur))
        cur = pmul([[c, key]], cur)
        t = "#DISTRIBUTE THE " + ptext([[c, key]])
        lines.append(t + (": TIMES EVERY TERM" if len(t) < 23 else ""))
        lines += wrap(ptext(cur))
        shown = True
    return cur, shown


def simplify_steps(e):
    # Add, subtract, multiply: (the work, the answer, boxes to draw)
    lines = []
    boxes = []
    plain = True
    for sg, c, key, groups in e:
        if groups and (c != ONE or key or len(groups) > 1 or groups[0][1] != 1):
            plain = False
    if plain:
        # Only adding and subtracting
        terms = []
        flip = False
        for sg, c, key, groups in e:
            if groups:
                flip = flip or sg < 0
                terms += [[mul(sg, t[0]), t[1]] for t in raw(groups[0][0])]
            else:
                terms.append([mul(sg, c), key])
        if flip:
            lines += ["#SUBTRACTING: DISTRIBUTE THE NEGATIVE",
                      "#(EVERY SIGN INSIDE FLIPS)"] + wrap(ptext(terms))
        ll, res = like_lines(terms, True)
        lines += ll
        if ptext(res) != ptext(combine(terms)) and len(letters(res)) <= 1:
            lines.append("#STANDARD FORM: HIGHEST POWER FIRST")
    else:
        many = len(e) > 1
        polys = []
        k = 0
        for part in e:
            if not part[3]:
                polys.append([part[0], [[part[1], part[2]]]])
                continue
            k += 1
            if many:
                lines += wrap("PART " + str(k) + ":  " + parttext(part), "#")
            cur, shown = expand_part(part, lines, boxes, many)
            if many and not shown:
                lines += wrap("= " + ptext(cur))
            polys.append([part[0], cur])
        if many:
            terms = []
            flip = False
            for sg, p in polys:
                flip = flip or (sg < 0 and len(p) > 1)
                terms += [[mul(sg, t[0]), t[1]] for t in p]
            lines.append("#PUT THE PARTS TOGETHER")
            if flip:
                lines.append("#(A MINUS IN FRONT FLIPS EVERY SIGN)")
            lines += wrap(ptext(terms))
            ll, res = like_lines(terms, True)
            lines += ll
        else:
            if polys[0][0] < 0:
                cur = [[neg(t[0]), t[1]] for t in cur]
                lines.append("#THE MINUS IN FRONT FLIPS EVERY SIGN")
            res = order(combine(cur))
    if len(letters(res)) > 1 and len(res) > 1:
        lines.append("#(THESE CAN GO IN ANY ORDER)")
    return lines + wrap(ptext(res), "*"), res, boxes


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
    # A highlighted answer line: colored text on a light band
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
    box(0, 0, W, 24, TOP)
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


def pick(title, items, hint, i=0, right=""):
    # A list to choose from. Returns the number picked, or None
    n = len(items)
    pitch = min(26, 160 // n)
    while True:
        start(title, right)
        for j in range(n):
            y = 30 + j * pitch
            mid = y + (pitch - 2) // 2
            if j == i:
                box(6, y, W - 12, pitch - 2, SOFT)
                box(6, y, 3, pitch - 2, ACCENT)
                box(14, mid - 7, 14, 14, ACCENT)
                text(17, mid + 5, str(j + 1), WHITE)
                bold(36, mid + 5, items[j])
            else:
                box(14, mid - 7, 14, 14, LINE)
                text(17, mid + 5, str(j + 1))
                text(36, mid + 5, items[j])
        finish(hint)
        k = key()
        if k == "up":
            i = (i - 1) % n
        elif k == "down":
            i = (i + 1) % n
        elif len(k) == 1 and k.isdigit() and 1 <= int(k) <= n:
            return int(k) - 1
        elif k == "enter":
            return i
        elif k == "esc":
            return None


def arrow(x, y, c):
    # A small arrow pointing right, on a line of text
    line(x, y - 4, x + 12, y - 4, c)
    line(x + 12, y - 4, x + 8, y - 7, c)
    line(x + 12, y - 4, x + 8, y - 1, c)


def infinity(x, y, minus, c):
    # The infinity sign (two small loops), with a minus if asked
    col(c)
    if minus:
        draw_line(int(x), int(y - 4), int(x + 5), int(y - 4))
        x += 9
    try:
        draw_circle(int(x + 3), int(y - 4), 3)
        draw_circle(int(x + 9), int(y - 4), 3)
    except Exception:
        draw_text(int(x), int(y), "oo")


def goes(x, y, xminus, yminus):
    # A highlighted "As x -> infinity, y -> infinity" line
    box(x, y - 14, 206, 20, SOFT)
    box(x, y - 14, 3, 20, ACCENT)
    bold(x + 9, y, "As x", ACCENT)
    arrow(x + 42, y, ACCENT)
    infinity(x + 60, y, xminus, ACCENT)
    x += 76 + (9 if xminus else 0)
    bold(x, y, ",  y", ACCENT)
    arrow(x + 28, y, ACCENT)
    infinity(x + 46, y, yminus, ACCENT)


# ---------- typing math ----------

def edit(v, cur, k, fresh):
    # One key on a typing line: (new text, new cursor), or None if
    # k is not a typing key. On a fresh line the first key starts over.
    if k == "del":
        if fresh:
            return "", 0
        if cur == 0:
            return v, 0
        return v[:cur - 1] + v[cur:], cur - 1
    if k == "clear":
        return "", 0
    ch = ""
    if k in NEG:
        ch = "-"
    elif k in DIV:
        ch = "/"
    elif k in MUL:
        ch = "*"
    elif k == "square":
        ch = "^2"
    elif len(k) == 1 and (k.isdigit() or k in ".+^()" or "a" <= k.lower() <= "z"):
        ch = k.lower()
    if not ch:
        return None
    if fresh:
        v = ""
        cur = 0
    if len(v) + len(ch) > 60:
        return v, cur
    return v[:cur] + ch + v[cur:], cur + len(ch)


def typebox(x, y, w, h, v, cur, fresh):
    # One typing line. cur is where the cursor is, or -1 when it is
    # not the current line. A fresh line is filled in: typing
    # replaces it. Each letter gets the same room, so the cursor fits.
    on = cur >= 0
    full = on and fresh and v
    box(x, y, w, h, ACCENT if full else (SOFT if on else WHITE))
    frame(x, y, w, h, ACCENT if on else LINE)
    room = (w - 12) // PW
    off = 0
    if on and len(v) > room:
        off = max(0, min(cur - room + 5, len(v) - room))
    j = 0
    for ch in v[off:off + room]:
        text(x + 6 + j * PW, y + h - 7, ch, WHITE if full else INK)
        j += 1
    if on and not full:
        box(x + 5 + (cur - off) * PW, y + 4, 1, h - 8, INK)


TIPS = ("x squared:  press  x  then  ^  then  2",
        "times:  (..)(..)      fractions:  (1/2)x")


def ask(title, labels, vals, note, build):
    # Lines to type math on, like on the paper. build(texts) turns
    # them into what the tool needs, or raises Bad(message, line).
    # Returns (what build made, the texts), or None for esc.
    n = len(labels)
    vals = list(vals) if vals else [""] * n
    i = 0
    cur = len(vals[0])
    fresh = True
    err = ""
    while True:
        start(title)
        for f in range(n):
            y = 30 + f * 50
            if f == i:
                bold(10, y + 14, labels[f], ACCENT)
            else:
                text(10, y + 14, labels[f], MUTED)
            typebox(10, y + 19, W - 20, 24, vals[f], cur if f == i else -1, fresh)
        y = 42 + n * 50
        if vals[i]:
            try:
                t = etext(parse(vals[i]))
                text(10, y, "It reads:", MUTED)
                text(10, y + 17, t if len(t) <= 42 else t[:39] + "...")
            except Bad:
                text(10, y, "(keep typing)", MUTED)
        elif n == 1:
            text(10, y, TIPS[0], MUTED)
            text(10, y + 17, TIPS[1], MUTED)
        if err:
            text(10, H - 30, err, RED)
        elif note:
            text(10, H - 30, note, MUTED)
        last = i == n - 1
        finish(("enter: SOLVE" if last else "enter: next line") +
               "   del: erase   esc: back")
        k = key()
        err = ""
        t = edit(vals[i], cur, k, fresh)
        if t is not None:
            vals[i], cur = t
            fresh = False
        elif k == "esc":
            return None
        elif k in ("left", "right"):
            # Starts editing what is there (no typing over it)
            cur = max(0, min(len(vals[i]), cur + (1 if k == "right" else -1)))
            fresh = False
        elif k == "up" and i > 0:
            i -= 1
            cur = len(vals[i])
            fresh = True
        elif (k in ("down", "tab") or k == "enter") and not last:
            i += 1
            cur = len(vals[i])
            fresh = True
        elif k == "enter":
            try:
                DEC[0] = "." in "".join(vals)
                return build(vals), vals
            except Bad as b:
                err = b.args[0]
                if len(b.args) > 1:
                    i = b.args[1]
                cur = len(vals[i])
                fresh = False


def typed(vals, f):
    # The expression on line f, or Bad pointing at that line
    try:
        return parse(vals[f])
    except Bad as b:
        raise Bad(b.args[0], f)


def one_letter(terms, f):
    vs = letters(terms)
    if len(vs) > 1:
        raise Bad("Use just one letter here", f)
    return vs[0] if vs else "x"


# ---------- remembering what was typed ----------
# Each tool's last lines go in a calculator list (alg3n1 ... alg3n4,
# alg3n0 for the menu), so they come back after quitting. The list
# holds each line's length, then one number per letter.

CH = "0123456789-./^+*()abcdefghijklmnopqrstuvwxyz"
LAST = {}


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
        store_list("alg3n" + str(n), out)
    except Exception:
        pass


def recall(n, count):
    # The last lines for tool n, or None
    if n in LAST:
        return list(LAST[n])
    try:
        got = [int(round(x)) for x in recall_list("alg3n" + str(n))]
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


# ---------- result pages ----------
# ("text", title, lines)   "*" answer, "#" gray heading,
#                          a tab starts a second column
# ("ans", title, [(label, value), ...])
# ("draw", title, fn)      a picture

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
            text(160, y, parts[1], MUTED if parts[1] == "(no like term)" else c)
        y += 19
    more = len(lines) > top + 8
    if more or top:
        scroll(30, 155, top, 8, len(lines))
    return more


def draw_answers(items):
    y = 34
    for lab, v in items:
        vs = wrap(v)
        h = 26 + 18 * len(vs)
        box(6, y, W - 12, h, SOFT)
        box(6, y, 4, h, ACCENT)
        text(18, y + 17, lab, MUTED)
        for j in range(len(vs)):
            bold(18, y + 37 + 18 * j, vs[j].strip(), ACCENT)
        y += h + 6


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
        if many:
            hint.append("< >: pages")
        if more or top:
            hint.append("up/down: scroll")
        hint.append("esc: back")
        finish("  ".join(hint))
        k = key()
        if k == "esc":
            return
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


# ---------- graphs ----------

def span(vals):
    # A window that holds these values (and 0), at least 10 wide
    lo = min(vals + [0])
    hi = max(vals + [0])
    pad = max(1.0, (hi - lo) * 0.15)
    lo -= pad
    hi += pad
    if hi - lo < 10:
        c = (lo + hi) / 2
        lo = c - 5
        hi = c + 5
    return lo, hi


def step(size):
    for s in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000):
        if size / s <= 16:
            return s
    return 10000


def graph(curves, pts, xs, ys):
    # Graph paper that fits the important points, then the curves.
    # curves: [(function, color)]; pts: [(x, y, label)]
    x0, x1 = span(xs)
    y0, y1 = span(ys)
    L = 8
    R = W - 8
    T = 30
    B = 184
    sx = (R - L) / (x1 - x0)
    sy = (B - T) / (y1 - y0)

    def X(x):
        return L + (x - x0) * sx

    def Y(y):
        return B - (y - y0) * sy

    stx = step(x1 - x0)
    sty = step(y1 - y0)
    g = int(x0 / stx) * stx
    if g < x0:
        g += stx
    while g <= x1:
        line(X(g), T, X(g), B, GRID)
        g += stx
    g = int(y0 / sty) * sty
    if g < y0:
        g += sty
    while g <= y1:
        line(L, Y(g), R, Y(g), GRID)
        g += sty
    if x0 < 0 < x1:
        line(X(0), T, X(0), B, MUTED)
    if y0 < 0 < y1:
        line(L, Y(0), R, Y(0), MUTED)
    frame(L, T, R - L, B - T, LINE)
    for f, c in curves:
        col(c)
        pen("medium")
        n = 96
        px = X(x0)
        py = Y(f(x0))
        for j in range(1, n + 1):
            x = x0 + (x1 - x0) * j / n
            qx = X(x)
            qy = Y(f(x))
            seg(px, py, qx, qy, T, B)
            px = qx
            py = qy
        pen("thin")
    for x, y, lab in pts:
        if x0 <= x <= x1 and y0 <= y <= y1:
            box(X(x) - 2, Y(y) - 2, 5, 5, INK)
            tx = X(x) + 6
            if tx + CW * len(lab) > R:
                tx = X(x) - 6 - CW * len(lab)
            ty = Y(y) - 5 if Y(y) > T + 16 else Y(y) + 15
            box(tx - 2, ty - 12, CW * len(lab) + 4, 15, WHITE)
            text(tx, ty, lab)
    t = "1 box = " + str(stx) if stx == sty else "boxes: x " + str(stx) + ", y " + str(sty)
    box(R - 6 - CW * len(t), B - 17, CW * len(t) + 4, 15, WHITE)
    text(R - 4 - CW * len(t), B - 5, t, MUTED)


def seg(px, py, qx, qy, T, B):
    # A line piece, cut off at the top and bottom of the graph
    if (py < T and qy < T) or (py > B and qy > B):
        return
    if py < T or py > B:
        e = T if py < T else B
        px = px + (qx - px) * (e - py) / (qy - py)
        py = e
    if qy < T or qy > B:
        e = T if qy < T else B
        qx = qx + (px - qx) * (e - qy) / (py - qy)
        qy = e
    draw_line(int(px), int(py), int(qx), int(qy))


def fn(terms):
    # A polynomial in one letter as something to graph
    cs = [(val(c), kdeg(k)) for c, k in terms]

    def f(x):
        y = 0
        for c, p in cs:
            y += c * x ** p
        return y
    return f


def window(f):
    # Where the graph does something: its turns and crossings
    xs = [0]
    ys = [0, f(0)]
    px = -8.0
    py = f(px)
    up = None
    for j in range(1, 161):
        x = -8 + j * 0.1
        y = f(x)
        if (py < 0) != (y < 0):
            xs.append(x)
        d = y > py
        if up is not None and d != up:
            xs.append(px)
            ys.append(py)
        up = d
        px = x
        py = y
    if len(xs) == 1:
        xs = [-3, 3]
    return xs, ys


# ---------- 1: classify + end behavior ----------

def build_poly(vals):
    e = typed(vals, 0)
    res = order(ev(e))
    v = one_letter(res, 0)
    if not res:
        raise Bad("That is just 0", 0)
    return e, res, v


def classify():
    vals = recall(1, 1)
    while True:
        got = ask("CLASSIFY + END BEHAVIOR", ["The polynomial (in any order):"],
                  vals, "Like:  x^2+6x^3-4+2x^5", build_poly)
        if got is None:
            return
        (e, res, v), vals = got
        remember(1, vals)
        view(classify_pages(e, res, v))


def classify_pages(e, res, v):
    d = kdeg(res[0][1])
    lc = res[0][0]
    n = len(res)
    name = pname(d, n)
    std = ptext(res)
    odd = d % 2 == 1
    pos = lc[0] > 0
    left_up = pos != odd

    def facts():
        box(6, 32, W - 12, 42, SOFT)
        box(6, 32, 4, 42, ACCENT)
        text(18, 48, "Standard form", MUTED)
        bold(18, 67, std if len(std) <= 40 else std[:37] + "...", ACCENT)
        y = 80
        for lab, s in (("Leading coefficient", fs(lc)), ("Degree", str(d)),
                       ("Number of terms", str(n)), ("Name", name)):
            line(6, y + 25, W - 6, y + 25)
            text(12, y + 17, lab, MUTED)
            bold(min(150, W - 14 - CW * len(s)), y + 17, s, ACCENT)
            y += 27

    how = ["#YOUR POLYNOMIAL"] + wrap(etext(e))
    work = raw(e)
    if len(combine(work)) != len(work) or ptext(order(combine(work))) != std:
        how += ["#SIMPLIFY IT FIRST (TOOL 2 SHOWS HOW)"] + wrap(ptext(combine(work)))
    how.append("#THE DEGREE (POWER) OF EACH TERM")
    ds = [ptext([t]) + ":  degree " + str(kdeg(t[1])) for t in combine(work)]
    for j in range(0, len(ds), 2):
        how.append(ds[j] + ("\t" + ds[j + 1] if j + 1 < len(ds) else ""))
    how += ["#STANDARD FORM: HIGHEST POWER FIRST"] + wrap(std, "*")
    how += ["#LEADING COEFFICIENT: THE NUMBER ON THE",
            "#HIGHEST POWER (NOT THE WHOLE TERM)", "*" + fs(lc)]
    if (abs(lc[0]), lc[1]) == ONE and d:
        how.append("#(NO NUMBER SHOWING MEANS 1)")
    how += ["#DEGREE: THE HIGHEST POWER", "*" + str(d),
            "#TERMS: COUNT THEM", "*" + str(n),
            "#NAME = THE DEGREE + HOW MANY TERMS",
            "1 monomial\t2 binomial", "3 trinomial\t4 or more: polynomial",
            "*" + name]

    def ends():
        if d == 0:
            text(12, 60, "Just a number: a flat line at y = " + fs(lc) + ".")
            text(12, 80, "Both ends stay at " + fs(lc) + ".")
            return
        text(12, 46, "LEADING COEFFICIENT TEST", MUTED)
        bold(12, 65, "Degree " + str(d) + ":  " + ("odd" if odd else "even"))
        bold(12, 84, "Leading coefficient " + fs(lc) + ":  " +
             ("positive" if pos else "negative"))
        text(12, 103, "Odd: the ends go opposite ways" if odd
             else "Even: both ends go the same way", MUTED)
        text(12, 121, "Positive: the right end goes up" if pos
             else "Negative: the right end goes down", MUTED)
        goes(6, 142, False, not pos)
        goes(6, 165, True, not left_up)
        text(12, 184, "Same ends as y = " + ("" if pos else "-") +
             (v if odd else v + "^2"), MUTED)
        # A little sketch of the two ends
        cx = 266
        cy = 154
        line(cx - 40, cy, cx + 40, cy, MUTED)
        line(cx, cy - 30, cx, cy + 30, MUTED)
        pen("medium")
        for sx, upw in ((-1, left_up), (1, pos)):
            sy = -1 if upw else 1
            x1 = cx + sx * 14
            y1 = cy + sy * 8
            x2 = cx + sx * 36
            y2 = cy + sy * 28
            line(x1, y1, x2, y2, ACCENT)
            line(x2, y2, x2 - sx * 9, y2 - sy * 2, ACCENT)
            line(x2, y2, x2 - sx * 2, y2 - sy * 9, ACCENT)
        pen("thin")

    f = fn(res)

    def pic():
        xs, ys = window(f)
        y0 = res[-1][0] if not res[-1][1] else ZERO
        graph([(f, ACCENT)], [(0, val(y0), "(0, " + fs(y0) + ")")], xs, ys)

    return [("draw", "CLASSIFY", facts),
            ("text", "HOW", how),
            ("draw", "END BEHAVIOR", ends),
            ("draw", "GRAPH", pic)]


# ---------- 2: add, subtract, multiply ----------

def box_page(rows, cols):
    # The box method drawn out: each box = its row times its column
    def pic():
        nc = len(cols)
        nr = len(rows)
        x0 = 70
        y0 = 66
        cw = (W - 10 - x0) // nc
        ch = min(40, 104 // nr)
        text(12, 44, "Each box = its row times its column", MUTED)
        for j in range(nc):
            t = ptext([cols[j]])
            bold(x0 + j * cw + (cw - CW * len(t)) / 2, y0 - 6, t, ACCENT)
        for i in range(nr):
            t = ptext([rows[i]])
            bold(x0 - 8 - CW * len(t), y0 + i * ch + ch / 2 + 5, t, ACCENT)
            for j in range(nc):
                frame(x0 + j * cw, y0 + i * ch, cw, ch, MUTED)
                t = ptext(pmul([rows[i]], [cols[j]]))
                text(x0 + j * cw + (cw - CW * len(t)) / 2, y0 + i * ch + ch / 2 + 5, t)
        text(12, y0 + nr * ch + 16, "Then add the like terms", MUTED)
    return pic


def boxable(rows, cols):
    # Small enough to draw?
    if len(rows) > 3 or len(cols) > 4:
        return False
    room = ((W - 80) // len(cols)) // CW - 1
    for t in pmul(rows, cols):
        if len(ptext([t])) > room:
            return False
    return True


def simplify():
    vals = recall(2, 1)
    while True:
        got = ask("ADD, SUBTRACT, MULTIPLY", ["Type it like on the paper:"], vals,
                  "Like:  (2x-7)^2   or   5x(3x-1)+(x+2)(x-3)",
                  lambda vs: typed(vs, 0))
        if got is None:
            return
        e, vals = got
        remember(2, vals)
        lines, res, boxes = simplify_steps(e)
        pages = [("text", "WORK", wrap(etext(e)) + lines)]
        for rows, cols in boxes:
            if boxable(rows, cols):
                pages.append(("draw", "BOX METHOD", box_page(rows, cols)))
        ans = [("Simplified", ptext(res))]
        if res and len(letters(res)) <= 1:
            ans.append(("It is a", pname(kdeg(res[0][1]), len(res))))
        view(pages + [("ans", "ANSWER", ans)])


# ---------- 3: plug in a number ----------

def build_value(vals):
    e = typed(vals, 0)
    res = order(ev(e))
    v = one_letter(res, 0)
    a = ev(typed(vals, 1))
    if len(a) > 1 or (a and a[0][1]):
        raise Bad("Just a number here, like 5 or -1/2", 1)
    return res, v, a[0][0] if a else ZERO


def value_steps(res, v, a):
    # f(a) with the plugging in shown: (the work, the answer)
    A = "(" + fs(a) + ")"
    put = ""
    got = []
    pows = []
    for c, k in res:
        p = kdeg(k)
        t = tt(c, ())
        if p:
            t = ("" if (abs(c[0]), c[1]) == ONE else
                 ("(" + t + ")" if "/" in t else t)) + A + ("^" + str(p) if p > 1 else "")
        put += ((" - " if c[0] < 0 else " + ") if put else ("-" if c[0] < 0 else "")) + t
        ap = ONE
        for j in range(p):
            ap = mul(ap, a)
        if p > 1 and A + "^" + str(p) + " = " + fs(ap) not in pows:
            pows.append(A + "^" + str(p) + " = " + fs(ap))
        got.append([mul(c, ap), ()])
    total = ZERO
    for t in got:
        total = add(total, t[0])
    lines = ["#PLUG IN " + fs(a) + " FOR EVERY " + v] + wrap("f" + A + " = " + (put or "0"))
    if pows:
        lines.append("#POWERS FIRST")
        for j in range(0, len(pows), 2):
            lines.append(pows[j] + ("\t" + pows[j + 1] if j + 1 < len(pows) else ""))
    if len(got) > 1:
        lines.append("#THEN MULTIPLY, THEN ADD")
        lines += wrap("= " + " + ".join([("(" + fs(t[0]) + ")" if t[0][0] < 0 else fs(t[0]))
                                         for t in got]))
    return lines + ["*f" + A + " = " + fs(total)], total


def plug_in():
    vals = recall(3, 2)
    while True:
        got = ask("PLUG IN A NUMBER", ["f(x) =", "x ="], vals, "", build_value)
        if got is None:
            return
        (res, v, a), vals = got
        remember(3, vals)
        lines, total = value_steps(res, v, a)
        y0 = res[-1][0] if res and not res[-1][1] else ZERO
        view([("text", "WORK", lines),
              ("ans", "ANSWER", [("f(" + fs(a) + ")", fs(total)),
                                 ("As a point", "(" + fs(a) + ", " + fs(total) + ")"),
                                 ("y-intercept: f(0)", "(0, " + fs(y0) + ")")])])


# ---------- 4: rectangle: area + domain ----------

def build_rect(vals):
    a = combine(raw(typed(vals, 0)))
    b = combine(raw(typed(vals, 1)))
    for f in (0, 1):
        if not (a, b)[f]:
            raise Bad("A side can't be 0", f)
    v = one_letter(a + b, 1)
    for f in (0, 1):
        try:
            side_rule((a, b)[f], v)
        except Bad as bad:
            raise Bad(bad.args[0], f)
    return a, b, v


def side_rule(s, v):
    # s > 0 solved for the letter: (the line, low bound, high bound)
    if kdeg(order(s)[0][1]) > 1:
        return ptext(s) + " > 0", None, None
    m = ZERO
    k = ZERO
    for c, key in s:
        if key:
            m = c
        else:
            k = c
    if m[0] == 0:
        if k[0] <= 0:
            raise Bad("A side can't be 0 or negative")
        return ptext(s) + " is always positive", None, None
    edge = div(neg(k), m)
    if m[0] > 0:
        return ptext(s) + " > 0   ->   " + v + " > " + fs(edge), edge, None
    return ptext(s) + " > 0   ->   " + v + " < " + fs(edge), None, edge


def rectangle():
    vals = recall(4, 2)
    while True:
        got = ask("RECTANGLE: AREA + DOMAIN", ["One side:", "Other side:"], vals,
                  "Like:  x+4   and   x+15", build_rect)
        if got is None:
            return
        (a, b, v), vals = got
        remember(4, vals)
        lines = ["#AREA = LENGTH TIMES WIDTH", "A = (" + ptext(a) + ")(" + ptext(b) + ")"]
        cur, shown = times_steps(a, b, lines, [], False)
        area = order(combine(cur))
        lines += wrap("A = " + ptext(area), "*")
        dom = ["#TO BE A REAL RECTANGLE, EVERY SIDE", "#HAS TO BE LONGER THAN 0"]
        lo = None
        hi = None
        n = 0
        for s in (a, b):
            t, l, h = side_rule(s, v)
            dom.append(t)
            if l is not None:
                n += 1
                lo = l if lo is None or val(l) > val(lo) else lo
            if h is not None:
                n += 1
                hi = h if hi is None or val(h) < val(hi) else hi
        if n > 1:
            dom += ["#BOTH HAVE TO BE TRUE, SO USE THE", "#STRICTER ONE"]
        if lo is not None and hi is not None:
            ans = fs(lo) + " < " + v + " < " + fs(hi) if val(lo) < val(hi) else "no " + v + " works"
        elif lo is not None:
            ans = v + " > " + fs(lo)
        elif hi is not None:
            ans = v + " < " + fs(hi)
        else:
            ans = "any " + v
        dom.append("*" + ans)
        if lo is not None and hi is None:
            dom += ["#AT " + v + " = " + fs(lo) + " A SIDE WOULD BE 0:",
                    "#NOT A RECTANGLE. ANYTHING BIGGER WORKS"]

        def pic():
            frame(100, 62, 160, 84, INK)
            frame(101, 63, 158, 82, INK)
            t = ptext(a)
            bold(180 - CW * len(t) / 2, 54, t, ACCENT)
            t = ptext(b)
            bold(92 - CW * len(t), 110, t, ACCENT)
            t = "A = " + ptext(area)
            if CW * len(t) < 150:
                text(180 - CW * len(t) / 2, 110, t)
            text(12, 172, "Domain:  " + ans, MUTED)

        view([("text", "AREA", lines),
              ("text", "DOMAIN", dom),
              ("draw", "PICTURE", pic),
              ("ans", "ANSWER", [("Area", ptext(area)),
                                 ("Domain (what " + v + " can be)", ans)])])


# ---------- 5: help ----------

def help_page():
    view([("text", "WHICH ONE?", [
        "#STANDARD FORM, LEADING COEFFICIENT,",
        "#DEGREE, TERMS, NAME, END BEHAVIOR",
        "*1  Classify + end behavior",
        "#SIMPLIFY: ( ) + ( ),  ( ) - ( ),  ( )( )",
        "*2  Add, subtract, multiply",
        "#FIND f(5), OR THE y-INTERCEPT",
        "*3  Plug in a number",
        "#AREA AND POSSIBLE DOMAIN",
        "*4  Rectangle"]),
        ("text", "CLASSIFY", [
        "#STANDARD FORM",
        "like terms combined, highest power first",
        "#LEADING COEFFICIENT",
        "the number on the highest power",
        "#DEGREE",
        "the highest power",
        "#NAME = DEGREE + NUMBER OF TERMS",
        "1 monomial\t2 binomial",
        "3 trinomial\t4 or more: polynomial",
        "*like:  fifth-degree binomial"]),
        ("text", "END BEHAVIOR", [
        "#DEGREE ODD: ENDS GO OPPOSITE WAYS",
        "+ leading:  left down, right up",
        "- leading:  left up, right down",
        "#DEGREE EVEN: BOTH ENDS THE SAME WAY",
        "+ leading:  both ends up",
        "- leading:  both ends down",
        "#ALWAYS WRITE BOTH:  AS x GOES TO",
        "#INFINITY, AND TO NEGATIVE INFINITY",
        "up: y goes to infinity",
        "down: y goes to negative infinity"]),
        ("text", "ADD, SUBTRACT, MULTIPLY", [
        "#ADD",
        "combine the like terms",
        "#SUBTRACT",
        "distribute the negative first",
        "#MULTIPLY",
        "2 terms x 2 terms:  FOIL",
        "bigger:  box method",
        "3 things:  one piece at a time",
        "#LIKE TERMS: SAME LETTERS, SAME POWERS",
        "#ANSWER IN STANDARD FORM"]),
        ("text", "KEYS", [
        "letters\tthe a-z keys",
        "^\tpowers:  x^2",
        "( )\tjust like the paper",
        "/\tfractions:  (1/2)x",
        "< >\tmove along the line",
        "del\terase",
        "esc\tgo back one screen",
        "last problem\tkept: type over it",
        "home, menu\tquit right away"])])


# ---------- menu ----------

def menu():
    items = [("Classify + end behavior", classify),
             ("Add, subtract, multiply", simplify),
             ("Plug in a number:  f(5)", plug_in),
             ("Rectangle: area + domain", rectangle),
             ("Help: which one? + rules", help_page)]
    last = recall(0, 1)
    i = int(last[0]) if last and last[0] and last[0] in "01234" else 0
    while True:
        try:
            j = pick("ALGEBRA SOLVER", [t[0] for t in items],
                     "1-5 or arrows + enter: open    esc: quit", i, "Topic 3   " + VER)
            if j is None:
                return
            i = j
            remember(0, [str(j)])
            items[j][1]()
        except Home:
            return


menu()
