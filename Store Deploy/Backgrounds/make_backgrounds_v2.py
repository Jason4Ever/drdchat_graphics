"""Drdchat store backgrounds v2 — vibrant gradient + warped halftone 'wave mesh' (reference style),
built from the brand colors in lib/core/colors.dart. Run: python3 make_backgrounds_v2.py"""
import os, sys, numpy as np
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))
def hx(h): h=h.lstrip('#'); return np.array([int(h[i:i+2],16) for i in (0,2,4)],dtype=np.float32)/255

MAIN=hx('4A0091'); LIGHT=hx('6200C5'); SEC=hx('B86AD7'); SEC_D=hx('C141FA')
GOLD=hx('D8B418'); NAVY=hx('000D8D'); DEEP=hx('44037D'); TUT=hx('280249')
MAGENTA=hx('A3129E'); INDIGO=hx('14064F'); BLUE=hx('1A22B8'); NIGHT=hx('07032E'); HOT=hx('E030D8'); GOLD_HI=hx('FFC53A')

# corners: TL, TR, BL, BR  | glows: (color, x, y, r, strength) screen-blended | dot tint, dot strength
STYLES = {
 'v2_01_neon_party': dict(c=(MAGENTA, INDIGO, BLUE, LIGHT),
     glows=[(HOT,0.0,0.0,0.40,0.50),(HOT,1.05,0.62,0.26,0.50),(BLUE,0.0,0.85,0.30,0.45),(SEC_D,0.5,0.13,0.18,0.20)],
     dot=hx('F2A8FF'), ds=0.38),
 'v2_02_royal_gold': dict(c=(MAIN, NIGHT, DEEP, TUT),
     glows=[(SEC_D,0.0,0.0,0.38,0.50),(GOLD_HI,1.05,0.97,0.26,0.45),(SEC_D,1.05,0.55,0.22,0.30),(GOLD_HI,0.5,0.12,0.16,0.12)],
     dot=hx('FFD36B'), ds=0.34),
 'v2_03_midnight': dict(c=(DEEP, NIGHT, NAVY, INDIGO),
     glows=[(LIGHT,0.0,0.05,0.38,0.55),(SEC_D,1.05,0.75,0.26,0.40),(BLUE,0.0,0.90,0.30,0.45),(SEC,0.5,0.13,0.16,0.15)],
     dot=hx('B9A6FF'), ds=0.36),
}
SIZES = {
 'apple_iphone_6.9_1320x2868': (1320, 2868), 'apple_iphone_6.5_1284x2778': (1284, 2778),
 'apple_ipad_13_2064x2752': (2064, 2752), 'google_phone_1080x2400': (1080, 2400),
 'google_phone_1080x1920': (1080, 1920), 'google_phone_1620x2880': (1620, 2880),
 'google_tablet_1600x2560': (1600, 2560), 'google_feature_1024x500': (1024, 500),
}

def screen(img, col, w): return 1-(1-img)*(1-col*w)

def base(st, w, h):
    S = STYLES[st]; sw, sh = max(w//4,64), max(h//4,64)
    y, x = np.mgrid[0:sh,0:sw].astype(np.float32); xr, yr = x/(sw-1), y/(sh-1)
    tl,tr,bl,br = S['c']
    img = (tl*((1-xr)*(1-yr))[...,None] + tr*(xr*(1-yr))[...,None] + bl*((1-xr)*yr)[...,None] + br*(xr*yr)[...,None])
    diag = np.sqrt(sw*sh) if sh>=sw else max(sw,sh)*0.7
    for col,ox,oy,r,a in S['glows']:
        d2 = ((x-ox*(sw-1))**2+(y-oy*(sh-1))**2)/(r*1.3*diag)**2
        img = screen(img, col[None,None,:], (a*np.exp(-d2*1.1))[...,None])
    sm = Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8))
    return np.asarray(sm.resize((w,h), Image.BICUBIC)).astype(np.float32)/255

def dots(st, w, h):
    S = STYLES[st]; s = np.sqrt(w*h)/88.0          # grid pitch in px
    y, x = np.mgrid[0:h,0:w].astype(np.float32)
    # warp the grid so rows bend like a 3D surface
    u = x/s + 1.3*np.sin(y/(s*9.0)) + 0.6*np.sin(x/(s*21.0)+1.0)
    v = y/s + 1.6*np.sin(x/(s*13.0) + y/(s*31.0))
    du, dv = u-np.round(u), v-np.round(v)
    dist = np.sqrt(du*du+dv*dv)*s
    # intensity: flowing bands * edge mask (calmer centre where the phone sits)
    ug, vg = np.round(u), np.round(v)
    band = 0.5+0.5*np.sin(2*np.pi*(vg/26.0 + 0.55*np.sin(ug/15.0) + 0.15*np.sin(ug/6.0+vg/9.0)))
    xr, yr = x/w, y/h
    d = np.sqrt(((xr-0.5)*1.25)**2 + ((yr-0.56)*(h/w if h>w else 1)*0.55)**2)
    edge = np.clip((d-0.16)/0.38, 0, 1)
    m = (0.15+0.85*band**1.5)*(0.25+0.75*edge)
    r = s*0.36*m
    cov = np.clip((r - dist)/1.1 + 0.5, 0, 1) * (r > 0.35)
    return (cov*m*S['ds'])[...,None]

def render(st, w, h, seed=11):
    img = base(st, w, h)
    img = screen(img, STYLES[st]['dot'][None,None,:], dots(st, w, h))
    img = img*255 + np.random.default_rng(seed).normal(0,1.4,img.shape)
    return Image.fromarray(np.clip(img,0,255).astype(np.uint8), 'RGB')

if __name__ == '__main__':
    only = sys.argv[1:]  # optional: 'preview'
    if 'preview' not in only:
        for st in STYLES:
            d = os.path.join(OUT, st); os.makedirs(d, exist_ok=True)
            for nm,(w,h) in SIZES.items():
                render(st,w,h).save(os.path.join(d,f'{st}_{nm}.png'), optimize=True)
            print('done', st)
    th = [render(st,540,1200) for st in STYLES]; fg = [render(st,1024,500) for st in STYLES]
    sheet = Image.new('RGB',(3*540+4*20, 1200+264+60),(255,255,255))
    for i,(a,b) in enumerate(zip(th,fg)):
        sheet.paste(a,(20+i*560,20)); sheet.paste(b.resize((540,264)),(20+i*560,1240))
    sheet.save(os.path.join(OUT,'_preview_v2.png'))
