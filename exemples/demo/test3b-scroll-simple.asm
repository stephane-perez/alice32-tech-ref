; =====================================================================
;  TEST 3 : scrolltext horizontal au point près, taille normale (40 tuiles), si le double ne marche pas
;  Exemple ORIGINAL du dépôt alice32-tech-ref (DASM : dasm test3b-scroll-simple.asm -f3 -obuild/test3b-scroll-simple.bin)
;  CLOADM puis EXEC 13312. ESPACE = recommencer, ENTRÉE = BASIC.
;  À observer : texte qui avance de façon régulière, couleurs qui tournent,
;  deux barres de dégradé, logo fixe en haut.
; =====================================================================
        PROCESSOR 6803
AVEC_MUSIQUE EQU 0
S_DBL   EQU 0
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
