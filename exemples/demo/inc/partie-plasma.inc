; =====================================================================
;  partie-plasma.inc : dégradé diagonal puis plasma plein écran
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;
;  Chaque case reçoit par KRF une tuile de trame (0/25/50/75 %) et deux
;  couleurs (attribut A) lues dans la palette TABC/TABA (commun.inc) :
;  64 teintes visibles avec 8 couleurs (doc 13 §10 « Plasma / dégradés »).
;  Plasma : v(x, y) = AX[x + décalage(y)] + BY(y), où AX et BY sont des
;  sommes de sinus recalculées à chaque image ; le décalage par rangée
;  rend le motif non séparable (ondulations).
;  Coût : ~41 cycles par case, 960 cases -> ~40 ms : environ 20 images/s.
;  Statut : [C] non testé sur machine réelle.
; =====================================================================

PARTIE2 clra
        jsr  EFFACE
        ldaa #8
        jsr  ECRROR
        clr  TXY
        ldx  #TITRE2
        ldaa #$70
        clrb
        jsr  TEXTE
; --- phase A : dégradé diagonal qui défile (~4 s) ---
        ldd  TICKS
        addd #61             ; 61 x 65,5 ms = 4 s
        std  PFIN
P2A     ldaa #8
        staa PY
        ldab PT1
        stab PV0
P2A1    ldab PV0
        stab BV
        addb #6              ; décalage d'une rangée à l'autre
        stab PV0
        ldaa #4
        staa BDV
        ldaa PY
        jsr  BARRE
        inc  PY
        ldaa PY
        cmpa #32
        bne  P2A1
        ldaa PT1
        adda #5
        staa PT1
        jsr  CONTROLE
        bne  P2FIN
        ldd  TICKS
        subd PFIN
        bmi  P2A
; --- phase B : plasma (~12 s) ---
        ldd  TICKS
        addd #183
        std  PFIN
P2B     jsr  P_CALC
        jsr  P_DESSINE
        jsr  CONTROLE
        bne  P2FIN
        ldd  TICKS
        subd PFIN
        bmi  P2B
P2FIN   rts

; --- tables de l'image : AXB[0..47], RBV[0..23], ROFF[0..23] --------------
P_CALC  ldaa PT1
        staa PA1
        ldaa PT2
        staa PA2
        ldx  #AXB
        ldaa #48
        staa PCPT
PC1     ldaa PA1
        adda #4
        staa PA1
        staa PC2+2
        ldaa PA2
        adda #7
        staa PA2
        staa PC3+2
PC2     ldaa SINUS           ; SINUS[PA1] (adresse modifiée)
PC3     adda SINUS           ; + SINUS[PA2]
        staa 0,x
        inx
        dec  PCPT
        bne  PC1
        ldaa PT3
        staa PA1
        ldaa PT4
        staa PA2
        ldaa PT6
        staa PA3
        ldx  #RBV
        ldaa #24
        staa PCPT
PC4     ldaa PA1
        adda #5
        staa PA1
        staa PC5+2
        ldaa PA2
        suba #3
        staa PA2
        staa PC6+2
PC5     ldaa SINUS
PC6     adda SINUS
        adda PT5             ; rotation lente de la palette
        staa 0,x             ; RBV[y]
        ldaa PA3
        adda #9
        staa PA3
        staa PC7+2
PC7     ldab SINUS
        lsrb
        lsrb
        lsrb
        lsrb                 ; 0..7
        stab 24,x            ; ROFF[y]
        inx
        dec  PCPT
        bne  PC4
; avancer les phases
        ldaa PT1
        adda #3
        staa PT1
        ldaa PT2
        suba #2
        staa PT2
        ldaa PT3
        adda #2
        staa PT3
        ldaa PT4
        adda #3
        staa PT4
        inc  PT5
        ldaa PT6
        adda #4
        staa PT6
        rts

; --- dessin des 24 rangées ---------------------------------------------
P_DESSINE
        clr  PY
PD1     ldab PY
        ldx  #RBV
        abx
        ldaa 0,x
        staa BV
        ldab 24,x            ; décalage de la rangée
        ldx  #AXB
        abx
        stx  PXR
        jsr  ATTEND
        ldaa PY
        adda #8
        staa R6
        clr  R7
        ldaa #B_GP0
        staa R2
        ldaa #C_KRF
        staa R0
        ldx  PXR
        ldaa #5
        staa PCPT
PD2
XX      SET 0
        REPEAT 8             ; 8 cases déroulées (28 octets chacune)
        ldab XX,x            ; AX[x + décalage]
        addb BV              ; + BY(y)
        stab .+8             ; octet faible de « ldaa TABC »
        stab .+8             ; octet faible de « ldab TABA »
        ldaa TABC
        ldab TABA
        tst  R0
        bmi  .-3
        staa R1
        stab XR3             ; KRF
XX      SET XX+1
        REPEND
        ldab #8
        abx
        dec  PCPT
        beq  PD3
        jmp  PD2
PD3     inc  PY
        ldaa PY
        cmpa #24
        beq  PD4
        jmp  PD1
PD4     rts

TITRE2  dc.b " ALICE 32 DEMO - 2/3 : PLASMA/DEGRADES",0

PFIN    dc.w 0
PXR     dc.w 0
PY      dc.b 0
PV0     dc.b 0
PCPT    dc.b 0
PA1     dc.b 0
PA2     dc.b 0
PA3     dc.b 0
PT1     dc.b 0
PT2     dc.b 64
PT3     dc.b 0
PT4     dc.b 128
PT5     dc.b 0
PT6     dc.b 0
