#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binaire brut -> image cassette .k7 (DCAlice) et, en option, .wav.
Exemple ORIGINAL du dépôt alice32-tech-ref.

Format écrit [C : déduit du format cassette Microsoft Color BASIC / MC-10,
non vérifié sur Alice ; voir docs/09-cassette-et-formats-de-fichiers.md] :
  128 x $55, bloc d'en-tête (type $00), 128 x $55, blocs de données
  (type $01, 255 octets au plus), bloc de fin (type $FF).
  Bloc = $55 $3C type longueur données somme $55 ;
  somme = (type + longueur + données) modulo 256.
  En-tête : nom (8 car.), type de fichier 2 (code machine), drapeau ASCII 0,
  drapeau d'intervalle 0, adresse d'exécution, adresse de chargement.
WAV : 44 100 Hz, 8 bits, mono ; un bit = une période, 1200 Hz pour 0 et
2400 Hz pour 1, poids faible d'abord (seuil de DCAlice : ~680 µs).

Usage : bin2k7.py prog.bin NOM [--org 0x3400] [--exec 0x3400] [-o prog.k7] [--wav prog.wav]
"""
import argparse
import math
import struct


def bloc(typ, data):
    s = (typ + len(data) + sum(data)) & 0xFF
    return bytes([0x55, 0x3C, typ, len(data)]) + bytes(data) + bytes([s, 0x55])


def k7(binaire, nom, org, exe):
    nom = nom.upper()[:8].ljust(8).encode('ascii')
    entete = nom + bytes([2, 0, 0, exe >> 8, exe & 0xFF, org >> 8, org & 0xFF])
    out = bytearray(b'\x55' * 128) + bloc(0x00, entete)
    out += b'\x55' * 128
    for i in range(0, len(binaire), 255):
        out += bloc(0x01, binaire[i:i + 255])
    out += bloc(0xFF, b'')
    return bytes(out)


def wav(k7data, chemin, rate=44100):
    """Reconstitue le signal : silences avant l'en-tête et avant les données."""
    echantillons = bytearray()

    def silence(sec):
        echantillons.extend([128] * int(sec * rate))

    phase = [0.0]

    def periode(freq):
        n = rate / freq
        k = 0
        while phase[0] < n:
            echantillons.append(int(128 + 100 * math.sin(2 * math.pi * phase[0] / n)))
            phase[0] += 1
            k += 1
        phase[0] -= n

    def octet(b):
        for i in range(8):
            periode(2400 if (b >> i) & 1 else 1200)

    # repère les deux amorces de 128 x $55 pour y placer un silence
    silence(1.0)
    i = 0
    amorces = 0
    while i < len(k7data):
        if k7data[i:i + 128] == b'\x55' * 128:
            if amorces:
                silence(0.5)
            amorces += 1
            for b in k7data[i:i + 128]:
                octet(b)
            i += 128
            continue
        octet(k7data[i])
        i += 1
    silence(0.5)
    with open(chemin, 'wb') as f:
        n = len(echantillons)
        f.write(b'RIFF' + struct.pack('<I', 36 + n) + b'WAVEfmt ' +
                struct.pack('<IHHIIHH', 16, 1, 1, rate, rate, 1, 8) +
                b'data' + struct.pack('<I', n) + bytes(echantillons))
    return n / rate


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('bin')
    ap.add_argument('nom')
    ap.add_argument('--org', default='0x3400')
    ap.add_argument('--exec', dest='exe', default=None)
    ap.add_argument('-o', '--out')
    ap.add_argument('--wav')
    a = ap.parse_args()
    org = int(a.org, 0)
    exe = int(a.exe, 0) if a.exe else org
    data = open(a.bin, 'rb').read()
    k = k7(data, a.nom, org, exe)
    out = a.out or a.bin.rsplit('.', 1)[0] + '.k7'
    open(out, 'wb').write(k)
    print("%s : %d octets, chargement $%04X, exécution $%04X (EXEC %d)"
          % (out, len(k), org, exe, exe))
    if a.wav:
        d = wav(k, a.wav)
        print("%s : %.1f s" % (a.wav, d))


if __name__ == '__main__':
    main()
