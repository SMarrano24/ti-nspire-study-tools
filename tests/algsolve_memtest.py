# Runs the program several times with one shared set of calculator lists
import os, sys, glob, re, subprocess, json
SP = os.path.dirname(os.path.abspath(__file__)); PROG = sys.argv[1]
NAMED = ("enter","esc","up","down","left","right","del","tab","menu","home")
def k(*parts):
    out = []
    for p in parts: out += [p] if p in NAMED else list(p)
    return out
E = "enter"
def run(title, keys, store):
    shots = SP + "/shots"
    for f in glob.glob(shots + "/s*.svg"): os.remove(f)
    env = dict(os.environ, KEYS=",".join(keys), SHOTS=shots, PYTHONPATH=SP + "/fake")
    if store: env["STORE"] = store
    else: env.pop("STORE", None)
    p = subprocess.run([sys.executable, PROG], env=env, capture_output=True, text=True)
    print("=" * 6, title, "rc", p.returncode, p.stderr[-400:])
    last = None
    for f in sorted(glob.glob(shots + "/s*.svg")):
        body = open(f).read()
        t = re.findall(r'<text[^>]*>([^<]*)</text>', body)
        if "enter:" not in t[-1] and "1-5" not in t[-1]: continue
        typedline = "".join(x for x in t[1:-1] if len(x) == 1)
        picked = [t[j] for j in range(1, len(t) - 1) if j + 1 < len(t) and t[j] == t[j + 1]]
        filled = 'fill="rgb(0,122,148)"/><rect' in body and 'height="24" fill="rgb(0,122,148)"' in body
        sig = t[0] + " | typed: " + typedline.replace("&lt;", "<") + " | bold: " + ", ".join(picked) + (" | FILLED (type over)" if filled else "")
        if sig != last: print("  ", os.path.basename(f), sig[:170])
        last = sig
st = SP + "/store.json"
if os.path.exists(st): os.remove(st)
run("run 1: type in tools 2, 3, 4, quit with home", k("2","(2x-7)^2",E,"esc","esc","3","x^2+1",E,"5",E,"esc","esc","4","x+4",E,"x+15",E,"home"), st)
print("   lists saved:", sorted(json.load(open(st)).keys()))
run("run 2: restart; menu sits on 4; every tool is filled in", k("enter","esc","2","esc","3","esc","1","esc","home"), st)
json.dump({"alg3n2": [99.0, 1.0], "alg3n0": [1.0, 44.0], "alg3n3": [1.0, 55.0, 0.0]}, open(st, "w"))
run("run 3: broken saved data must not crash", k("2","esc","3","esc","home"), st)
run("run 4: no calculator lists at all", k("2","x+x",E,"esc","esc","2","home"), None)
