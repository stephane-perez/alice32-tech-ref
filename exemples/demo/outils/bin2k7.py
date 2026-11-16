#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binaire brut -> image cassette .k7 (DCAlice) et, en option, .wav.
Exemple ORIGINAL du dépôt alice32-tech-ref.

Format .k7 (notice de DCALICEK7, docs/09) : chaque bloc est précédé d'UN
octet $55 (DCAlice et DCALICEK7 reconstituent l'amorce) :
  $55 $3C type longueur données somme $55
  somme = (type + longueur + données) modulo 256.
  Bloc d'en-tête (type $00, 15 octets) : nom (8 car.), type de fichier 2
  (code machine), drapeau ASCII 0, drapeau d'intervalle 0, adresse
  d'exécution, adresse de chargement (disposition du Color BASIC / MC-10,
  vérifiée sur Alice 32 réelle). Blocs de données $01 (255 octets au plus),
  bloc de fin $FF.
Le .wav est produit par k7wav.py (même signal que DCALICEK7).

Usage : bin2k7.py prog.bin NOM [--org 0x3400] [--exec 0x3400] [-o prog.k7] [--wav prog.wav]
"""
import argparse


def bloc(typ, data):
    s = (typ + len(data) + sum(data)) & 0xFF
    return bytes([0x55, 0x3C, typ, len(data)]) + bytes(data) + bytes([s, 0x55])


def k7(binaire, nom, org, exe):
    nom = nom.upper()[:8].ljust(8).encode('ascii')
    entete = nom + bytes([2, 0, 0, exe >> 8, exe & 0xFF, org >> 8, org & 0xFF])
    out = bytearray(bloc(0x00, entete))
    for i in range(0, len(binaire), 255):
        out += bloc(0x01, binaire[i:i + 255])
    out += bloc(0xFF, b'')
    return bytes(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('bin')
    ap.add_argument('nom')
    ap.add_argument('--org', default='0x3400')
    ap.add_argument('--exec', dest='exe', default=None)
    ap.add_argument('-o', '--out')
    ap.add_argument('--wav')
    ap.add_argument('--silence-initial', type=float, default=None, metavar='S',
                    help='secondes de silence au début du .wav (DCALICEK7 : 20)')
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
        import k7wav
        w = k7wav.k7_vers_wav(k, journal=lambda *x: None, silence_initial=a.silence_initial)
        open(a.wav, 'wb').write(w)
        print("%s : %.1f s" % (a.wav, (len(w) - 44) / 44100))


if __name__ == '__main__':
    main()
