#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
k7wav.py : conversion des cassettes Alice entre le format .k7 de DCAlice
et le format .wav, dans les deux sens. Réécriture en Python du
comportement de DCALICEK7 version 2011.04 de Daniel Coulom
(alice32.free.fr), établi en lisant sa notice et son code machine
(voir docs/09-cassette-et-formats-de-fichiers.md). Code ORIGINAL.

  k7wav.py prog.k7                   -> prog.wav   (k7 > wav)
  k7wav.py prog.wav                  -> prog.k7    (wav > k7)
  k7wav.py entree -o sortie          (sens donné par les extensions)

Paramètres (mêmes noms et valeurs par défaut que DCALICEK7) :
  --seuil 30        seuil initial entre bit 1 et bit 0, en échantillons à 44 100 Hz
  --zero 128        niveau zéro (0-255) ; seul paramètre utilisé pour k7 > wav
  --bruit 40        amplitude minimale (crête à crête, 0-255) d'une alternance
  --inversion       inversion de phase
  --transitions     amélioration des transitions
  --silence-initial S  k7 > wav : durée en secondes du silence avant le premier
                    bloc (DCALICEK7 : 20 s), par exemple 2
  --entete-corrigee k7 > wav : taille du bloc « data » exacte (DCALICEK7 écrit
                    taille - 45 au lieu de taille - 44)

FORMAT .k7 : suite de blocs « $55 $3C type longueur données somme $55 »
(somme = type + longueur + données, modulo 256), chacun précédé, s'il a
été produit par DCALICEK7, de l'en-tête de 8 octets $DC, 0, nombre
d'octets de synchronisation (16 bits), longueur du silence avant le
bloc en échantillons (32 bits), poids faible d'abord.

FORMAT .wav (k7 > wav) : 44 100 Hz, 8 bits, mono. Un bit = une période
carrée, alternance haute (240) puis basse (16) : bit 1 = 10 + 10
échantillons (2 205 Hz), bit 0 = 20 + 20 (1 102,5 Hz) ; octets poids
faible d'abord, sans bit de start ni de stop. Sans en-tête $DC :
silence de 882 000 échantillons (20 s) avant un bloc $00, de 16 000
avant le premier bloc qui suit un bloc $00, de 128 sinon ; 127 octets
$55 avant un bloc $00 ou le bloc qui le suit, 1 sinon ; 88 200
échantillons de silence à la fin.
"""
import argparse
import os
import struct
import sys

F = 44100


class ErreurK7(Exception):
    pass


# =====================================================================
#  k7 > wav
# =====================================================================
def octet_wav(sortie, v):
    for _ in range(8):
        n = 10 if v & 1 else 20
        sortie += b'\xf0' * n
        sortie += b'\x10' * n
        v >>= 1


def k7_vers_wav(k7, zero=128, entete_corrigee=False, journal=print, silence_initial=None):
    """Retourne les octets du fichier .wav. silence_initial : secondes de
    silence avant le premier bloc (None = comportement de DCALICEK7)."""
    premier = True
    w = bytearray(b'RIFF\0\0\0\0WAVEfmt \x10\0\0\0\x01\0\x01\0'
                  b'\x44\xac\0\0\x44\xac\0\0\x01\0\x08\0data\0\0\0\0')
    pos = 0
    precedent = 0xFF                       # type du bloc précédent
    n = len(k7)
    while True:
        nsync = silence = 0
        # chercher « $55 $3C » (ou un en-tête $DC)
        while pos < n:
            if k7[pos] == 0xDC:
                if pos + 1 < n and k7[pos + 1] == 0 and pos + 7 < n:
                    nsync = k7[pos + 2] | (k7[pos + 3] << 8)
                    silence = struct.unpack('<I', k7[pos + 4:pos + 8])[0]
                    pos += 8
                else:
                    pos += 2
                continue
            if k7[pos] == 0x3C and pos > 0 and k7[pos - 1] == 0x55:
                break
            pos += 1
        else:
            break                          # fin du fichier
        if pos + 2 >= n:
            raise ErreurK7("Erreur fin prématurée du fichier à convertir")
        typ, long_ = k7[pos + 1], k7[pos + 2]
        pos += 3
        if precedent == 0xFF and typ != 0:
            raise ErreurK7("Erreur dans l'entête de bloc : type inattendu")
        if precedent == 0 and typ != 1:
            raise ErreurK7("Erreur dans l'entête de bloc : type inattendu")
        if pos + long_ >= n:
            raise ErreurK7("Erreur fin prématurée du fichier à convertir")
        donnees = k7[pos:pos + long_]
        pos += long_
        somme_lue = k7[pos]
        pos += 1
        somme = (typ + long_ + sum(donnees)) & 0xFF
        if nsync == 0:
            if typ == 0 or precedent == 0:
                nsync = 0x7F
        if silence == 0:
            silence = 882000 if typ == 0 else 128
            if precedent == 0:
                silence = 16000
        if premier and silence_initial is not None:
            silence = int(round(silence_initial * F))
        premier = False
        if typ == 0:
            journal("Fichier : " + ''.join(chr(c) if c else ' ' for c in donnees[:8]))
        journal("Bloc %02X : long=%02x gap=%i synchro=%i checksum lue=%02x calculée=%02x"
                % (typ, long_, silence, nsync, somme_lue, somme))
        if somme != somme_lue:
            raise ErreurK7("Erreur checksum lue différente du calcul")
        precedent = typ
        w += bytes([zero & 0xFF]) * silence
        for _ in range(max(nsync, 1)):
            octet_wav(w, 0x55)
        for v in (0x3C, typ, long_):
            octet_wav(w, v)
        for v in donnees:
            octet_wav(w, v)
        octet_wav(w, somme)
        octet_wav(w, 0x55)
    w += bytes([zero & 0xFF]) * 88200
    taille = len(w) - 8
    w[4:8] = struct.pack('<I', taille)
    w[40:44] = struct.pack('<I', len(w) - 44 if entete_corrigee else taille - 0x25)
    return bytes(w)


# =====================================================================
#  wav > k7
# =====================================================================
def lit_wav(donnees):
    """Échantillons 8 bits (0-255) du canal droit, et la fréquence."""
    if len(donnees) <= 0x31 or donnees[8:12] != b'WAVE':
        raise ErreurK7("Erreur de structure du fichier .wav")
    freq = donnees[0x18] | (donnees[0x19] << 8) | (donnees[0x1A] << 16)
    par = donnees[0x20]                    # octets par trame
    # comme DCALICEK7 : données lues à partir de l'octet 48 ; on garde le
    # DERNIER octet de chaque trame (poids fort en 16 bits, canal droit)
    brut = donnees[0x30:]
    if par <= 1:
        ech = bytearray(brut)
    else:
        ech = bytearray(((brut[i] + 0x80) & 0xFF) for i in range(par - 1, len(brut), par))
    return ech, freq, par


def creneaux(ech, freq, zero=128, bruit=40, inversion=False, transitions=False, seuil=30):
    """Largeurs signées des alternances (positives > 0, négatives < 0),
    ramenées à 44 100 Hz."""
    res = []
    prec = zero
    dernier = 0
    demi = freq // 2
    for n, v in enumerate(ech, 1):
        if v < zero:
            if prec < zero:
                prec = v
                continue
        else:
            if prec >= zero:
                prec = v
                continue
        # passage par zéro
        if abs(v - zero) * 2 < bruit:
            continue                       # trop faible : bruit
        largeur = int((F * (n - dernier) + demi) / freq)
        res.append(-largeur if prec < zero else largeur)
        prec = v
        dernier = n
    if inversion:
        res = [-x for x in res]
    if transitions:
        for i in range(1, len(res)):
            if res[i] <= 0:
                p = res[i - 1]
                s = abs(res[i] + p)
                if p > seuil:
                    if s <= seuil // 4:
                        res[i] = -p
                elif s <= seuil // 6:
                    res[i] = -p
    return res


class FinDonnees(Exception):
    pass


MESSAGES = {-24: "Erreur bit trop court (premiere demi-periode)",
            -25: "Erreur bit trop long (premiere demi-periode)"}


class Decodeur:
    def __init__(self, cr, seuil):
        self.cr = cr
        self.n = len(cr)
        self.seuil0 = seuil
        self.t = seuil
        self.pos = 0

    def periode(self, i):
        return self.cr[i] - self.cr[i + 1]

    def octet(self):
        """8 bits, poids faible d'abord ; -1 en fin de données,
        -24 bit trop court, -25 bit trop long (codes de DCALICEK7)."""
        t = self.t
        v = 0
        fin = self.pos + 16
        while True:
            if self.pos + 1 >= self.n:
                return -1
            p = self.periode(self.pos)
            self.pos += 2
            if p < t // 2:
                return -24
            if p > (3 * t) // 2:
                return -25
            v >>= 1
            if p < t:
                v |= 0x80
            if self.pos == fin:
                return v

    def bloc(self):
        """Décode un bloc. Retourne None à la fin, sinon un dictionnaire."""
        cr, n = self.cr, self.n
        silence = 0
        debut = self.pos
        if self.pos >= n:
            return None
        if cr[self.pos] < 0:
            self.pos += 1
        self.t = t = self.seuil0
        # phase A : 3 paires (bit 0, bit 1) de suite avec le seuil initial
        while True:
            somme = paires = 0
            ok = False
            while True:
                i = self.pos
                if i + 1 >= n:
                    return None
                a = self.periode(i)
                self.pos = i + 2
                if a < t or a > (3 * t) // 2:
                    break
                if i + 3 >= n:
                    return None
                b = self.periode(i + 2)
                self.pos = i + 4
                if b > t or b < t // 2:
                    break
                somme += a + b
                paires += 2
                if paires == 6:
                    ok = True
                    break
            if ok:
                break
        # phase B : suite de la synchronisation, seuil ajusté
        i = self.pos
        debut_b = i
        depart = i
        while True:
            if i + 1 >= n:
                return None
            p1 = self.periode(i)
            if p1 < t or p1 > (3 * t) // 2:
                break
            if i + 3 >= n:
                return None
            p2 = self.periode(i + 2)
            if p2 > t or p2 < t // 2:
                break
            t = (p2 + 2 * t + 2 + p1) >> 2
            self.t = t
            somme += p1 + p2
            paires += 2
            i += 4
            depart = i
        # silence : tout ce qui précède la synchronisation (moins 12 alternances)
        for j in range(debut, debut_b - 12):
            silence += abs(cr[j])
        bauds = (F * paires + somme // 2) // somme if somme else 0
        nsync = (paires + 4) >> 3
        # chercher $3C en glissant d'un bit
        k = depart
        while True:
            self.pos = k
            v = self.octet()
            if v == -1:
                return None
            if v == 0x3C:
                break
            k += 2                         # bit invalide ou autre octet : on glisse

        def lit():
            v = self.octet()
            if v == -1:
                raise FinDonnees()
            if v < 0:
                raise ErreurK7(MESSAGES[v])
            return v
        try:
            typ = lit()
            long_ = lit()
            donnees = [lit() for _ in range(long_)]
            somme_lue = lit()
        except FinDonnees:
            return None
        p = self.pos
        if self.octet() < 0:               # $55 final illisible : on recule
            self.pos = p - 2
        calc = (typ + long_ + sum(donnees)) & 0xFF
        return dict(type=typ, long=long_, donnees=donnees, somme=somme_lue,
                    calcul=calc, nsync=nsync, silence=silence, seuil=t, bauds=bauds)


def wav_vers_k7(donnees_wav, seuil=30, zero=128, bruit=40, inversion=False,
                transitions=False, journal=print):
    ech, freq, par = lit_wav(donnees_wav)
    journal("%i octet%s par échantillon - %i échantillons par seconde"
            % (par, 's' if par > 1 else '', freq))
    cr = creneaux(ech, freq, zero, bruit, inversion, transitions, seuil)
    journal("Nombre de créneaux détectés : %i" % len(cr))
    dec = Decodeur(cr, seuil)
    k7 = bytearray()
    erreurs = 0
    while True:
        try:
            b = dec.bloc()
        except ErreurK7 as e:              # DCALICEK7 s'arrête à la première erreur
            journal(str(e))
            erreurs += 1
            break
        if b is None:
            break
        if b['type'] == 0:
            journal("Fichier : " + ''.join(chr(c) if c else ' ' for c in b['donnees'][:8]))
        msg = ("Bloc %02X : long=%02x gap=%i synchro=%i seuil=%i bauds=%i checksum lue=%02x, calculée=%02x"
               % (b['type'], b['long'], b['silence'], b['nsync'], b['seuil'], b['bauds'],
                  b['somme'], b['calcul']))
        if b['somme'] != b['calcul']:
            journal(msg + " ERREUR!")
            erreurs += 1
            break
        journal(msg + " OK")
        k7 += bytes([0xDC, 0]) + struct.pack('<H', b['nsync'] & 0xFFFF) + struct.pack('<I', b['silence'])
        k7 += bytes([0x55, 0x3C, b['type'], b['long']] + b['donnees'] + [b['somme'], 0x55])
    if not k7 and not erreurs:
        raise ErreurK7("Erreur aucun bloc valide dans le fichier wav")
    return bytes(k7), erreurs


# =====================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('entree')
    ap.add_argument('-o', '--sortie')
    ap.add_argument('--seuil', type=int, default=30)
    ap.add_argument('--zero', type=int, default=128)
    ap.add_argument('--bruit', type=int, default=40)
    ap.add_argument('--inversion', action='store_true')
    ap.add_argument('--transitions', action='store_true')
    ap.add_argument('--silence-initial', type=float, default=None, metavar='S')
    ap.add_argument('--entete-corrigee', action='store_true')
    ap.add_argument('-q', '--silencieux', action='store_true')
    a = ap.parse_args()
    journal = (lambda *x: None) if a.silencieux else print
    base, ext = os.path.splitext(a.entree)
    ext = ext.lower()
    if ext not in ('.k7', '.wav'):
        sys.exit("Erreur dans le nom du fichier en entrée (.k7 ou .wav attendu)")
    sortie = a.sortie or base + ('.wav' if ext == '.k7' else '.k7')
    if os.path.splitext(sortie)[1].lower() == ext:
        sys.exit("Erreur : même extension en entrée et en sortie")
    donnees = open(a.entree, 'rb').read()
    journal("Debut de conversion cassette Alice : %s ---> %s" % (a.entree, sortie))
    try:
        if ext == '.k7':
            res = k7_vers_wav(donnees, a.zero, a.entete_corrigee, journal, a.silence_initial)
            erreurs = 0
        else:
            res, erreurs = wav_vers_k7(donnees, a.seuil, a.zero, a.bruit, a.inversion,
                                       a.transitions, journal)
    except ErreurK7 as e:
        sys.exit(str(e))
    open(sortie, 'wb').write(res)
    journal("Conversion terminée sans erreur" if not erreurs
            else "Conversion terminée avec %i erreurs" % erreurs)


if __name__ == '__main__':
    main()
