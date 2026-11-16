; =====================================================================
;  image.inc : afficher une image HIRES 160 x 125 (80 colonnes, mosaïque)
;  produite par outils/img2hires.py
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;
;  Entrée : X = image (DOR, MAT, puis 25 rangées x 40 x (C pair, C impair,
;  attributs)). Les données sont déjà dans le rangement de la mémoire de
;  l'EF9345 (docs/04 §8.1) : on écrit l'octet d'attributs dans R3 une fois
;  par paire, puis les deux codes par KRL avec incrémentation (le
;  composant prend le quartet haut de R3 pour la colonne paire, le bas
;  pour l'impaire, et passe seul à la colonne suivante).
;  Durée : ~2 000 KRL, environ 60 ms.
;  Statut : [C] non testé sur machine réelle.
; =====================================================================

AFF_IMAGE
        stx  IM_P
        clra                 ; 80 colonnes
        staa TECRAN
        jsr  INASS
        ldx  IM_P
        ldaa 0,x             ; DOR : couleur d'encre
        ldab #4
        jsr  ECRIND
        ldx  IM_P
        ldaa 1,x             ; MAT : fond (= marge)
        ldab #IND_MAT
        jsr  ECRIND
        ldx  IM_P
        inx
        inx
        clr  IM_R
IM1     jsr  ATTEND
        ldaa IM_R            ; rangée 0 = rangée de service (Y = 0),
        beq  IM2             ; puis Y = 8 à 31
        adda #7
IM2     staa R6
        clr  R7              ; colonne 0, paire
        ldaa #$51            ; KRL écriture + incrémentation
        staa R0
        ldab #40
IM3     ldaa 2,x             ; attributs de la paire
IM4     tst  R0
        bmi  IM4
        staa R3
        ldaa 0,x             ; colonne paire
        staa XR1
        ldaa 1,x             ; colonne impaire
IM5     tst  R0
        bmi  IM5
        staa XR1
        inx
        inx
        inx
        decb
        bne  IM3
        inc  IM_R
        ldaa IM_R
        cmpa #25
        bne  IM1
        rts

IM_P    dc.w 0
IM_R    dc.b 0
