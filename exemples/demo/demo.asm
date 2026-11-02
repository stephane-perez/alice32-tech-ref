; =====================================================================
;  DÉMO ALICE 32 : logo YOR + plasma/dégradés + scrolltext + musique
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM :
;      dasm demo.asm -f3 -obuild/demo.bin -lbuild/demo.lst
;  (ou : python3 outils/asm6803.py demo.asm -o build/demo.bin)
;  NON testé sur machine réelle : voir README.md.
;
;  Chargement : CLOADM puis EXEC 13312 ($3400). Sans extension mémoire.
;  Touches : ESPACE = partie suivante, ENTRÉE = retour au BASIC.
; =====================================================================
        PROCESSOR 6803

AVEC_MUSIQUE EQU 1           ; mélodie sous interruptions pendant toute la démo
S_DBL   EQU 1                ; scrolltext en double hauteur/largeur
VITESSE EQU 2                ; points par image du scrolltext

        ORG $3400
DEBUT   jmp  DEMARRE         ; commun.inc : init puis PRINCIPAL

PRINCIPAL
        jsr  PARTIE1         ; logo « ALICE 32 » qui monte puis redescend
        jsr  PARTIE2         ; dégradé puis plasma
        jsr  PARTIE3         ; scrolltext (une fois le texte entier)
        bra  PRINCIPAL

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/musique.inc"
        INCLUDE "inc/partie-logo.inc"
        INCLUDE "inc/partie-plasma.inc"
        INCLUDE "inc/partie-scroll.inc"
        INCLUDE "inc/donnees-logo.inc"
        INCLUDE "inc/donnees-police.inc"
        INCLUDE "inc/donnees-texte.inc"
        INCLUDE "inc/donnees-musique.inc"
        INCLUDE "inc/fin.inc"
