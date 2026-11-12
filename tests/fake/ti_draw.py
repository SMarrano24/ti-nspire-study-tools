# Stand-in for the calculator's ti_draw: every painted screen becomes an SVG file
import os
S=[]; C=["#000"]; N=[0]; W_=[1]
OUT=os.environ.get("SHOTS","/tmp")
def _c(): return C[0]
def set_color(r,g,b): C[0]="rgb(%d,%d,%d)"%(r,g,b)
def set_pen(size, style): W_[0]={"thin":1,"medium":2,"thick":3}[size]
def fill_rect(x,y,w,h): S.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>'%(x,y,w,h,_c()))
def draw_rect(x,y,w,h): S.append('<rect x="%s" y="%s" width="%s" height="%s" fill="none" stroke="%s"/>'%(x,y,w,h,_c()))
def draw_line(a,b,c,d): S.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>'%(a,b,c,d,_c(),W_[0]))
def draw_circle(x,y,r): S.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s"/>'%(x,y,r,_c()))
def draw_text(x,y,t):
    assert all(32 <= ord(ch) < 127 for ch in t), "non-plain letter drawn: %r" % t
    t=t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    S.append('<text x="%s" y="%s" fill="%s" font-family="Helvetica" font-size="13" xml:space="preserve">%s</text>'%(x,y,_c(),t))
def use_buffer(): S.clear()
def paint_buffer():
    N[0]+=1
    open(os.path.join(OUT,"s%03d.svg"%N[0]),"w").write('<svg xmlns="http://www.w3.org/2000/svg" width="636" height="424" viewBox="0 0 318 212"><rect width="318" height="212" fill="#fff"/>'+"".join(S)+'</svg>')
