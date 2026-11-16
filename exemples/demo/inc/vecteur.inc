; =====================================================================
;  vecteur.inc : 3D fil de fer en mode 80 colonnes « mosaïque » 160 x 125
;  Exemple ORIGINAL du dépôt alice32-tech-ref (syntaxe DASM, 6803).
;  Le programme principal définit SANS_PALETTE et inclut ce fichier
;  après commun.inc, puis donnees-persp.inc et fin.inc.
;
;  Le mode (doc 04 §8, doc 13 §3.10) : en 80 colonnes, une cellule 6 x 10
;  dont l'octet C a le bit 7 à 1 est une MOSAÏQUE de 10 sous-blocs de
;  3 x 2 pixels (2 colonnes x 5 bandes) : 160 x 125 « points » presque
;  carrés. Bit n du mot de 10 bits = bande n/2, moitié gauche (n pair) ou
;  droite (n impair) ; bits 0-6 = C, bits 7-9 = bits 1-3 du quartet A ;
;  bit 0 de A (D) = couleur du trait (DOR : vert ou blanc), fond = marge.
;  [B : d'après la fiche et l'émulation EF9345 de MAME, non vu sur machine]
;
;  Méthode :
;  - une COPIE de la fenêtre en RAM (64 cellules x 20 rangées, 2 octets
;    par cellule : le mot de 10 bits, bit 15 = « à envoyer ») ;
;  - à chaque image : on efface en RAM les cellules de l'image précédente
;    (liste ANCIENNE), on trace les arêtes en RAM (Bresenham au point
;    près, on note chaque cellule nouvellement touchée dans la liste
;    NOUVELLE), puis on envoie à l'EF9345 par KRL chaque cellule des deux
;    listes UNE SEULE FOIS, avec son contenu final : pas de scintillement ;
;  - 3 rotations (Y, X, Z) par multiplications signées 8 x 8 (MUL),
;    perspective par une table 1/z.
;  Coût mesuré dans le simulateur : voir README.md.
;  Statut : [C] non testé sur machine réelle.
; =====================================================================

V_LARG  EQU 64               ; largeur de la fenêtre en cellules (128 points)
V_HAUT  EQU 20               ; hauteur en rangées (100 points)
V_RB    EQU 128              ; octets par rangée de la copie (64 x 2)
V_C0    EQU 8                ; première colonne (sur 80) de la fenêtre
V_Y0    EQU 10               ; première rangée mémoire (8 = haut du corps)
V_MX    EQU 64               ; centre en points
V_MY    EQU 50
M3_CX   EQU V_MX             ; paramètres de math3d.inc
M3_CY   EQU V_MY
M3_W    EQU 2*V_LARG
M3_H    EQU 5*V_HAUT
M3_X15  EQU 0
V_LMAX  EQU 256              ; cellules au plus par liste
V_DUREE EQU 183              ; un objet pendant 183 x 65,5 ms = 12 s

; --- zones de travail (après le programme) --------------------------------
V_COPIE EQU [FINPROG+255]&$FF00   ; V_HAUT x V_RB octets
V_LA    EQU V_COPIE+V_HAUT*V_RB   ; liste A (pointeurs)
V_LB    EQU V_LA+2*V_LMAX         ; liste B
V_PX    EQU V_LB+2*V_LMAX         ; 16 x : abscisses projetées ($FF = hors fenêtre)
V_PY    EQU V_PX+16               ; 16 x : ordonnées
V_FINRAM EQU V_PY+16

; =====================================================================
PARTIE5 clra                 ; 0 = 80 x 25 (mode HIRES du BASIC)
        staa TECRAN
        jsr  INASS           ; DOR = $FA : couleur 0 vert, couleur 1 blanc
        clr  TXY
        ldx  #V_TITRE
        ldaa #1              ; blanc
        clrb
        jsr  TEXTE80
        ldaa #31
        staa TXY
        ldx  #V_AIDE
        clra                 ; vert
        ldab #20
        jsr  TEXTE80
; copie de la fenêtre à zéro, listes vides
        ldx  #V_COPIE
V5A     clr  0,x
        inx
        cpx  #V_COPIE+V_HAUT*V_RB
        bne  V5A
        ldx  #V_LA
        stx  V_ANC
        stx  V_ANCF          ; ancienne liste vide
        ldx  #V_LB
        stx  V_NOUV
        ldx  #OBJ_CUBE
        stx  V_OBJ
V5NOUV  ldd  TICKS
        addd #V_DUREE
        std  V_FIN
        jsr  V_CHOISIT
; --- boucle d'image ---
V5B     jsr  V_IMAGE
        jsr  CONTROLE        ; ENTRÉE quitte
        bne  V5SUIV          ; ESPACE : objet suivant
        ldd  TICKS
        subd V_FIN
        bmi  V5B
V5SUIV  ldx  V_OBJ           ; objet suivant (liste circulaire)
        cpx  #OBJ_CUBE
        bne  V5S1
        ldx  #OBJ_VAIS
        bra  V5S2
V5S1    ldx  #OBJ_CUBE
V5S2    stx  V_OBJ
        bra  V5NOUV

; =====================================================================
;  Une image
; =====================================================================
V_IMAGE jsr  V_ANGLES
        jsr  V_TRANSF
; 1. effacer en RAM les cellules de l'image précédente (et les marquer)
        ldx  V_ANC
V1      cpx  V_ANCF
        beq  V2
        stx  V_P
        ldx  0,x
        ldd  #$8000          ; vide, « à envoyer »
        std  0,x
        ldx  V_P
        inx
        inx
        bra  V1
; 2. tracer les arêtes
V2      ldx  V_NOUV
        stx  V_NPTR
        ldd  V_NOUV
        addd #2*V_LMAX
        std  V_NFIN
        ldx  V_ARET
        ldaa V_NA
        staa V_CPT
V2A     stx  V_P
        ldab 0,x             ; sommet de départ
        ldx  #V_PX
        abx
        ldaa 0,x
        cmpa #$FF
        beq  V2S
        staa L_X0
        ldaa 16,x
        staa L_Y0
        ldx  V_P
        ldab 1,x             ; sommet d'arrivée
        ldx  #V_PX
        abx
        ldaa 0,x
        cmpa #$FF
        beq  V2S
        staa L_X1
        ldaa 16,x
        staa L_Y1
        jsr  LIGNE
V2S     ldx  V_P
        inx
        inx
        dec  V_CPT
        bne  V2A
; 3. envoyer : d'abord la nouvelle liste, puis ce qui reste de l'ancienne
        ldx  V_NOUV
V3      cpx  V_NPTR
        beq  V4
        stx  V_P
        ldx  0,x
        jsr  V_ENVOI
        ldx  V_P
        inx
        inx
        bra  V3
V4      ldx  V_ANC
V4A     cpx  V_ANCF
        beq  V5
        stx  V_P
        ldx  0,x
        tst  0,x             ; encore « à envoyer » : cellule devenue vide
        bpl  V4B
        jsr  V_ENVOI
V4B     ldx  V_P
        inx
        inx
        bra  V4A
; 4. la nouvelle liste devient l'ancienne
V5      ldx  V_NOUV
        ldd  V_ANC
        std  V_NOUV
        stx  V_ANC
        ldx  V_NPTR
        stx  V_ANCF
        rts

; =====================================================================
;  Envoyer la cellule X (pointeur dans la copie) par KRL, effacer sa marque
; =====================================================================
V_ENVOI stx  V_E
        ldaa V_E             ; rangée = (décalage >> 7)
        suba #V_COPIE>>8
        asla
        ldab V_E+1
        bpl  VE1
        inca
VE1     adda #V_Y0
        staa V_EY
        ldab V_E+1           ; colonne = (décalage & $7F) >> 1
        andb #$7F
        lsrb
        addb #V_C0           ; colonne sur 80
        lsrb                 ; R7 = colonne / 2, parité dans le bit 7
        bcc  VE2
        orab #$80
VE2     stab V_EX
        ldd  0,x             ; A = bits 15-8, B = bits 7-0
        anda #$7F
        staa 0,x             ; marque effacée
        asld                 ; A = bits 9-7 du mot
        anda #7
        asla                 ; -> bits 3-1 du quartet A
        oraa V_COUL          ; bit 0 : D (couleur)
        tab
        aslb
        aslb
        aslb
        aslb
        aba                  ; quartet répété (haut et bas de R3)
        ldab 1,x
        orab #$80            ; C : bit 7 = mosaïque
VE3     tst  R0
        bmi  VE3
        stab R1
        staa R3
        ldaa V_EY
        staa R6
        ldaa V_EX
        staa R7
        ldaa #C_KRL
        staa XR0             ; KRL avec exécution
        rts

; =====================================================================
;  Ajouter la cellule X à la nouvelle liste si elle est encore vide
; =====================================================================
FRAIS   ldaa 0,x
        anda #$03
        oraa 1,x
        bne  FR1
        stx  V_E
        ldx  V_NPTR
        cpx  V_NFIN
        beq  FR0             ; liste pleine : tant pis
        ldd  V_E
        std  0,x
        inx
        inx
        stx  V_NPTR
FR0     ldx  V_E
FR1     rts

; =====================================================================
;  Tracer un segment (L_X0, L_Y0) - (L_X1, L_Y1) dans la copie (Bresenham)
;  Coordonnées dans la fenêtre : x 0-127, y 0-99.
;  État : X = cellule, L_M = masque 16 bits du point, L_H = moitié (0/1),
;  L_B = bande (0-4).
; =====================================================================
LIGNE   ldaa L_X1            ; toujours de gauche à droite
        cmpa L_X0
        bhs  LG1
        ldab L_X0
        staa L_X0
        stab L_X1
        ldaa L_Y0
        ldab L_Y1
        staa L_Y1
        stab L_Y0
LG1     ldaa L_X1
        suba L_X0
        staa L_DX
        clr  L_DIR           ; 0 = vers le bas
        ldaa L_Y1
        suba L_Y0
        bcc  LG2
        nega
        inc  L_DIR           ; 1 = vers le haut
LG2     staa L_DY
; position de départ
        ldaa L_Y0
        clrb
LG3     cmpa #5              ; rangée = y / 5, bande = y mod 5
        blo  LG4
        suba #5
        incb
        bra  LG3
LG4     staa L_B
        tba
        clrb
        lsrd                 ; D = rangée x 128
        addd #V_COPIE
        std  V_E
        ldx  V_E
        ldab L_X0
        andb #$FE            ; 2 octets par cellule
        abx
        ldab L_X0
        andb #1
        stab L_H
        ldaa L_B             ; masque = 1 << (2 x bande + moitié)
        asla
        adda L_H
        staa L_N
        ldd  #1
LG5     tst  L_N
        beq  LG6
        asld
        dec  L_N
        bra  LG5
LG6     std  L_M
        jsr  FRAIS
        ldaa L_DX
        cmpa L_DY
        blo  LY
; --- x principal : deux copies de la boucle (moitié gauche / droite) ---
        inca
        staa L_N             ; DX + 1 points
        ldaa L_DX
        lsra
        staa L_E
        tst  L_H
        bne  LXD
LXG     ldd  L_M             ; point dans la moitié gauche
        oraa 0,x
        orab 1,x
        std  0,x
        dec  L_N
        beq  LFIN
        ldd  L_M             ; x + 1 : moitié droite de la même cellule
        asld
        std  L_M
        ldaa L_E
        suba L_DY
        bcc  LXG1
        adda L_DX
        staa L_E
        jsr  YPAS
        bra  LXD
LXG1    staa L_E
LXD     ldd  L_M             ; point dans la moitié droite
        oraa 0,x
        orab 1,x
        std  0,x
        dec  L_N
        beq  LFIN
        ldd  L_M             ; x + 1 : moitié gauche de la cellule suivante
        lsrd
        std  L_M
        inx
        inx
        jsr  FRAIS
        ldaa L_E
        suba L_DY
        bcc  LXD1
        adda L_DX
        staa L_E
        jsr  YPAS
        bra  LXG
LXD1    staa L_E
        bra  LXG
LFIN    rts
; --- y principal : une boucle par sens ---
LY      ldaa L_DY
        inca
        staa L_N
        ldaa L_DY
        lsra
        staa L_E
        tst  L_DIR
        bne  LYH
LYB     ldd  L_M             ; vers le bas
        oraa 0,x
        orab 1,x
        std  0,x
        dec  L_N
        beq  LFIN
        inc  L_B
        ldaa L_B
        cmpa #5
        beq  LYB1
        ldd  L_M
        asld
        asld
        std  L_M
        bra  LYB2
LYB1    jsr  YP2
LYB2    ldaa L_E
        suba L_DX
        bcc  LYB3
        adda L_DY
        staa L_E
        jsr  XPAS
        bra  LYB
LYB3    staa L_E
        bra  LYB
LYH     ldd  L_M             ; vers le haut
        oraa 0,x
        orab 1,x
        std  0,x
        dec  L_N
        beq  LFIN
        dec  L_B
        bmi  LYH1
        ldd  L_M
        lsrd
        lsrd
        std  L_M
        bra  LYH2
LYH1    jsr  YP4
LYH2    ldaa L_E
        suba L_DX
        bcc  LYH3
        adda L_DY
        staa L_E
        jsr  XPAS
        bra  LYH
LYH3    staa L_E
        bra  LYH

; --- un point vers la droite -------------------------------------------
XPAS    tst  L_H
        bne  XP2
        inc  L_H             ; moitié gauche -> droite : bit suivant
        ldd  L_M
        asld
        std  L_M
        rts
XP2     clr  L_H             ; moitié droite -> cellule suivante, à gauche
        ldd  L_M
        lsrd
        std  L_M
        inx
        inx
        jmp  FRAIS

; --- un point vers le bas ou vers le haut ------------------------------
YPAS    tst  L_DIR
        bne  YP3
        inc  L_B             ; vers le bas
        ldaa L_B
        cmpa #5
        beq  YP2
        ldd  L_M
        asld
        asld
        std  L_M
        rts
YP2     clr  L_B             ; bande 4 -> bande 0 de la rangée suivante
        ldd  L_M
        tab
        clra
        std  L_M
        ldab #V_RB
        abx
        jmp  FRAIS
YP3     dec  L_B             ; vers le haut
        bmi  YP4
        ldd  L_M
        lsrd
        lsrd
        std  L_M
        rts
YP4     ldaa #4              ; bande 0 -> bande 4 de la rangée précédente
        staa L_B
        ldd  L_M
        tba
        clrb
        std  L_M
        stx  V_E
        ldd  V_E
        subd #V_RB
        std  V_E
        ldx  V_E
        jmp  FRAIS

; =====================================================================
;  Texte en 80 colonnes : X = chaîne, B = colonne (0-79), TXY = rangée,
;  A = quartet d'attribut (bit 0 : couleur). KRL + incrémentation : le
;  composant passe seul à la colonne suivante (parité dans le bit 7 de R7).
; =====================================================================
TEXTE80 psha
        jsr  ATTEND
        pula
        staa TMPC
        asla
        asla
        asla
        asla
        oraa TMPC
        staa R3
        lsrb
        bcc  T81
        orab #$80
T81     stab R7
        ldaa TXY
        staa R6
        ldaa #C_KRLI
        staa R0
T82     ldaa 0,x
        beq  T8F
        inx
T83     tst  R0
        bmi  T83
        staa XR1
        bra  T82
T8F     rts

        INCLUDE "inc/math3d.inc"

V_TITRE dc.b " ALICE 32 - MODE HIRES 160 X 125 : 3D FIL DE FER",0
V_AIDE  dc.b "ESPACE : OBJET SUIVANT    ENTREE : BASIC",0

; --- variables -----------------------------------------------------------
V_FIN   dc.w 0
V_ANC   dc.w 0
V_ANCF  dc.w 0
V_NOUV  dc.w 0
V_NPTR  dc.w 0
V_NFIN  dc.w 0
V_E     dc.w 0
L_M     dc.w 0
V_CPT   dc.b 0
V_EX    dc.b 0
V_EY    dc.b 0
L_X0    dc.b 0
L_Y0    dc.b 0
L_X1    dc.b 0
L_Y1    dc.b 0
L_DX    dc.b 0
L_DY    dc.b 0
L_DIR   dc.b 0
L_E     dc.b 0
L_N     dc.b 0
L_H     dc.b 0
L_B     dc.b 0
