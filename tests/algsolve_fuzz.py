# Random problems: the program's answers checked against plain arithmetic
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake"))
os.environ.setdefault("KEYS", ""); os.environ.setdefault("SHOTS", "/tmp")
src = open(sys.argv[1]).read().rsplit("\nmenu()", 1)[0]
M = {}; exec(src, M)
from fractions import Fraction as Fr
random.seed(11)
def num():
    r = random.random()
    if r < 0.75: n = random.randint(1, 12); return str(n), Fr(n)
    if r < 0.9: a, b = random.randint(1, 9), random.randint(2, 9); return "%d/%d" % (a, b), Fr(a, b)
    a = random.randint(1, 99); return "%d.%02d" % (a // 10, a % 100) if False else ("0.%02d" % a), Fr(a, 100)
def mono(vs):
    # (text, function of env)
    c, cv = num() if random.random() < 0.7 else ("", Fr(1))
    t = c; ps = []
    for v in random.sample(vs, random.randint(0, len(vs))):
        p = random.randint(1, 4)
        t += v + ("^%d" % p if p > 1 or random.random() < 0.1 else "")
        ps.append((v, p))
    if not t: t, cv = "1", Fr(1)
    return t, (lambda env, cv=cv, ps=ps: cv * __import__("functools").reduce(lambda a, b: a * b, [env[v] ** p for v, p in ps], Fr(1)))
def summ(vs, n, depth):
    parts = []; fs_ = []
    for j in range(n):
        sg = random.choice("+-") if j or random.random() < 0.2 else ""
        t, f = prod(vs, depth) if depth and random.random() < 0.45 else mono(vs)
        parts.append((sg if sg != "+" or j else "") + t if j == 0 else sg + t)
        fs_.append((-1 if sg == "-" else 1, f))
    return "".join(parts), (lambda env, fs_=fs_: sum(s * f(env) for s, f in fs_))
def prod(vs, depth):
    t = ""; fl = []
    if random.random() < 0.3:
        mt, mf = mono(vs); t += mt; fl.append((mf, 1))
    for j in range(random.randint(1, 3 if depth > 1 else 2)):
        st, sf = summ(vs, random.randint(2, 3), depth - 1 if random.random() < 0.15 else 0)
        p = 2 if random.random() < 0.15 else 1
        t += ("*" if t and random.random() < 0.1 else "") + "(" + st + ")" + ("^2" if p == 2 else "")
        fl.append((sf, p))
    return t, (lambda env, fl=fl: __import__("functools").reduce(lambda a, b: a * b, [f(env) ** p for f, p in fl], Fr(1)))
def pv(terms, env):
    return sum(Fr(c[0], c[1]) * __import__("functools").reduce(lambda a, b: a * b, [env[v] ** p for v, p in k], Fr(1)) for c, k in terms)
bad = 0; n = 0; wide = 0; widest = ""
for trial in range(4000):
    vs = random.choice([["x"], ["x"], ["n"], ["a", "b"], ["x", "y"]])
    s, f = summ(vs, random.randint(1, 3), 2)
    if len(s) > 60: continue
    n += 1
    try:
        M["DEC"][0] = "." in s
        e = M["parse"](s)
        envs = [{v: Fr(random.randint(-5, 5), random.randint(1, 3)) for v in "abnxy"} for _ in range(3)]
        got = M["ev"](e)
        for env in envs:
            assert pv(got, env) == f(env), "ev"
        lines, res, boxes = M["simplify_steps"](e)
        for env in envs:
            assert pv(res, env) == f(env), "steps answer"
        assert len(res) == len(M["combine"](res)), "like terms left"
        assert lines[-1][:1] == "*"
        # reading it back gives the same thing
        back = M["etext"](e).replace(" ", "")
        for env in envs[:1]:
            assert pv(M["ev"](M["parse"](back)), env) == f(env), "etext round trip"
        for l in lines:
            w = len(l.lstrip("*#").split("\t")[0])
            if w > 42:
                wide += 1; widest = l
        if len(vs) == 1 and res:
            pages = M["classify_pages"](e, M["order"](got), vs[0])
            d = M["kdeg"](res[0][1])
            assert all(M["kdeg"](t[1]) < d for t in res[1:]), "standard form order"
            a = Fr(random.randint(-4, 4), random.choice([1, 1, 2]))
            vl, total = M["value_steps"](res, vs[0], (a.numerator, a.denominator))
            assert Fr(total[0], total[1]) == f({vs[0]: a, "b": 0, "y": 0, "a": a, "n": a, "x": a}), "plug in"
    except Exception as ex:
        bad += 1
        if bad < 8: print("FAIL", repr(s), repr(ex)[:200])
print("checked", n, "random problems; failures:", bad, "; lines too wide:", wide, widest[:80])
# things that must be refused, not crash
for s in ["", "(", "x+", "x^", "x^-2", "2x/3", "(x+1", "x+1)", "3*", "*x", "x^2^3", "1/0", "()", "x^100", "1..2", "(x+1)^9"]:
    try:
        M["parse"](s); print("NOT REFUSED:", repr(s))
    except M["Bad"] as b:
        pass
print("bad typing is refused cleanly")
