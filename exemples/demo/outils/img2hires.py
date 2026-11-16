#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertit une image (PNG, JPEG, GIF…) pour le mode HIRES 160 x 125 de
l'Alice 32 (80 colonnes, cellules « mosaïque ») : image DUOCHROME, une
couleur d'encre et une couleur de fond parmi les 8 de l'EF9345.
Exemple ORIGINAL du dépôt alice32-tech-ref.

Format produit (3 002 octets) — c'est directement le rangement de la
mémoire de l'EF9345 en 80 colonnes (docs/04-ef9345-video.md §8.1) :
  octet 0 : DOR (couleur d'encre, bits d'insertion comme la ROM)
  octet 1 : MAT (couleur de fond = couleur de la marge)
  puis 25 rangées (rangée de service, puis les 24 rangées du corps) de
  40 paires de colonnes : C pair, C impair, octet d'attributs
  (quartet haut = colonne paire, quartet bas = colonne impaire).
Mosaïque : bit n du mot de 10 bits = bande n / 2 (2 lignes de points),
moitié gauche si n est pair ; bits 0-6 dans C, bits 7-9 dans A1-A3.
[B : d'après l'émulation EF9345 de MAME, source S25]

Usage :
  img2hires.py image.png -o inc/image.inc [--bin image.bin]
               [--encre blanc] [--fond noir] [--tramage floyd|ordonne|seuil]
               [--seuil 128] [--contraste 1.0] [--inverse] [--apercu apercu.png]
"""
import argparse

from PIL import Image, ImageEnhance, ImageOps

COULEURS = {'noir': 0, 'rouge': 1, 'vert': 2, 'jaune': 3, 'bleu': 4,
            'magenta': 5, 'cyan': 6, 'blanc': 7}
LARG, HAUT = 160, 125
# Un point fait 3 pixels de 80 colonnes sur 2 lignes : sur un écran 4:3,
# il est à peine plus large que haut (rapport ~1,04).
RAPPORT_POINT = (3 / 480 * 4) / (2 / 250 * 3)

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def prepare(chemin, contraste, inverse, fond_clair):
    im = Image.open(chemin).convert('L')
    if contraste != 1.0:
        im = ImageEnhance.Contrast(im).enhance(contraste)
    if inverse:
        im = ImageOps.invert(im)
    # garder les proportions : 160 x 125 points de rapport RAPPORT_POINT
    w, h = im.size
    s = min(LARG * RAPPORT_POINT / w, HAUT / h)
    nw, nh = max(1, round(w * s / RAPPORT_POINT)), max(1, round(h * s))
    im = im.resize((nw, nh), Image.LANCZOS)
    toile = Image.new('L', (LARG, HAUT), 255 if fond_clair else 0)
    toile.paste(im, ((LARG - nw) // 2, (HAUT - nh) // 2))
    return toile


def binarise(im, tramage, seuil):
    """Retourne une liste de lignes de 160 booléens (True = encre)."""
    px = im.load()
    if tramage == 'floyd':
        b = im.convert('1')                    # Floyd-Steinberg de Pillow
        p = b.load()
        return [[p[x, y] != 0 for x in range(LARG)] for y in range(HAUT)]
    if tramage == 'ordonne':
        return [[px[x, y] > (BAYER4[y % 4][x % 4] + 0.5) * 16 for x in range(LARG)]
                for y in range(HAUT)]
    return [[px[x, y] >= seuil for x in range(LARG)] for y in range(HAUT)]


def encode(points, encre, fond):
    dor = 0x88 | (encre << 4) | encre          # encre en C0 et C1 (D indifférent)
    mat = 0x28 | fond                          # comme la ROM, marge = fond
    data = [dor, mat]
    for r in range(25):
        for paire in range(40):
            mots = []
            for c in (2 * paire, 2 * paire + 1):
                w = 0
                for bande in range(5):
                    for moitie in range(2):
                        if points[5 * r + bande][2 * c + moitie]:
                            w |= 1 << (2 * bande + moitie)
                mots.append(w)
            ca, cb = (0x80 | (w & 0x7F) for w in mots)
            qa, qb = ((((w >> 7) & 7) << 1) for w in mots)   # D = 0
            data += [ca, cb, (qa << 4) | qb]
    return data


def apercu(points, encre, fond, chemin):
    pal = [((c & 1) * 255, ((c >> 1) & 1) * 255, ((c >> 2) & 1) * 255) for c in range(8)]
    im = Image.new('RGB', (480, 250))
    p = im.load()
    for y in range(250):
        for x in range(480):
            p[x, y] = pal[encre if points[y // 2][x // 3] else fond]
    im.resize((960, 720), Image.NEAREST).save(chemin)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('image')
    ap.add_argument('-o', '--inc', help='fichier .inc (DASM) à produire')
    ap.add_argument('--bin', help='fichier binaire brut (3 002 octets)')
    ap.add_argument('--etiquette', default='IMAGE')
    ap.add_argument('--encre', default='blanc', choices=COULEURS)
    ap.add_argument('--fond', default='noir', choices=COULEURS)
    ap.add_argument('--tramage', default='floyd', choices=('floyd', 'ordonne', 'seuil'))
    ap.add_argument('--seuil', type=int, default=128)
    ap.add_argument('--contraste', type=float, default=1.0)
    ap.add_argument('--inverse', action='store_true', help='encre là où l\'image est sombre')
    ap.add_argument('--apercu', help='PNG montrant le résultat attendu (proportions 4:3)')
    a = ap.parse_args()
    encre, fond = COULEURS[a.encre], COULEURS[a.fond]
    im = prepare(a.image, a.contraste, a.inverse, False)
    points = binarise(im, a.tramage, a.seuil)
    data = encode(points, encre, fond)
    if a.inc:
        with open(a.inc, 'w', encoding='utf-8') as f:
            f.write("; Fichier GÉNÉRÉ par outils/img2hires.py à partir de %s\n" % a.image)
            f.write("; Image HIRES 160 x 125 duochrome : DOR, MAT, puis 25 x 40 x (C pair,\n"
                    "; C impair, attributs). Encre %s, fond %s, tramage %s.\n"
                    % (a.encre, a.fond, a.tramage))
            for i in range(0, len(data), 24):
                lab = a.etiquette if i == 0 else ''
                f.write('%-8s dc.b %s\n' % (lab, ','.join('$%02X' % b for b in data[i:i + 24])))
    if a.bin:
        open(a.bin, 'wb').write(bytes(data))
    if a.apercu:
        apercu(points, encre, fond, a.apercu)
    allumes = sum(sum(l) for l in points)
    print("%s : %d octets, %d points d'encre sur %d" % (a.inc or a.bin or '-', len(data),
                                                         allumes, LARG * HAUT))


if __name__ == '__main__':
    main()
