; =====================================================================
;  partie-scroll.inc : scrolltext horizontal au point près
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;
;  Le programme principal définit AVANT l'inclusion :
;    S_DBL   EQU 1   ; 1 = double hauteur + double largeur (20 tuiles)
;                    ; 0 = taille normale (40 tuiles), si le double ne
;                    ;     s'affiche pas correctement sur l'émulateur
;    VITESSE EQU 2   ; points (de tuile) par image
;  PARTIE3 n'est assemblée que si partie-logo.inc est inclus AVANT (logo
;  fixe en haut de l'écran) ; sinon seul le moteur (S_INIT, S_AVANCE,
;  S_ENVOI) est disponible, comme pour partie-combo.inc.
;
;  Principe (doc 13 §10 « Scrolltext horizontal ») : la rangée de texte
;  est faite de S_N caractères redéfinis consécutifs (codes 64…) ; leurs
;  tranches sont gardées en RAM (SLIG, 7 lignes de S_N octets, bit 0 =
;  point de gauche) ; à chaque image on décale ces lignes d'un point
;  (ROR en chaîne, de droite à gauche) en faisant entrer la colonne
;  suivante du caractère courant, puis on renvoie les 7 x S_N tranches
;  par OCT avec incrémentation (X = 4 x tranche + (code & 3)).
;  Coût (S_DBL = 1, VITESSE = 2) : ~10 ms par image avec les barres.
;  Statut : [C] non testé sur machine réelle.
; =====================================================================

        IF S_DBL
S_N     EQU 20
S_B     EQU B_GP0+$0A        ; G'0 + double hauteur (bit 1) + double largeur (bit 3)
        ELSE
S_N     EQU 40
S_B     EQU B_GP0
        ENDIF
S_CODE0 EQU 64               ; premier code des tuiles du texte
S_Y     EQU 22               ; rangée mémoire du texte (rangée d'écran 14)

        IFCONST L_TUILES
PARTIE3 clra
        jsr  EFFACE
        ldaa #8
        jsr  ECRROR
        clr  TXY
        ldx  #TITRE3
        ldaa #$70
        clrb
        jsr  TEXTE
; logo fixe (rangées de carte 24-30 -> rangées mémoire 10-16)
        clr  LP
        jsr  L_TUILES
        ldaa #LOGO_M0
        staa LM
P3L     ldaa LM
        jsr  L_PREP
        ldaa LM
        suba #LOGO_M0-10
        jsr  L_ECR
        inc  LM
        ldaa LM
        cmpa #LOGO_M0+LOGO_H
        bne  P3L
; textes fixes (jeu G0)
        ldaa #28
        staa TXY
        ldx  #CREDIT1
        ldaa #$60            ; cyan sur noir
        ldab #4
        jsr  TEXTE
        ldaa #30
        staa TXY
        ldx  #CREDIT2
        ldaa #$30            ; jaune sur noir
        ldab #4
        jsr  TEXTE
        jsr  S_INIT
; --- boucle d'image ---
P3B     jsr  VSYNC
        jsr  S_ENVOI         ; d'abord les tuiles (pendant le retour de trame)
        jsr  S_CASES         ; couleurs qui tournent
        jsr  S_BARRES        ; barres de dégradé au-dessus et au-dessous
        REPEAT VITESSE
        jsr  S_AVANCE
        REPEND
        inc  SPH
        jsr  CONTROLE
        bne  P3F
        ldaa SFIN
        beq  P3B
P3F     rts
        ENDIF

; --- préparer le texte : tuiles vides, lignes en RAM à zéro, début du texte
S_INIT
        ldaa #S_CODE0
        staa TMPC
P3V     ldx  #TRAMES         ; 10 octets nuls
        ldaa TMPC
        jsr  DEFCAR
        inc  TMPC
        ldaa TMPC
        cmpa #S_CODE0+S_N
        bne  P3V
        ldx  #SLIG
P3Z     clr  0,x
        inx
        cpx  #SLIG+7*S_N
        bne  P3Z
        ldx  #SCROLLTXT
        stx  STPTR
        clr  SCOLS
        clr  SFIN
        clr  SPH
        rts

; --- décaler le texte d'un point -----------------------------------------
S_AVANCE
        ldaa SCOLS
        bne  SA2
SA0     ldx  STPTR           ; caractère suivant
        ldab 0,x
        bne  SA1
        ldaa #1              ; fin du texte : on le signale et on reboucle
        staa SFIN
        ldx  #SCROLLTXT
        stx  STPTR
        bra  SA0
SA1     inx
        stx  STPTR
        subb #$20
        clra
        asld
        asld
        asld                 ; 8 octets par caractère
        addd #POLICE
        std  TMPW
        ldx  TMPW
XX      SET 0
        REPEAT 7
        ldaa XX,x
        staa SGLY+XX
XX      SET XX+1
        REPEND
        ldaa 7,x             ; largeur (points, espace compris)
        staa SCOLS
SA2     dec  SCOLS
        ldx  #SLIG
        clr  SLN
SA3     ldab SLN
        pshx
        ldx  #SGLY
        abx
        lsr  0,x             ; C = colonne la plus à gauche du caractère
        pulx                 ; (PULX, LDX et ABX ne touchent pas à C)
XX      SET S_N-1
        REPEAT S_N           ; de droite à gauche : bit 0 -> C -> bit 7 du voisin
        ror  XX,x
XX      SET XX-1
        REPEND
        ldab #S_N
        abx
        inc  SLN
        ldab SLN
        cmpb #7
        bne  SA3
        rts

; --- renvoyer les tranches 1 à 7 des S_N tuiles ---------------------------
S_ENVOI clr  SJ
SE1     jsr  ATTEND
        ldaa SJ
        adda #S_CODE0/4
        staa R4              ; tampon des codes 64+4j à 67+4j
        ldaa #$C4            ; bloc 3, X = 4 (tranche 1, code & 3 = 0)
        staa R5
        ldaa #C_OCTAI
        staa R0
        ldab SJ
        aslb
        aslb
        ldx  #SLIG
        abx
        ldaa #7
        staa SCPT
SE2
XX      SET 0
        REPEAT 4
        ldaa XX,x
        tst  R0
        bmi  .-3
        staa XR1             ; OCT : X de l'EF9345 avance de 1
XX      SET XX+1
        REPEND
        ldab #S_N
        abx
        dec  SCPT
        bne  SE2
        inc  SJ
        ldaa SJ
        cmpa #S_N/4
        bne  SE1
        rts

; --- écrire les cases du texte avec des couleurs qui tournent -------------
S_CASES ldaa #S_Y
        bsr  S_RANG
        IF S_DBL
        ldaa #S_Y+1          ; double hauteur : même code sur la rangée suivante
        bsr  S_RANG
        ENDIF
        rts
S_RANG  psha
        jsr  ATTEND
        pula
        staa R6
        clr  R7
        ldaa #S_B
        staa R2
        ldaa #C_KRF
        staa R0
        ldab SPH
        lsrb
        lsrb
        andb #7
        ldx  #SCOUL
        abx
        ldaa #S_N
        staa SCPT
        ldab #S_CODE0
SR1     ldaa 0,x             ; attribut de la colonne
SR2     tst  R0
        bmi  SR2
        stab R1
        staa XR3
        IF S_DBL
SR3     tst  R0              ; double largeur : même code dans la case X+1
        bmi  SR3
        stab R1
        staa XR3
        ENDIF
        inx
        incb
        dec  SCPT
        bne  SR1
        rts

; --- deux barres de dégradé ---------------------------------------------
S_BARRES
        ldaa SPH
        asla
        staa BV
        ldaa #3
        staa BDV
        ldaa #S_Y-2
        jsr  BARRE
        ldaa SPH
        asla
        nega
        staa BV
        ldaa #-3
        staa BDV
        ldaa #S_Y+3
        jmp  BARRE

; couleurs du texte (attribut A : premier plan, fond noir), cycle de 8
SCOUL
        REPEAT [S_N+8]/8+1
        dc.b $10,$30,$70,$30,$10,$50,$40,$50
        REPEND

TITRE3  dc.b " ALICE 32 DEMO - 3/3 : SCROLLTEXT",0
CREDIT1 dc.b "EF9345 + 6803 A 1 MHZ, 8 KO DE RAM",0
CREDIT2 dc.b "ESPACE : SUITE   ENTREE : BASIC",0

STPTR   dc.w 0
SGLY    ds.b 7
SCOLS   dc.b 0
SFIN    dc.b 0
SPH     dc.b 0
SLN     dc.b 0
SJ      dc.b 0
SCPT    dc.b 0
