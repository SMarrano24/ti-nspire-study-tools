# sheet.py OUT.svg frame.svg ...  -> one picture with the frames 2 across
import sys, re
out = sys.argv[1]; frames = sys.argv[2:]
rows = (len(frames) + 1) // 2
side = max(1300, rows * 433 + 10)
o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><rect width="%d" height="%d" fill="#888"/>' % (side, side, side, side, side, side)]
for n, f in enumerate(frames):
    body = open(f).read()
    inner = body[body.index(">") + 1: body.rindex("</svg>")]
    o.append('<svg x="%d" y="%d" width="636" height="424" viewBox="0 0 318 212">%s</svg>' % (10 + (n % 2) * 645, 10 + (n // 2) * 433, inner))
o.append("</svg>")
open(out, "w").write("".join(o))
