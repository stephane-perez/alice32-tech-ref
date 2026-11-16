; =====================================================================
;  TEST 3 : scrolltext horizontal au point près, double hauteur et double largeur
;  Exemple ORIGINAL du dépôt alice32-tech-ref (DASM : dasm test3-scroll.asm -f3 -obuild/test3-scroll.bin)
;  CLOADM puis EXEC 13312. ESPACE = recommencer, ENTRÉE = BASIC.
;  À observer : texte qui avance de façon régulière, couleurs qui tournent,
;  deux barres de dégradé, logo fixe en haut.
; =====================================================================
        PROCESSOR 6803
AVEC_MUSIQUE EQU 0
S_DBL   EQU 1
VITESSE EQU 2

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        jsr  PARTIE3
        bra  PRINCIPAL

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/partie-logo.inc"
        INCLUDE "inc/partie-scroll.inc"
        INCLUDE "inc/donnees-logo.inc"
        INCLUDE "inc/donnees-police.inc"
        INCLUDE "inc/donnees-texte.inc"
        INCLUDE "inc/fin.inc"
