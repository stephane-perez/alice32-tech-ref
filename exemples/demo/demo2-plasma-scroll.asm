; =====================================================================
;  DÉMO 2 : plasma plein écran + scrolltext par-dessus + musique
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM :
;      dasm demo2-plasma-scroll.asm -f3 -obuild/demo2-plasma-scroll.bin
;  CLOADM puis EXEC 13312. ESPACE = recommencer, ENTRÉE = BASIC.
;  NON testé sur machine réelle : voir README.md.
; =====================================================================
        PROCESSOR 6803

AVEC_MUSIQUE EQU 1
S_DBL   EQU 1                ; texte en double hauteur/largeur
VITESSE EQU 2

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        jsr  PARTIE4
        bra  PRINCIPAL

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/musique.inc"
        INCLUDE "inc/partie-plasma.inc"
        INCLUDE "inc/partie-scroll.inc"
        INCLUDE "inc/partie-combo.inc"
        INCLUDE "inc/donnees-police.inc"
        INCLUDE "inc/donnees-texte.inc"
        INCLUDE "inc/donnees-musique.inc"
        INCLUDE "inc/fin.inc"
