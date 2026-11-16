; =====================================================================
;  DÉMO 4 : fenêtre en VRAI bitmap 160 x 150 en 40 colonnes
;  (cube et vaisseau en fil de fer, courbe de Lissajous)
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM :
;      dasm demo4-bitmap.asm -f3 -obuild/demo4-bitmap.bin
;  CLOADM puis EXEC 13312. ESPACE = figure suivante, ENTRÉE = BASIC.
;  À comparer avec demo3-vectoriel (mode HIRES 160 x 125, tout l'écran).
;  NON testé sur machine réelle.
; =====================================================================
        PROCESSOR 6803

AVEC_MUSIQUE EQU 0
SANS_PALETTE EQU 1
CL_SEUIL EQU 1               ; ~10 images/s : anti-rebond court

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        jsr  PARTIE6
        bra  PRINCIPAL

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/bitmap.inc"
        INCLUDE "inc/donnees-persp.inc"
        INCLUDE "inc/fin.inc"
