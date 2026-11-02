; =====================================================================
;  TEST 4 : musique sous interruptions (OCF + TOF), programme non bloqué
;  Exemple ORIGINAL du dépôt alice32-tech-ref (DASM : dasm test4-musique.asm -f3 -obuild/test4-musique.bin)
;  CLOADM puis EXEC 13312. ENTRÉE = BASIC.
;  À observer : la mélodie (~17 s, en boucle) ; la couleur de la marge
;  change à chaque note ; les deux barres de dégradé continuent de
;  défiler pendant que la musique joue.
; =====================================================================
        PROCESSOR 6803
AVEC_MUSIQUE EQU 1

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        clra
        jsr  EFFACE
        ldaa #8
        jsr  ECRROR
        clr  TXY
        ldx  #TITRE4
        ldaa #$70
        clrb
        jsr  TEXTE
        ldaa #12
        staa TXY
        ldx  #LIGNE4A
        ldaa #$70
        ldab #3
        jsr  TEXTE
        ldaa #14
        staa TXY
        ldx  #LIGNE4B
        ldaa #$60
        ldab #3
        jsr  TEXTE
M4      jsr  VSYNC
        ldaa NOTEACT         ; couleur de marge = note & 7
        anda #7
        oraa #$28            ; valeur de MAT de la ROM, marge colorée
        ldab #IND_MAT
        jsr  ECRIND
        inc  M4PH
        ldaa M4PH
        staa BV
        ldaa #5
        staa BDV
        ldaa #20
        jsr  BARRE
        ldaa M4PH
        nega
        staa BV
        ldaa #20+2
        jsr  BARRE
        jsr  CONTROLE        ; ENTRÉE quitte ; ESPACE ignoré
        bra  M4

TITRE4  dc.b " ALICE 32 - TEST MUSIQUE (OCF + TOF)",0
LIGNE4A dc.b "LA MELODIE JOUE SOUS INTERRUPTIONS",0
LIGNE4B dc.b "ET LES BARRES CONTINUENT A DEFILER",0
M4PH    dc.b 0

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/musique.inc"
        INCLUDE "inc/donnees-musique.inc"
        INCLUDE "inc/fin.inc"
