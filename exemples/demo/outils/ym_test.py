#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabrique musiques/test-alice.ym : un fichier YM6 ORIGINAL (non compressé)
pour essayer ym2alice.py sans dépendre de musiques sous droits.
Voie A : mélodie (volume qui décroît) ; voie B : basse à ENVELOPPE
(forme $00, relancée à chaque note) ; voie C : batterie au BRUIT
(grosse caisse et charleston), son coupé. Horloge 2 MHz (Atari ST), 50 Hz.
"""
import os
import struct

ICI = os.path.dirname(os.path.abspath(__file__))
HORLOGE, CADENCE, TPS = 2000000, 50, 6          # 6 trames par seizième
NOMS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def freq(nom):
    n, o = (nom[:-1], int(nom[-1]))
    midi = 12 * (o + 1) + NOMS.index(n)
    return 440.0 * 2 ** ((midi - 69) / 12)


def periode(f):
    return int(round(HORLOGE / (16 * f)))


MEL = """E5:4 D5:2 C5:2 B4:4 C5:2 D5:2 E5:4 A4:4 A4:2 B4:2 C5:4
D5:4 C5:2 B4:2 A4:4 G4:2 B4:2 A4:8 R:4 E4:2 G4:2""".split()
BASSE = ['A2', 'F2', 'C3', 'G2']                  # une par mesure (2 mesures chacune ici)
trames = []
notes = []
for tok in MEL:
    n, d = tok.split(':')
    notes += [(n, int(d))]
t_mel = []
for n, d in notes:
    for k in range(d * TPS):
        t_mel.append((n, k))
nb = len(t_mel)
for i in range(nb):
    r = [0] * 16
    n, k = t_mel[i]
    seiz = i // TPS
    if n != 'R':
        p = periode(freq(n))
        r[0], r[1] = p & 255, p >> 8
        r[8] = max(15 - k // 3, 9)
    # basse : une note par mesure (16 seizièmes), enveloppe relancée chaque noire
    b = BASSE[(seiz // 16) % 4]
    p = periode(freq(b))
    r[2], r[3] = p & 255, p >> 8
    r[9] = 16                                    # volume = enveloppe
    r[11], r[12] = 2336 & 255, 2336 >> 8         # ~0,3 s pour 32 pas
    r[13] = 0x00 if (i % (4 * TPS)) == 0 else 0xFF
    # batterie : grosse caisse sur les temps 1 et 3, charleston sur les croches
    pos = i % (8 * TPS)
    if pos < 3:
        r[6], r[10] = 31, 15 - 3 * pos           # bruit grave, décroissant
    elif (i % (2 * TPS)) < 2:
        r[6], r[10] = 2, 11 - 3 * (i % (2 * TPS))  # bruit aigu bref
    else:
        r[10] = 0
    # mixeur : A son, B son, C bruit seul
    r[7] = 0b011100 | 0b100000 * 0
    r[7] = (1 << 2) | (1 << 3) | (1 << 4)        # son C coupé, bruit A et B coupés
    trames.append(r)
n = len(trames)
corps = bytes(trames[t][reg] for reg in range(16) for t in range(n))   # entrelacé
entete = (b'YM6!' + b'LeOnArD!' + struct.pack('>IIHIHIH', n, 1, 0, HORLOGE, CADENCE, 0, 0)
          + b'Test Alice 32\0' + b'alice32-tech-ref\0' + b'ym_test.py\0')
chemin = os.path.join(ICI, '..', 'musiques', 'test-alice.ym')
open(chemin, 'wb').write(entete + corps + b'End!')
print("musiques/test-alice.ym : %d trames (%.1f s)" % (n, n / CADENCE))
