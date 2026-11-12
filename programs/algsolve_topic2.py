# Algebra solver for TI-Nspire CX II
# Topic 2: quadratics and complex numbers, with the work shown
# the way an Algebra 2 class does it. Answers are exact: fractions,
# simplest radical form and i.
# Arrows move, enter picks, esc goes back one screen,
# home or menu quits the program right away.
# Each tool remembers its last numbers, even after quitting.
from math import sqrt
from ti_draw import *
from ti_system import get_key
try:
    from ti_system import store_list, recall_list
except ImportError:
    store_list = recall_list = None

W = 318
H = 212
CW = 7  # rough width of one letter, for centering
NEG = ("-", "−", "(-)", "neg")
DIV = ("/", "÷")
HOME = ("menu", "home")


class Home(Exception):
    # The home or menu key: drop everything and quit
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


def lcm(a, b):
    return a * b // gcd(a, b)


def F(n, d=1):
    if d < 0:
        n = -n
        d = -d
    g = gcd(n, d) or 1
    return (n // g, d // g)


ZERO = (0, 1)
ONE = (1, 1)


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


def sub(x, y):
    return add(x, neg(y))


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
    # "7/2", "-91"
    x = fr(x)
    if x[1] == 1:
        return str(x[0])
    return str(x[0]) + "/" + str(x[1])


def pm(x):
    # " + 5" or " - 91" (nothing for 0)
    x = fr(x)
    if x[0] < 0:
        return " - " + fs(neg(x))
    if x[0] > 0:
        return " + " + fs(x)
    return ""


def dec(x):
    # A decimal: 2 places, no "-0", no ".0"
    x = round(x, 2)
    if x == int(x):
        return str(int(x))
    return str(x)


def whole(cs):
    # Fractions -> whole numbers in the same ratio (times the LCM)
    L = 1
    for c in cs:
        L = lcm(L, fr(c)[1])
    return L, [fr(c)[0] * (L // fr(c)[1]) for c in cs]


def num(s):
    # Text typed in a box -> fraction: "4", "-2.5", "1/3"
    if "/" in s:
        p = s.split("/")
        if len(p) != 2:
            raise ValueError
        b = num(p[1])
        if b[0] == 0:
            raise ValueError
        return div(num(p[0]), b)
    sign = 1
    if s[:1] == "-":
        sign = -1
        s = s[1:]
    p = s.split(".")
    if len(p) > 2 or not "".join(p).isdigit():
        raise ValueError
    tail = p[1] if len(p) == 2 else ""
    return F(sign * int("".join(p)), 10 ** len(tail))


def isqrt(n):
    r = int(sqrt(n))
    while r * r > n:
        r -= 1
    while (r + 1) * (r + 1) <= n:
        r += 1
    return r


def rad(n):
    # sqrt(n) = k sqrt(m) for a whole n >= 0; m has no square factor
    k = 1
    f = 2
    while f * f <= n:
        while n % (f * f) == 0:
            k *= f
            n //= f * f
        f += 1
    return k, n


def rs(k, m, im):
    # Text for k (i) sqrt(m): "4i sqrt(3)", "2i", "sqrt(7)"
    if m == 1:
        if im:
            return ("" if k == 1 else str(k)) + "i"
        return str(k)
    t = ("" if k == 1 else str(k)) + ("i" if im else "")
    return (t + " " if t else "") + "sqrt(" + str(m) + ")"


def sqrt_text(R):
    # sqrt of a fraction in simplest radical form (i if negative)
    p, q = R
    k, m = rad(abs(p) * q)
    g = gcd(k, q)
    t = rs(k // g, m, p < 0)
    if q // g != 1:
        t += "/" + str(q // g)
    return t


def split(n):
    # sqrt of a whole number split up like the key:
    # -48 -> "sqrt(-1) * sqrt(16) * sqrt(3)", or None if nothing comes out
    k, m = rad(abs(n))
    parts = []
    if n < 0:
        parts.append("sqrt(-1)")
    if k > 1:
        parts.append("sqrt(" + str(k * k) + ")")
    if m > 1:
        parts.append("sqrt(" + str(m) + ")")
    return " * ".join(parts) if len(parts) > 1 else None


# ---------- writing math ----------

def term(c, p):
    # The size part of one term: "2x^2", "x", "(1/3)x", "21"
    m = (abs(c[0]), c[1])
    if p == 0:
        return fs(m)
    v = "x^2" if p == 2 else "x"
    if m == ONE:
        return v
    if m[1] != 1:
        return "(" + fs(m) + ")" + v
    return fs(m) + v


def expr(ts):
    # [(coefficient, power), ...] -> "2x^2 + 14x - 3x - 21"
    out = ""
    for c, p in ts:
        c = fr(c)
        if c[0] == 0:
            continue
        t = term(c, p)
        if out:
            out += (" - " if c[0] < 0 else " + ") + t
        else:
            out = ("-" if c[0] < 0 else "") + t
    return out or "0"


def poly(cs):
    # [a, b, c] -> "ax^2 + bx + c"; [m, n] -> "mx + n"
    n = len(cs)
    return expr([(cs[i], n - 1 - i) for i in range(n)])


def lead(a):
    # How a number looks in front of parentheses: "", "-", "4", "(1/3)"
    a = fr(a)
    if a == ONE:
        return ""
    if a == (-1, 1):
        return "-"
    if a[1] != 1:
        return "(" + fs(a) + ")"
    return fs(a)


def vform(a, h, k):
    # a(x - h)^2 + k
    h = fr(h)
    core = "x^2" if h[0] == 0 else "(" + poly([1, neg(h)]) + ")^2"
    return lead(a) + core + pm(k)


def pt(x, y):
    return "(" + fs(x) + ", " + fs(y) + ")"


def itx(c):
    # A number with i: "5i", "-i", "22/17 i"
    c = fr(c)
    if c[0] == 0:
        return "0"
    if c == ONE:
        return "i"
    if c == (-1, 1):
        return "-i"
    if c[1] != 1:
        return fs(c) + " i"
    return fs(c) + "i"


def cx(re, im):
    # a + bi: "10 + 6i", "3/17 + 22/17 i", "-21i"
    re = fr(re)
    im = fr(im)
    if im[0] == 0:
        return fs(re)
    if re[0] == 0:
        return itx(im)
    return fs(re) + (" - " if im[0] < 0 else " + ") + itx((abs(im[0]), im[1]))


def isum(ts):
    # [(number, "" or "i" or "i^2"), ...] -> "8 + 2i + 20i + 5i^2"
    out = ""
    for c, u in ts:
        c = fr(c)
        if c[0] == 0:
            continue
        m = (abs(c[0]), c[1])
        if not u:
            t = fs(m)
        elif m == ONE:
            t = u
        elif m[1] != 1:
            t = "(" + fs(m) + ")" + u
        else:
            t = fs(m) + u
        if out:
            out += (" - " if c[0] < 0 else " + ") + t
        else:
            out = ("-" if c[0] < 0 else "") + t
    return out or "0"


def over(re, im, den):
    # (re + im i) / den reduced, written like the key: "(3 + 22i)/17"
    re = fr(re)
    im = fr(im)
    den = fr(den)
    if re[1] != 1 or im[1] != 1 or den[1] != 1:
        return cx(div(re, den), div(im, den))
    g = gcd(gcd(re[0], im[0]), den[0])
    P, Q, R = re[0] // g, im[0] // g, den[0] // g
    if R == 1 or P == 0 or Q == 0:
        return cx(F(P, R), F(Q, R))
    return "(" + cx(P, Q) + ")/" + str(R)


def at(a, b, c, x):
    # ax^2 + bx + c at x
    return add(add(mul(a, mul(x, x)), mul(b, x)), c)


# ---------- quadratic work ----------

def disc(a, b, c):
    return b * b - 4 * a * c


def nature(D):
    if D > 0:
        s = isqrt(D)
        return "2 real roots (" + ("rational" if s * s == D else "irrational") + ")"
    if D == 0:
        return "1 real root (a double root)"
    return "2 complex (non-real) roots"


def rat_roots(a, b, c):
    # Zeros of ax^2 + bx + c (whole numbers, a != 0) as fractions,
    # smallest first (just one for a double root), or None if they
    # aren't rational
    D = disc(a, b, c)
    s = isqrt(D) if D >= 0 else -1
    if s * s != D:
        return None
    r = [F(-b - s, 2 * a), F(-b + s, 2 * a)]
    if val(r[0]) > val(r[1]):
        r = [r[1], r[0]]
    return r[:1] if D == 0 else r


def roots(a, b, c):
    # Zeros of ax^2 + bx + c (whole numbers, a != 0):
    # (exact text, decimal text)
    D = disc(a, b, c)
    r = rat_roots(a, b, c)
    if r:
        return (" and ".join(["x = " + fs(x) for x in r]),
                " and ".join(["x = " + dec(val(x)) for x in r]))
    k, m = rad(abs(D))
    P, Q, R = -b, k, 2 * a
    if R < 0:
        P, R = -P, -R
    g = gcd(gcd(P, Q), R)
    P, Q, R = P // g, Q // g, R // g
    t = rs(Q, m, D < 0)
    t = (str(P) + " +/- " + t) if P else "+/- " + t
    if R != 1:
        t = "(" + t + ")/" + str(R) if P else t + "/" + str(R)
    w = Q * sqrt(m) / R
    if D < 0:
        d = "x = " + (dec(P / R) + " " if P else "") + "+/- " + dec(w) + "i"
    else:
        d = "x = " + dec(P / R - w) + " and x = " + dec(P / R + w)
    return "x = " + t, d


def standard(s):
    # [a, b, c, d, e, f] for ax^2 + bx + c = dx^2 + ex + f
    # -> whole numbers A, B, C (A > 0) and the work
    a, b, c, d, e, f = s
    cs = [sub(a, d), sub(b, e), sub(c, f)]
    lines = []
    if d[0] or e[0] or f[0]:
        lines += ["#MOVE EVERYTHING TO THE LEFT", poly(cs) + " = 0"]
    L, ws = whole(cs)
    if L > 1:
        lines += ["#TIMES " + str(L) + " TO CLEAR FRACTIONS", poly(ws) + " = 0"]
    if ws[0] < 0:
        ws = [-w for w in ws]
        lines += ["#TIMES -1 SO x^2 IS POSITIVE", poly(ws) + " = 0"]
    if lines and lines[-1] == poly(ws) + " = 0":
        lines = lines[:-1]
    head = ["#YOUR EQUATION", poly([a, b, c]) + " = " + poly([d, e, f])]
    if not lines:
        head = ["#ALREADY IN STANDARD FORM"]
    A, B, C = ws
    return A, B, C, len(head), head + lines + [
        "*" + poly(ws) + " = 0",
        "a = " + str(A) + ",  b = " + str(B) + ",  c = " + str(C)]


def disc_steps(A, B, C):
    D = disc(A, B, C)
    lines = ["D = b^2 - 4ac",
             "D = (" + str(B) + ")^2 - 4(" + str(A) + ")(" + str(C) + ")",
             "D = " + str(B * B) + pm(-4 * A * C),
             "*D = " + str(D) + (" > 0" if D > 0 else (" < 0" if D < 0 else "")),
             "#WHAT IT MEANS"]
    if D > 0:
        s = isqrt(D)
        lines.append("D > 0: 2 different real roots")
        if s * s == D:
            lines += [str(D) + " = " + str(s) + "^2, a perfect square,",
                      "so the roots are rational"]
        else:
            lines += [str(D) + " is not a perfect square,",
                      "so the roots are irrational"]
    elif D == 0:
        lines.append("D = 0: 1 real root (a double root)")
    else:
        lines += ["D < 0: no real roots, so", "2 complex (non-real) roots"]
    return lines + ["*" + nature(D)]


def pair(prod, s):
    # Two whole numbers that multiply to prod and add to s
    n = abs(prod)
    d = 1
    while d * d <= n:
        if n % d == 0:
            e = prod // d
            if d + e == s:
                return d, e
            if -d - e == s:
                return -d, -e
        d += 1
    return None


def fac(f):
    # A factor (m, n) as text: "(2x - 3)", or "x" for (1, 0)
    if f == (1, 0):
        return "x"
    return "(" + poly([f[0], f[1]]) + ")"


def factor_steps(A, B, C):
    # Factor like class: GCF first; then two numbers that multiply
    # to c and add to b (a = 1), or the AC method and grouping.
    # Returns (work, factors or None)
    lines = []
    g = gcd(gcd(A, B), C)
    a, b, c = A // g, B // g, C // g
    pre = str(g) if g > 1 else ""
    if g > 1:
        lines += ["#GCF IS " + str(g), pre + "(" + poly([a, b, c]) + ")"]
    if c == 0:
        lines += ["#FACTOR OUT x"]
        fs_ = [(1, 0), (a, b)]
    elif a == 1:
        two = pair(c, b)
        lines += ["#MULTIPLY TO " + str(c) + ", ADD TO " + str(b)]
        if two is None:
            return lines + ["no two whole numbers work", "*It doesn't factor.",
                            "Use completing the square", "or the quadratic formula."], None
        lines += [str(two[0]) + " and " + str(two[1])]
        fs_ = [(1, two[0]), (1, two[1])]
    else:
        ac = a * c
        two = pair(ac, b)
        lines += ["#a IS NOT 1: AC METHOD", "a(c) = " + str(a) + "(" + str(c) + ") = " + str(ac),
                  "#MULTIPLY TO " + str(ac) + ", ADD TO " + str(b)]
        if two is None:
            return lines + ["no two whole numbers work", "*It doesn't factor.",
                            "Use completing the square", "or the quadratic formula."], None
        p, q = two
        if gcd(a, q) > gcd(a, p):
            p, q = q, p
        G = gcd(a, p)
        m1 = a // G
        n1 = p // G
        k = q // m1
        bn = "(" + poly([m1, n1]) + ")"
        lines += [str(p) + " and " + str(q),
                  "#SPLIT THE MIDDLE", expr([(a, 2), (p, 1), (q, 1), (c, 0)]),
                  "#GROUP",
                  ("" if G == 1 else str(G)) + "x" + bn +
                  (" - " if k < 0 else " + ") + str(abs(k)) + bn]
        fs_ = [(G, k), (m1, n1)]
    if fs_[0] == fs_[1]:
        whole_ = pre + fac(fs_[0]) + "^2"
    else:
        whole_ = pre + fac(fs_[0]) + fac(fs_[1])
    lines += ["#FACTORED", "*" + whole_ + " = 0", "#ZERO PRODUCT: SET EACH FACTOR = 0"]
    done = []
    for f in fs_:
        if f in done:
            continue
        done.append(f)
        if f == (1, 0):
            lines.append("x = 0")
        elif f[0] == 1:
            lines.append(poly([1, f[1]]) + " = 0  ->  x = " + fs(-f[1]))
        else:
            # 2x - 3 = 0 -> 2x = 3 -> x = 3/2
            lines.append(poly([f[0], f[1]]) + " = 0 -> " + term((f[0], 1), 1) +
                         " = " + fs(-f[1]) + " -> x = " + fs(F(-f[1], f[0])))
    return lines + ["*" + roots(A, B, C)[0]], fs_


def half(b, h, h2):
    # "#HALF OF -4, SQUARED: (-2)^2 = 4", on two lines if it's long
    t = "(" + fs(h) + ")^2 = " + fs(h2)
    if len(fs(b) + t) > 17:
        return ["#HALF OF " + fs(b) + ", SQUARED", t]
    return ["#HALF OF " + fs(b) + ", SQUARED: " + t]


def square_steps(A, B, C):
    # Complete the square the textbook way: the number goes to
    # the left, the x's stay on the right (divide by a first if needed)
    lines = ["0 = " + poly([A, B, C])]
    b = F(B, A)
    c = F(C, A)
    if A != 1:
        lines += ["#DIVIDE EVERYTHING BY " + str(A), "0 = " + poly([1, b, c])]
    left = neg(c)
    if c[0]:
        lines += ["#MOVE THE CONSTANT (" + ("+" if left[0] > 0 else "") +
                  fs(left) + " BOTH SIDES)", fs(left) + " = " + poly([1, b, 0])]
    h = div(b, 2)
    h2 = mul(h, h)
    R = add(left, h2)
    if b[0]:
        lines += half(b, h, h2) + [
                  "#ADD " + fs(h2) + " TO BOTH SIDES",
                  (fs(left) + pm(h2) if c[0] else fs(h2)) + " = " + poly([1, b, h2]),
                  "#FACTOR THE RIGHT SIDE",
                  fs(R) + " = (" + poly([1, h]) + ")^2"]
    side = poly([1, h])
    lines.append("#SQUARE ROOT BOTH SIDES (+/-)")
    ex = roots(A, B, C)[0]
    if R[0] == 0:
        return lines + ["0 = " + side, "*" + ex]
    t = sqrt_text(R)
    lines.append("+/- sqrt(" + fs(R) + ") = " + side)
    if R[1] == 1 and split(R[0]):
        lines.append("#sqrt(" + fs(R) + ") = " + split(R[0]))
    if t != "sqrt(" + fs(R) + ")":
        lines.append("+/- " + t + " = " + side)
    if h[0]:
        last = "x = " + fs(neg(h)) + " +/- " + t
        lines.append("#" + ("ADD " + fs(neg(h)) + " TO" if h[0] < 0 else
                            "SUBTRACT " + fs(h) + " FROM") + " BOTH SIDES")
        if last != ex:
            lines.append(last)
    return lines + ["*" + ex]


def formula_steps(A, B, C):
    D = disc(A, B, C)
    lines = ["a = " + str(A) + ",  b = " + str(B) + ",  c = " + str(C),
             "#x = (-b +/- sqrt(b^2 - 4ac)) / (2a)",
             "b^2 - 4ac = (" + str(B) + ")^2 - 4(" + str(A) + ")(" + str(C) + ")"]
    if B and C:
        lines.append("          = " + str(B * B) + pm(-4 * A * C))
    lines += ["          = " + str(D),
              "x = (-(" + str(B) + ") +/- sqrt(" + str(D) + ")) / (2(" + str(A) + "))",
              "x = (" + str(-B) + " +/- sqrt(" + str(D) + ")) / " + str(2 * A)]
    s = isqrt(D) if D >= 0 else -1
    if s * s == D:
        lines.append("sqrt(" + str(D) + ") = " + str(s))
        if D:
            for sg in (" + ", " - "):
                r = F(-B + (s if sg == " + " else -s), 2 * A)
                lines.append("x = (" + str(-B) + sg + str(s) + ") / " +
                             str(2 * A) + " = " + fs(r))
    else:
        k, m = rad(abs(D))
        t = rs(k, m, D < 0)
        if split(D):
            lines += ["sqrt(" + str(D) + ") = " + split(D),
                      "          = " + t]
        else:
            lines.append("sqrt(" + str(D) + ") = " + t)
        lines.append("x = (" + str(-B) + " +/- " + t + ") / " + str(2 * A))
        g = gcd(gcd(B, k), 2 * A)
        if g > 1:
            # Every number on top and the bottom must share it
            ns = ([str(-B)] if B else []) + [str(k), str(2 * A)]
            lines.append("#" + ", ".join(ns[:-1]) + " AND " + ns[-1] +
                         (" ALL" if B else " BOTH") + " DIVIDE BY " + str(g))
    return lines + ["*" + roots(A, B, C)[0]]


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
    if k in DIV:
        if v and "/" not in v and v[-1] not in "-.":
            return v + "/"
        return v
    if len(k) == 1 and (k.isdigit() or k == "."):
        part = v.split("/")[-1]
        if (k == "." and "." in part) or len(v) >= 10:
            return v
        return v + k
    return None


def cell(x, y, w, h, v, cur, fresh):
    # One number box. The current box is colored; a fresh one is
    # filled in, meaning typing replaces it.
    if cur and fresh and v:
        box(x, y, w, h, ACCENT)
        text(x + 6, y + h - 6, v, WHITE)
        return
    box(x, y, w, h, SOFT if cur else WHITE)
    frame(x, y, w, h, ACCENT if cur else LINE)
    text(x + 6, y + h - 6, v + ("_" if cur else ""))


def form(title, rows, n, vals=None, note="", check=None):
    # Boxes laid out in rows of text and box numbers, like the
    # equation on paper. ">" puts a row's box in the right column.
    # Returns (numbers, texts) or None for esc; blank boxes give
    # None. check(nums) returns None or (message, box to fix).
    vals = list(vals) if vals else [""] * n
    gap = 40 if len(rows) <= 3 else 142 // len(rows)
    bh = min(26, gap - 6)
    i = 0
    fresh = True
    err = ""
    while True:
        start(title)
        for r in range(len(rows)):
            y = 36 + r * gap
            x = 10
            wide = ">" in rows[r]
            mine = i in rows[r]
            for p in rows[r]:
                if p == ">":
                    x = 176
                elif type(p) == str:
                    if wide and mine:
                        bold(x, y + bh - 7, p, ACCENT)
                    else:
                        text(x, y + bh - 7, p)
                    x += CW * len(p)
                else:
                    w = W - 10 - x if wide else 52
                    cell(x, y, w, bh, vals[p], p == i, fresh)
                    x += w + 4
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
                if vals[f] == "":
                    nums.append(None)
                    continue
                try:
                    nums.append(num(vals[f]))
                except ValueError:
                    err = "That box isn't a number"
                    i = f
                    fresh = True
                    break
            bad = None if err or not check else check(nums)
            if bad:
                err, i = bad
                fresh = True
            if not err:
                return nums, vals


def zeros(nums):
    # Blank boxes count as 0
    return [v or ZERO for v in nums]


# ---------- remembering the last numbers ----------
# Each tool's last boxes go in a calculator list (algin1 ... algin7,
# algin0 for the menu), so they come back after quitting. The list
# holds each box's length, then one number per letter.

CH = "0123456789-./"
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
        store_list("algin" + str(n), out)
    except Exception:
        pass


def recall(n, count):
    # The last boxes for tool n, or None
    if n in LAST:
        return list(LAST[n])
    try:
        got = [int(round(x)) for x in recall_list("algin" + str(n))]
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
            text(160, y, parts[1], c)
        y += 19
    more = len(lines) > top + 8
    if more or top:
        scroll(30, 155, top, 8, len(lines))
    return more


def draw_answers(items):
    y = 34
    for lab, v in items:
        box(6, y, W - 12, 44, SOFT)
        box(6, y, 4, 44, ACCENT)
        text(18, y + 17, lab, MUTED)
        bold(18, y + 37, v, ACCENT)
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


def graph(curves, pts, xs, ys, axis=None):
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
    if axis is not None:
        yy = T
        while yy < B:
            line(X(axis), yy, X(axis), min(yy + 4, B), FAINT)
            yy += 8
    for f, c in curves:
        col(c)
        pen("medium")
        n = 72
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


def parab(a, b, c):
    va = val(a)
    vb = val(b)
    vc = val(c)
    return lambda x: va * x * x + vb * x + vc


# ---------- 1: transform x^2 ----------

def transform():
    rows = [["Stretch / shrink by", ">", 0],
            ["Move right (- = left)", ">", 1],
            ["Move up (- = down)", ">", 2]]
    vals = recall(1, 3)
    while True:
        got = form("TRANSFORM x^2", rows, 3, vals,
                   "Reflected? Put a minus on the first box",
                   lambda v: ("The stretch can't be 0", 0)
                   if v[0] is not None and v[0][0] == 0 else None)
        if got is None:
            return
        nums, vals = got
        remember(1, vals)
        a = nums[0] or ONE
        h, k = zeros(nums[1:])
        aa = (abs(a[0]), a[1])
        lines = ["#START", "f(x) = x^2"]
        if aa != ONE:
            lines += ["#" + ("SHRINK (COMPRESS)" if val(aa) < 1 else "STRETCH") +
                      " BY " + fs(aa), vform(aa, 0, 0)]
        if a[0] < 0:
            lines += ["#REFLECT OVER THE x-AXIS", vform(a, 0, 0)]
        if h[0]:
            lines += ["#" + ("RIGHT " if h[0] > 0 else "LEFT ") + fs((abs(h[0]), h[1])) +
                      ": x BECOMES (" + poly([1, neg(h)]) + ")", vform(a, h, 0)]
        if k[0]:
            kk = fs((abs(k[0]), k[1]))
            lines += ["#" + ("UP " + kk + ": ADD " if k[0] > 0 else "DOWN " + kk + ": SUBTRACT ") +
                      kk + " AT THE END", vform(a, h, k)]
        lines += ["*g(x) = " + vform(a, h, k),
                  "vertex " + pt(h, k) + ", opens " + ("up" if a[0] > 0 else "down")]
        g = parab(a, mul(-2, mul(a, h)), add(mul(a, mul(h, h)), k))

        def pic():
            graph([(lambda x: x * x, LINE), (g, ACCENT)],
                  [(val(h), val(k), pt(h, k))], [0, val(h)], [0, val(k)])
            box(12, 33, CW * 23 + 4, 16, WHITE)
            text(14, 46, "gray: x^2   color: g(x)", MUTED)

        view([("text", "STEPS", lines), ("draw", "PICTURE", pic)])


# ---------- 2: square root of a negative ----------

def radicals():
    vals = recall(2, 2)
    while True:
        got = form("SQUARE ROOTS", [[0, "  sqrt(", 1, " )"]], 2, vals,
                   "Blank first box = 1. Negative inside ok",
                   lambda v: ("Type the number inside", 1) if v[1] is None
                   else (("Use a whole number inside", 1) if v[1][1] != 1 else None))
        if got is None:
            return
        nums, vals = got
        remember(2, vals)
        view([("text", "SIMPLIFY", radical_steps(nums[0] or ONE, nums[1][0]))])


def radical_steps(c, n):
    # c sqrt(n) like the key: split off sqrt(-1) and the biggest
    # perfect square, -3 sqrt(-98) = -3 * sqrt(-1) * sqrt(49) * sqrt(2)
    k, m = rad(abs(n))
    orig = (lead(c) + " " if c != ONE else "") + "sqrt(" + str(n) + ")"
    if c == (-1, 1):
        orig = "-sqrt(" + str(n) + ")"
    co = mul(c, k)
    if n == 0:
        res = "0"
    else:
        sg = "-" if co[0] < 0 else ""
        co = (abs(co[0]), co[1])
        if co[1] == 1:
            res = sg + rs(co[0], m, n < 0)
        else:
            res = sg + "(" + fs(co) + ")" + ("i" if n < 0 else "") + \
                (" sqrt(" + str(m) + ")" if m > 1 else "")
    lines = []
    if k > 1:
        lines.append("#BIGGEST PERFECT SQUARE IN " + str(abs(n)) + ": " + str(k * k))
    elif n > 1:
        lines.append("#NO PERFECT SQUARE GOES INTO " + str(n))
    if n < 0:
        lines.append("#NEGATIVE INSIDE: sqrt(-1) = i")
    if n < 0 or k > 1:
        # The pieces, then what each piece comes out to
        pre = [] if c == ONE else [fs(c) if c[1] == 1 else "(" + fs(c) + ")"]
        pieces = pre + (split(n) or "sqrt(" + str(n) + ")").split(" * ")
        got = ([] if n > 0 else ["i"]) + ([str(k)] if k > 1 else []) + \
            (["sqrt(" + str(m) + ")"] if m > 1 else [])
        lines.append(orig)
        if len(pieces) > 1:
            lines.append("= " + " * ".join(pieces))
        lines.append("= " + " * ".join(pre + got))
        if c != ONE and k > 1:
            lines.append("#MULTIPLY THE NUMBERS: " + pre[0] + "(" + str(k) + ") = " +
                         fs(mul(c, k)))
    return lines + ["*" + orig + " = " + res]


# ---------- 3: solve (factor, square, formula) ----------

EQ = [[0, " x^2 + ", 1, " x + ", 2], ["="], [3, " x^2 + ", 4, " x + ", 5]]


def solve_ok(v):
    v = zeros(v)
    if sub(v[0], v[3])[0] == 0:
        return "No x^2 term left: not a quadratic", 0
    return None


def solve():
    vals = recall(3, 6)
    while True:
        got = form("SOLVE A QUADRATIC", EQ, 6, vals,
                   "Blank = 0. Right side usually blank", solve_ok)
        if got is None:
            return
        nums, vals = got
        remember(3, vals)
        A, B, C, nh, std = standard(zeros(nums))
        ex, dx = roots(A, B, C)
        view([("text", "STANDARD FORM", std),
              ("text", "DISCRIMINANT", disc_steps(A, B, C)),
              ("text", "FACTORING", factor_steps(A, B, C)[0]),
              ("text", "COMPLETE THE SQUARE", square_steps(A, B, C)),
              ("text", "QUADRATIC FORMULA", formula_steps(A, B, C)),
              ("ans", "ANSWER", [("Zeros", ex), ("As decimals", dx),
                                 ("Nature of the roots", nature(disc(A, B, C)))])])


# ---------- 4: parabola facts ----------

def parabola():
    vals = recall(4, 3)
    while True:
        got = form("PARABOLA", [["y = ", 0, " x^2 + ", 1, " x + ", 2]], 3, vals,
                   "Blank = 0.  Use / for fractions",
                   lambda v: ("a can't be 0 (that's a line)", 0)
                   if not v[0] or v[0][0] == 0 else None)
        if got is None:
            return
        nums, vals = got
        remember(4, vals)
        view(parabola_pages(*zeros(nums)))


def parabola_pages(a, b, c):
    h = div(neg(b), mul(2, a))
    k = at(a, b, c, h)
    up = a[0] > 0
    # Vertex by x = -b / 2a, then plug in
    plug = [lead(a) + "(" + fs(h) + ")^2"]
    vals_ = [fs(mul(a, mul(h, h)))]
    if b[0]:
        bb = (abs(b[0]), b[1])
        plug.append((" - " if b[0] < 0 else " + ") +
                    ("" if bb == ONE else fs(bb)) + "(" + fs(h) + ")")
        vals_.append(pm(mul(b, h)) or " + 0")
    if c[0]:
        plug.append(pm(c))
        vals_.append(pm(c))
    vx = ["x = -b / (2a)",
          "x = -(" + fs(b) + ") / (2(" + fs(a) + "))",
          "x = " + fs(neg(b)) + " / " + fs(mul(2, a)),
          "*x = " + fs(h),
          "#PLUG IN x = " + fs(h),
          "y = " + "".join(plug),
          "y = " + "".join(vals_),
          "*y = " + fs(k),
          "*vertex: " + pt(h, k)]
    # Table centered on the vertex
    mid = int(val(h) // 1 + (1 if val(h) % 1 >= 0.5 else 0))
    xs = [mid + d for d in (-2, -1, 0, 1, 2)]
    ys = [at(a, b, c, x) for x in xs]
    L, ws = whole([a, b, c])
    D = disc(ws[0], ws[1], ws[2])
    ex = roots(ws[0], ws[1], ws[2])[0]
    many = 2 if D > 0 else (1 if D == 0 else 0)
    # x-intercepts are points; zeros are just the x's (from the review)
    zs = rat_roots(ws[0], ws[1], ws[2])
    if D < 0:
        xi = "none (it never crosses)"
    elif zs:
        xi = " and ".join([pt(z, 0) for z in zs])
    else:
        w = sqrt(D) / (2 * abs(ws[0]))
        xi = "about (" + dec(val(h) - w) + ", 0) and (" + dec(val(h) + w) + ", 0)"
    q = ["#AXIS OF SYMMETRY", "*x = " + fs(h),
         "#VERTEX", "*" + pt(h, k),
         "#Y-INTERCEPT", "*" + pt(0, c),
         "#MAXIMUM OR MINIMUM?",
         "*" + ("minimum (opens up, a > 0)" if up else "maximum (opens down, a < 0)"),
         "#" + ("MINIMUM" if up else "MAXIMUM") + " VALUE", "*y = " + fs(k),
         "#HOW MANY x-INTERCEPTS?", "*" + str(many) + "   (D = " + str(D) + ")",
         "#x-INTERCEPTS (POINTS)", "*" + xi,
         "#ZEROS (JUST THE x VALUES)", "*" + (ex if D >= 0 else "none real: " + ex),
         "#DOMAIN AND RANGE",
         "*all real x;  y " + (">= " if up else "<= ") + fs(k)]
    f = parab(a, b, c)
    pts = [(val(h), val(k), pt(h, k)), (0, val(c), pt(0, c))]
    xs_ = [val(h), 0]
    if D > 0:
        w = sqrt(D) / (2 * abs(ws[0]))
        exact = isqrt(D) ** 2 == D
        for z in (val(h) - w, val(h) + w):
            xs_.append(z)
            if abs(z) < 1e-9 and c[0] == 0:
                continue  # same point as the y-intercept
            lab = fs(F(int(round(z * 2 * ws[0])), 2 * ws[0])) if exact else dec(z)
            pts.append((z, 0, "(" + lab + ", 0)"))

    def tab():
        cw = 52
        x0 = 10
        y0 = 40
        box(x0, y0, 28, 52, SOFT)
        text(x0 + 10, y0 + 18, "x")
        text(x0 + 10, y0 + 44, "y")
        for j in range(5):
            bx = x0 + 28 + j * cw
            if fr(xs[j]) == h:
                box(bx, y0, cw, 52, SOFT)
            frame(bx, y0, cw, 26, LINE)
            frame(bx, y0 + 26, cw, 26, LINE)
            sx_ = fs(xs[j])
            sy_ = fs(ys[j])
            text(bx + cw / 2 - CW * len(sx_) / 2, y0 + 18, sx_)
            text(bx + cw / 2 - CW * len(sy_) / 2, y0 + 44, sy_, ACCENT)
        frame(x0, y0, 28 + 5 * cw, 52, MUTED)
        text(12, 118, "x's are centered on the vertex,", MUTED)
        text(12, 136, "x = " + fs(h) + " (the axis of symmetry).", MUTED)
        text(12, 154, "Matching y's on each side show", MUTED)
        text(12, 172, "the symmetry.", MUTED)

    def pic():
        graph([(f, ACCENT)], pts, xs_, [val(k), val(c)], val(h))

    return [("text", "VERTEX", vx),
            ("text", "VERTEX FORM: y =", vform_steps(a, b, c, "y")),
            ("text", "VERTEX FORM: 0 =", vform_steps(a, b, c, "0")),
            ("draw", "TABLE", tab),
            ("draw", "GRAPH", pic),
            ("text", "QUESTIONS", q)]


def vform_steps(a, b, c, y):
    # Vertex form like class: constant to the left, factor out a, add
    # (half of b)^2 inside and a times it on the left. y is "y" for
    # y = ..., or "0" for 0 = ... (for an equation set equal to 0)
    h = div(neg(b), mul(2, a))
    k = at(a, b, c, h)
    lines = [y + " = " + poly([a, b, c])]
    if b[0] == 0:
        return lines + ["#NO x TERM, SO h = 0:", "#IT'S ALREADY IN VERTEX FORM",
                        "*" + y + " = " + vform(a, h, k), "*vertex: " + pt(h, k)]

    def side(v):
        # The left side holding the number v: "y - 10" or "-10"
        return y + pm(v) if y == "y" else fs(v)

    if c[0]:
        lines += ["#MOVE THE CONSTANT TO THE LEFT", side(neg(c)) + " = " + poly([a, b, 0])]
    bb = div(b, a)
    if a != ONE:
        lines += ["#FACTOR OUT " + fs(a),
                  side(neg(c)) + " = " + lead(a) + "(" + poly([1, bb, 0]) + ")"]
    hh = div(bb, 2)
    h2 = mul(hh, hh)
    add_ = mul(a, h2)
    lines += half(bb, hh, h2) + [
              "#ADD " + fs(h2) + (" TO BOTH SIDES" if a == ONE else
                                 " INSIDE, " + fs(add_) + " ON THE LEFT"),
              side(neg(c)) + pm(add_) + " = " + lead(a) + "(" + poly([1, bb, h2]) + ")",
              side(sub(add_, c)) + " = " + vform(a, h, 0)]
    if sub(add_, c)[0]:
        lines.append("#BRING THE CONSTANT BACK")
    return lines + ["*" + y + " = " + vform(a, h, k), "*vertex: " + pt(h, k)]


# ---------- 5: complex numbers ----------

def times(a, b, c, d):
    # (a + bi)(c + di) like the key: FOIL into one line, or just
    # distribute when one side is a single term like 2i.
    # Returns (how, lines, real, imaginary)
    ac = mul(a, c)
    ad = mul(a, d)
    bc = mul(b, c)
    bd = mul(b, d)
    how = "FOIL"
    if a[0] == 0 or b[0] == 0 or c[0] == 0 or d[0] == 0:
        how = "DISTRIBUTE"
    lines = [isum([(ac, ""), (ad, "i"), (bc, "i"), (bd, "i^2")])]
    if bd[0]:
        lines += ["#i^2 = -1, SO " + isum([(bd, "i^2")]) + " = " + fs(neg(bd)),
                  isum([(ac, ""), (ad, "i"), (bc, "i"), (neg(bd), "")])]
    return how, lines, sub(ac, bd), add(ad, bc)


def grp(re, im):
    # A complex number ready to multiply: "2i", "(4 - i)"
    t = cx(re, im)
    if (re[0] == 0 or im[0] == 0) and "/" not in t:
        return t
    return "(" + t + ")"


def sq(x):
    # x squared as written on the key: "4^2", "(-3)^2"
    return fs(x) + "^2" if x[1] == 1 and x[0] >= 0 else "(" + fs(x) + ")^2"


def complex_tool():
    ops = ["times", "divided by", "plus", "minus"]
    o = 0
    while True:
        o = pick("COMPLEX NUMBERS", ["Multiply  (a + bi)(c + di)", "Divide  (a + bi) / (c + di)",
                                     "Add", "Subtract"],
                 "1-4 or arrows + enter    esc: back", o)
        if o is None:
            return
        rows = [["( ", 0, " + ", 1, " i )"], [ops[o]], ["( ", 2, " + ", 3, " i )"]]
        vals = recall(5, 4)
        while True:
            got = form("COMPLEX: " + ops[o].upper(), rows, 4, vals,
                       "2i alone: leave its first box blank",
                       lambda v: ("Can't divide by 0", 2)
                       if o == 1 and not (v[2] and v[2][0]) and not (v[3] and v[3][0])
                       else None)
            if got is None:
                break
            nums, vals = got
            remember(5, vals)
            a, b, c, d = zeros(nums)
            z1 = "(" + cx(a, b) + ")"
            z2 = "(" + cx(c, d) + ")"
            whole_ = None
            if o == 0:
                how, top, re, im = times(a, b, c, d)
                lines = [grp(a, b) + z2, "#" + how] + top
            elif o == 1 and d[0] == 0:
                # Dividing by a plain number: split it up
                lines = [z1 + " / " + fs(c), "#DIVIDE EACH PART BY " + fs(c)]
                re = div(a, c)
                im = div(b, c)
            elif o == 1:
                # Like the key: times the conjugate on top and bottom;
                # the bottom is c^2 + d^2
                con = cx(c, neg(d))
                how, top, re, im = times(a, b, c, neg(d))
                den = add(mul(c, c), mul(d, d))
                lines = [z1 + " / " + z2,
                         "#TIMES (" + con + ") ON TOP AND BOTTOM",
                         "#(THE CONJUGATE OF THE BOTTOM)",
                         "#TOP: " + how + " " + grp(a, b) + "(" + con + ")"] + top + [
                         "= " + cx(re, im),
                         "#BOTTOM: " + sq(c) + " + " + sq((abs(d[0]), d[1])) +
                         " = " + fs(den)]
                whole_ = over(re, im, den)
                re = div(re, den)
                im = div(im, den)
            else:
                s = 1 if o == 2 else -1
                lines = [z1 + (" + " if s > 0 else " - ") + z2,
                         "#REAL PARTS TOGETHER, i PARTS TOGETHER",
                         "(" + fs(a) + pm(mul(s, c)) + ") + (" + fs(b) + pm(mul(s, d)) + ")i"]
                re = add(a, mul(s, c))
                im = add(b, mul(s, d))
            ans = cx(re, im)
            if whole_ and whole_ != ans:
                view([("text", "WORK", lines + ["*" + whole_]),
                      ("ans", "ANSWER", [("As one fraction (like the key)", whole_),
                                         ("Split into a + bi form", ans)])])
            else:
                view([("text", "WORK", lines + ["*" + ans]),
                      ("ans", "ANSWER", [("In a + bi form", ans)])])


# ---------- 6: system: parabola and line ----------

def system():
    rows = [["y = ", 0, " x^2 + ", 1, " x + ", 2], ["y = ", 3, " x + ", 4]]
    vals = recall(6, 5)
    while True:
        got = form("SYSTEM: PARABOLA + LINE", rows, 5, vals,
                   "Line: y = mx + b (y-2x=6 -> y=2x+6)",
                   lambda v: ("The parabola needs an x^2 number", 0)
                   if not v[0] or v[0][0] == 0 else None)
        if got is None:
            return
        nums, vals = got
        remember(6, vals)
        view(system_pages(*zeros(nums)))


def system_pages(a, b, c, m, k):
    A, B, C, nh, std = standard([a, b, c, ZERO, m, k])
    eq = ["#BOTH ARE y, SO SET THEM EQUAL",
          poly([a, b, c]) + " = " + poly([m, k])] + std[nh:]
    work, fs_ = factor_steps(A, B, C)
    if fs_ is None:
        work = ["#IT DOESN'T FACTOR: QUADRATIC FORMULA"] + formula_steps(A, B, C)
    D = disc(A, B, C)
    pts = []
    find = []
    s = isqrt(D) if D >= 0 else -1
    if D < 0:
        find = ["No real x, so the line and the", "parabola never cross.",
                "*no real solution"]
    elif s * s == D:
        xs = [F(-B - s, 2 * A), F(-B + s, 2 * A)]
        if val(xs[0]) > val(xs[1]):
            xs = [xs[1], xs[0]]
        if D == 0:
            xs = xs[:1]
        for x in xs:
            y = add(mul(m, x), k)
            find += ["#x = " + fs(x), "y = " + lead(m) + "(" + fs(x) + ")" + pm(k) +
                     " = " + fs(y), "*" + pt(x, y)]
            pts.append((val(x), val(y), pt(x, y)))
    else:
        w = sqrt(D) / (2 * A)
        for x in (-B / (2 * A) - w, -B / (2 * A) + w):
            y = val(m) * x + val(k)
            find += ["#x = " + dec(x), "y = " + lead(m) + "(" + dec(x) + ")" + pm(k) +
                     " = " + dec(y), "*(" + dec(x) + ", " + dec(y) + ")"]
            pts.append((x, y, "(" + dec(x) + ", " + dec(y) + ")"))
        find = ["#EXACT: " + roots(A, B, C)[0]] + find
    how = ["0: they never cross", "1: the line just touches", "2: the line crosses twice"]
    f = parab(a, b, c)
    vm = val(m)
    vk = val(k)
    h = -val(b) / (2 * val(a))

    def pic():
        graph([(f, ACCENT), (lambda x: vm * x + vk, INK)], pts,
              [p[0] for p in pts] + [h], [p[1] for p in pts] + [f(h), vk])

    return [("text", "SET EQUAL", eq),
            ("text", "SOLVE FOR x", work),
            ("text", "FIND y", find),
            ("draw", "PICTURE", pic),
            ("ans", "ANSWER", [("Solutions", " and ".join([p[2] for p in pts]) or "none (no real solution)"),
                               ("How many", how[len(pts)])])]


# ---------- 7: vertex + point -> equation ----------

def vertex_point():
    rows = [["vertex  (", 0, " , ", 1, " )"], ["point   (", 2, " , ", 3, " )"]]
    vals = recall(7, 4)
    while True:
        got = form("VERTEX + POINT", rows, 4, vals, "Fractions: use the / key", vp_ok)
        if got is None:
            return
        nums, vals = got
        remember(7, vals)
        h, k, x, y = nums
        d = sub(x, h)
        sq = mul(d, d)
        a = div(sub(y, k), sq)
        lines = ["y = a(x - h)^2 + k",
                 "#PUT IN THE VERTEX " + pt(h, k),
                 "y = a" + vform(ONE, h, k),
                 "#PUT IN THE POINT " + pt(x, y),
                 fs(y) + " = a(" + fs(x) + pm(neg(h)) + ")^2" + pm(k),
                 fs(y) + " = a(" + fs(d) + ")^2" + pm(k),
                 fs(y) + " = " + lead(sq) + "a" + pm(k),
                 fs(sub(y, k)) + " = " + lead(sq) + "a",
                 "*a = " + fs(a),
                 "*y = " + vform(a, h, k)]
        f = parab(a, mul(-2, mul(a, h)), add(mul(a, mul(h, h)), k))

        def pic():
            graph([(f, ACCENT)], [(val(h), val(k), pt(h, k)), (val(x), val(y), pt(x, y))],
                  [val(h), val(x)], [val(k), val(y)], val(h))

        view([("text", "STEPS", lines), ("draw", "PICTURE", pic)])


def vp_ok(v):
    for j in range(4):
        if v[j] is None:
            return "Fill in all four boxes", j
    if v[2] == v[0]:
        return "The point needs a different x", 2
    if v[3] == v[1]:
        return "That makes a = 0 (not a parabola)", 3
    return None


# ---------- 8: help ----------

def help_page():
    view([("text", "WHICH ONE?", [
        "#x^2 MOVED, STRETCHED, REFLECTED",
        "*1  Transform x^2",
        "#sqrt OF A NEGATIVE NUMBER",
        "*2  Square roots",
        "#ZEROS / ROOTS / DISCRIMINANT",
        "*3  Solve (factor, square, formula)",
        "#VERTEX, VERTEX FORM, TABLE, GRAPH",
        "*4  Parabola",
        "#VERTEX FORM: PAGE 2 (y =), 3 (0 =)",
        "#(a + bi) TIMES, DIVIDED, + OR -",
        "*5  Complex numbers",
        "#y = PARABOLA AND y = LINE",
        "*6  System",
        "#GIVEN THE VERTEX AND A POINT",
        "*7  Vertex + point"]),
        ("text", "FORMULAS", [
        "vertex:  x = -b / (2a)",
        "x = (-b +/- sqrt(b^2 - 4ac)) / (2a)",
        "D = b^2 - 4ac",
        "D > 0: 2 real\tD = 0: 1 real",
        "D < 0: 2 complex (non-real)",
        "vertex form:  y = a(x - h)^2 + k",
        "i = sqrt(-1)\ti^2 = -1",
        "conjugate of a + bi:  a - bi",
        "zeros: x = 3\tx-intercepts: (3, 0)"]),
        ("text", "COMPLETING THE SQUARE", [
        "1. Move the constant to the left",
        "2. Half of b, then square it",
        "3. Add that to both sides",
        "4. Factor: number = (x + b/2)^2",
        "5. Square root both sides: +/- !",
        "6. Simplify the radical, solve",
        "#VERTEX FORM: SAME IDEA, BUT KEEP y",
        "#(OR 0) AND FACTOR OUT a FIRST"]),
        ("text", "KEYS", [
        "arrows\tmove, change page",
        "enter\tnext box / solve",
        "1 - 8\topen from the menu",
        "/ key\tfractions like 1/3",
        "(-)\tnegative number",
        "del\terase",
        "esc\tgo back one screen",
        "last numbers\tkept: type over them",
        "home, menu\tquit right away",
        "blank box\tcounts as 0"])])


# ---------- menu ----------

def menu():
    items = [("Transform x^2", transform),
             ("Square roots (with i)", radicals),
             ("Solve: factor, square, formula", solve),
             ("Parabola: vertex form, graph", parabola),
             ("Complex numbers", complex_tool),
             ("System: parabola + line", system),
             ("Vertex + point -> equation", vertex_point),
             ("Help: which one? + formulas", help_page)]
    last = recall(0, 1)
    i = int(last[0]) if last and last[0] and last[0] in "01234567" else 0
    while True:
        try:
            j = pick("ALGEBRA SOLVER", [t[0] for t in items],
                     "1-8 or arrows + enter: open    esc: quit", i, "Topic 2")
            if j is None:
                return
            i = j
            remember(0, [str(j)])
            items[j][1]()
        except Home:
            return


menu()
