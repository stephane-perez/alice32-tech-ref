; =====================================================================
;  DÉMO 3 : 3D fil de fer (cube, vaisseau) en mode HIRES 160 x 125
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM :
;      dasm demo3-vectoriel.asm -f3 -obuild/demo3-vectoriel.bin
;  CLOADM puis EXEC 13312. ESPACE = objet suivant, ENTRÉE = BASIC.
;  NON testé sur machine réelle : voir README.md.
; =====================================================================
        PROCESSOR 6803

AVEC_MUSIQUE EQU 0
SANS_PALETTE EQU 1           ; pas de palette 40 colonnes : RAM pour la copie d'écran

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        jsr  PARTIE5         ; ne revient pas (ENTRÉE passe par QUITTE)
        bra  PRINCIPAL

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/vecteur.inc"
        INCLUDE "inc/donnees-persp.inc"
        INCLUDE "inc/fin.inc"
