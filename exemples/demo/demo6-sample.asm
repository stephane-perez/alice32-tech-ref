; =====================================================================
;  DÉMO 6 : son échantillonné sur le haut-parleur 1 bit (sigma-delta)
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM :
;      python3 outils/wav2sample.py mon_son.wav -o inc/donnees-sample.inc
;      dasm demo6-sample.asm -f3 -obuild/demo6-sample.bin
;  CLOADM puis EXEC 13312. ESPACE = rejouer, ENTRÉE = BASIC.
;  NON testé sur machine réelle.
; =====================================================================
        PROCESSOR 6803

AVEC_MUSIQUE EQU 0
SANS_PALETTE EQU 1
V_FINRAM EQU FINPROG

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        ldaa #$70
        jsr  EFFACE
        clr  TXY
        ldx  #S6_T1
        ldaa #$70
        clrb
        jsr  TEXTE
        ldaa #14
        staa TXY
        ldx  #S6_T2
        ldaa #$60
        ldab #4
        jsr  TEXTE
S6J     jsr  JOUE_SAMPLE
S6A     jsr  VSYNC
        jsr  CONTROLE        ; ENTRÉE : BASIC
        bne  S6J             ; ESPACE : rejouer
        bra  S6A

S6_T1   dc.b " ALICE 32 - SON ECHANTILLONNE 1 BIT",0
S6_T2   dc.b "ESPACE : REJOUER  ENTREE : BASIC",0

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/sample.inc"
        INCLUDE "inc/donnees-sample.inc"
        INCLUDE "inc/fin.inc"
