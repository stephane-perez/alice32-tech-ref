; =====================================================================
;  DÉMO 10 (EXPÉRIENCE) : 40 et 80 colonnes dans la même image ?
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM.
;  CLOADM puis EXEC 13312. ESPACE = descendre la coupure, ENTRÉE = BASIC.
;
;  Le haut de la page (rangées mémoire 8-19) contient du texte rangé en
;  40 colonnes (blocs 0, 1, 2), le bas (rangées 20-31) du texte rangé en
;  80 colonnes (blocs 0, 2, 4). À chaque trame : TGS = $10 (40 col.)
;  juste après la synchro, puis TGS = $D0 (80 col.) à l'instant
;  « coupure » (µs après la synchro, affiché en haut). ESPACE ajoute
;  640 µs (une rangée).
;  Ce qu'il faut regarder : y a-t-il un instant où le haut est lisible
;  en 40 colonnes ET le bas en 80 colonnes ? La coupure est-elle nette,
;  stable ? Si l'EF9345 ne relit le format qu'en début de trame, tout
;  l'écran sera dans un seul mode [C].
;  DOR = $72 : en 80 colonnes, couleurs vert / blanc ; en 40 colonnes,
;  pas de caractère redéfini utilisé. NON testé sur machine réelle.
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
        ldaa #$72            ; DOR commun aux deux modes
        ldab #4
        jsr  ECRIND
        ldaa #8              ; haut : 40 colonnes
        staa P10_Y
P10A    ldaa P10_Y
        staa TXY
        ldx  #T10_40
        ldaa P10_Y           ; couleurs variées
        anda #7
        bne  P10A1
        inca
P10A1   asla
        asla
        asla
        asla
        ldab #2
        jsr  TEXTE
        inc  P10_Y
        ldaa P10_Y
        cmpa #20
        bne  P10A
P10B    ldaa P10_Y           ; bas : 80 colonnes (KRL)
        staa TXY
        ldx  #T10_80
        clra
        ldab #0
        jsr  TEXTE80
        inc  P10_Y
        ldaa P10_Y
        cmpa #32
        bne  P10B
        ldd  #7680           ; coupure initiale : 12 rangées
        std  P10_COUP
        jsr  P10_AFF
P10     jsr  VSYNC
        sei
        jsr  R_DEPART
        ldaa #$10            ; TGS : 40 colonnes long
        ldab #1
        jsr  R_IND
        ldd  P10_COUP
        jsr  R_ATT
        ldaa #$D0            ; TGS : 80 colonnes long
        ldab #1
        jsr  R_IND
        cli
        jsr  CONTROLE
        beq  P10
        ldd  P10_COUP        ; ESPACE : une rangée plus bas
        addd #640
        std  P10_COUP
        subd #19200          ; au-delà de la trame : retour à 0
        bcs  P10C
        ldd  #0
        std  P10_COUP
P10C    jsr  P10_AFF
        bra  P10

; --- afficher la coupure dans la rangée de service ----------------------
P10_AFF ldd  P10_COUP
        jsr  R_DEC
        clr  TXY
        ldx  #T10_T
        ldaa #$70
        clrb
        jsr  TEXTE
        ldx  #R_TXT
        ldaa #$70
        ldab #30
        jmp  TEXTE

T10_T   dc.b " 40/80 COLONNES - COUPURE A       US",0
T10_40  dc.b "CETTE LIGNE EST EN 40 COLONNES",0
T10_80  dc.b "CETTE LIGNE EST RANGEE EN 80 COLONNES : ELLE N'EST LISIBLE QU'EN MODE 80 (TGS)",0
P10_COUP dc.w 0
P10_Y   dc.b 0

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/raster.inc"
        INCLUDE "inc/fin.inc"
