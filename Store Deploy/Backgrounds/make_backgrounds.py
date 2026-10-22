"""Generate Drdchat store-screenshot backgrounds from the app's brand colors (lib/core/colors.dart).
Run: python3 make_backgrounds.py   -> writes PNGs (RGB, no alpha) next to this script."""
import os, numpy as np
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))
def hx(h): h=h.lstrip('#'); return np.array([int(h[i:i+2],16) for i in (0,2,4)],dtype=np.float32)/255

# Brand palette (colors.dart)
LAV    = hx('E7E0F6')  # drdParentBackground
LAV_HI = hx('F4F0FC')
MAIN   = hx('4A0091')  # drdBrandingMainColor
LIGHT  = hx('6200C5')  # drdBrandingMainColorLight
SEC    = hx('B86AD7')  # drdBrandingSecondaryColor
SEC_D  = hx('C141FA')  # drdBrandingSecondaryColorDarker
GOLD   = hx('D8B418')  # drdBrandingThirdColor
NAVY   = hx('000D8D')  # primaryTalkerBarBackground1
DEEP   = hx('44037D')  # primaryTalkerBarBackground2 / primaryDrdchatColor
TUT    = hx('280249')  # primaryPartyTutuorialBackground
CYAN   = hx('8FDDF2')  # soft accent seen in existing store art

# Each style: top color, bottom color, orbs [(color, x, y, radius, strength)] in relative coords.
# Orbs are kept mostly in the lower 2/3 so the headline area at the top stays clean.
STYLES = {
 '01_lavender_glow': (LAV_HI, LAV, [
     (SEC_D, 0.10, 0.78, 0.30, 0.45), (LIGHT, 0.62, 0.62, 0.26, 0.22),
     (CYAN,  0.92, 0.90, 0.30, 0.55), (SEC,   0.95, 0.18, 0.22, 0.25)]),
 '02_lavender_gold': (LAV_HI, LAV, [
     (GOLD,  0.05, 0.92, 0.30, 0.45), (SEC,   0.90, 0.60, 0.30, 0.50),
     (LIGHT, 0.45, 1.00, 0.28, 0.25), (SEC_D, 0.05, 0.25, 0.18, 0.18)]),
 '03_brand_deep': (DEEP, TUT, [
     (NAVY,  0.00, 0.55, 0.40, 0.90), (SEC_D, 0.95, 0.88, 0.32, 0.45),
     (LIGHT, 0.65, 0.35, 0.30, 0.45), (SEC,   0.25, 1.00, 0.26, 0.25)]),
 '04_purple_gold': (LIGHT, MAIN, [
     (SEC_D, 0.00, 0.08, 0.32, 0.40), (GOLD,  1.00, 1.00, 0.30, 0.45),
     (NAVY,  0.05, 0.85, 0.32, 0.70), (SEC,   0.90, 0.45, 0.24, 0.22)]),
}

DARK = {'03_brand_deep', '04_purple_gold'}

SIZES = {  # name: (w, h)
 'apple_iphone_6.9_1320x2868': (1320, 2868),
 'apple_iphone_6.5_1284x2778': (1284, 2778),
 'apple_ipad_13_2064x2752':    (2064, 2752),
 'google_phone_1080x2400':     (1080, 2400),
 'google_phone_1620x2880':     (1620, 2880),
 'google_tablet_1600x2560':    (1600, 2560),
 'google_feature_1024x500':    (1024, 500),
}

def render(style, w, h, seed=7):
    top, bot, orbs = STYLES[style]
    s = 4  # render small then upscale for perfectly smooth gradients
    sw, sh = max(w//s, 64), max(h//s, 64)
    y, x = np.mgrid[0:sh, 0:sw].astype(np.float32)
    xr, yr = x/(sw-1), y/(sh-1)
    img = top[None,None,:]*(1-yr[...,None]) + bot[None,None,:]*yr[...,None]
    diag = np.sqrt(sw*sh) if sh >= sw else max(sw, sh)*0.7   # keep glows broad on landscape art
    dark = style in DARK
    for col, ox, oy, r, a in orbs:
        d2 = ((x-ox*(sw-1))**2 + (y-oy*(sh-1))**2) / (r*1.35*diag)**2
        wgt = (a*np.exp(-d2*1.1))[...,None]
        if dark:   # screen blend: glows add light instead of mixing to mud
            img = 1-(1-img)*(1-col[None,None,:]*wgt)
        else:
            img = img*(1-wgt) + col[None,None,:]*wgt
    small = Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8), 'RGB')
    big = np.asarray(small.resize((w,h), Image.BICUBIC)).astype(np.float32)
    big += np.random.default_rng(seed).normal(0, 1.6, big.shape)  # fine grain: kills banding after compression
    return Image.fromarray(np.clip(big,0,255).astype(np.uint8), 'RGB')

if __name__ == '__main__':
    for st in STYLES:
        d = os.path.join(OUT, st); os.makedirs(d, exist_ok=True)
        for nm,(w,h) in SIZES.items():
            render(st,w,h).save(os.path.join(d, f'{st}_{nm}.png'), optimize=True)
        print('done', st)
    # preview sheet
    th = [render(st,330,717) for st in STYLES]
    fg = [render(st,500,244) for st in STYLES]
    sheet = Image.new('RGB', (4*330+5*20, 717+244+60), (255,255,255))
    for i,(a,b) in enumerate(zip(th,fg)):
        sheet.paste(a,(20+i*350,20)); sheet.paste(b.resize((330,161)),(20+i*350,757))
    sheet.save(os.path.join(OUT,'_preview.png'))
