; =====================================================================
;  DÉMO 7 : musique à 3 voix sur le haut-parleur 1 bit (processeur à 100 %)
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM :
;      dasm demo7-trois-voix.asm -f3 -obuild/demo7-trois-voix.bin
;  CLOADM puis EXEC 13312. ESPACE = recommencer, ENTRÉE = BASIC.
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
        ldx  #T7_1
        ldaa #$70
        clrb
        jsr  TEXTE
        ldaa #12
        staa TXY
        ldx  #T7_2
        ldaa #$60
        ldab #2
        jsr  TEXTE
        ldaa #14
        staa TXY
        ldx  #T7_3
        ldaa #$30
        ldab #2
        jsr  TEXTE
P7      jsr  JOUE3
        cmpa #2
        bne  P7              ; fin du morceau ou ESPACE : on recommence
        jmp  QUITTE

T7_1    dc.b " ALICE 32 - MUSIQUE A 3 VOIX (1 BIT)",0
T7_2    dc.b "MELODIE + BASSE + ARPEGE, MELANGE PAR OU",0
T7_3    dc.b "ESPACE : REPRENDRE  ENTREE : BASIC",0

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/beeper3.inc"
        INCLUDE "inc/donnees-musique3.inc"
        INCLUDE "inc/fin.inc"
