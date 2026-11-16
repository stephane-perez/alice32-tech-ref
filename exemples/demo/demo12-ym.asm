; =====================================================================
;  DÉMO 12 : musique YM (Atari ST / YM2149) convertie et jouée en 1 bit
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM :
;      python3 outils/ym2alice.py musique.ym -o inc/donnees-ym.inc
;      dasm demo12-ym.asm -f3 -obuild/demo12-ym.bin
;  CLOADM puis EXEC 13312. ESPACE = reprendre au début, ENTRÉE = BASIC.
;  NON testé sur machine réelle.
; =====================================================================
        PROCESSOR 6803

AVEC_MUSIQUE EQU 0
SANS_PALETTE EQU 1
SANS_SINUS EQU 1               ; pas de table de sinus : place pour la musique
V_FINRAM EQU FINPROG

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        ldaa #$70
        jsr  EFFACE
        clr  TXY
        ldx  #T12_1
        ldaa #$70
        clrb
        jsr  TEXTE
        ldaa #12
        staa TXY
        ldx  #YM_TITRE
        ldaa #$30            ; titre en jaune
        ldab #1
        jsr  TEXTE
        ldaa #14
        staa TXY
        ldx  #YM_AUTEUR
        ldaa #$60            ; auteur en cyan
        ldab #1
        jsr  TEXTE
        ldaa #30
        staa TXY
        ldx  #T12_2
        ldaa #$70
        ldab #4
        jsr  TEXTE
P12     jsr  YM_JOUE
        cmpa #2
        bne  P12             ; ESPACE : on reprend au début
        jmp  QUITTE

T12_1   dc.b " ALICE 32 - MUSIQUE YM (3 VOIX + BRUIT)",0
T12_2   dc.b "ESPACE : REPRENDRE  ENTREE : BASIC",0

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/ymplay.inc"
        INCLUDE "inc/donnees-ym.inc"
        INCLUDE "inc/fin.inc"
