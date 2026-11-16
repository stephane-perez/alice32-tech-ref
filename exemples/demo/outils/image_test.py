#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dessine l'image de test images/paysage.png (exemple ORIGINAL du dépôt) :
ciel en dégradé, soleil, montagnes, lac, texte. 640 x 480."""
import math
import os
from PIL import Image, ImageDraw, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
W, H = 640, 480
im = Image.new('L', (W, H))
d = ImageDraw.Draw(im)
for y in range(H):                                   # ciel : sombre en haut
    d.line([(0, y), (W, y)], fill=int(20 + 200 * (y / 300) ** 1.4) if y < 300 else 0)
for r in range(90, 0, -1):                           # soleil à halo
    d.ellipse([430 - r, 150 - r, 430 + r, 150 + r], fill=min(255, 150 + int(105 * (1 - r / 90) ** 0.5)))
pts = [(0, 330)]
for x in range(0, W + 20, 20):                       # montagnes
    h = 300 - 90 * abs(math.sin(x / 110.0)) - 40 * abs(math.sin(x / 37.0 + 1))
    pts.append((x, h))
pts += [(W, 330), (0, 330)]
d.polygon(pts, fill=35)
for y in range(330, H):                              # lac : reflets
    v = 40 + int(60 * ((y - 330) / 150)) + (50 if (y // 6) % 3 == 0 and 360 < y < 440 else 0)
    d.line([(0, y), (W, y)], fill=v)
d.rectangle([380, 340, 480, 346], fill=230)
d.rectangle([400, 356, 460, 360], fill=200)
try:
    police = ImageFont.load_default(size=56)
except TypeError:
    police = ImageFont.load_default()
d.text((30, 380), "ALICE 32", fill=255, font=police)
im.save(os.path.join(ICI, '..', 'images', 'paysage.png'))
print("images/paysage.png")
