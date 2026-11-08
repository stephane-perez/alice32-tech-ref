#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère les fichiers de données (inc/donnees-*.inc) de la démo Alice 32.
Exemple ORIGINAL du dépôt : police, logo, tables et mélodie sont dessinés
ou composés pour ce dépôt.

Usage : python3 gen_donnees.py   (écrit dans ../inc/)
"""
import math
import os
import unicodedata

ICI = os.path.dirname(os.path.abspath(__file__))
INC = os.path.join(ICI, '..', 'inc')


def ecrit(nom, texte):
    with open(os.path.join(INC, nom), 'w', encoding='utf-8') as f:
        f.write(texte)


def octets(lab, data, par_ligne=16):
    out = []
    for i in range(0, len(data), par_ligne):
        morceau = ','.join('$%02X' % (b & 0xFF) for b in data[i:i + par_ligne])
        out.append('%-8s dc.b %s' % (lab if i == 0 else '', morceau))
    return '\n'.join(out) + '\n'


ENTETE = ("; Fichier GÉNÉRÉ par outils/gen_donnees.py : ne pas modifier à la main.\n"
          "; Exemple ORIGINAL du dépôt alice32-tech-ref.\n")

# ---------------------------------------------------------------------------
# 1. Table de sinus : 256 valeurs de 1 à 127 (centre 64)
# ---------------------------------------------------------------------------
sinus = [int(round(64 + 63 * math.sin(2 * math.pi * i / 256))) for i in range(256)]
ecrit('donnees-sinus.inc', ENTETE +
      "; SINUS[i] = 64 + 63 sin(2 pi i / 256). À placer sur une frontière de page\n"
      "; (ALIGN 256) : le code remplace l'octet faible de l'adresse.\n" +
      octets('SINUS', sinus))

# ---------------------------------------------------------------------------
# 2. Logo « ALICE32 » : une case = une tuile 8 x 10 ; valeur = couleur (0 = vide)
# ---------------------------------------------------------------------------
LETTRES = {
    'A': [".XXX.", "XX.XX", "XX.XX", "XXXXX", "XX.XX", "XX.XX", "XX.XX"],
    'L': ["XX..", "XX..", "XX..", "XX..", "XX..", "XX..", "XXXX"],
    'I': ["XX", "XX", "XX", "XX", "XX", "XX", "XX"],
    'C': [".XXX", "XX..", "XX..", "XX..", "XX..", "XX..", ".XXX"],
    'E': ["XXXX", "XX..", "XX..", "XXX.", "XX..", "XX..", "XXXX"],
    '3': ["XXX.", "..XX", "..XX", ".XX.", "..XX", "..XX", "XXX."],
    '2': ["XXX.", "..XX", "..XX", ".XX.", "XX..", "XX..", "XXXX"],
}
# couleurs B V R : 1 rouge, 2 vert, 3 jaune, 4 bleu, 5 magenta, 6 cyan, 7 blanc
COUL = {'A': 1, 'L': 3, 'I': 2, 'C': 6, 'E': 5, '3': 7, '2': 7}
MOT = "ALICE 32"
HAUT = 7
colonnes = []          # liste de colonnes (HAUT valeurs)
for i, ch in enumerate(MOT):
    if ch == ' ':
        colonnes += [[0] * HAUT] * 2
        continue
    motif = LETTRES[ch]
    for x in range(len(motif[0])):
        colonnes.append([COUL[ch] if motif[y][x] == 'X' else 0 for y in range(HAUT)])
    if i + 1 < len(MOT) and MOT[i + 1] != ' ':
        colonnes.append([0] * HAUT)
larg = len(colonnes)
assert larg <= 40, larg
gauche = (40 - larg) // 2
logo = []
for y in range(HAUT):
    ligne = [0] * 40
    for x, col in enumerate(colonnes):
        ligne[gauche + x] = col[y]
    logo += ligne

# Tuile « pleine » du logo (bit 0 = point de gauche) : bloc de 7 x 9 points,
# une colonne et une ligne vides : effet « grille de LED » qui rend le
# défilement au point près bien visible.
PLEIN = [0x7F] * 9 + [0x00]
VIDE = [0x00] * 10
ecrit('donnees-logo.inc', ENTETE +
      "; Logo « %s » : %d rangées x 40 cases, valeur = couleur (0 = vide).\n"
      "LOGO_H   EQU %d\n" % (MOT, HAUT, HAUT) +
      octets('LOGOZ', [0] * 40, 20) +
      octets('LOGO', logo, 20) +
      octets('LOGOZ2', [0] * 40, 20) +
      "; Tranches de la tuile « pleine » (les tuiles décalées en sont tirées).\n" +
      octets('PLEIN', PLEIN, 10))

# ---------------------------------------------------------------------------
# 3. Police 5 x 7 du scrolltext (dessin original), 64 caractères $20-$5F.
#    8 octets par caractère : 7 tranches (bit 0 = gauche) + largeur en points.
# ---------------------------------------------------------------------------
G = {
    ' ': ["", "", "", "", "", "", ""],
    '!': ["X", "X", "X", "X", "X", ".", "X"],
    '"': ["X.X", "X.X", "", "", "", "", ""],
    "'": ["X", "X", "", "", "", "", ""],
    '$': ["..X..", ".XXXX", "X.X..", ".XXX.", "..X.X", "XXXX.", "..X.."],
    '%': ["XX..X", "XX..X", "...X.", "..X..", ".X...", "X..XX", "X..XX"],
    '(': [".X", "X.", "X.", "X.", "X.", "X.", ".X"],
    ')': ["X.", ".X", ".X", ".X", ".X", ".X", "X."],
    '*': ["", "X.X.X", ".XXX.", "XXXXX", ".XXX.", "X.X.X", ""],
    '+': ["", "..X..", "..X..", "XXXXX", "..X..", "..X..", ""],
    ',': ["", "", "", "", ".X", ".X", "X."],
    '-': ["", "", "", "XXXX", "", "", ""],
    '.': ["", "", "", "", "", "", "X"],
    '/': ["....X", "...X.", "...X.", "..X..", ".X...", ".X...", "X...."],
    '0': [".XXX.", "X...X", "X..XX", "X.X.X", "XX..X", "X...X", ".XXX."],
    '1': ["..X..", ".XX..", "..X..", "..X..", "..X..", "..X..", ".XXX."],
    '2': [".XXX.", "X...X", "....X", "...X.", "..X..", ".X...", "XXXXX"],
    '3': ["XXXX.", "....X", "....X", ".XXX.", "....X", "....X", "XXXX."],
    '4': ["...X.", "..XX.", ".X.X.", "X..X.", "XXXXX", "...X.", "...X."],
    '5': ["XXXXX", "X....", "XXXX.", "....X", "....X", "X...X", ".XXX."],
    '6': ["..XX.", ".X...", "X....", "XXXX.", "X...X", "X...X", ".XXX."],
    '7': ["XXXXX", "....X", "...X.", "..X..", ".X...", ".X...", ".X..."],
    '8': [".XXX.", "X...X", "X...X", ".XXX.", "X...X", "X...X", ".XXX."],
    '9': [".XXX.", "X...X", "X...X", ".XXXX", "....X", "...X.", ".XX.."],
    ':': ["", "", "X", "", "", "X", ""],
    ';': ["", "", ".X", "", ".X", ".X", "X."],
    '=': ["", "", "XXXX", "", "XXXX", "", ""],
    '?': [".XXX.", "X...X", "....X", "...X.", "..X..", "", "..X.."],
    'A': [".XXX.", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"],
    'B': ["XXXX.", "X...X", "X...X", "XXXX.", "X...X", "X...X", "XXXX."],
    'C': [".XXX.", "X...X", "X....", "X....", "X....", "X...X", ".XXX."],
    'D': ["XXXX.", "X...X", "X...X", "X...X", "X...X", "X...X", "XXXX."],
    'E': ["XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "XXXXX"],
    'F': ["XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "X...."],
    'G': [".XXX.", "X...X", "X....", "X.XXX", "X...X", "X...X", ".XXXX"],
    'H': ["X...X", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"],
    'I': ["XXX", ".X.", ".X.", ".X.", ".X.", ".X.", "XXX"],
    'J': ["..XXX", "...X.", "...X.", "...X.", "...X.", "X..X.", ".XX.."],
    'K': ["X...X", "X..X.", "X.X..", "XX...", "X.X..", "X..X.", "X...X"],
    'L': ["X....", "X....", "X....", "X....", "X....", "X....", "XXXXX"],
    'M': ["X...X", "XX.XX", "X.X.X", "X.X.X", "X...X", "X...X", "X...X"],
    'N': ["X...X", "XX..X", "X.X.X", "X..XX", "X...X", "X...X", "X...X"],
    'O': [".XXX.", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."],
    'P': ["XXXX.", "X...X", "X...X", "XXXX.", "X....", "X....", "X...."],
    'Q': [".XXX.", "X...X", "X...X", "X...X", "X.X.X", "X..X.", ".XX.X"],
    'R': ["XXXX.", "X...X", "X...X", "XXXX.", "X.X..", "X..X.", "X...X"],
    'S': [".XXXX", "X....", "X....", ".XXX.", "....X", "....X", "XXXX."],
    'T': ["XXXXX", "..X..", "..X..", "..X..", "..X..", "..X..", "..X.."],
    'U': ["X...X", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."],
    'V': ["X...X", "X...X", "X...X", "X...X", ".X.X.", ".X.X.", "..X.."],
    'W': ["X...X", "X...X", "X...X", "X.X.X", "X.X.X", "XX.XX", "X...X"],
    'X': ["X...X", "X...X", ".X.X.", "..X..", ".X.X.", "X...X", "X...X"],
    'Y': ["X...X", "X...X", ".X.X.", "..X..", "..X..", "..X..", "..X.."],
    'Z': ["XXXXX", "....X", "...X.", "..X..", ".X...", "X....", "XXXXX"],
}
police = []
for code in range(0x20, 0x60):
    ch = chr(code)
    motif = G.get(ch)
    if motif is None:
        police += [0] * 7 + [0]
        continue
    largeur = max((len(l.rstrip('.')) for l in motif), default=0)
    tranches = []
    for l in motif:
        v = 0
        for x, c in enumerate(l):
            if c == 'X':
                v |= 1 << x
        tranches.append(v)
    police += tranches + [largeur + 1 if ch != ' ' else 4]
ecrit('donnees-police.inc', ENTETE +
      "; Police 5 x 7 (dessin original), caractères $20 à $5F.\n"
      "; 8 octets par caractère : 7 tranches (bit 0 = point de gauche), puis la largeur.\n" +
      octets('POLICE', police, 8))

# ---------------------------------------------------------------------------
# 4. Texte du scrolltext (majuscules, sans accents ; les accents sont retirés)
# ---------------------------------------------------------------------------
TEXTE = (
    "      BONJOUR ET BIENVENUE DANS CETTE PETITE DEMO POUR ALICE 32 !    "
    "TOUT EST ECRIT EN ASSEMBLEUR 6803 A 1 MHZ, AVEC 20 000 CYCLES PAR IMAGE "
    "ET PAS UN DE PLUS...    "
    "LE LOGO DU DEBUT DEFILE GRACE AU REGISTRE ROR DE L'EF9345 : ON CHANGE "
    "L'ORIGINE VERTICALE YOR ET L'ECRAN BOUGE D'UNE RANGEE SANS RIEN RECOPIER. "
    "LE DEFILEMENT AU POINT PRES VIENT DE TROIS TUILES REDEFINIES A CHAQUE IMAGE.    "
    "LE PLASMA, LUI, EST FAIT DE QUATRE TUILES TRAMEES (0, 25, 50 ET 75 %) "
    "ET DE DEUX COULEURS PAR CASE, CALCULEES PAR UNE TABLE DE SINUS : "
    "UN DEGRADE DE 64 TEINTES AVEC SEULEMENT 8 COULEURS !    "
    "CE TEXTE AVANCE AU POINT PRES : 20 CARACTERES REDEFINIS DANS LE JEU G'0, "
    "EN DOUBLE HAUTEUR ET DOUBLE LARGEUR, SONT DECALES PUIS RENVOYES A L'EF9345 "
    "PAR LA COMMANDE OCT A CHAQUE TRAME.    "
    "LA MUSIQUE JOUE SANS BLOQUER LA DEMO : L'INTERRUPTION DE COMPARAISON DU "
    "TIMER (OCF) INVERSE LE BIT 7 DE $BFFF A LA BONNE FREQUENCE, ET LE DEBORDEMENT "
    "DU COMPTEUR (TOF, TOUTES LES 65 MS) FAIT AVANCER LA PARTITION.    "
    "SALUTATIONS A TOUS LES AMATEURS D'ALICE, DE MATRA ET DE MC-10, "
    "A DANIEL COULOM POUR DCALICE, ET AUX AUTEURS DE TETRICE, DE TUILES CURIEUSES "
    "ET D'IN THE DARK !    "
    "TOUCHES : ESPACE = PARTIE SUIVANTE, ENTREE = RETOUR AU BASIC.    "
    "LA DEMO RECOMMENCE...          "
)


def sans_accents(t):
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return t.upper()


txt = sans_accents(TEXTE)
for c in txt:
    assert 0x20 <= ord(c) < 0x60 and c in G, "caractère sans dessin : %r" % c
lignes = []
for i in range(0, len(txt), 48):
    morceau = txt[i:i + 48].replace('"', "'")
    lignes.append('%-8s dc.b "%s"' % ('SCROLLTXT' if i == 0 else '', morceau))
ecrit('donnees-texte.inc', ENTETE +
      "; Texte du scrolltext : %d caractères, terminé par 0.\n" % len(txt) +
      '\n'.join(lignes) + '\n         dc.b 0\n')

# ---------------------------------------------------------------------------
# 5. Musique : demi-périodes (µs, 1 cycle = 1 µs) et mélodie originale
# ---------------------------------------------------------------------------
NOMS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
notes = {}
periodes = []
n = 1
for octave in (3, 4, 5, 6):
    for i, nom in enumerate(NOMS):
        if octave == 6 and i > 0:
            break
        midi = 12 * (octave + 1) + i
        f = 440.0 * 2 ** ((midi - 69) / 12)
        notes['%s%d' % (nom, octave)] = n
        periodes.append(int(round(1e6 / (2 * f))))
        n += 1

# Mélodie originale en la mineur. Une unité = un débordement du timer = 65,5 ms.
# Format : "note:durée", R = silence.
PARTITION = """
A3:2 E4:2 A4:2 C5:2 E5:2 C5:2 A4:2 E4:2
F3:2 C4:2 F4:2 A4:2 C5:2 A4:2 F4:2 C4:2
C4:2 G4:2 C5:2 E5:2 G5:2 E5:2 C5:2 G4:2
G3:2 D4:2 G4:2 B4:2 D5:2 B4:2 G4:2 D4:2
E5:4 D5:2 C5:2 B4:4 C5:2 D5:2
E5:4 A4:4 A4:2 B4:2 C5:4
D5:4 C5:2 B4:2 A4:4 G4:2 B4:2
A4:8 R:4 E4:2 G4:2
A4:1 C5:1 E5:1 A5:1 A4:1 C5:1 E5:1 A5:1 A4:1 C5:1 E5:1 A5:1 A4:1 C5:1 E5:1 A5:1
F4:1 A4:1 C5:1 F5:1 F4:1 A4:1 C5:1 F5:1 F4:1 A4:1 C5:1 F5:1 F4:1 A4:1 C5:1 F5:1
C5:1 E5:1 G5:1 C6:1 C5:1 E5:1 G5:1 C6:1 C5:1 E5:1 G5:1 C6:1 C5:1 E5:1 G5:1 C6:1
G4:1 B4:1 D5:1 G5:1 G4:1 B4:1 D5:1 G5:1 G4:1 B4:1 D5:1 G5:1 G4:1 B4:1 D5:1 G5:1
E5:4 D5:2 C5:2 B4:4 C5:2 D5:2
E5:4 A5:4 G5:2 E5:2 C5:4
D5:4 C5:2 B4:2 G4:4 B4:2 D5:2
A4:8 R:8
"""
melodie = []
for tok in PARTITION.split():
    nom, d = tok.split(':')
    melodie += [0 if nom == 'R' else notes[nom], int(d)]
melodie.append(0xFF)
mus = ENTETE + "; Demi-périodes en µs (cycles) des notes 1 à %d (C3 à C6).\n" % len(periodes)
for i in range(0, len(periodes), 8):
    mus += '%-8s dc.w %s\n' % ('PERIODES' if i == 0 else '',
                               ','.join(str(p) for p in periodes[i:i + 8]))
mus += ("; Mélodie : paires (note, durée en débordements du timer de 65,5 ms) ;\n"
        "; note 0 = silence ; $FF = reprise au début.\n")
mus += octets('MELODIE', melodie, 16)
ecrit('donnees-musique.inc', mus)

print("logo : %d colonnes ; police : %d octets ; texte : %d caractères ; "
      "mélodie : %d octets" % (larg, len(police), len(txt), len(melodie)))

# ---------------------------------------------------------------------------
# 6. Perspective du programme vectoriel : PERSP[z + 128] = 150 x 300 / (300 + z)
#    (facteur d'échelle sur 256 : x écran = x x PERSP / 256), plafonné à 255.
# ---------------------------------------------------------------------------
persp = [min(255, int(round(150 * 300 / (300 + z)))) for z in range(-128, 128)]
ecrit('donnees-persp.inc', ENTETE +
      "; Perspective : PERSP[z + 128] = 150 x 300 / (300 + z), z = -128..127.\n" +
      octets('PERSP', persp))
print("perspective : %d à %d" % (persp[128 - 60], persp[128 + 60]))
