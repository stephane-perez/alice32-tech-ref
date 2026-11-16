#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ym2alice.py : convertit une musique .ym (Atari ST et autres machines à
YM2149 / AY-3-8910) pour le lecteur 3 voix + bruit de l'Alice 32
(inc/ymplay.inc). Code ORIGINAL du dépôt alice32-tech-ref.

Formats lus : YM2!, YM3!, YM3b, YM5!, YM6! (description d'après le
lecteur AtariAudio d'Arnaud Carré, licence MIT), bruts ou compressés
LHA (-lh0-, -lh5-, comme la plupart des fichiers .ym).

Conversion, trame par trame (50 Hz en général) :
  - voie A, B, C : période de son -> incrément de phase du lecteur ;
    volume (ou enveloppe, MOYENNÉE sur la trame) -> rapport cyclique ;
  - mixeur (registre 7) : son et/ou bruit par voie ; une voie à bruit
    seul joue le bruit « haché » à la fréquence du bruit du YM ;
  - non reproduits : effets spéciaux YM5/YM6 (voix SID, digidrums,
    sync-buzzer), forme d'onde des enveloppes rapides, volume du bruit
    indépendant de la voie.
Sortie : inc/donnees-ym.inc (table des fréquences + flux compact).

Boucle : par défaut celle du fichier (souvent la trame 0). --boucle B
--fin F jouent les trames 0 à F-1 puis reprennent à la trame B (par
exemple une intro puis un motif qui se répète) ; --cherche-boucle
indique les répétitions exactes trouvées dans le fichier.

Usage : ym2alice.py musique.ym [-o inc/donnees-ym.inc] [--secondes 30]
        [--boucle B --fin F] [--cherche-boucle] [--titre T --auteur A]
        [--fin 0x4E00] [--ecoute apercu.wav] [--transpose 0]
"""
import argparse
import math
import os
import struct
import sys
import wave

TIC_CYCLES = 122                 # doit être égal à la durée d'un tic de ymplay.inc
TICS_S = 1e6 / TIC_CYCLES
RC = [0, 1, 1, 1, 1, 2, 2, 3, 4, 6, 8, 11, 16, 22, 28, 40]   # = YM_RC de ymplay.inc


class ErreurYM(Exception):
    pass


# =====================================================================
#  LHA : en-têtes de niveau 0, 1, 2 ; méthodes -lh0- et -lh5-
# =====================================================================
def crc16(data):
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def est_lha(d):
    return len(d) > 22 and d[2:4] == b'-l' and d[6:7] == b'-'


def lit_lha(d):
    niveau = d[20]
    methode = d[2:7]
    if niveau in (0, 1):
        h = d[0] + 2
        taille_c, taille_o = struct.unpack('<II', d[7:15])
        nlen = d[21]
        crc = struct.unpack('<H', d[22 + nlen:24 + nlen])[0]
        debut = h
        if niveau == 1:                      # en-têtes étendus comptés dans taille_c
            p = h - 2
            ext = struct.unpack('<H', d[p:p + 2])[0]
            q = h
            while ext:
                taille_c -= ext
                nxt = struct.unpack('<H', d[q + ext - 2:q + ext])[0]
                q += ext
                ext = nxt
            debut = q
    elif niveau == 2:
        h = struct.unpack('<H', d[0:2])[0]
        taille_c, taille_o = struct.unpack('<II', d[7:15])
        crc = struct.unpack('<H', d[21:23])[0]
        debut = h
    else:
        raise ErreurYM("en-tête LHA de niveau %d non géré" % niveau)
    data = d[debut:debut + taille_c]
    if methode == b'-lh0-':
        out = bytes(data)
    elif methode == b'-lh5-':
        out = lh5(data, taille_o)
    else:
        raise ErreurYM("méthode LHA %s non gérée (décompresser avec 7-Zip)" % methode.decode())
    if crc16(out) != crc:
        raise ErreurYM("décompression LHA incorrecte (CRC) : décompresser le fichier avec 7-Zip")
    return out


class Bits:
    def __init__(self, data):
        self.d = data
        self.p = 0                         # position en bits

    def lit(self, n):
        v = 0
        for _ in range(n):
            i = self.p >> 3
            b = (self.d[i] >> (7 - (self.p & 7))) & 1 if i < len(self.d) else 0
            v = (v << 1) | b
            self.p += 1
        return v

    def regarde(self, n):
        p = self.p
        v = self.lit(n)
        self.p = p
        return v


def huffman(longueurs):
    """Codes canoniques (ordre des longueurs puis des symboles) -> dict."""
    table = {}
    code = 0
    maxl = max(longueurs) if longueurs else 0
    for l in range(1, maxl + 1):
        for s, ls in enumerate(longueurs):
            if ls == l:
                table[(l, code)] = s
                code += 1
        code <<= 1
    return table


def decode_sym(b, table, unique):
    if unique is not None:
        return unique
    code = 0
    l = 0
    while True:
        code = (code << 1) | b.lit(1)
        l += 1
        s = table.get((l, code))
        if s is not None:
            return s
        if l > 24:
            raise ErreurYM("flux -lh5- invalide")


def lh5(data, taille):
    NC, NT, NP, TBIT, CBIT, PBIT = 510, 19, 14, 5, 9, 4
    b = Bits(data)
    out = bytearray()

    def lit_pt(nn, nbit, special):
        n = b.lit(nbit)
        if n == 0:
            c = b.lit(nbit)
            return [0] * nn, c
        lens = []
        while len(lens) < n:
            c = b.regarde(3)
            if c == 7:
                b.lit(3)
                while b.lit(1):
                    c += 1
            else:
                b.lit(3)
            lens.append(c)
            if len(lens) == special:
                for _ in range(b.lit(2)):
                    lens.append(0)
        lens += [0] * (nn - len(lens))
        return lens[:nn], None

    def lit_c(pt_t, pt_u):
        n = b.lit(CBIT)
        if n == 0:
            c = b.lit(CBIT)
            return [0] * NC, c
        lens = []
        while len(lens) < n:
            c = decode_sym(b, pt_t, pt_u)
            if c <= 2:
                k = 1 if c == 0 else (b.lit(4) + 3 if c == 1 else b.lit(CBIT) + 20)
                lens += [0] * k
            else:
                lens.append(c - 2)
        lens += [0] * (NC - len(lens))
        return lens[:NC], None

    reste = 0
    while len(out) < taille:
        if reste == 0:
            reste = b.lit(16)
            ptl, ptu = lit_pt(NT, TBIT, 3)
            pt_t = huffman(ptl) if ptu is None else None
            cl, cu = lit_c(pt_t, ptu)
            c_t = huffman(cl) if cu is None else None
            pl, pu = lit_pt(NP, PBIT, -1)
            p_t = huffman(pl) if pu is None else None
        reste -= 1
        c = decode_sym(b, c_t, cu)
        if c < 256:
            out.append(c)
        else:
            longueur = c - 253
            j = decode_sym(b, p_t, pu)
            if j > 1:
                j = (1 << (j - 1)) + b.lit(j - 1)
            pos = len(out) - j - 1
            for k in range(longueur):
                out.append(out[pos + k])
    return bytes(out[:taille])


# =====================================================================
#  Fichier YM -> liste de trames de 16 registres
# =====================================================================
def lit_ym(d):
    if est_lha(d):
        d = lit_lha(d)
    tag = d[:4]
    info = {'titre': '', 'auteur': '', 'horloge': 2000000, 'cadence': 50, 'boucle': 0,
            'format': tag.decode('latin-1')}
    if tag in (b'YM2!', b'YM3!', b'YM3b'):
        corps = d[4:]
        if tag == b'YM3b':
            info['boucle'] = struct.unpack('<I', corps[-4:])[0]
            corps = corps[:-4]
        n = len(corps) // 14
        trames = [[corps[r * n + t] for r in range(14)] + [0, 0] for t in range(n)]
        return trames, info
    if tag in (b'YM5!', b'YM6!'):
        if d[4:12] != b'LeOnArD!':
            raise ErreurYM("en-tête YM5/YM6 invalide")
        n, attr = struct.unpack('>II', d[12:20])
        ndd = struct.unpack('>H', d[20:22])[0]
        info['horloge'] = struct.unpack('>I', d[22:26])[0]
        info['cadence'] = struct.unpack('>H', d[26:28])[0]
        info['boucle'] = struct.unpack('>I', d[28:32])[0]
        p = 34 + struct.unpack('>H', d[32:34])[0]
        for _ in range(ndd):                 # digidrums : ignorés
            p += 4 + struct.unpack('>I', d[p:p + 4])[0]
        chaines = []
        for _ in range(3):
            q = d.index(b'\0', p)
            chaines.append(d[p:q].decode('latin-1', 'replace'))
            p = q + 1
        info['titre'], info['auteur'] = chaines[0], chaines[1]
        corps = d[p:p + 16 * n]
        if attr & 1:                          # registres entrelacés
            trames = [[corps[r * n + t] for r in range(16)] for t in range(n)]
        else:
            trames = [list(corps[t * 16:t * 16 + 16]) for t in range(n)]
        return trames, info
    if tag in (b'MIX1', b'YMT1', b'YMT2'):
        raise ErreurYM("format %s (échantillons numériques ou tracker) : pas une suite de "
                       "registres YM2149, non géré" % tag.decode('latin-1'))
    raise ErreurYM("format %r non géré (YM2!, YM3!, YM3b, YM5!, YM6!)" % tag)


# =====================================================================
#  Émulation du YM2149 trame par trame -> état des 3 voix
# =====================================================================
class Enveloppe:
    """Enveloppe du YM2149 (32 pas), niveau moyen sur une trame."""
    def __init__(self):
        self.forme = 0
        self.pos = 0.0                         # en pas depuis le départ

    def depart(self, forme):
        self.forme = forme & 15
        self.pos = 0.0

    def niveau(self, pos):
        f = self.forme
        cont, att, alt, hold = f & 8, f & 4, f & 2, f & 1
        cycle, pas = divmod(int(pos), 32)
        if cycle == 0:
            return pas if att else 31 - pas
        if not cont:
            return 0
        if hold:
            fin = 31 if att else 0
            return (31 - fin) if alt else fin
        monte = bool(att) ^ (alt and cycle % 2 == 1)
        return pas if monte else 31 - pas

    def trame(self, duree, periode, horloge):
        periode = max(periode, 1)
        pas = duree * horloge / (8.0 * periode)    # pas de l'enveloppe pendant la trame
        n = 16
        somme = sum(self.niveau(self.pos + pas * k / n) for k in range(n))
        self.pos += pas
        return somme / n                          # 0..31


def emule(trames, info, transpose=0):
    horloge, cadence = info['horloge'], info['cadence']
    duree = 1.0 / cadence
    env = Enveloppe()
    etats = []
    for t in trames:
        r = t
        if r[13] != 0xFF:
            if not etats or r[13] != getattr(env, 'derniere', None) or info['format'] in ('YM5!', 'YM6!'):
                env.depart(r[13])
            env.derniere = r[13]
        niv_env = env.trame(duree, r[11] | (r[12] << 8), horloge) / 2.0   # -> 0..15,5
        voix = []
        bruit_p = max(r[6] & 31, 1)
        for k in range(3):
            tp = max(r[2 * k] | ((r[2 * k + 1] & 15) << 8), 1)
            son = not (r[7] >> k) & 1
            bruit = not (r[7] >> (k + 3)) & 1
            vol = r[8 + k]
            v = int(round(min(15, niv_env))) if vol & 16 else vol & 15
            if son:
                f = horloge / (16.0 * tp) * 2 ** (transpose / 12)
                if f > TICS_S * 0.45:
                    v = 0                     # trop aigu pour le lecteur
            elif bruit:
                f = min(horloge / (16.0 * bruit_p), TICS_S / 4)   # porteuse du bruit
            else:
                v, f = 0, 0.0
            if v == 0:
                f = 0.0
            voix.append((f, v, 1 if bruit and v else 0))
        etats.append(voix)
    return etats


# =====================================================================
#  Encodage du flux
# =====================================================================
def incr(f):
    return min(65535, int(round(f * 65536 / TICS_S)))


def dictionnaire(etats, maxi=255):
    valeurs = sorted({incr(f) for e in etats for (f, v, n) in e})
    if len(valeurs) <= maxi:
        return valeurs, {x: x for x in valeurs}
    # trop de valeurs : regroupement logarithmique de plus en plus grossier
    pas = 1 / 64
    while True:
        cle = {}
        for x in valeurs:
            cle[x] = 0 if x == 0 else round(math.log2(x) / pas)
        groupes = {}
        for x, c in cle.items():
            groupes.setdefault(c, []).append(x)
        if len(groupes) <= maxi:
            rep = {c: int(round(2 ** (c * pas))) if c else 0 for c in groupes}
            vers = {x: rep[cle[x]] for x in valeurs}
            return sorted(set(vers.values())), vers
        pas *= 1.25


def encode(etats, boucle, max_octets):
    table, vers = dictionnaire(etats)
    max_octets -= 2 * len(table)              # la table des fréquences compte aussi
    index = {x: i for i, x in enumerate(table)}
    flux = bytearray()
    prec = None
    repet = 0
    boucle_ofs = 0
    n_trames = 0
    for i, e in enumerate(etats):
        cle = []
        for (f, v, n) in e:
            cle.append((index[vers[incr(f)]], v, n))
        cle_f = (cle[0][0], cle[1][0], cle[2][0])
        vol12 = (cle[0][1] << 4) | cle[1][1]
        vol3n = (cle[2][1] << 4) | cle[0][2] | (cle[1][2] << 1) | (cle[2][2] << 2)
        etat = cle_f + (vol12, vol3n)
        cle_trame = bytearray()
        force = (i == 0 or i == boucle)
        if i == boucle:
            if repet:
                flux.append(0x80 | repet)
                repet = 0
            boucle_ofs = len(flux)
        if not force and etat == prec:
            repet += 1
            if repet == 127:
                flux.append(0x80 | repet)
                repet = 0
        else:
            if repet:
                cle_trame.append(0x80 | repet)
                repet = 0
            m = 0
            octets = []
            for k in range(3):
                if force or etat[k] != prec[k]:
                    m |= 1 << k
                    octets.append(etat[k])
            if force or etat[3] != prec[3]:
                m |= 8
                octets.append(etat[3])
            if force or etat[4] != prec[4]:
                m |= 16
                octets.append(etat[4])
            cle_trame += bytes([m] + octets)
        if len(flux) + len(cle_trame) + 3 + (1 if repet else 0) > max_octets:
            break
        flux += cle_trame
        prec = etat
        n_trames = i + 1
    if repet:
        flux.append(0x80 | repet)
    if boucle >= n_trames:
        boucle_ofs = 0
    return table, flux, boucle_ofs, n_trames, vers


def ecoute(etats, n_trames, cadence, chemin, vers):
    """Aperçu WAV du rendu du lecteur (impulsions OU, bruit LFSR)."""
    tpf = round(TICS_S / cadence)
    lf = 0xACE1
    ph = [0, 0, 0]
    rate = 22050
    sortie = bytearray()
    acc = 0.0
    pas = rate / TICS_S
    for e in etats[:n_trames]:
        inc = [vers[incr(f)] for (f, v, n) in e]
        rc = [RC[v] for (f, v, n) in e]
        br = [n for (f, v, n) in e]
        for _ in range(tpf):
            o = 0
            for k in range(3):
                ph[k] = (ph[k] + inc[k]) & 0xFFFF
                bit = (ph[k] >> 8) < rc[k]
                if br[k]:
                    bit = bit and (lf >> 15)
                o |= bit
            lf = ((lf << 1) & 0xFFFF) ^ (0x2D if lf & 0x8000 else 0)
            acc += pas
            while acc >= 1:
                sortie.append(200 if o else 56)
                acc -= 1
    with wave.open(chemin, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(rate)
        w.writeframes(bytes(sortie))


def cherche_boucle(trames, cadence, pmax=2000):
    """Plus petites périodes P telles que P trames de suite se répètent
    à l'identique (registres 0-13), et leur début."""
    t = [tuple(x[:14]) for x in trames]
    n = len(t)
    trouves = []
    for p in range(8, min(pmax, n // 2) + 1):
        suite = 0
        for i in range(n - p):
            if t[i] == t[i + p]:
                suite += 1
                if suite >= p:
                    debut = i - p + 1
                    if not any(p % q == 0 and abs(debut - d) <= q for q, d in trouves):
                        trouves.append((p, debut))
                    break
            else:
                suite = 0
        if len(trouves) >= 5:
            break
    if not trouves:
        print("Aucune répétition exacte trouvée")
    for p, d in trouves:
        print("Répétition : motif de %d trames (%.2f s) à partir de la trame %d (%.2f s) "
              "-> --boucle %d --fin %d" % (p, p / cadence, d, d / cadence, d, d + p))


def ascii_alice(t, n=38):
    import unicodedata
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn').upper()
    return ''.join(c if 32 <= ord(c) < 96 and c != '"' else ' ' for c in t)[:n]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ym')
    ap.add_argument('-o', '--inc', default=None)
    ap.add_argument('--secondes', type=float, default=None, help='durée maximale')
    ap.add_argument('--octets', type=int, default=5400,
                    help='place pour la table des fréquences + le flux '
                         '(défaut : 5 400, RAM de base sans extension)')
    ap.add_argument('--transpose', type=int, default=0, help='demi-tons')
    ap.add_argument('--boucle', type=int, default=None, help='trame de reprise')
    ap.add_argument('--fin', type=int, default=None, help='trame de fin (exclue)')
    ap.add_argument('--cherche-boucle', action='store_true',
                    help='afficher les répétitions exactes (début, période)')
    ap.add_argument('--titre', default=None)
    ap.add_argument('--auteur', default=None)
    ap.add_argument('--ecoute', help='WAV de l\'aperçu du rendu attendu')
    a = ap.parse_args()
    try:
        trames, info = lit_ym(open(a.ym, 'rb').read())
    except ErreurYM as e:
        sys.exit("Erreur : %s" % e)
    if a.titre is not None:
        info['titre'] = a.titre
    if a.auteur is not None:
        info['auteur'] = a.auteur
    if not info['titre']:
        info['titre'] = os.path.basename(a.ym)
    if a.cherche_boucle:
        cherche_boucle(trames, info['cadence'])
    if a.fin is not None:
        trames = trames[:a.fin]
    if a.boucle is not None:
        info['boucle'] = a.boucle
    if a.secondes:
        trames = trames[:int(a.secondes * info['cadence'])]
    etats = emule(trames, info, a.transpose)
    table, flux, boucle_ofs, n, vers = encode(etats, info['boucle'], a.octets)
    tpf = round(TICS_S / info['cadence'])
    if tpf > 255:
        sys.exit("cadence trop basse (%d Hz)" % info['cadence'])
    print("%s : %s, %d trames à %d Hz (%.1f s), horloge %d Hz"
          % (a.ym, info['format'], len(trames), info['cadence'], len(trames) / info['cadence'],
             info['horloge']))
    print("Titre : %s / auteur : %s" % (info['titre'], info['auteur']))
    print("Converti : %d trames (%.1f s), %d fréquences, flux %d octets (%.1f octets/trame)"
          % (n, n / info['cadence'], len(table), len(flux), len(flux) / max(n, 1)))
    effets = sum(1 for t in trames[:n] if (t[1] & 0x30) or (t[3] & 0x30))
    if effets:
        print("Note : %d trames sur %d utilisent des effets spéciaux YM5/YM6 (voix SID, "
              "digidrums, sync-buzzer), non reproduits" % (effets, n))
    if a.inc:
        with open(a.inc, 'w', encoding='utf-8') as f:
            f.write("; Fichier GÉNÉRÉ par outils/ym2alice.py à partir de %s\n"
                    % os.path.basename(a.ym))
            f.write("; %s - %s : %d trames, %d fréquences, flux %d octets\n"
                    % (info['titre'], info['auteur'], n, len(table), len(flux)))
            f.write("YM_TPF   EQU %d               ; tics par trame (%d Hz)\n" % (tpf, info['cadence']))
            f.write('YM_TITRE dc.b "%s",0\n' % ascii_alice(info['titre']))
            f.write('YM_AUTEUR dc.b "%s",0\n' % ascii_alice(info['auteur']))
            for i in range(0, len(table), 8):
                f.write('%-8s dc.w %s\n' % ('YM_TABF' if i == 0 else '',
                                           ','.join(str(v) for v in table[i:i + 8])))
            for i in range(0, len(flux), 24):
                f.write('%-8s dc.b %s\n' % ('YM_FLUX' if i == 0 else '',
                                           ','.join('$%02X' % v for v in flux[i:i + 24])))
            f.write('         dc.b $80             ; fin : reprise à la trame de boucle\n')
            f.write('         dc.w YM_FLUX+%d\n' % boucle_ofs)
        print("Écrit :", a.inc)
    if a.ecoute:
        ecoute(etats, n, info['cadence'], a.ecoute, vers)
        print("Aperçu :", a.ecoute)


if __name__ == '__main__':
    main()
