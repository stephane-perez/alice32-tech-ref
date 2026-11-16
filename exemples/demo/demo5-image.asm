; =====================================================================
;  DÉMO 5 : afficher une image convertie (HIRES 160 x 125, duochrome)
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM :
;      python3 outils/img2hires.py mon_image.png -o inc/donnees-image.inc
;      dasm demo5-image.asm -f3 -obuild/demo5-image.bin
;  CLOADM puis EXEC 13312. ENTRÉE = BASIC.
;  NON testé sur machine réelle.
; =====================================================================
        PROCESSOR 6803

AVEC_MUSIQUE EQU 0
SANS_PALETTE EQU 1
V_FINRAM EQU FINPROG

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        ldx  #IMAGE
        jsr  AFF_IMAGE
ATTENTE jsr  VSYNC
        jsr  CONTROLE        ; ENTRÉE : retour au BASIC
        bra  ATTENTE

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/image.inc"
        INCLUDE "inc/donnees-image.inc"
        INCLUDE "inc/fin.inc"
