; =====================================================================
;  DÉMO 11 (EXPÉRIENCE) : bandes de couleur sur TOUTE la largeur de l'écran
;  Exemple ORIGINAL du dépôt alice32-tech-ref, syntaxe DASM.
;  CLOADM puis EXEC 13312. ESPACE = autre méthode, ENTRÉE = BASIC.
;
;  Les bandes viennent du registre MAT (couleur de la marge), changé une
;  fois par rangée (640 µs : réglage stable sur machine réelle, S26).
;  Pour qu'elles apparaissent aussi DANS l'écran :
;   1. 80 colonnes (image HIRES) : d'après l'émulation de MAME (S25), le
;      fond de chaque cellule 80 colonnes EST la couleur de la marge ;
;   2. 40 colonnes : fond d'espaces « masqués » (octet B bit 2, PAT
;      bit 3 = 1), de fond BLEU, texte normal par-dessus.
;  Résultats sur Alice 32 réelle (S26) : méthode 1 = les bandes passent
;  derrière l'image ; méthode 2 (fond noir à l'essai précédent) = les
;  bandes restent dans la bordure, le fond masqué reste noir. Le fond est
;  maintenant bleu : bleu à l'écran => une cellule masquée montre son
;  propre fond (et non la marge) ; noir => elle est forcée au noir.
; =====================================================================
        PROCESSOR 6803

AVEC_MUSIQUE EQU 0
SANS_PALETTE EQU 1
V_FINRAM EQU FINPROG

        ORG $3400
DEBUT   jmp  DEMARRE
PRINCIPAL
        clr  P11_M
        jsr  P11_INIT
P11     jsr  VSYNC
        sei
        jsr  R_DEPART
        ldd  #0
        std  P11_C
        ldaa #29
        staa P11_I
        ldaa P11_PH
        staa P11_K
P11A    ldd  P11_C
        jsr  R_ATT
        ldab P11_K
        andb #7
        ldx  #P11_COUL
        abx
        ldaa 0,x
        ldab #IND_MAT
        jsr  R_IND
        inc  P11_K
        ldd  P11_C
        addd #640
        std  P11_C
        dec  P11_I
        bne  P11A
        ldaa #$28            ; marge noire jusqu'à la trame suivante
        ldab #IND_MAT
        jsr  R_IND
        cli
        inc  P11_T           ; les bandes descendent d'une rangée toutes les 4 images
        ldaa P11_T
        anda #3
        bne  P11B
        dec  P11_PH
P11B    jsr  CONTROLE
        beq  P11
        ldaa P11_M
        eora #1
        staa P11_M
        jsr  P11_INIT
        bra  P11

; --- préparer l'écran de la méthode P11_M ------------------------------
P11_INIT
        tst  P11_M
        bne  P11_40
        ldx  #IMAGE          ; 1. image HIRES en 80 colonnes
        jsr  AFF_IMAGE
        jsr  ATTEND
        ldaa #C_VRM          ; INASS ne remet pas forcément VRM
        staa XR0
        rts
P11_40  jsr  INITECRAN       ; 2. 40 colonnes
        ldaa #$6F            ; PAT : valeur de la ROM + bit 3 (masquage actif)
        ldab #3
        jsr  ECRIND
        jsr  ATTEND          ; remplir la page d'espaces MASQUÉS (CLF)
        ldaa #$20
        staa R1
        ldaa #$04            ; B : G0 + masquage (bit 2)
        staa R2
        ldaa #$74            ; A : fond BLEU (pour voir ce qu'affiche une
        staa R3              ; cellule masquée : son fond ? la marge ?)
        clr  R6
        clr  R7
        ldaa #C_CLF
        staa XR0
        ldx  #2500
P11W    dex
        bne  P11W
        ldaa #C_NOP
        staa XR0
        ldaa #12             ; texte normal (non masqué) par-dessus
        staa P11_Y
        ldx  #P11_TXT
P11T    ldaa P11_Y
        staa TXY
        pshx
        ldaa #$70
        ldab #6
        jsr  TEXTE
        pulx
        inc  P11_Y
        inc  P11_Y
        ldaa P11_Y
        cmpa #22
        bne  P11T
        clr  TXY
        ldx  #P11_TIT
        ldaa #$70
        clrb
        jmp  TEXTE

P11_COUL dc.b $29,$2B,$2A,$2E,$2C,$2D,$2F,$2B   ; MAT : couleurs de marge
P11_TXT dc.b " BANDES DERRIERE LE TEXTE ",0
P11_TIT dc.b " 40 COL. : FOND MASQUE BLEU = MARGE ?",0
P11_C   dc.w 0
P11_I   dc.b 0
P11_K   dc.b 0
P11_M   dc.b 0
P11_PH  dc.b 0
P11_T   dc.b 0
P11_Y   dc.b 0

        INCLUDE "inc/commun.inc"
        INCLUDE "inc/raster.inc"
        INCLUDE "inc/image.inc"
        INCLUDE "inc/donnees-image.inc"
        INCLUDE "inc/fin.inc"
