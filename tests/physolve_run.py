# Drive physolve.py with scripted keys; print each scenario's result pages.
import os, sys, glob, re, subprocess, shutil
SP = os.path.dirname(os.path.abspath(__file__)); PROG = sys.argv[1]
ALL = "-a" in sys.argv
only = [a for a in sys.argv[2:] if a != "-a"]
NAMED = ("enter","esc","up","down","left","right","del","tab","menu","home","EE")
def k(*parts):
    out = []
    for p in parts: out += [p] if p in NAMED else list(p)
    return out
E="enter"; R="right"; D="down"
X = k("esc","esc","esc")
S = {
 # Force PS (Ch 5)
 "5.1 helicopter": k("2","3770",E,E,E,"1.34",E,R,R)+[D]*2+X,
 "5.5 flea": k("3","4.9","EE","-","7",E,E,E,"0",E,"2400",E,R,R)+X,
 "5.6a ride accel": k("6","0",E,"50",E,"7",E,E,E,R)+X,
 "5.6b ride seat": k("2",E,"1120",E,E,"7.14",E,R,R)+X,
 "5.6c ride seat a=7": k("2",E,"1120",E,E,"7",E,R,R)+X,
 "11.1 cup saucer": k("5",E,"0.176",E,"0.165",E,E,R,R)+X,
 "11.2 stack": k("5","170",E,"8",E,"18",E,"37",E,R)+[D]*6+[R]+X,
 "12.1 hiker": k("3",E,"1040",E,E,"0",E,"1.1",E,R,R)+X,
 "12.2 monkey bars": k("2","27",E,E,E,"0",E,R,R)+X,
 # worksheets
 "ws1.1 rocket flat": k("3","2350",E,E,"28913",E,"0",E,E,R,R)+X,
 "ws1.2 rocket up": k("2",E,"15",E,"120",E,E,R,R)+X,
 "ws1.3 desk": k("4","42.5",E,E,"0.68",E,E,R,R)+X,
 "ws1.4 puck": k("6","21.1",E,"0",E,E,"197.1",E,E,R)+[D]*4+X,
 "ws2.1 block friction": k("3","20",E,E,"128",E,E,"0.8",E,R,R)+X,
 "ws2.2 bag": k("2","18",E,E,E,"3",E,R,R)+X,
 "ws2.3 elevator": k("2",E,"850",E,"750",E,E,R,R)+X,
 "ws2.4 car": k("6","60",E,"0",E,E,"650",E,E,R)+[D]*4+X,
 # lecture + others
 "lec 30kg": k("1","30",E,E,E,R)+X,
 "lec T-W 40N a2": k("2",E,"40",E,E,"2",E,R,R)+X,
 "4.4 neptune": k("1","13.6",E,"154",E,E,R)+X,
 "moon": k("1","70",E,E,"1.66",E,R)+X,
 "5.2 patty": k("3","0.125",E,E,"0.8",E,"2.3",E,E,R,R)+X,
 "5.7 excavator": k("2",E,E,"225000",E,"0.2",E,R,R)+X,
 "20.2 firefighter": k("2",E,"812",E,E,"-","1.45",E,R,R)+X,
 "20.3 box": k("6","3.9",E,"0",E,"3.1",E,E,"1.1",E,R)+[D]*6+X,
 "11.4 box push": k("5","8",E,"6",E,E,E,R,R)+X,
 "fric find mu": k("4","20",E,E,E,"112",E,R,R)+X,
 "fric find m": k("4",E,E,"0.5",E,"265",E,R,R)+X,
 "side find m": k("3",E,E,"100",E,"20",E,"4",E,R,R)+X,
 "help": k("7")+[D]*5+[R]+[D]*4+[R]+[D]*3+[R]+[D]*6+[R]+X[:2],
 "errs": k("2",E,E,E,E,"esc","2","5",E,E,"9",E,"1",E,"esc","3","5",E,E,E,E,E,"esc","5",E,E,E,E,"esc","6",E,E,E,E,E,"esc","1",E,E,E,"esc","4","-","1",E,E,"1",E,E,"esc","esc"),
 "edit": k("2","10",E,E,E,"2",E,"esc","20",E,E,E,E,R,"esc","esc","esc"),
 "home": k("2","5",E,"menu","1"),
}
shots = SP + "/shots"
for name, keys in S.items():
    if only and not any(o in name for o in only): continue
    for f in glob.glob(shots + "/s*.svg"): os.remove(f)
    e = dict(os.environ, KEYS=",".join(keys), SHOTS=shots, PYTHONPATH=SP + "/fake")
    e.pop("STORE", None)
    p = subprocess.run([sys.executable, PROG], env=e, capture_output=True, text=True)
    print("=" * 6, name, "rc", p.returncode, p.stderr[-600:])
    keep = os.path.join(SP, "sc", "p_" + re.sub(r"\W+", "_", name))
    shutil.rmtree(keep, ignore_errors=True); os.makedirs(keep)
    last = None; seen = set()
    for f in sorted(glob.glob(shots + "/s*.svg")):
        t = [x.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&") for x in re.findall(r'<text[^>]*>([^<]*)</text>', open(f).read())]
        sig = " | ".join(t)
        if sig == last: continue
        last = sig
        shutil.copy(f, keep)
        isform = "del: erase" in t[-1] or "open" in t[-1]
        if ALL or not isform or any(c in sig for c in ("must","Leave exactly","Type the","Type at","Can't","Need","no minus","Type a number")):
            if sig not in seen: print("  ", os.path.basename(f), sig[:420])
            seen.add(sig)
