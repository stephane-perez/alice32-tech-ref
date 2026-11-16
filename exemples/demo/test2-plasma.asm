; =====================================================================
;  TEST 2 : dégradé diagonal (4 s) puis plasma plein écran (12 s)
;  Exemple ORIGINAL du dépôt alice32-tech-ref (DASM : dasm test2-plasma.asm -f3 -obuild/test2-plasma.bin)
;  CLOADM puis EXEC 13312. ESPACE = recommencer, ENTRÉE = BASIC.
;  À observer : 64 teintes obtenues par trames 0/25/50/75 % et deux
;  couleurs par case ; environ 20 images/s pour le plasma.
; =====================================================================
        PROCESSOR 6803
AVEC_MUSIQUE EQU 0

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        jsr  PARTIE2
        bra  PRINCIPAL

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/partie-plasma.inc"
        INCLUDE "inc/fin.inc"
