# Drive algsolve.py with scripted keys; print the result pages of each scenario.
# usage: run.py PROG [-a] [names...]   (-a prints every screen, forms too)
import os, sys, glob, re, subprocess, shutil
SP = os.path.dirname(os.path.abspath(__file__))
PROG = sys.argv[1]
ALL = "-a" in sys.argv
only = [a for a in sys.argv[2:] if a != "-a"]
NAMED = ("enter","esc","up","down","left","right","del","tab","menu","home","square","clear")
def k(*parts):
    out = []
    for p in parts:
        out += [p] if p in NAMED else list(p)
    return out
E = "enter"; R = "right"; D = "down"
S = {
 # 3-1 and 3-2 worksheet
 "w1": k("1","x^2+6x^3-4+2x^5",E) + [R]*3 + [D]*14 + k("esc","esc","esc"),
 "w2": k("1","x^3-7x^2+10x",E,R,R,R,"esc","esc","esc"),
 "w3a": k("2","(4x^3+2x+2x^2-8)+(2x^2+x^2+9)",E) + [D]*6 + [R] + k("esc","esc","esc"),
 "w3b": k("2","(9a^3+6ab-4)-(10a^3b-6a^2b^2-6)",E) + [D]*8 + [R] + k("esc","esc","esc"),
 "w3c": k("2","5x(3x-1)+(2x^2+x)(8x-3)",E) + [D]*12 + [R] + k("esc","esc","esc"),
 "w4": k("2","(2x-7)^2",E) + [D]*4 + [R] + k("esc","esc","esc"),
 "w5": k("2","(x-3)(2x+1)(3x+5)",E) + [D]*14 + [R,R] + k("esc","esc","esc"),
 "w6": k("2","(8x+2)(3x^2+4x-5)",E) + [D]*6 + [R,R] + k("esc","esc","esc"),
 "w7": k("2","(5b-6)(5b^2+4b-2)",E) + [D]*6 + [R,R] + k("esc","esc","esc"),
 "w8": k("4","x+4",E,"x+15",E) + [D]*2 + [R] + [D]*4 + [R,R] + k("esc","esc","esc"),
 # notes
 "n31a": k("1","-4x+9+2x^3",E,R,R,"esc","esc","esc"),
 "n31try": k("1","x^5+2x^6-3x^4-8x+4x^3",E,R,R,"esc","esc","esc"),
 "n31end": k("1","3x^2-3x^5-14x-2x^3+x^4-5",E,R,R,R,"esc","esc","esc"),
 "n31even": k("1","2x^6-5x^5+6x^4-x^3+4x^2-x+1",E,R,R,R,"esc","esc","esc"),
 "n31neg": k("1","-5x^3+8x+4",E,R,R,R,"esc","esc","esc"),
 "n31ex5": k("3","-0.12x^3+x^2-3.38x+13.16",E,"5",E) + [D]*4 + [R] + k("esc","esc","esc"),
 "n31shoe": k("3","-3x^4+4x^3-2x^2+5x+10",E,"1",E) + [D]*4 + [R] + k("esc","esc","esc"),
 "n32sub": k("2","(3x^2y^2+2xy^2+6x^2)-(2x^2y^2+3xy^2-2x^2)",E) + [D]*8 + [R] + k("esc","esc","esc"),
 "n32mul": k("2","(6n^2-7)(n^2+n+3)",E) + [D]*6 + [R,R] + k("esc","esc","esc"),
 "n32add2": k("2","4a(3a^3-4)+(6a^2+7)(-3a^2-5a)",E) + [D]*12 + [R] + k("esc","esc","esc"),
 "help": k("5") + [R]*4 + k("esc","esc"),
 "edit": k("2","(2x-7)^3",E,"esc","left","left","del","2",E,"esc","esc","esc"),
 "errs": k("2",E,"(x+1",E,"del","del","del","del","x/2",E,"esc","1","xy+1",E,"esc","3","x+1",E,"x",E,"esc","4","x-x",E,"esc","esc"),
 "home": k("2","(x+1)(x+2)",E,"down","menu","1","1"),
}
shots = SP + "/shots"
for name, keys in S.items():
    if only and name not in only:
        continue
    for f in glob.glob(shots + "/s*.svg"):
        os.remove(f)
    e = dict(os.environ, KEYS=",".join(keys), SHOTS=shots, PYTHONPATH=SP + "/fake")
    e.pop("STORE", None)
    p = subprocess.run([sys.executable, PROG], env=e, capture_output=True, text=True)
    print("=" * 8, name, "rc", p.returncode, p.stderr[-700:])
    keep = os.path.join(SP, "sc", name)
    shutil.rmtree(keep, ignore_errors=True); os.makedirs(keep)
    last = None
    for f in sorted(glob.glob(shots + "/s*.svg")):
        t = [x.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
             for x in re.findall(r'<text[^>]*>([^<]*)</text>', open(f).read())]
        sig = " | ".join(t)
        if sig == last:
            continue
        last = sig
        shutil.copy(f, keep)
        form = "enter:" in t[-1] or "1-5" in t[-1]
        if form and not ALL:
            continue
        print("--", os.path.basename(f), t[0], "  [" + t[-1] + "]")
        body = t[1:-1]
        if form:
            # typing lines are drawn one letter at a time: glue them back
            out = []; run = ""
            for x in body:
                if len(x) == 1: run += x
                else:
                    if run: out.append(run); run = ""
                    out.append(x)
            if run: out.append(run)
            body = out
        for x in body:
            print("     " + x)
