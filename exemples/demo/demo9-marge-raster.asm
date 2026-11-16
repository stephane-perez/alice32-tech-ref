; =====================================================================
;  DÉMO 9 (EXPÉRIENCE) : bandes de couleur dans la marge (« overscan »)
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM.
;  CLOADM puis EXEC 13312. ESPACE = réglage suivant (4 réglages), ENTRÉE = BASIC.
;
;  Après la synchro trame, le registre MAT (couleur de la marge) est
;  changé à intervalles fixes, mesurés au compteur du timer (1 µs) :
;    réglage 1 : 29 changements, un par rangée (640 µs) ;
;    réglage 2 : 125 changements, toutes les 2 lignes TV (128 µs) ;
;    réglage 3 : 140 changements aussi vite que possible (test de BUSY
;                compris : ~125 µs, le 6803 ne suit pas une ligne TV) ;
;    réglage 4 : rafale déroulée SANS test de BUSY à partir de 8 ms :
;                240 changements, un toutes les 10 µs (6 par ligne TV).
;                Les écritures faites pendant une suspension de
;                l'EF9345 (~104 µs par rangée) peuvent se perdre.
;  Ce qu'il faut regarder : des bandes horizontales dans la marge ?
;  nettes ou tremblantes ? de quelle hauteur (une rangée = 10 lignes) ?
;  Les commandes de l'EF9345 (IND compris) sont suspendues ~104 µs par
;  rangée : on s'attend à des bandes par rangée, pas par ligne [C].
;  Interruptions masquées pendant la trame. NON testé sur machine réelle.
; =====================================================================
        PROCESSOR 6803

AVEC_MUSIQUE EQU 0
SANS_PALETTE EQU 1
V_FINRAM EQU FINPROG

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        ldaa #$70
        jsr  EFFACE
        clr  TXY
        ldx  #T9_1
        ldaa #$70
        clrb
        jsr  TEXTE
        ldaa #30
        staa TXY
        ldx  #T9_2
        ldaa #$30
        ldab #4
        jsr  TEXTE
        clr  P9_M
        jsr  P9_REGLE
P9      jsr  VSYNC
        sei
        jsr  R_DEPART
        ldaa P9_M
        cmpa #3
        bne  P9R
        jmp  P9_RAFALE
P9R
        ldd  P9_DEB
        std  P9_C
        ldd  P9_NB
        std  P9_I
        clr  P9_COUL
P9A     ldd  P9_C
        jsr  R_ATT
        ldaa P9_COUL
        anda #7
        oraa #$28            ; valeur de MAT de la ROM, couleur de marge
        ldab #IND_MAT
        jsr  R_IND
        inc  P9_COUL
        ldd  P9_C
        addd P9_PAS
        std  P9_C
        ldx  P9_I
        dex
        stx  P9_I
        bne  P9A
P9FIN   ldaa #$28            ; marge noire jusqu'à la trame suivante
        ldab #IND_MAT
        jsr  R_IND
        cli
        jsr  CONTROLE
        beq  P9
        inc  P9_M
        ldaa P9_M
        cmpa #4
        bne  P9B
        clr  P9_M
P9B     jsr  P9_REGLE
        bra  P9

; --- réglage P9_M : début, pas, nombre ; nom affiché ---------------------
P9_REGLE
        ldab P9_M
        ldaa #6
        mul
        addd #P9_TAB
        std  TMPW
        ldx  TMPW
        ldd  0,x
        std  P9_DEB
        ldd  2,x
        std  P9_PAS
        ldd  4,x
        std  P9_NB
        ldab P9_M
        ldaa #32
        mul
        addd #P9_NOMS
        std  TMPW
        ldx  TMPW
        ldaa #14
        staa TXY
        ldaa #$60
        ldab #4
        jmp  TEXTE

; --- réglage 4 : rafale, 10 cycles par changement --------------------------
P9_RAFALE
        ldd  #8000
        jsr  R_ATT
        ldab #$80+IND_MAT
XX      SET 0
        REPEAT 240
        ldaa #$28+[XX&7]     ; 2
        staa R1              ; 4
        stab XR0             ; 4  BUSY non testé
XX      SET XX+1
        REPEND
        jmp  P9FIN

P9_TAB  dc.w 0,640,29        ; début (µs après la synchro), pas, nombre
        dc.w 1000,128,125
        dc.w 1000,1,140
        dc.w 0,0,1
P9_NOMS dc.b "UNE BANDE PAR RANGEE (640 US) ",0
        dc.b "TOUTES LES 2 LIGNES (128 US)  ",0
        dc.b "AUSSI VITE QUE POSSIBLE       ",0
        dc.b "RAFALE SANS BUSY (10 US)      ",0
T9_1    dc.b " ALICE 32 - EXPERIENCE : MARGE RASTER",0
T9_2    dc.b "ESPACE : REGLAGE  ENTREE : BASIC",0
P9_DEB  dc.w 0
P9_PAS  dc.w 0
P9_NB   dc.w 0
P9_C    dc.w 0
P9_I    dc.w 0
P9_M    dc.b 0
P9_COUL dc.b 0

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/raster.inc"
        INCLUDE "inc/fin.inc"
