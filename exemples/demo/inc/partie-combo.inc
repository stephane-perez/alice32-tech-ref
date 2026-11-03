; =====================================================================
;  partie-combo.inc : plasma plein écran + scrolltext par-dessus
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;  À inclure APRÈS partie-plasma.inc et partie-scroll.inc.
;
;  Problème : le plasma complet coûte ~49 ms, le scrolltext doit être
;  renvoyé à chaque image (20 ms) pour rester fluide.
;  Solution : à chaque image, d'abord le scrolltext (tuiles + décalage,
;  ~5 ms), puis le plasma PAR TRANCHES de rangées tant que le compteur du
;  timer ($09, 1 µs) dit qu'il reste du temps avant la trame suivante.
;  Une étape « calcul des tables » (P_CALC) est intercalée à chaque tour.
;  -> texte à 50 images/s, plasma à ~15 images/s.
;  Sous le texte, chaque case prend comme fond la couleur du plasma
;  (couleur de fond de la teinte), et une couleur de texte qui contraste.
;  Statut : [C] non testé sur machine réelle.
; =====================================================================

C_LIM_RANG EQU 15500         ; plus de rangée après 15,5 ms (une rangée ~1,9 ms)
C_LIM_CALC EQU 13000         ; plus de calcul après 13 ms (P_CALC ~4,5 ms)
C_TY0   EQU S_Y-8            ; rangée (0-23) du texte dans le plasma

PARTIE4 clra
        jsr  EFFACE
        ldaa #8
        jsr  ECRROR
        clr  TXY
        ldx  #TITRE4C
        ldaa #$70
        clrb
        jsr  TEXTE
        jsr  S_INIT
        ldaa #24             ; 24 = étape « calcul des tables »
        staa CRY
; --- boucle d'image ---
C4B     jsr  VSYNC
        ldd  TCNT
        std  CT0             ; début de l'image
        jsr  S_ENVOI         ; tuiles du texte (pendant le retour de trame)
        REPEAT VITESSE
        jsr  S_AVANCE
        REPEND
        inc  SPH
C4R     ldaa CRY             ; plasma par tranches, tant qu'il reste du temps
        cmpa #24
        bne  C4R1
        ldd  TCNT
        subd CT0
        subd #C_LIM_CALC
        bcc  C4X             ; temps écoulé >= limite : on s'arrête
        jsr  P_CALC
        clr  CRY
        bra  C4R
C4R1    ldd  TCNT
        subd CT0
        subd #C_LIM_RANG
        bcc  C4X
        jsr  C_RANG
        bra  C4R
C4X     jsr  CONTROLE
        bne  C4F
        ldaa SFIN
        beq  C4B
C4F     rts

; --- une rangée : plasma, ou texte sur fond de plasma ---------------------
C_RANG  ldaa CRY
        staa PY
        cmpa #C_TY0
        beq  CR_T
        IF S_DBL
        cmpa #C_TY0+1
        beq  CR_T
        ENDIF
        jsr  P_RANG
        bra  CR_N
CR_T    jsr  T_RANG
CR_N    inc  CRY
        rts

; --- rangée de texte : codes du scrolltext, fond = couleur du plasma -------
T_RANG  ldab PY
        ldx  #RBV
        abx
        ldaa 0,x
        staa BV
        ldab 24,x
        ldx  #AXB
        abx
        stx  PXR
        jsr  ATTEND
        ldaa PY
        adda #8
        staa R6
        clr  R7
        ldaa #S_B
        staa R2
        ldaa #C_KRF
        staa R0
        ldx  PXR
        ldab #S_CODE0
        stab TCODE
        ldaa #S_N
        staa PCPT
TR1     ldab 0,x             ; teinte du plasma sous la case
        addb BV
        stab TR2+2
TR2     ldaa TABA            ; (adresse modifiée)
        anda #7              ; couleur de fond de la teinte
        pshx
        ldx  #CONTR
        tab
        abx
        oraa 0,x             ; + couleur de texte qui contraste
        pulx
        ldab TCODE
TR3     tst  R0
        bmi  TR3
        stab R1
        staa XR3             ; KRF
        IF S_DBL
TR4     tst  R0              ; double largeur : même code en X+1
        bmi  TR4
        stab R1
        staa XR3
        inx
        ENDIF
        inx
        inc  TCODE
        dec  PCPT
        bne  TR1
        rts

; couleur du texte (premier plan) selon le fond : noir, rouge, vert, jaune,
; bleu, magenta, cyan, blanc
CONTR   dc.b $70,$70,$00,$40,$70,$70,$00,$40

TITRE4C dc.b " ALICE 32 - PLASMA + SCROLL + MUSIQUE",0
CT0     dc.w 0
CRY     dc.b 0
TCODE   dc.b 0
