#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulateur MINIMAL pour vérifier la logique des programmes de ce dossier
(exemple ORIGINAL du dépôt alice32-tech-ref). Ce n'est PAS un émulateur
d'Alice 32 : il remplace DCAlice ou MAME seulement pour un premier essai.

Modélisé :
  - 6803 (jeu d'instructions complet du 6801, cycles approximatifs),
    timer (compteur, TOF, OCF, interruptions), clavier ESPACE/ENTRÉE,
    son (instants des inversions du bit 7 de $BFFF) ;
  - EF9345 réduit à ce que la démo utilise : KRF, OCT, IND, CLF, NOP,
    VRM, BUSY, VSYNC (bit 2), ROR/YOR, jeu G'0 dans le bloc 3,
    double hauteur / largeur ; jeu G0 remplacé par la police de la démo ;
  - ROM : seul INASS ($D42C) est simulé.
Non modélisé : suspensions des commandes pendant l'affichage, vraies
durées de l'EF9345, police de la ROM, clignotement, quadrichromes…

Usage : simulateur.py prog.bin --png sortie --a 1.0,2.5 [--touche 3.0:ESPACE]
"""
import argparse
import os
import struct
import sys

ORG = 0x3400

# ---------------------------------------------------------------------------
class EF9345:
    def __init__(self, sim):
        self.sim = sim
        self.r = [0] * 8
        self.blk = [[[0] * 40 for _ in range(32)] for _ in range(16)]
        self.busy_until = 0
        self.vrm = False
        self.tgs, self.mat, self.pat, self.dor, self.ror = 0x10, 0x28, 0x67, 0x13, 0x08
        self.ecritures_busy = 0

    def busy(self):
        return self.sim.cycles < self.busy_until

    def status(self):
        s = 0x80 if self.busy() else 0
        if self.vrm:
            if (self.sim.cycles % 20000) >= 128:
                s |= 0x04
        return s

    def mp(self):
        r6, r7 = self.r[6], self.r[7]
        z = ((r6 >> 6) & 1) * 8 + ((r6 >> 5) & 1) * 4 + ((r7 >> 6) & 1) * 2 + ((r7 >> 7) & 1)
        return z, r6 & 31, r7 & 63

    def ap(self):
        r4, r5 = self.r[4], self.r[5]
        z = ((self.r[6] >> 6) & 1) * 8 + ((r4 >> 5) & 1) * 4 + ((r5 >> 6) & 1) * 2 + ((r5 >> 7) & 1)
        return z, r4 & 31, r5 & 63

    def write(self, a, v):
        reg = a & 7
        exe = a & 8
        if reg != 0 and self.busy():
            self.ecritures_busy += 1
        self.r[reg] = v
        if exe:
            self.execute()

    def read(self, a):
        reg = a & 7
        v = self.status() if reg == 0 else self.r[reg]
        if a & 8:
            self.execute()
        return v

    def execute(self):
        c = self.r[0]
        t = 4
        if c in (0x00, 0x01):                       # KRF écriture
            z, y, x = self.mp()
            if x < 40:
                self.blk[z][y][x] = self.r[1]
                self.blk[(z + 1) & 15][y][x] = self.r[2]
                self.blk[(z + 2) & 15][y][x] = self.r[3]
            if c & 1:
                self.r[7] = (self.r[7] & 0xC0) | ((x + 1) % 40)
        elif c & 0xF8 == 0x30 and not c & 0x08:     # OCT écriture
            if c & 4:
                z, y, x = self.ap()
                if x < 40:
                    self.blk[z][y][x] = self.r[1]
                if c & 1:
                    self.r[5] = (self.r[5] & 0xC0) | ((x + 1) % 40)
            else:
                z, y, x = self.mp()
                if x < 40:
                    self.blk[z][y][x] = self.r[1]
                if c & 1:
                    self.r[7] = (self.r[7] & 0xC0) | ((x + 1) % 40)
        elif 0x80 <= c <= 0x87:                     # IND écriture
            n = c & 7
            v = self.r[1]
            if n == 1: self.tgs = v
            if n == 2: self.mat = v
            if n == 3: self.pat = v
            if n == 4: self.dor = v
            if n == 7: self.ror = v
            t = 2
        elif c == 0x05:                             # CLF
            z, _, _ = self.mp()
            for k, val in enumerate((self.r[1], self.r[2], self.r[3])):
                b = self.blk[(z + k) & 15]
                for y in range(32):
                    b[y] = [val] * 40
            t = 4700
        elif c == 0x91:
            t = 1
        elif c == 0x95:
            self.vrm = True
            t = 1
        elif c == 0x99:
            self.vrm = False
            t = 1
        else:
            self.sim.log("EF9345 : commande non simulée $%02X" % c)
        self.busy_until = self.sim.cycles + t

    def inass(self):
        self.tgs, self.mat, self.pat, self.dor, self.ror = 0x10, 0x28, 0x67, 0x13, 0x08
        for k, val in enumerate((0x20, 0x00, 0x70)):
            for y in range(32):
                self.blk[k][y] = [val] * 40

    # ---- affichage ----
    def image(self, police):
        from PIL import Image
        W, H, M = 320, 250, 16
        img = Image.new('RGB', (W + 2 * M, H + 2 * M))
        pal = [((c & 1) * 255, ((c >> 1) & 1) * 255, ((c >> 2) & 1) * 255) for c in range(8)]
        px = img.load()
        bord = pal[self.mat & 7]
        for yy in range(H + 2 * M):
            for xx in range(W + 2 * M):
                px[xx, yy] = bord
        yor = self.ror & 31
        rangs = [0] + [8 + ((yor - 8 + s) % 24) for s in range(24)]
        dh_haut = [None] * 40
        for s, y in enumerate(rangs):
            if s == 0 and not self.pat & 1:
                continue
            dw_gauche = None
            for x in range(40):
                c, b, a = self.blk[0][y][x], self.blk[1][y][x], self.blk[2][y][x]
                jeu = b >> 4
                fg, bg = (a >> 4) & 7, a & 7
                if a & 0x80:
                    fg, bg = bg, fg
                # doubles
                moitie_d = False
                if b & 0x08:
                    if dw_gauche == c:
                        moitie_d, dw_gauche = True, None
                    else:
                        dw_gauche = c
                else:
                    dw_gauche = None
                bas = False
                if b & 0x02 and s > 0:
                    if dh_haut[x] == c:
                        bas, dh_haut[x] = True, None
                    else:
                        dh_haut[x] = c
                elif s > 0:
                    dh_haut[x] = None
                for ligne in range(10):
                    src_l = ligne
                    if b & 0x02:
                        src_l = (ligne // 2) + (5 if bas else 0)
                    if jeu == 8:
                        z = self.dor & 15
                        tr = self.blk[z][c >> 2][(c & 3) + 4 * src_l]
                    elif jeu == 0:
                        g = police.get(c & 0x7F)
                        tr = 0
                        if g and 1 <= src_l <= 7:
                            tr = g[src_l - 1] << 1
                    else:
                        tr = 0
                    for col in range(8):
                        sc = col
                        if b & 0x08:
                            sc = col // 2 + (4 if moitie_d else 0)
                        on = (tr >> sc) & 1
                        px[M + x * 8 + col, M + s * 10 + ligne] = pal[fg if on else bg]
        return img.resize(((W + 2 * M) * 2, (H + 2 * M) * 2), Image.NEAREST)


# ---------------------------------------------------------------------------
class Sim:
    def __init__(self, binaire, org=ORG):
        self.m = bytearray(65536)
        self.m[org:org + len(binaire)] = binaire
        for i in range(0x3200, 0x3215, 3):
            self.m[i] = 0x3B                         # RTI dans les trampolines
        for v, adr in ((0xFFF0, 0x3200), (0xFFF2, 0x3203), (0xFFF4, 0x3206),
                       (0xFFF6, 0x3209), (0xFFF8, 0x320C), (0xFFFA, 0x320F),
                       (0xFFFC, 0x3212)):
            self.m[v], self.m[v + 1] = adr >> 8, adr & 0xFF
        self.m[0xD42C] = 0x39                        # RTS (INASS simulé)
        self.A = self.B = 0
        self.X = 0
        self.S = 0x4F80
        self.PC = org
        self.CC = 0xD0                               # I = 1
        self.cycles = 0
        self.ef = EF9345(self)
        self.tcsr = 0
        self.ocr = 0xFFFF
        self.lu_tof = self.lu_ocf = False
        self.port1 = 0xFF
        self.touches = set()
        self.son = []                                # instants des écritures du bit 7
        self.dernier_son = 0
        self.journal = []
        self.fini = False
        # retour au « BASIC » : adresse sentinelle
        self.push16(0xFFF0)

    def log(self, t):
        if len(self.journal) < 50:
            self.journal.append(t)

    # ---- mémoire ----
    def rd(self, a):
        a &= 0xFFFF
        if a < 0x20:
            if a == 0x02: return self.port1
            if a == 0x03: return 0xFF
            if a == 0x08:
                self.lu_tof = bool(self.tcsr & 0x20)
                self.lu_ocf = bool(self.tcsr & 0x40)
                return self.tcsr
            if a == 0x09:
                if self.lu_tof:
                    self.tcsr &= ~0x20
                    self.lu_tof = False
                return (self.cycles >> 8) & 0xFF
            if a == 0x0A: return self.cycles & 0xFF
            if a == 0x0B: return self.ocr >> 8
            if a == 0x0C: return self.ocr & 0xFF
            return self.m[a]
        if 0xBF20 <= a <= 0xBF2F:
            return self.ef.read(a)
        if a == 0xBFFF:
            v = 0x7F
            col = [i for i in range(8) if not (self.port1 >> i) & 1]
            for (c, l) in self.touches:
                if c in col:
                    v &= ~(1 << l)
            return v
        return self.m[a]

    def wr(self, a, v):
        a &= 0xFFFF
        v &= 0xFF
        if a < 0x20:
            if a == 0x02: self.port1 = v
            elif a == 0x08: self.tcsr = (self.tcsr & 0xE0) | (v & 0x1F)
            elif a in (0x0B, 0x0C):
                if a == 0x0B: self.ocr = (v << 8) | (self.ocr & 0xFF)
                else: self.ocr = (self.ocr & 0xFF00) | v
                if self.lu_ocf:
                    self.tcsr &= ~0x40
                    self.lu_ocf = False
            self.m[a] = v
            return
        if 0xBF20 <= a <= 0xBF2F:
            self.ef.write(a, v)
            return
        if a == 0xBFFF:
            if (v & 0x80) != self.dernier_son:
                self.son.append(self.cycles)
                self.dernier_son = v & 0x80
            return
        if a >= 0xC000:
            self.log("écriture en ROM $%04X" % a)
            return
        self.m[a] = v

    def rd16(self, a):
        return (self.rd(a) << 8) | self.rd(a + 1)

    def wr16(self, a, v):
        self.wr(a, v >> 8)
        self.wr(a + 1, v)

    def push(self, v):
        self.m[self.S] = v & 0xFF
        self.S = (self.S - 1) & 0xFFFF

    def pull(self):
        self.S = (self.S + 1) & 0xFFFF
        return self.m[self.S]

    def push16(self, v):
        self.push(v)
        self.push(v >> 8)

    def pull16(self):
        h = self.pull()
        return (h << 8) | self.pull()

    def fetch(self):
        v = self.m[self.PC]
        self.PC = (self.PC + 1) & 0xFFFF
        return v

    def fetch16(self):
        h = self.fetch()
        return (h << 8) | self.fetch()

    # ---- drapeaux ----
    def nz8(self, r):
        self.CC = (self.CC & ~0x0C) | (0x08 if r & 0x80 else 0) | (0x04 if r & 0xFF == 0 else 0)

    def nz16(self, r):
        self.CC = (self.CC & ~0x0C) | (0x08 if r & 0x8000 else 0) | (0x04 if r & 0xFFFF == 0 else 0)

    def setf(self, mask, cond):
        if cond:
            self.CC |= mask
        else:
            self.CC &= ~mask

    def add8(self, a, b, c=0):
        r = a + b + c
        self.setf(0x20, ((a & 0xF) + (b & 0xF) + c) > 0xF)
        self.setf(0x01, r > 0xFF)
        self.setf(0x02, (~(a ^ b) & (a ^ r)) & 0x80)
        r &= 0xFF
        self.nz8(r)
        return r

    def sub8(self, a, b, c=0):
        r = a - b - c
        self.setf(0x01, r < 0)
        self.setf(0x02, ((a ^ b) & (a ^ r)) & 0x80)
        r &= 0xFF
        self.nz8(r)
        return r

    @property
    def D(self):
        return (self.A << 8) | self.B

    @D.setter
    def D(self, v):
        self.A, self.B = (v >> 8) & 0xFF, v & 0xFF

    # ---- interruptions et timer ----
    def tick(self, n):
        avant = self.cycles
        self.cycles += n
        if (avant >> 16) != (self.cycles >> 16):
            self.tcsr |= 0x20
        o = self.ocr
        lo, hi = avant & 0xFFFF, self.cycles & 0xFFFF
        if (lo < o <= hi) or (hi < lo and (o > lo or o <= hi)):
            self.tcsr |= 0x40

    def irq(self):
        if self.CC & 0x10:
            return
        vec = None
        if self.tcsr & 0x40 and self.tcsr & 0x08:
            vec = 0xFFF4
        elif self.tcsr & 0x20 and self.tcsr & 0x04:
            vec = 0xFFF2
        if vec is None:
            return
        self.push16(self.PC)
        self.push16(self.X)
        self.push(self.A)
        self.push(self.B)
        self.push(self.CC)
        self.CC |= 0x10
        self.PC = self.rd16(vec)
        self.tick(12)

    # ---- exécution ----
    def ea(self, mode):
        if mode == 'dir':
            return self.fetch()
        if mode == 'ext':
            return self.fetch16()
        if mode == 'idx':
            return (self.X + self.fetch()) & 0xFFFF
        raise ValueError(mode)

    def step(self):
        if self.PC == 0xD42C:
            self.ef.inass()
        if self.PC == 0xFFF0:
            self.fini = True
            return
        pc0 = self.PC
        op = self.fetch()
        cyc = OPS.get(op)
        if cyc is None:
            raise RuntimeError("opcode inconnu $%02X en $%04X" % (op, pc0))
        f, mode, n = cyc
        f(self, mode)
        self.tick(n)
        self.irq()

    def run_until(self, cycles):
        while self.cycles < cycles and not self.fini:
            self.step()


# ---------------------------------------------------------------------------
# Table des instructions : opcode -> (fonction, mode, cycles)
OPS = {}


def op(code, mode, n):
    def deco(f):
        OPS[code] = (f, mode, n)
        return f
    return deco


def operand8(s, mode):
    if mode == 'imm':
        return s.fetch()
    return s.rd(s.ea(mode))


def operand16(s, mode):
    if mode == 'imm':
        return s.fetch16()
    return s.rd16(s.ea(mode))


def branch(s, cond):
    off = s.fetch()
    if off & 0x80:
        off -= 256
    if cond:
        s.PC = (s.PC + off) & 0xFFFF


def C(s): return s.CC & 1
def Z(s): return (s.CC >> 2) & 1
def N(s): return (s.CC >> 3) & 1
def V(s): return (s.CC >> 1) & 1


BR = {0x20: lambda s: True, 0x21: lambda s: False,
      0x22: lambda s: not (C(s) or Z(s)), 0x23: lambda s: bool(C(s) or Z(s)),
      0x24: lambda s: not C(s), 0x25: lambda s: bool(C(s)),
      0x26: lambda s: not Z(s), 0x27: lambda s: bool(Z(s)),
      0x28: lambda s: not V(s), 0x29: lambda s: bool(V(s)),
      0x2A: lambda s: not N(s), 0x2B: lambda s: bool(N(s)),
      0x2C: lambda s: N(s) == V(s), 0x2D: lambda s: N(s) != V(s),
      0x2E: lambda s: not Z(s) and N(s) == V(s), 0x2F: lambda s: bool(Z(s) or N(s) != V(s))}
for code, cond in BR.items():
    OPS[code] = ((lambda cond: lambda s, m: branch(s, cond(s)))(cond), None, 3)


def bsr(s, m):
    off = s.fetch()
    if off & 0x80:
        off -= 256
    s.push16(s.PC)
    s.PC = (s.PC + off) & 0xFFFF
OPS[0x8D] = (bsr, None, 6)


def inh(code, n):
    return lambda f: OPS.__setitem__(code, (f, None, n)) or f


@inh(0x01, 2)
def _nop(s, m): pass
@inh(0x04, 3)
def _lsrd(s, m):
    d = s.D; s.setf(1, d & 1); d >>= 1; s.D = d; s.nz16(d); s.setf(2, C(s))
@inh(0x05, 3)
def _asld(s, m):
    d = s.D; s.setf(1, d & 0x8000); d = (d << 1) & 0xFFFF; s.D = d; s.nz16(d); s.setf(2, N(s) ^ C(s))
@inh(0x06, 2)
def _tap(s, m): s.CC = s.A | 0xC0
@inh(0x07, 2)
def _tpa(s, m): s.A = s.CC | 0xC0
@inh(0x08, 3)
def _inx(s, m): s.X = (s.X + 1) & 0xFFFF; s.setf(4, s.X == 0)
@inh(0x09, 3)
def _dex(s, m): s.X = (s.X - 1) & 0xFFFF; s.setf(4, s.X == 0)
@inh(0x0A, 2)
def _clv(s, m): s.CC &= ~2
@inh(0x0B, 2)
def _sev(s, m): s.CC |= 2
@inh(0x0C, 2)
def _clc(s, m): s.CC &= ~1
@inh(0x0D, 2)
def _sec(s, m): s.CC |= 1
@inh(0x0E, 2)
def _cli(s, m): s.CC &= ~0x10
@inh(0x0F, 2)
def _sei(s, m): s.CC |= 0x10
@inh(0x10, 2)
def _sba(s, m): s.A = s.sub8(s.A, s.B)
@inh(0x11, 2)
def _cba(s, m): s.sub8(s.A, s.B)
@inh(0x16, 2)
def _tab(s, m): s.B = s.A; s.nz8(s.B); s.CC &= ~2
@inh(0x17, 2)
def _tba(s, m): s.A = s.B; s.nz8(s.A); s.CC &= ~2
@inh(0x1B, 2)
def _aba(s, m): s.A = s.add8(s.A, s.B)
@inh(0x30, 3)
def _tsx(s, m): s.X = (s.S + 1) & 0xFFFF
@inh(0x31, 3)
def _ins(s, m): s.S = (s.S + 1) & 0xFFFF
@inh(0x32, 4)
def _pula(s, m): s.A = s.pull()
@inh(0x33, 4)
def _pulb(s, m): s.B = s.pull()
@inh(0x34, 3)
def _des(s, m): s.S = (s.S - 1) & 0xFFFF
@inh(0x35, 3)
def _txs(s, m): s.S = (s.X - 1) & 0xFFFF
@inh(0x36, 3)
def _psha(s, m): s.push(s.A)
@inh(0x37, 3)
def _pshb(s, m): s.push(s.B)
@inh(0x38, 5)
def _pulx(s, m): s.X = s.pull16()
@inh(0x39, 5)
def _rts(s, m): s.PC = s.pull16()
@inh(0x3A, 3)
def _abx(s, m): s.X = (s.X + s.B) & 0xFFFF
@inh(0x3B, 10)
def _rti(s, m):
    s.CC = s.pull() | 0xC0; s.B = s.pull(); s.A = s.pull(); s.X = s.pull16(); s.PC = s.pull16()
@inh(0x3C, 4)
def _pshx(s, m): s.push(s.X & 0xFF); s.push(s.X >> 8)
@inh(0x3D, 10)
def _mul(s, m): s.D = s.A * s.B; s.setf(1, s.B & 0x80)


# opérations sur un octet (accumulateur ou mémoire)
def neg(s, v): r = s.sub8(0, v); return r
def com(s, v): r = (~v) & 0xFF; s.nz8(r); s.CC = (s.CC & ~2) | 1; return r
def lsr(s, v): s.setf(1, v & 1); r = v >> 1; s.nz8(r); s.setf(2, C(s)); return r
def ror(s, v): c = C(s); s.setf(1, v & 1); r = (v >> 1) | (c << 7); s.nz8(r); s.setf(2, N(s) ^ C(s)); return r
def asr(s, v): s.setf(1, v & 1); r = (v >> 1) | (v & 0x80); s.nz8(r); s.setf(2, N(s) ^ C(s)); return r
def asl(s, v): s.setf(1, v & 0x80); r = (v << 1) & 0xFF; s.nz8(r); s.setf(2, N(s) ^ C(s)); return r
def rol(s, v): c = C(s); s.setf(1, v & 0x80); r = ((v << 1) | c) & 0xFF; s.nz8(r); s.setf(2, N(s) ^ C(s)); return r
def dec(s, v): r = (v - 1) & 0xFF; s.setf(2, v == 0x80); s.nz8(r); return r
def inc(s, v): r = (v + 1) & 0xFF; s.setf(2, v == 0x7F); s.nz8(r); return r
def tst(s, v): s.nz8(v); s.CC &= ~3; return None
def clr(s, v): s.CC = (s.CC & ~0x0F) | 0x04; return 0


RMW = {0x0: neg, 0x3: com, 0x4: lsr, 0x6: ror, 0x7: asr, 0x8: asl, 0x9: rol,
       0xA: dec, 0xC: inc, 0xD: tst, 0xF: clr}
for low, f in RMW.items():
    def fa(s, m, f=f):
        r = f(s, s.A)
        if r is not None: s.A = r
    def fb(s, m, f=f):
        r = f(s, s.B)
        if r is not None: s.B = r
    def fm(s, m, f=f):
        a = s.ea(m)
        r = f(s, s.rd(a))
        if r is not None: s.wr(a, r)
    OPS[0x40 + low] = (fa, None, 2)
    OPS[0x50 + low] = (fb, None, 2)
    OPS[0x60 + low] = (fm, 'idx', 6)
    OPS[0x70 + low] = (fm, 'ext', 6)


def jmp(s, m): s.PC = s.ea(m)
OPS[0x6E] = (jmp, 'idx', 3)
OPS[0x7E] = (jmp, 'ext', 3)


def jsr(s, m):
    a = s.ea(m)
    s.push16(s.PC)
    s.PC = a
OPS[0x9D] = (jsr, 'dir', 5)
OPS[0xAD] = (jsr, 'idx', 6)
OPS[0xBD] = (jsr, 'ext', 6)

MODES = [('imm', 0x00, 2), ('dir', 0x10, 3), ('idx', 0x20, 4), ('ext', 0x30, 4)]


def acc_ops(base, reg):
    def get(s): return s.A if reg == 'A' else s.B
    def put(s, v):
        if reg == 'A': s.A = v
        else: s.B = v
    tab = {
        0x0: lambda s, v: put(s, s.sub8(get(s), v)),
        0x1: lambda s, v: s.sub8(get(s), v),
        0x2: lambda s, v: put(s, s.sub8(get(s), v, C(s))),
        0x4: lambda s, v: (put(s, get(s) & v), s.nz8(get(s)), s.setf(2, 0)),
        0x5: lambda s, v: (s.nz8(get(s) & v), s.setf(2, 0)),
        0x6: lambda s, v: (put(s, v), s.nz8(v), s.setf(2, 0)),
        0x8: lambda s, v: (put(s, get(s) ^ v), s.nz8(get(s)), s.setf(2, 0)),
        0x9: lambda s, v: put(s, s.add8(get(s), v, C(s))),
        0xA: lambda s, v: (put(s, get(s) | v), s.nz8(get(s)), s.setf(2, 0)),
        0xB: lambda s, v: put(s, s.add8(get(s), v)),
    }
    for low, f in tab.items():
        for mode, off, n in MODES:
            OPS[base + off + low] = ((lambda f: lambda s, m: f(s, operand8(s, m)))(f), mode, n)
    # STA
    def sta(s, m):
        v = get(s)
        s.wr(s.ea(m), v)
        s.nz8(v); s.setf(2, 0)
    for mode, off, n in MODES[1:]:
        OPS[base + off + 0x7] = (sta, mode, n)


acc_ops(0x80, 'A')
acc_ops(0xC0, 'B')

MODES16 = [('imm', 0x00, 3), ('dir', 0x10, 4), ('idx', 0x20, 5), ('ext', 0x30, 5)]


def subd(s, v, store=True):
    d = s.D
    r = d - v
    s.setf(1, r < 0)
    s.setf(2, ((d ^ v) & (d ^ r)) & 0x8000)
    r &= 0xFFFF
    s.nz16(r)
    if store:
        s.D = r


def addd(s, v):
    d = s.D
    r = d + v
    s.setf(1, r > 0xFFFF)
    s.setf(2, (~(d ^ v) & (d ^ r)) & 0x8000)
    r &= 0xFFFF
    s.nz16(r)
    s.D = r


def cpx(s, v):
    x = s.X
    r = x - v
    s.setf(1, r < 0)
    s.setf(2, ((x ^ v) & (x ^ r)) & 0x8000)
    s.nz16(r & 0xFFFF)


def ld16(attr):
    def f(s, v):
        setattr(s, attr, v)
        s.nz16(v); s.setf(2, 0)
    return f


for base, f, extra in ((0x83, lambda s, v: subd(s, v), 1), (0xC3, addd, 1), (0x8C, cpx, 1),
                       (0xCC, ld16('D'), 0), (0xCE, ld16('X'), 0), (0x8E, ld16('S'), 0)):
    for mode, off, n in MODES16:
        OPS[base + off] = ((lambda f: lambda s, m: f(s, operand16(s, m)))(f), mode, n + extra)


def st16(attr):
    def f(s, m):
        v = getattr(s, attr)
        s.wr16(s.ea(m), v)
        s.nz16(v); s.setf(2, 0)
    return f


for base, attr in ((0xCD, 'D'), (0xCF, 'X'), (0x8F, 'S')):
    for mode, off, n in MODES16[1:]:
        OPS[base + off] = (st16(attr), mode, n)


# ---------------------------------------------------------------------------
def charge_police(chemin):
    """Lit inc/donnees-police.inc pour dessiner le jeu G0 du simulateur."""
    data = []
    with open(chemin, encoding='utf-8') as f:
        for l in f:
            if 'dc.b' in l:
                data += [int(v.strip()[1:], 16) for v in l.split('dc.b')[1].split(',')]
    pol = {}
    for i in range(64):
        g = data[i * 8:i * 8 + 7]
        pol[0x20 + i] = g
        if 0x41 <= 0x20 + i <= 0x5A:
            pol[0x20 + i + 32] = g
    return pol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bin')
    ap.add_argument('--png', default='capture')
    ap.add_argument('--a', default='1', help='instants des captures (s), séparés par des virgules')
    ap.add_argument('--touche', action='append', default=[],
                    help='t:ESPACE ou t:ENTREE (appui de 0,2 s)')
    ap.add_argument('--son', help='fichier WAV du son produit')
    a = ap.parse_args()
    ici = os.path.dirname(os.path.abspath(__file__))
    police = charge_police(os.path.join(ici, '..', 'inc', 'donnees-police.inc'))
    s = Sim(open(a.bin, 'rb').read())
    instants = sorted(float(t) for t in a.a.split(','))
    touches = []
    for t in a.touche:
        tt, nom = t.split(':')
        cl = {'ESPACE': (7, 3), 'ENTREE': (6, 3)}[nom.upper()]
        touches.append((float(tt), float(tt) + 0.2, cl))
    evts = sorted(set(instants + [t for t, _, _ in touches] + [t for _, t, _ in touches]))
    for t in evts:
        s.run_until(int(t * 1e6))
        s.touches = {cl for (t0, t1, cl) in touches if t0 <= t < t1}
        if t in instants:
            nom = '%s-%05.1fs.png' % (a.png, t)
            s.ef.image(police).save(nom)
            print("capture", nom, "PC=$%04X" % s.PC, "ROR=$%02X" % s.ef.ror)
        if s.fini:
            print("retour au BASIC à %.2f s" % (s.cycles / 1e6))
            break
    print("cycles : %d ; écritures pendant BUSY : %d ; inversions du son : %d"
          % (s.cycles, s.ef.ecritures_busy, len(s.son)))
    for j in s.journal:
        print("  !", j)
    if a.son and s.son:
        rate = 22050
        n = int(s.cycles / 1e6 * rate)
        buf = bytearray([128 - 40] * n)
        niveau, k = 0, 0
        ev = s.son + [s.cycles]
        for i in range(n):
            t = i * 1e6 / rate
            while k < len(s.son) and s.son[k] <= t:
                niveau ^= 1
                k += 1
            buf[i] = 128 + (40 if niveau else -40)
        with open(a.son, 'wb') as f:
            f.write(b'RIFF' + struct.pack('<I', 36 + n) + b'WAVEfmt ' +
                    struct.pack('<IHHIIHH', 16, 1, 1, rate, rate, 1, 8) +
                    b'data' + struct.pack('<I', n) + bytes(buf))
        print("son :", a.son)


if __name__ == '__main__':
    main()
