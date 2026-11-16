#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini-assembleur 6803 compatible avec le sous-ensemble de la syntaxe DASM
employé par les sources de ce dossier (exemple ORIGINAL du dépôt).

Il existe parce que DASM n'est pas toujours disponible : les sources
restent écrites pour DASM (`dasm prog.asm -f3 -oprog.bin`) et doivent
donner le même binaire.

Gère : PROCESSOR, ORG, EQU, SET, '=', DC.B / DC.W / DC / BYTE / WORD,
DS.B / DS, ALIGN, INCLUDE, REPEAT / REPEND, IF / IFCONST / ELSE / ENDIF, ECHO, ERR,
le compteur courant '.', les nombres $hex, %bin, décimal, 'c',
les opérateurs + - * / & | ^ << >> ~ et les parenthèses ( ) ou [ ].

Usage : asm6803.py source.asm -o sortie.bin [-l listing.lst] [-s symboles.sym]
"""
import os
import re
import sys

# ---------------------------------------------------------------------------
# Table des instructions du 6801/6803
# modes : inh, rel, imm, imm16, dir, idx, ext
# ---------------------------------------------------------------------------
INH = {
    'NOP': 0x01, 'LSRD': 0x04, 'ASLD': 0x05, 'LSLD': 0x05, 'TAP': 0x06, 'TPA': 0x07,
    'INX': 0x08, 'DEX': 0x09, 'CLV': 0x0A, 'SEV': 0x0B, 'CLC': 0x0C, 'SEC': 0x0D,
    'CLI': 0x0E, 'SEI': 0x0F, 'SBA': 0x10, 'CBA': 0x11, 'TAB': 0x16, 'TBA': 0x17,
    'DAA': 0x19, 'ABA': 0x1B, 'TSX': 0x30, 'INS': 0x31, 'PULA': 0x32, 'PULB': 0x33,
    'DES': 0x34, 'TXS': 0x35, 'PSHA': 0x36, 'PSHB': 0x37, 'PULX': 0x38, 'RTS': 0x39,
    'ABX': 0x3A, 'RTI': 0x3B, 'PSHX': 0x3C, 'MUL': 0x3D, 'WAI': 0x3E, 'SWI': 0x3F,
    'NEGA': 0x40, 'COMA': 0x43, 'LSRA': 0x44, 'RORA': 0x46, 'ASRA': 0x47,
    'ASLA': 0x48, 'LSLA': 0x48, 'ROLA': 0x49, 'DECA': 0x4A, 'INCA': 0x4C,
    'TSTA': 0x4D, 'CLRA': 0x4F,
    'NEGB': 0x50, 'COMB': 0x53, 'LSRB': 0x54, 'RORB': 0x56, 'ASRB': 0x57,
    'ASLB': 0x58, 'LSLB': 0x58, 'ROLB': 0x59, 'DECB': 0x5A, 'INCB': 0x5C,
    'TSTB': 0x5D, 'CLRB': 0x5F,
}
REL = {
    'BRA': 0x20, 'BRN': 0x21, 'BHI': 0x22, 'BLS': 0x23, 'BCC': 0x24, 'BHS': 0x24,
    'BCS': 0x25, 'BLO': 0x25, 'BNE': 0x26, 'BEQ': 0x27, 'BVC': 0x28, 'BVS': 0x29,
    'BPL': 0x2A, 'BMI': 0x2B, 'BGE': 0x2C, 'BLT': 0x2D, 'BGT': 0x2E, 'BLE': 0x2F,
    'BSR': 0x8D,
}
# lecture-modification-écriture : pas de mode direct sur le 6801
RMW = {'NEG': 0x60, 'COM': 0x63, 'LSR': 0x64, 'ROR': 0x66, 'ASR': 0x67,
       'ASL': 0x68, 'LSL': 0x68, 'ROL': 0x69, 'DEC': 0x6A, 'INC': 0x6C,
       'TST': 0x6D, 'JMP': 0x6E, 'CLR': 0x6F}
# groupes A et B : base = code du mode immédiat ; dir +$10, idx +$20, ext +$30
ACC8 = {'SUBA': 0x80, 'CMPA': 0x81, 'SBCA': 0x82, 'ANDA': 0x84, 'BITA': 0x85,
        'LDAA': 0x86, 'EORA': 0x88, 'ADCA': 0x89, 'ORAA': 0x8A, 'ADDA': 0x8B,
        'SUBB': 0xC0, 'CMPB': 0xC1, 'SBCB': 0xC2, 'ANDB': 0xC4, 'BITB': 0xC5,
        'LDAB': 0xC6, 'EORB': 0xC8, 'ADCB': 0xC9, 'ORAB': 0xCA, 'ADDB': 0xCB}
ACC16 = {'SUBD': 0x83, 'CPX': 0x8C, 'LDS': 0x8E, 'ADDD': 0xC3, 'LDD': 0xCC,
         'LDX': 0xCE}
STORE = {'STAA': 0x87, 'STAB': 0xC7, 'STS': 0x8F, 'STD': 0xCD, 'STX': 0xCF,
         'JSR': 0x8D}
ALIAS = {'LDA': 'LDAA', 'LDB': 'LDAB', 'STA': 'STAA', 'STB': 'STAB',
         'ORA': 'ORAA', 'ORB': 'ORAB'}


class AsmError(Exception):
    pass


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------
TOKEN_RE = re.compile(r"""\s*(
      \$[0-9A-Fa-f]+ | %[01]+ | \d+ | '.' |
      <<|>>|<=|>=|==|!=|<|> | [-+*/&|^~()\[\]] | \. | [A-Za-z_][A-Za-z0-9_.]* )""", re.X)


class Expr:
    def __init__(self, asm, text):
        self.asm = asm
        self.toks = []
        pos = 0
        text = text.strip()
        while pos < len(text):
            m = TOKEN_RE.match(text, pos)
            if not m:
                raise AsmError("expression illisible : %r" % text)
            self.toks.append(m.group(1))
            pos = m.end()
            while pos < len(text) and text[pos].isspace():
                pos += 1
        self.i = 0
        self.unknown = False

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def take(self):
        t = self.peek()
        self.i += 1
        return t

    def parse(self):
        v = self.p_or()
        if self.peek() is not None:
            raise AsmError("reste inattendu dans l'expression : %r" % self.toks[self.i:])
        return v

    def binop(self, sub, ops):
        v = sub()
        while self.peek() in ops:
            op = self.take()
            w = sub()
            v = ops[op](v, w)
        return v

    def p_or(self):
        return self.binop(self.p_cmp, {'|': lambda a, b: a | b})

    def p_cmp(self):
        return self.binop(self.p_xor, {
            '<': lambda a, b: int(a < b), '>': lambda a, b: int(a > b),
            '<=': lambda a, b: int(a <= b), '>=': lambda a, b: int(a >= b),
            '==': lambda a, b: int(a == b), '!=': lambda a, b: int(a != b)})

    def p_xor(self):
        return self.binop(self.p_and, {'^': lambda a, b: a ^ b})

    def p_and(self):
        return self.binop(self.p_shift, {'&': lambda a, b: a & b})

    def p_shift(self):
        return self.binop(self.p_add, {'<<': lambda a, b: a << b,
                                       '>>': lambda a, b: a >> b})

    def p_add(self):
        return self.binop(self.p_mul, {'+': lambda a, b: a + b,
                                       '-': lambda a, b: a - b})

    def p_mul(self):
        return self.binop(self.p_unary, {'*': lambda a, b: a * b,
                                         '/': lambda a, b: a // b if b else 0})

    def p_unary(self):
        t = self.peek()
        if t == '-':
            self.take()
            return -self.p_unary()
        if t == '~':
            self.take()
            return ~self.p_unary()
        if t == '+':
            self.take()
            return self.p_unary()
        return self.p_atom()

    def p_atom(self):
        t = self.take()
        if t is None:
            raise AsmError("expression incomplète")
        if t in '([':
            v = self.p_or()
            f = self.take()
            if f not in (')', ']'):
                raise AsmError("parenthèse manquante")
            return v
        if t.startswith('$'):
            return int(t[1:], 16)
        if t.startswith('%'):
            return int(t[1:], 2)
        if t[0].isdigit():
            return int(t)
        if t.startswith("'"):
            return ord(t[1])
        if t == '.':
            return self.asm.pc
        name = t.upper()
        if name in self.asm.symbols:
            return self.asm.symbols[name]
        self.unknown = True
        if self.asm.final:
            raise AsmError("symbole inconnu : %s" % t)
        return 0


# ---------------------------------------------------------------------------
# Assembleur
# ---------------------------------------------------------------------------
class Assembler:
    def __init__(self):
        self.symbols = {}
        self.setsyms = set()
        self.final = False

    def ev(self, text):
        e = Expr(self, text)
        v = e.parse()
        return v, e.unknown

    def load(self, path):
        lines = []
        with open(path, encoding='utf-8') as f:
            for n, l in enumerate(f, 1):
                lines.append((path, n, l.rstrip('\n')))
        return lines

    def split(self, line):
        # retire le commentaire (hors chaînes et caractères)
        out, q = [], None
        i = 0
        while i < len(line):
            c = line[i]
            if q:
                out.append(c)
                if c == q:
                    q = None
            elif c == '"':
                q = c
                out.append(c)
            elif c == "'" and i + 2 < len(line) and line[i + 2] == "'":
                out.append(line[i:i + 3])
                i += 2
            elif c == ';':
                break
            else:
                out.append(c)
            i += 1
        line = ''.join(out).rstrip()
        if not line.strip():
            return None, None, None
        label = None
        if not line[0].isspace():
            parts = line.split(None, 1)
            label = parts[0].rstrip(':')
            rest = parts[1] if len(parts) > 1 else ''
        else:
            rest = line.strip()
        if not rest:
            return label, None, None
        parts = rest.split(None, 1)
        op = parts[0].upper()
        arg = parts[1].strip() if len(parts) > 1 else ''
        return label, op, arg

    def define(self, name, value, is_set=False):
        name = name.upper()
        if is_set:
            self.setsyms.add(name)
        elif name in self.defined_this_pass:
            raise AsmError("étiquette définie deux fois : %s" % name)
        else:
            self.defined_this_pass.add(name)
        old = self.symbols.get(name)
        if old is not None and old != value and name not in self.setsyms:
            self.changed = True
        self.symbols[name] = value

    def emit(self, data):
        for b in data:
            if self.pc in self.mem and self.final and self.mem[self.pc] != (b & 0xFF):
                raise AsmError("chevauchement à $%04X" % self.pc)
            self.mem[self.pc] = b & 0xFF
            self.pc += 1

    def split_args(self, arg):
        res, cur, q = [], '', None
        for c in arg:
            if q:
                cur += c
                if c == q:
                    q = None
            elif c == '"':
                q = c
                cur += c
            elif c == ',':
                res.append(cur)
                cur = ''
            else:
                cur += c
        res.append(cur)
        return [r.strip() for r in res]

    def run_lines(self, lines):
        i = 0
        while i < len(lines):
            path, n, text = lines[i]
            try:
                i = self.do_line(lines, i, path, n, text)
            except AsmError as e:
                raise AsmError("%s:%d: %s\n    %s" % (path, n, e, text.strip()))

    def collect_block(self, lines, i, start, end):
        depth, j, body = 1, i + 1, []
        while j < len(lines):
            _, op, _ = self.split(lines[j][2])
            if op in start:
                depth += 1
            elif op in end:
                depth -= 1
                if depth == 0:
                    return body, j
            body.append(lines[j])
            j += 1
        raise AsmError("bloc non fermé")

    def do_line(self, lines, i, path, n, text):
        label, op, arg = self.split(text)
        if op is None:
            if label:
                self.define(label, self.pc)
                self.listing.append((self.pc, b'', text))
            return i + 1
        if op in ('EQU', '=', 'SET'):
            v, _ = self.ev(arg)
            self.define(label, v, op == 'SET')
            self.listing.append((None, b'', text))
            return i + 1
        if op in ('IF', 'IFCONST', 'IFNCONST'):
            if op == 'IF':
                v, unk = self.ev(arg)
            else:
                v = (arg.strip().upper() in self.symbols) == (op == 'IFCONST')
            body, j = self.collect_block(lines, i, ('IF', 'IFCONST', 'IFNCONST'),
                                         ('ENDIF', 'EIF'))
            # séparer la branche ELSE de même niveau
            depth, k = 0, 0
            yes, no, cur = [], [], None
            cur = yes
            for l in body:
                _, o, _ = self.split(l[2])
                if o in ('IF', 'IFCONST', 'IFNCONST'):
                    depth += 1
                elif o in ('ENDIF', 'EIF'):
                    depth -= 1
                elif o == 'ELSE' and depth == 0:
                    cur = no
                    continue
                cur.append(l)
            self.run_lines(yes if v else no)
            return j + 1
        if op == 'REPEAT':
            v, _ = self.ev(arg)
            body, j = self.collect_block(lines, i, ('REPEAT',), ('REPEND',))
            for _ in range(v):
                self.run_lines(body)
            return j + 1
        if label:
            self.define(label, self.pc)
        start = self.pc
        before = len(self.mem)
        if op == 'PROCESSOR':
            pass
        elif op == 'ORG':
            v, _ = self.ev(arg)
            self.pc = v
            if self.origin is None:
                self.origin = v
            start = v
        elif op == 'INCLUDE':
            fn = arg.strip().strip('"')
            # comme DASM : relatif au répertoire courant (ici celui du source principal)
            full = os.path.join(self.basedir, fn)
            self.run_lines(self.load(full))
            return i + 1
        elif op in ('DC.B', 'DC', 'BYTE', 'DC.W', 'WORD'):
            word = op in ('DC.W', 'WORD')
            data = []
            for a in self.split_args(arg):
                if a.startswith('"'):
                    data.extend(ord(c) for c in a[1:-1])
                else:
                    v, _ = self.ev(a)
                    if word:
                        data.extend([(v >> 8) & 0xFF, v & 0xFF])
                    else:
                        if self.final and not -128 <= v <= 255:
                            raise AsmError("valeur hors octet : %d" % v)
                        data.append(v & 0xFF)
            self.emit(data)
        elif op in ('DS.B', 'DS'):
            a = self.split_args(arg)
            v, _ = self.ev(a[0])
            fill = self.ev(a[1])[0] if len(a) > 1 else 0
            self.emit([fill] * v)
        elif op == 'ALIGN':
            v, _ = self.ev(arg)
            while self.pc % v:
                self.emit([0])
        elif op == 'ECHO':
            if self.final:
                out = []
                for a in self.split_args(arg):
                    if a.startswith('"'):
                        out.append(a[1:-1])
                    else:
                        out.append('$%04X' % (self.ev(a)[0] & 0xFFFF))
                print(' '.join(out))
        elif op == 'ERR':
            if self.final:
                raise AsmError("directive ERR atteinte")
        else:
            self.emit(self.instr(op, arg))
        data = bytes(self.mem[a] for a in range(start, self.pc)) if self.pc > start else b''
        self.listing.append((start, data, text))
        return i + 1

    def instr(self, op, arg):
        op = ALIAS.get(op, op)
        if op in INH:
            if arg:
                raise AsmError("opérande inattendu")
            return [INH[op]]
        if op in REL:
            v, unk = self.ev(arg)
            off = v - (self.pc + 2)
            if self.final and not -128 <= off <= 127:
                raise AsmError("branchement hors de portée (%d)" % off)
            return [REL[op], off & 0xFF]
        # opérande
        a = arg.strip()
        idx = None
        m = re.match(r'^(.*),\s*[xX]$', a)
        if m:
            idx = m.group(1).strip() or '0'
        if op in RMW:
            base = RMW[op]
            if a.startswith('#'):
                raise AsmError("mode immédiat impossible")
            if idx is not None:
                v, _ = self.ev(idx)
                self.chk8(v)
                return [base, v & 0xFF]
            v, _ = self.ev(a)
            return [base + 0x10, (v >> 8) & 0xFF, v & 0xFF]
        if op in ACC8 or op in ACC16 or op in STORE:
            if op in ACC8:
                base, imm16, store = ACC8[op], False, False
            elif op in ACC16:
                base, imm16, store = ACC16[op], True, False
            else:
                base, imm16, store = STORE[op], False, True
            if a.startswith('#'):
                if store:
                    raise AsmError("mode immédiat impossible")
                v, _ = self.ev(a[1:])
                if imm16:
                    return [base, (v >> 8) & 0xFF, v & 0xFF]
                if self.final and not -128 <= v <= 255:
                    raise AsmError("immédiat hors octet : %d" % v)
                return [base, v & 0xFF]
            if idx is not None:
                v, _ = self.ev(idx)
                self.chk8(v)
                return [base + 0x20, v & 0xFF]
            force_ext = a.startswith('>')
            force_dir = a.startswith('<')
            if force_ext or force_dir:
                a = a[1:]
            v, unk = self.ev(a)
            if force_dir or (not force_ext and not unk and 0 <= v < 0x100):
                return [base + 0x10, v & 0xFF]
            return [base + 0x30, (v >> 8) & 0xFF, v & 0xFF]
        raise AsmError("instruction inconnue : %s" % op)

    def chk8(self, v):
        if self.final and not 0 <= v <= 255:
            raise AsmError("décalage indexé hors de 0..255 : %d" % v)

    def assemble(self, path):
        self.basedir = os.path.dirname(os.path.abspath(path))
        lines = self.load(path)
        for passe in range(12):
            self.final = False
            self.changed = False
            self.pass_once(lines)
            if not self.changed and passe > 0:
                break
        self.final = True
        self.pass_once(lines)

    def pass_once(self, lines):
        self.pc = 0
        self.origin = None
        self.mem = {}
        self.listing = []
        self.setsyms = set()
        self.defined_this_pass = set()
        self.run_lines(lines)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('source')
    ap.add_argument('-o', '--out', required=True)
    ap.add_argument('-l', '--lst')
    ap.add_argument('-s', '--sym')
    a = ap.parse_args()
    asm = Assembler()
    try:
        asm.assemble(a.source)
    except AsmError as e:
        print("ERREUR :", e, file=sys.stderr)
        sys.exit(1)
    lo, hi = min(asm.mem), max(asm.mem)
    data = bytes(asm.mem.get(x, 0) for x in range(lo, hi + 1))
    with open(a.out, 'wb') as f:
        f.write(data)
    print("%s : $%04X-$%04X (%d octets)" % (a.out, lo, hi, len(data)))
    if a.lst:
        with open(a.lst, 'w', encoding='utf-8') as f:
            for adr, d, t in asm.listing:
                hexs = ' '.join('%02X' % b for b in d[:6])
                f.write('%-5s %-18s %s\n' % ('%04X' % adr if adr is not None else '', hexs, t))
    if a.sym:
        with open(a.sym, 'w', encoding='utf-8') as f:
            for k, v in sorted(asm.symbols.items(), key=lambda kv: kv[1]):
                f.write('%-16s $%04X\n' % (k, v & 0xFFFF))


if __name__ == '__main__':
    main()
