import os, sys, glob, re, subprocess, json
SP = os.path.dirname(os.path.abspath(__file__)); PROG = sys.argv[1]
NAMED = ("enter","esc","up","down","left","right","del","tab","menu","home","EE")
def k(*parts):
    out = []
    for p in parts: out += [p] if p in NAMED else list(p)
    return out
E="enter"
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
        t = re.findall(r'<text[^>]*>([^<]*)</text>', open(f).read())
        sig = " | ".join(t)[:200]
        if sig != last: print("  ", sig)
        last = sig
st = SP + "/storep.json"
if os.path.exists(st): os.remove(st)
run("run 1: type in tool 2 and 5, quit with home", k("2","3770",E,E,E,"1.34",E,"esc","esc","5","170",E,"8",E,"home"), st)
print("   saved:", sorted(json.load(open(st)).keys()))
run("run 2: restart; menu on 5; tool 5 and 2 filled", k("enter","esc","2","esc","esc"), st)
json.dump({"phy7n2": [99.0, 1.0], "phy7n0": [1.0, 44.0]}, open(st, "w"))
run("run 3: broken saved data must not crash", k("2","esc","esc"), st)
run("run 4: no calculator lists at all", k("2","5",E,"esc","esc","2","esc","esc"), None)
