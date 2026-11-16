#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertit un son (.wav PCM) en échantillons 4 bits pour le lecteur
« sigma-delta 1 bit » de l'Alice 32 (inc/sample.inc).
Exemple ORIGINAL du dépôt alice32-tech-ref.

Le lecteur sort SM_N « tics » de 12 cycles par échantillon, plus 40
cycles par octet (2 échantillons) : fréquence = 2 000 000 / (24 N + 40) Hz
(N = 16 : 4 717 Hz). Les échantillons sont rangés par 2 dans un octet
(quartet haut d'abord), valeur 0-15, silence = 8.

Usage :
  wav2sample.py son.wav -o inc/donnees-sample.inc [--n 16] [--max 5000]
  wav2sample.py --synthese -o inc/donnees-sample.inc   (son de test original)
  options : --compression 0.5 (rapproche les sons faibles), --ecoute x.wav
"""
import argparse
import math
import wave

import numpy as np


def frequence(n):
    return 2_000_000 / (24 * n + 40)


def lit_wav(chemin):
    with wave.open(chemin, 'rb') as w:
        nc, sw, fr, nf = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        brut = w.readframes(nf)
    if sw == 1:
        x = (np.frombuffer(brut, np.uint8).astype(np.float64) - 128) / 128
    elif sw == 2:
        x = np.frombuffer(brut, '<i2').astype(np.float64) / 32768
    else:
        raise SystemExit("seuls les WAV PCM 8 ou 16 bits sont lus (convertir avec ffmpeg)")
    x = x.reshape(-1, nc).mean(axis=1)
    return x, fr


def synthese(fr=22050):
    """Son de test original : 3 notes pincées, une batterie, une voyelle."""
    t = np.arange(int(2.4 * fr)) / fr
    x = np.zeros_like(t)
    for i, f in enumerate((523.25, 659.25, 783.99)):      # do mi sol pincés
        t0 = 0.22 * i
        m = t >= t0
        tt = t[m] - t0
        x[m] += 0.5 * np.exp(-tt * 6) * (np.sin(2 * np.pi * f * tt) +
                                         0.4 * np.sin(4 * np.pi * f * tt))
    rng = np.random.default_rng(32)
    for t0, kind in ((0.80, 'grosse'), (1.05, 'caisse'), (1.18, 'grosse'), (1.30, 'caisse')):
        m = (t >= t0) & (t < t0 + 0.2)
        tt = t[m] - t0
        if kind == 'grosse':
            x[m] += 0.9 * np.exp(-tt * 25) * np.sin(2 * np.pi * (120 * np.exp(-tt * 20) + 45) * tt)
        else:
            x[m] += 0.6 * np.exp(-tt * 30) * rng.uniform(-1, 1, m.sum())
    # voyelle « a » puis « i » : train d'impulsions à 120 Hz dans 2 résonateurs
    m = t >= 1.5
    tt = t[m] - 1.5
    src = (np.mod(tt * 120, 1.0) < 0.08).astype(np.float64) - 0.08
    sortie = np.zeros_like(src)
    for formant in (0, 1):
        etat1 = etat2 = 0.0
        for k in range(len(src)):
            a = min(1.0, tt[k] / 0.8)                       # glissement a -> i
            f = (730 + (270 - 730) * a) if formant == 0 else (1090 + (2290 - 1090) * a)
            r = 0.97
            c1 = 2 * r * math.cos(2 * math.pi * f / fr)
            v = src[k] + c1 * etat1 - r * r * etat2
            etat2, etat1 = etat1, v
            sortie[k] += v * (1.0 if formant == 0 else 0.6)
    sortie *= np.minimum(1, (0.9 - tt).clip(0) * 8)          # fin douce
    x[m] += 0.8 * sortie / (np.abs(sortie).max() + 1e-9)
    return x, fr


def reechantillonne(x, fr, cible):
    n = int(len(x) * cible / fr)
    # filtre anti-repliement simple : moyenne glissante sur fr/cible points
    k = max(1, int(round(fr / cible)))
    if k > 1:
        x = np.convolve(x, np.ones(k) / k, mode='same')
    pos = np.arange(n) * fr / cible
    return np.interp(pos, np.arange(len(x)), x)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('wav', nargs='?')
    ap.add_argument('--synthese', action='store_true')
    ap.add_argument('-o', '--inc', required=True)
    ap.add_argument('--n', type=int, default=16, help='tics par échantillon (SM_N)')
    ap.add_argument('--max', type=int, default=5000, help='octets au plus')
    ap.add_argument('--compression', type=float, default=0.6,
                    help='exposant appliqué à l\'amplitude (1 = aucune)')
    ap.add_argument('--ecoute', help='WAV du signal 4 bits attendu (pour comparer)')
    a = ap.parse_args()
    x, fr = synthese() if a.synthese else lit_wav(a.wav)
    cible = frequence(a.n)
    y = reechantillonne(x, fr, cible)
    y = y - y.mean()
    y = y / (np.abs(y).max() + 1e-9)
    y = np.sign(y) * np.abs(y) ** a.compression
    q = np.clip(np.round(y * 7.49 + 8), 0, 15).astype(int)
    q = q[: 2 * a.max]
    if len(q) % 2:
        q = np.append(q, 8)
    octets = [(int(q[i]) << 4) | int(q[i + 1]) for i in range(0, len(q), 2)]
    with open(a.inc, 'w', encoding='utf-8') as f:
        f.write("; Fichier GÉNÉRÉ par outils/wav2sample.py (%s)\n"
                % ('son de synthèse original' if a.synthese else a.wav))
        f.write("; %d échantillons 4 bits à %.0f Hz (SM_N = %d), %.2f s\n"
                % (len(q), cible, a.n, len(q) / cible))
        f.write("SM_N     EQU %d\n" % a.n)
        for i in range(0, len(octets), 24):
            f.write('%-8s dc.b %s\n' % ('SAMPLE' if i == 0 else '',
                                       ','.join('$%02X' % b for b in octets[i:i + 24])))
        f.write('SAMPLE_FIN\n')
    if a.ecoute:
        import wave as wv
        with wv.open(a.ecoute, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(1)
            w.setframerate(int(cible))
            w.writeframes(bytes(int(v * 16) for v in q))
    print("%s : %d octets, %d échantillons à %.0f Hz = %.2f s"
          % (a.inc, len(octets), len(q), cible, len(q) / cible))


if __name__ == '__main__':
    main()
