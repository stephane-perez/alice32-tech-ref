; =====================================================================
;  TEST 1 : logo « ALICE 32 » en tuiles, défilement vertical fluide (YOR)
;  Exemple ORIGINAL du dépôt alice32-tech-ref (DASM : dasm test1-logo.asm -f3 -obuild/test1-logo.bin)
;  CLOADM puis EXEC 13312. ESPACE = recommencer, ENTRÉE = BASIC.
;  À observer : le logo monte du bas jusqu'au milieu (pause), sort en haut,
;  revient du haut au milieu (pause) et sort en bas, point par point.
; =====================================================================
        PROCESSOR 6803
AVEC_MUSIQUE EQU 0

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        jsr  PARTIE1
        bra  PRINCIPAL

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/partie-logo.inc"
        INCLUDE "inc/donnees-logo.inc"
        INCLUDE "inc/fin.inc"
